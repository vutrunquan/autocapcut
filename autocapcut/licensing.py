"""
Licensing and Activation System for AutoCapCut Studio.
Supports:
- 3-day free trial on first run with anti-clock-rollback protection.
- Hardware-bound Machine ID (HWID) across Windows and macOS (Intel & Apple Silicon M).
- Cryptographic HMAC-SHA256 lifetime license key verification.
- Offline and independent activation without requiring a centralized server.
- Built-in payment details and VietQR support for 150k lifetime packages.
"""

import os
import sys
import json
import time
import hmac
import hashlib
import uuid
import base64
import subprocess
from typing import Optional, Dict, Any, Tuple

# Secret salt known only to the AutoCapCut developer/admin key generator
SECRET_SALT = "AutoCapCut_Studio_Lifetime_Secret_2026_x99a_Commercial_Edition"
TRIAL_DURATION_SECONDS = 3 * 24 * 3600  # 3 days in seconds


class LicenseExpiredError(Exception):
    """Raised when the 3-day trial has expired and no lifetime key has been activated."""
    pass


# ----------------------------------------------------------------------
# 1. HARDWARE ID (HWID) GENERATION (Cross-platform Windows & macOS)
# ----------------------------------------------------------------------
def get_raw_hardware_id() -> str:
    """
    Extract a permanent hardware identifier unique to this computer.
    - Windows: MachineGuid from Registry (works on Windows 10/11 including 24H2 without wmic).
    - macOS: IOPlatformUUID from IORegistry (works on Intel and Apple Silicon M1-M4).
    - Fallback: System UUID / MAC address.
    """
    raw_id = ""

    # Windows: Read MachineGuid from Registry
    if sys.platform == "win32":
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Cryptography")
            guid, _ = winreg.QueryValueEx(key, "MachineGuid")
            winreg.CloseKey(key)
            if guid and len(str(guid).strip()) > 10:
                raw_id = f"WIN-{guid.strip()}"
        except Exception:
            pass

    # macOS: Read IOPlatformUUID
    elif sys.platform == "darwin":
        try:
            cmd = "ioreg -rd1 -c IOPlatformExpertDevice | grep -i IOPlatformUUID"
            out = subprocess.check_output(cmd, shell=True, text=True, timeout=3)
            import re
            m = re.search(r'"IOPlatformUUID"\s*=\s*"([^"]+)"', out, re.IGNORECASE)
            if m:
                raw_id = f"MAC-{m.group(1).strip()}"
        except Exception:
            pass

    # Linux: Read /etc/machine-id
    elif sys.platform.startswith("linux"):
        for path in ["/etc/machine-id", "/var/lib/dbus/machine-id"]:
            if os.path.exists(path):
                try:
                    with open(path, "r") as f:
                        raw_id = f"LNX-{f.read().strip()}"
                        break
                except Exception:
                    pass

    # Universal fallback: MAC address + platform node
    if not raw_id:
        node_id = str(uuid.getnode())
        raw_id = f"NODE-{node_id}-{sys.platform}"

    return raw_id


def get_machine_id() -> str:
    """
    Return a clean, human-readable Machine ID format:
    Example: AC-3635-81C2-BEC2
    """
    raw_id = get_raw_hardware_id()
    h = hashlib.sha256(f"HWID_SALT_{raw_id}".encode("utf-8")).hexdigest().upper()
    return f"AC-{h[:4]}-{h[4:8]}-{h[8:12]}"


# ----------------------------------------------------------------------
# 2. KEY GENERATION & CRYPTOGRAPHIC VERIFICATION
# ----------------------------------------------------------------------
def generate_license_key(hwid: str) -> str:
    """
    Admin key generator function:
    Takes Machine ID (e.g. AC-3635-81C2-BEC2) and generates a matching
    lifetime license key (e.g. ACCP-3635-8AB7-844D-3293).
    """
    clean_hwid = hwid.strip().upper().replace("AC-", "").replace("-", "")
    if len(clean_hwid) < 8:
        raise ValueError("Mã máy (Machine ID) không đúng định dạng!")

    sig = hmac.new(
        SECRET_SALT.encode("utf-8"),
        f"LIFETIME:{clean_hwid}".encode("utf-8"),
        hashlib.sha256
    ).hexdigest().upper()

    # Format: ACCP-[HWID_PART]-[SIG_1]-[SIG_2]-[SIG_3]
    return f"ACCP-{clean_hwid[:4]}-{sig[:4]}-{sig[4:8]}-{sig[8:12]}"


def verify_license_key(key: str, hwid: Optional[str] = None) -> bool:
    """
    Verify if a license key is cryptographically valid for a specific HWID.
    """
    if not key or not isinstance(key, str):
        return False

    key = key.strip().upper()
    parts = key.split("-")
    if len(parts) != 5 or parts[0] != "ACCP":
        return False

    target_hwid = (hwid or get_machine_id()).strip().upper().replace("AC-", "").replace("-", "")
    if parts[1] != target_hwid[:4]:
        return False

    expected_sig = hmac.new(
        SECRET_SALT.encode("utf-8"),
        f"LIFETIME:{target_hwid}".encode("utf-8"),
        hashlib.sha256
    ).hexdigest().upper()[:12]

    provided_sig = "".join(parts[2:])
    return hmac.compare_digest(expected_sig, provided_sig)


# ----------------------------------------------------------------------
# 3. STORAGE & ANTI-TAMPERING (Trial tracking & activation state)
# ----------------------------------------------------------------------
def _get_storage_path() -> str:
    """Get the primary encrypted license storage path."""
    if sys.platform == "win32":
        app_data = os.environ.get("APPDATA") or os.path.expanduser("~")
        target_dir = os.path.join(app_data, "AutoCapCut")
    elif sys.platform == "darwin":
        target_dir = os.path.join(os.path.expanduser("~"), "Library", "Application Support", "AutoCapCut")
    else:
        target_dir = os.path.join(os.path.expanduser("~"), ".autocapcut")

    os.makedirs(target_dir, exist_ok=True)
    return os.path.join(target_dir, ".lic_store")


def _read_secondary_stamp() -> Optional[float]:
    """Read hidden secondary first_run timestamp to prevent casual trial deletion."""
    if sys.platform == "win32":
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\AutoCapCut", 0, winreg.KEY_READ)
            val, _ = winreg.QueryValueEx(key, "InitStamp")
            winreg.CloseKey(key)
            if val:
                return float(val)
        except Exception:
            pass
    else:
        sec_path = os.path.expanduser("~/.config/.autocapcut_sys")
        if os.path.exists(sec_path):
            try:
                with open(sec_path, "r") as f:
                    return float(f.read().strip())
            except Exception:
                pass
    return None


def _write_secondary_stamp(timestamp: float):
    """Write hidden secondary first_run timestamp."""
    if sys.platform == "win32":
        try:
            import winreg
            key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\AutoCapCut")
            winreg.SetValueEx(key, "InitStamp", 0, winreg.REG_SZ, str(timestamp))
            winreg.CloseKey(key)
        except Exception:
            pass
    else:
        try:
            sec_dir = os.path.expanduser("~/.config")
            os.makedirs(sec_dir, exist_ok=True)
            with open(os.path.join(sec_dir, ".autocapcut_sys"), "w") as f:
                f.write(str(timestamp))
        except Exception:
            pass


def _encrypt_dict(data: dict) -> str:
    raw_json = json.dumps(data, ensure_ascii=False)
    # Simple XOR cipher keyed with SECRET_SALT and encoded in base64
    key_bytes = SECRET_SALT.encode("utf-8")
    json_bytes = raw_json.encode("utf-8")
    xored = bytes([b ^ key_bytes[i % len(key_bytes)] for i, b in enumerate(json_bytes)])
    return base64.b64encode(xored).decode("ascii")


def _decrypt_dict(payload_str: str) -> Optional[dict]:
    try:
        xored = base64.b64decode(payload_str.encode("ascii"))
        key_bytes = SECRET_SALT.encode("utf-8")
        json_bytes = bytes([b ^ key_bytes[i % len(key_bytes)] for i, b in enumerate(xored)])
        return json.loads(json_bytes.decode("utf-8"))
    except Exception:
        return None


def _load_store() -> dict:
    store_file = _get_storage_path()
    hwid = get_machine_id()
    now = time.time()

    if os.path.exists(store_file):
        try:
            with open(store_file, "r", encoding="utf-8") as f:
                content = f.read().strip()
            data = _decrypt_dict(content)
            if data and isinstance(data, dict):
                # Verify stored HWID matches current computer
                if data.get("hwid") == hwid:
                    return data
        except Exception:
            pass

    # If primary file doesn't exist or is invalid, check secondary stamp
    sec_stamp = _read_secondary_stamp()
    first_run = sec_stamp if sec_stamp else now
    if not sec_stamp:
        _write_secondary_stamp(first_run)

    new_store = {
        "hwid": hwid,
        "first_run": first_run,
        "last_run": now,
        "status": "trial",
        "license_key": ""
    }
    _save_store(new_store)
    return new_store


def _save_store(data: dict):
    store_file = _get_storage_path()
    try:
        encrypted = _encrypt_dict(data)
        with open(store_file, "w", encoding="utf-8") as f:
            f.write(encrypted)
    except Exception:
        pass


# ----------------------------------------------------------------------
# 4. LICENSE STATUS INSPECTION & ACTIVATION
# ----------------------------------------------------------------------
def get_license_info() -> Dict[str, Any]:
    """
    Inspect the current license state of the machine.
    Returns:
    {
        'hwid': 'AC-XXXX-XXXX-XXXX',
        'status': 'lifetime' | 'trial' | 'expired',
        'is_valid': bool,
        'days_left': int,
        'hours_left': int,
        'remaining_seconds': float,
        'license_key': str,
        'message': str
    }
    """
    hwid = get_machine_id()
    store = _load_store()
    now = time.time()

    # 1. Check if activated with Lifetime key
    saved_key = store.get("license_key", "").strip()
    if saved_key and verify_license_key(saved_key, hwid):
        return {
            "hwid": hwid,
            "status": "lifetime",
            "is_valid": True,
            "days_left": 9999,
            "hours_left": 9999,
            "remaining_seconds": 99999999.0,
            "license_key": saved_key,
            "message": "Bản quyền vĩnh viễn đã được kích hoạt."
        }

    # 2. Check Trial period
    first_run = float(store.get("first_run", now))
    last_run = float(store.get("last_run", now))

    # Anti-Clock Rollback: if current time is rolled back by > 1 hour, use last_run
    if now < last_run - 3600:
        first_run = first_run - (last_run - now)  # penalized elapsed time

    # Update last_run
    if now > last_run:
        store["last_run"] = now
        _save_store(store)

    elapsed = now - first_run
    remaining = TRIAL_DURATION_SECONDS - elapsed

    if remaining > 0:
        days_left = int(remaining // 86400)
        hours_left = int((remaining % 86400) // 3600)
        return {
            "hwid": hwid,
            "status": "trial",
            "is_valid": True,
            "days_left": days_left,
            "hours_left": hours_left,
            "remaining_seconds": round(remaining, 1),
            "license_key": "",
            "message": f"Đang trong thời gian dùng thử (Còn {days_left} ngày {hours_left} giờ)."
        }
    else:
        return {
            "hwid": hwid,
            "status": "expired",
            "is_valid": False,
            "days_left": 0,
            "hours_left": 0,
            "remaining_seconds": 0.0,
            "license_key": "",
            "message": "Bản dùng thử 3 ngày đã hết hạn. Vui lòng kích hoạt gói bản quyền 150.000 VNĐ."
        }


def check_license_valid() -> bool:
    """
    Raise LicenseExpiredError if the trial has expired and app is not activated.
    Used by core engine to enforce license before building drafts.
    """
    info = get_license_info()
    if not info["is_valid"]:
        raise LicenseExpiredError(
            f"Bản dùng thử 3 ngày của máy ({info['hwid']}) đã hết hạn!\n"
            "Vui lòng thanh toán 150.000đ để nhận mã kích hoạt bản quyền vĩnh viễn."
        )
    return True


def activate_license(key: str) -> Tuple[bool, str]:
    """
    Activate lifetime license on this computer with provided license key.
    """
    hwid = get_machine_id()
    if not key or not isinstance(key, str):
        return False, "Vui lòng nhập mã kích hoạt bản quyền!"

    key = key.strip().upper()
    if not verify_license_key(key, hwid):
        return False, "Mã kích hoạt không hợp lệ hoặc không khớp với mã thiết bị của máy này!"

    store = _load_store()
    store["status"] = "lifetime"
    store["license_key"] = key
    store["activated_at"] = time.time()
    _save_store(store)

    return True, "Kích hoạt bản quyền vĩnh viễn thành công! Cảm ơn bạn đã tin dùng AutoCapCut Studio."


# ----------------------------------------------------------------------
# 5. PAYMENT & VIETQR CONFIGURATION
# ----------------------------------------------------------------------
DEFAULT_PAYMENT_CONFIG = {
    "bank_name": "MBBank",
    "bank_account": "0346730482",
    "account_name": "VU TRUNG QUAN",
    "price_vnd": 150000,
    "zalo_contact": "0346730482",
    "facebook_contact": "",
    "telegram_contact": "",
    "support_note": "Gửi mã máy (Machine ID) qua Zalo (0346730482) sau khi chuyển khoản để nhận mã kích hoạt ngay trong 5 phút."
}


def _get_config_path() -> str:
    candidates = [
        os.path.join(os.path.dirname(sys.executable), "license_config.json"),
        os.path.join(getattr(sys, '_MEIPASS', ''), "license_config.json"),
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "license_config.json"),
        os.path.join(os.getcwd(), "license_config.json")
    ]
    for c in candidates:
        if c and os.path.exists(c):
            return c
    if getattr(sys, 'frozen', False):
        return os.path.join(os.path.dirname(sys.executable), "license_config.json")
    return os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "license_config.json")


def get_payment_info() -> Dict[str, Any]:
    """
    Get payment details and auto-generated VietQR URL.
    """
    cfg_file = _get_config_path()
    cfg = dict(DEFAULT_PAYMENT_CONFIG)
    if os.path.exists(cfg_file):
        try:
            with open(cfg_file, "r", encoding="utf-8") as f:
                user_cfg = json.load(f)
                if isinstance(user_cfg, dict):
                    cfg.update(user_cfg)
        except Exception:
            pass

    hwid = get_machine_id()
    # VietQR format: https://img.vietqr.io/image/<BANK>-<ACCOUNT>-compact2.png?amount=<AMOUNT>&addInfo=<INFO>&accountName=<NAME>
    bank = cfg.get("bank_name", "MBBank").strip().replace(" ", "")
    acc = cfg.get("bank_account", "").strip().replace(" ", "")
    price = cfg.get("price_vnd", 150000)
    acc_name = cfg.get("account_name", "").strip().upper()
    transfer_msg = f"CAPCUT {hwid.replace('AC-', '')}"

    vietqr_url = f"https://img.vietqr.io/image/{bank}-{acc}-compact2.png?amount={price}&addInfo={transfer_msg}&accountName={acc_name}"

    cfg["hwid"] = hwid
    cfg["transfer_content"] = transfer_msg
    cfg["vietqr_url"] = vietqr_url
    return cfg


def update_payment_config(new_config: dict):
    """Save updated payment info to license_config.json."""
    cfg_file = _get_config_path()
    cfg = get_payment_info()
    for k, v in new_config.items():
        if k in DEFAULT_PAYMENT_CONFIG:
            cfg[k] = v
    # Remove transient computed fields before saving
    save_data = {k: cfg[k] for k in DEFAULT_PAYMENT_CONFIG}
    with open(cfg_file, "w", encoding="utf-8") as f:
        json.dump(save_data, f, ensure_ascii=False, indent=2)
