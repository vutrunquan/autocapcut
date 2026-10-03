"""
In-App Auto-Updater System for AutoCapCut Studio.
Supports:
- Checking remote version.json and GitHub Releases for updates.
- Comparing SemVer versions (e.g. 1.0.0 < 1.1.0).
- Background downloading with real-time percentage progress callback.
- Seamless in-place replacement and process restart without losing license data.
"""

import os
import sys
import json
import time
import zipfile
import shutil
import tempfile
import subprocess
import urllib.request
from typing import Optional, Dict, Any, Callable, Tuple

CURRENT_VERSION = "1.3.8"
GOOGLE_DRIVE_VERSION_URL = "https://drive.usercontent.google.com/download?id=1SfGAiG8cN7vUnpSTq2cF0BAuY8jy5VPU&export=download&confirm=t"
GITHUB_CONTENTS_URL = "https://api.github.com/repos/vutrunquan/autocapcut/contents/version.json"
VERSION_CHECK_URL = "https://raw.githubusercontent.com/vutrunquan/autocapcut/main/version.json"
GITHUB_API_URL = "https://api.github.com/repos/vutrunquan/autocapcut/releases/latest"


def parse_version_tuple(v_str: str) -> Tuple[int, ...]:
    """Parse version string like '1.2.3' or 'v1.2.3' into a comparable tuple of ints."""
    clean = v_str.strip().lower().lstrip("v")
    # Take only numeric dot parts
    parts = []
    for p in clean.split("."):
        digits = "".join(ch for ch in p if ch.isdigit())
        parts.append(int(digits) if digits else 0)
    return tuple(parts) if parts else (0, 0, 0)


def is_newer_version(remote_ver: str, local_ver: str = CURRENT_VERSION) -> bool:
    """Return True if remote_ver is strictly greater than local_ver."""
    try:
        return parse_version_tuple(remote_ver) > parse_version_tuple(local_ver)
    except Exception:
        return False


def get_os_download_url(data: Dict[str, Any]) -> str:
    """Extract appropriate download URL based on current operating system."""
    if sys.platform == "darwin":
        return data.get("download_url_mac") or data.get("download_url") or ""
    elif sys.platform == "win32":
        return data.get("download_url_win") or data.get("download_url") or ""
    return data.get("download_url") or ""


def check_for_updates(timeout: int = 5) -> Dict[str, Any]:
    """
    Check if a newer version of AutoCapCut is available online.
    Prioritizes Google Drive direct streaming endpoint, then falls back to GitHub.
    Automatically matches download package for current OS (macOS / Windows).
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Cache-Control": "no-cache"
    }

    # 1. Primary: Google Drive Direct Endpoint
    if GOOGLE_DRIVE_VERSION_URL:
        try:
            req = urllib.request.Request(GOOGLE_DRIVE_VERSION_URL, headers=headers)
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                remote_ver = data.get("version", "").strip()
                if remote_ver and is_newer_version(remote_ver, CURRENT_VERSION):
                    return {
                        "has_update": True,
                        "latest_version": remote_ver,
                        "current_version": CURRENT_VERSION,
                        "release_date": data.get("release_date", ""),
                        "changelog": data.get("changelog", []),
                        "download_url": get_os_download_url(data),
                        "manual_url": data.get("manual_page_url", "https://github.com/vutrunquan/autocapcut/releases"),
                        "title": data.get("title", f"AutoCapCut Studio v{remote_ver}")
                    }
                elif remote_ver:
                    return {
                        "has_update": False,
                        "latest_version": remote_ver,
                        "current_version": CURRENT_VERSION,
                        "changelog": data.get("changelog", [])
                    }
        except Exception:
            pass

    # 2. Secondary fallback: version.json on raw.githubusercontent.com
    cache_bust = f"?t={int(time.time())}"
    try:
        req = urllib.request.Request(VERSION_CHECK_URL + cache_bust, headers=headers)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            remote_ver = data.get("version", "").strip()
            if remote_ver and is_newer_version(remote_ver, CURRENT_VERSION):
                return {
                    "has_update": True,
                    "latest_version": remote_ver,
                    "current_version": CURRENT_VERSION,
                    "release_date": data.get("release_date", ""),
                    "changelog": data.get("changelog", []),
                    "download_url": get_os_download_url(data),
                    "manual_url": data.get("manual_page_url", "https://github.com/vutrunquan/autocapcut/releases"),
                    "title": data.get("title", f"AutoCapCut Studio v{remote_ver}")
                }
            else:
                return {
                    "has_update": False,
                    "latest_version": remote_ver or CURRENT_VERSION,
                    "current_version": CURRENT_VERSION,
                    "changelog": data.get("changelog", [])
                }
    except Exception:
        pass

    # 3. Fallback to GitHub Releases API with OS matching
    try:
        req = urllib.request.Request(GITHUB_API_URL, headers=headers)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            gh_data = json.loads(resp.read().decode("utf-8"))
            tag = gh_data.get("tag_name", "").strip().lstrip("v")
            if tag and is_newer_version(tag, CURRENT_VERSION):
                target_os_kw = "mac" if sys.platform == "darwin" else "win"
                download_url = ""
                # First pass: match exact OS keyword in zip asset name
                for asset in gh_data.get("assets", []):
                    name_lower = asset.get("name", "").lower()
                    if name_lower.endswith(".zip") and target_os_kw in name_lower:
                        download_url = asset.get("browser_download_url", "")
                        break
                # Second pass: fallback to any zip asset
                if not download_url:
                    for asset in gh_data.get("assets", []):
                        if asset.get("name", "").lower().endswith(".zip"):
                            download_url = asset.get("browser_download_url", "")
                            break
                if not download_url:
                    download_url = gh_data.get("zipball_url", "")

                body = gh_data.get("body", "")
                changelog = [line.strip("- *").strip() for line in body.splitlines() if line.strip()]

                return {
                    "has_update": True,
                    "latest_version": tag,
                    "current_version": CURRENT_VERSION,
                    "release_date": gh_data.get("published_at", "")[:10],
                    "changelog": changelog or ["Cập nhật phiên bản mới AutoCapCut"],
                    "download_url": download_url,
                    "manual_url": gh_data.get("html_url", ""),
                    "title": gh_data.get("name", f"AutoCapCut Studio v{tag}")
                }
    except Exception:
        pass

    return {
        "has_update": False,
        "latest_version": CURRENT_VERSION,
        "current_version": CURRENT_VERSION
    }


def download_update_file(
    download_url: str,
    target_path: str,
    progress_callback: Optional[Callable[[float, int, int], None]] = None
):
    """
    Download update file with streaming and real-time progress callbacks.
    progress_callback(pct: float 0.0-1.0, downloaded_bytes: int, total_bytes: int)
    """
    import re
    actual_url = download_url.strip()
    if "drive.google.com" in actual_url or "drive.usercontent.google.com" in actual_url:
        m = re.search(r'(?:/file/d/|id=)([a-zA-Z0-9_-]+)', actual_url)
        if m:
            file_id = m.group(1)
            actual_url = f"https://drive.usercontent.google.com/download?id={file_id}&export=download&confirm=t"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    req = urllib.request.Request(actual_url, headers=headers)

    with urllib.request.urlopen(req, timeout=60) as resp:
        total_len = resp.headers.get("Content-Length")
        total_bytes = int(total_len) if total_len and total_len.isdigit() else 0
        downloaded = 0
        chunk_size = 128 * 1024  # 128 KB chunk

        with open(target_path, "wb") as f_out:
            while True:
                chunk = resp.read(chunk_size)
                if not chunk:
                    break
                f_out.write(chunk)
                downloaded += len(chunk)
                if progress_callback:
                    pct = (downloaded / total_bytes) if total_bytes > 0 else 0.0
                    progress_callback(pct, downloaded, total_bytes)

    if progress_callback:
        progress_callback(1.0, downloaded, total_bytes or downloaded)


def apply_update_package(zip_path: str) -> Tuple[bool, str]:
    """
    Extract the downloaded update package and spawn the detached updater script
    that replaces application files and restarts AutoCapCut.
    """
    if not os.path.exists(zip_path):
        return False, "File cập nhật không tồn tại."

    # 1. Determine current application root directory
    if getattr(sys, "frozen", False):
        app_dir = os.path.dirname(sys.executable)
        is_frozen = True
    else:
        app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        is_frozen = False

    # 2. Extract ZIP to a temporary staging area
    stage_dir = os.path.join(tempfile.gettempdir(), f"autocapcut_update_{int(time.time())}")
    os.makedirs(stage_dir, exist_ok=True)

    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(stage_dir)
    except Exception as e:
        return False, f"Lỗi giải nén gói cập nhật: {e}"

    # 3. Locate source directory inside stage (could be nested inside a root folder like AutoCapCut_Studio)
    source_dir = stage_dir
    for root, dirs, files in os.walk(stage_dir):
        if "AutoCapCut.exe" in files or "version.json" in files:
            source_dir = root
            break

    # 4. Generate and trigger OS-specific detached restart updater
    if sys.platform == "win32":
        bat_script = os.path.join(tempfile.gettempdir(), f"apply_update_{int(time.time())}.bat")
        exe_path = os.path.join(app_dir, "AutoCapCut.exe")
        target_launch = f'"{exe_path}"' if is_frozen else f'"{sys.executable}" "{os.path.join(app_dir, "gui.py")}"'

        script_content = f"""@echo off
chcp 65001 > nul

:: 1. Dung ping thay timeout vi timeout loi trong process khong co console
:: Moi lan ping mat ~1 giay -> -n 4 = doi ~3 giay
ping 127.0.0.1 -n 4 > nul

:: 2. Buoc dong tien trinh cu neu chua tat
taskkill /F /IM AutoCapCut.exe > nul 2>&1

:: 3. Doi them 2 giay cho Windows giai phong file lock
ping 127.0.0.1 -n 3 > nul

:: 4. Sao chep de toan bo file ban moi (bao toan license_config.json)
robocopy "{source_dir}" "{app_dir}" /E /IS /IT /R:3 /W:1 /XF license_config.json > nul

:: 5. Don dep thu muc tam va file ZIP da tai
rmdir /s /q "{stage_dir}" > nul 2>&1
del "{zip_path}" > nul 2>&1

:: 6. Chuyen thu muc lam viec va khoi dong lai ung dung
cd /d "{app_dir}"
start "" {target_launch}

:: 7. Tu huy file script tam nay
del "%~f0" > nul 2>&1
exit
"""
        with open(bat_script, "w", encoding="utf-8") as f:
            f.write(script_content)

        # Create a VBScript silent launcher — runs .bat with NO visible CMD window
        vbs_launcher = os.path.join(tempfile.gettempdir(), f"silent_update_{int(time.time())}.vbs")
        vbs_content = f'CreateObject("WScript.Shell").Run "cmd /c ""{bat_script}""", 0, False\n'
        with open(vbs_launcher, "w", encoding="utf-8") as f:
            f.write(vbs_content)

        # Launch via wscript.exe (GUI host, no console window at all)
        flags = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS
        subprocess.Popen(["wscript.exe", vbs_launcher], creationflags=flags, close_fds=True,
                         stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        return True, "Bản cập nhật đã sẵn sàng! Ứng dụng sẽ tự động khởi động lại trong giây lát."

    elif sys.platform == "darwin":
        sh_script = os.path.join(tempfile.gettempdir(), f"apply_update_{int(time.time())}.sh")
        script_content = f"""#!/bin/bash

# 1. Doi ung dung cu thoat
sleep 3

# 2. Buoc dong tien trinh cu neu chua tat
pkill -f "AutoCapCut" 2>/dev/null || true
sleep 1

# 3. Bao toan license_config.json
LICENSE_BAK=""
if [ -f "{app_dir}/license_config.json" ]; then
    LICENSE_BAK="/tmp/autocapcut_license_bak.json"
    cp "{app_dir}/license_config.json" "$LICENSE_BAK"
fi

# 4. Sao chep de toan bo file ban moi
cp -R "{source_dir}/"* "{app_dir}/"

# 5. Khoi phuc license_config.json
if [ -n "$LICENSE_BAK" ] && [ -f "$LICENSE_BAK" ]; then
    cp "$LICENSE_BAK" "{app_dir}/license_config.json"
    rm -f "$LICENSE_BAK"
fi

# 6. Don dep thu muc tam va file ZIP da tai
rm -rf "{stage_dir}"
rm -f "{zip_path}"

# 7. Khoi dong lai ung dung
cd "{app_dir}"
if [ -d "{app_dir}/AutoCapCut.app" ]; then
    open "{app_dir}/AutoCapCut.app"
else
    python3 "{app_dir}/gui.py" &
fi

# 8. Tu huy script tam
rm -f "$0"
"""
        with open(sh_script, "w", encoding="utf-8") as f:
            f.write(script_content)
        os.chmod(sh_script, 0o755)

        subprocess.Popen(["/bin/bash", sh_script], start_new_session=True, close_fds=True,
                         stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True, "Bản cập nhật đã sẵn sàng! Đang khởi động lại ứng dụng."

    return False, "Hệ điều hành hiện tại chưa hỗ trợ tự động thay thế."
