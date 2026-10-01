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

CURRENT_VERSION = "1.0.1"
GITHUB_CONTENTS_URL = "https://api.github.com/repos/buoncuoi123/autocapcut/contents/version.json"
VERSION_CHECK_URL = "https://raw.githubusercontent.com/buoncuoi123/autocapcut/main/version.json"
GITHUB_API_URL = "https://api.github.com/repos/buoncuoi123/autocapcut/releases/latest"


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


def check_for_updates(timeout: int = 5) -> Dict[str, Any]:
    """
    Check if a newer version of AutoCapCut is available online.
    Returns:
    {
        'has_update': bool,
        'latest_version': str,
        'current_version': str,
        'release_date': str,
        'changelog': list of str,
        'download_url': str,
        'manual_url': str,
        'title': str
    }
    """
    headers = {
        "User-Agent": f"AutoCapCut-Updater/{CURRENT_VERSION}",
        "Cache-Control": "no-cache"
    }

    # 1. Primary: GitHub Contents API (Real-time, zero CDN caching lag)
    try:
        req = urllib.request.Request(GITHUB_CONTENTS_URL, headers=headers)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            api_resp = json.loads(resp.read().decode("utf-8"))
            raw_b64 = api_resp.get("content", "")
            if raw_b64:
                import base64
                raw_json = base64.b64decode(raw_b64).decode("utf-8")
                data = json.loads(raw_json)
                remote_ver = data.get("version", "").strip()
                if remote_ver and is_newer_version(remote_ver, CURRENT_VERSION):
                    return {
                        "has_update": True,
                        "latest_version": remote_ver,
                        "current_version": CURRENT_VERSION,
                        "release_date": data.get("release_date", ""),
                        "changelog": data.get("changelog", []),
                        "download_url": data.get("download_url", ""),
                        "manual_url": data.get("manual_page_url", "https://github.com/buoncuoi123/autocapcut"),
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
                    "download_url": data.get("download_url", ""),
                    "manual_url": data.get("manual_page_url", "https://github.com/buoncuoi123/autocapcut"),
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

    # 2. Fallback to GitHub Releases API
    try:
        req = urllib.request.Request(GITHUB_API_URL, headers=headers)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            gh_data = json.loads(resp.read().decode("utf-8"))
            tag = gh_data.get("tag_name", "").strip().lstrip("v")
            if tag and is_newer_version(tag, CURRENT_VERSION):
                # Look for zip asset
                download_url = ""
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
    headers = {
        "User-Agent": f"AutoCapCut-Updater/{CURRENT_VERSION}"
    }
    req = urllib.request.Request(download_url, headers=headers)

    with urllib.request.urlopen(req, timeout=30) as resp:
        total_len = resp.headers.get("Content-Length")
        total_bytes = int(total_len) if total_len and total_len.isdigit() else 0
        downloaded = 0
        chunk_size = 64 * 1024  # 64 KB

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

    # 3. Locate source directory inside stage (could be nested inside a root folder)
    source_dir = stage_dir
    sub_entries = os.listdir(stage_dir)
    if len(sub_entries) == 1 and os.path.isdir(os.path.join(stage_dir, sub_entries[0])):
        source_dir = os.path.join(stage_dir, sub_entries[0])

    # 4. Generate and trigger OS-specific detached restart updater
    if sys.platform == "win32":
        bat_script = os.path.join(tempfile.gettempdir(), f"apply_update_{int(time.time())}.bat")
        exe_path = os.path.join(app_dir, "AutoCapCut.exe")
        target_launch = f'"{exe_path}"' if is_frozen else f'"{sys.executable}" "{os.path.join(app_dir, "gui.py")}"'

        script_content = f"""@echo off
chcp 65001 > nul
echo Đang cập nhật AutoCapCut Studio lên phiên bản mới...
timeout /t 2 /nobreak > nul

:: Copy all updated files, preserving existing license_config.json
robocopy "{source_dir}" "{app_dir}" /E /IS /IT /XF license_config.json > nul

:: Clean up staging directory
rmdir /s /q "{stage_dir}" > nul 2>&1
del "{zip_path}" > nul 2>&1

:: Restart application
echo Khởi động lại ứng dụng...
start "" {target_launch}

:: Self-destruct updater script
del "%~f0" > nul 2>&1
exit
"""
        with open(bat_script, "w", encoding="utf-8") as f:
            f.write(script_content)

        # Launch detached updater process
        flags = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS
        subprocess.Popen(["cmd.exe", "/c", bat_script], creationflags=flags, close_fds=True)

        return True, "Bản cập nhật đã sẵn sàng! Ứng dụng sẽ tự động khởi động lại trong giây lát."

    elif sys.platform == "darwin":
        sh_script = os.path.join(tempfile.gettempdir(), f"apply_update_{int(time.time())}.sh")
        script_content = f"""#!/bin/bash
sleep 2
cp -R "{source_dir}/"* "{app_dir}/"
rm -rf "{stage_dir}"
rm -f "{zip_path}"
if [ -d "{app_dir}/AutoCapCut.app" ]; then
    open "{app_dir}/AutoCapCut.app"
else
    python3 "{app_dir}/gui.py" &
fi
rm -f "$0"
"""
        with open(sh_script, "w", encoding="utf-8") as f:
            f.write(script_content)
        os.chmod(sh_script, 0o755)

        subprocess.Popen(["/bin/bash", sh_script], start_new_session=True, close_fds=True)
        return True, "Bản cập nhật đã sẵn sàng! Đang khởi động lại ứng dụng."

    return False, "Hệ điều hành hiện tại chưa hỗ trợ tự động thay thế."
