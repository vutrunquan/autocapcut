"""
Utilities for AutoCapCut.
Detects CapCut paths, updates root_meta_info.json, and inspects audio media.
"""

import os
import sys
import json
import time
import uuid
import shutil
import subprocess
from typing import Optional, Tuple
from pymediainfo import MediaInfo


def ensure_macos_path():
    """Ensure Homebrew bin directories are in PATH on macOS (both Apple Silicon arm64 and Intel x86_64)."""
    if sys.platform == 'darwin':
        extra_paths = ['/opt/homebrew/bin', '/usr/local/bin', os.path.expanduser('~/.nvm/current/bin')]
        current_path = os.environ.get('PATH', '')
        for ep in extra_paths:
            if os.path.exists(ep) and ep not in current_path:
                os.environ['PATH'] = f"{ep}:{os.environ.get('PATH', '')}"


# Run once on import
ensure_macos_path()


def open_path_in_os(path: str):
    """Open a file or directory in native Explorer (Windows) or Finder (macOS)."""
    if not path or not os.path.exists(path):
        return
    if sys.platform == 'win32':
        os.startfile(path)
    elif sys.platform == 'darwin':
        subprocess.Popen(['open', path])
    else:
        subprocess.Popen(['xdg-open', path])


def is_capcut_running() -> bool:
    """Check if CapCut or JianYing desktop application is currently running."""
    if sys.platform == 'win32':
        try:
            res = subprocess.run(['tasklist', '/fi', 'imagename eq CapCut.exe'], capture_output=True, text=True, timeout=3)
            if 'CapCut.exe' in res.stdout:
                return True
            res_jy = subprocess.run(['tasklist', '/fi', 'imagename eq JianyingPro.exe'], capture_output=True, text=True, timeout=3)
            return 'JianyingPro.exe' in res_jy.stdout
        except Exception:
            return False
    elif sys.platform == 'darwin':
        try:
            for proc_name in ['CapCut', 'JianyingPro']:
                res = subprocess.run(['pgrep', '-x', proc_name], capture_output=True, text=True, timeout=3)
                if bool(res.stdout.strip()):
                    return True
        except Exception:
            return False
    return False


def get_capcut_window_hwnd() -> Optional[int]:
    """Find visible CapCut or JianYing main window handle on Windows."""
    if sys.platform != 'win32':
        return None
    try:
        import ctypes
        from ctypes import wintypes
        user32 = ctypes.windll.user32

        found_hwnd = []
        def enum_proc(hwnd, lParam):
            if user32.IsWindowVisible(hwnd):
                length = user32.GetWindowTextLengthW(hwnd)
                if length > 0:
                    buff = ctypes.create_unicode_buffer(length + 1)
                    user32.GetWindowTextW(hwnd, buff, length + 1)
                    title = buff.value.lower()
                    if 'capcut' in title or 'jianying' in title:
                        # Exclude AutoCapCut's own windows
                        if 'autocapcut' not in title:
                            found_hwnd.append(hwnd)
            return 1

        WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
        user32.EnumWindows(WNDENUMPROC(enum_proc), 0)
        return found_hwnd[0] if found_hwnd else None
    except Exception:
        return None


def focus_capcut_window() -> bool:
    """Bring running CapCut window to the foreground."""
    if sys.platform == 'win32':
        try:
            hwnd = get_capcut_window_hwnd()
            if hwnd:
                import ctypes
                user32 = ctypes.windll.user32
                kernel32 = ctypes.windll.kernel32

                user32.ShowWindow(hwnd, 9)  # SW_RESTORE
                fore_hwnd = user32.GetForegroundWindow()
                fore_thread = user32.GetWindowThreadProcessId(fore_hwnd, None)
                cur_thread = kernel32.GetCurrentThreadId()

                if fore_thread != cur_thread:
                    user32.AttachThreadInput(cur_thread, fore_thread, True)
                    user32.BringWindowToTop(hwnd)
                    user32.SetForegroundWindow(hwnd)
                    user32.SetFocus(hwnd)
                    user32.AttachThreadInput(cur_thread, fore_thread, False)
                else:
                    user32.BringWindowToTop(hwnd)
                    user32.SetForegroundWindow(hwnd)
                    user32.SetFocus(hwnd)
                return True
        except Exception:
            pass
    elif sys.platform == 'darwin':
        try:
            subprocess.run(['osascript', '-e', 'tell application "CapCut" to activate'], capture_output=True, timeout=3)
            return True
        except Exception:
            pass
    return False


def restart_capcut_app() -> bool:
    """Safely terminate lingering CapCut processes and launch fresh so projects update immediately."""
    if sys.platform == 'win32':
        try:
            subprocess.run(['taskkill', '/F', '/IM', 'CapCut.exe'], capture_output=True, timeout=5)
            subprocess.run(['taskkill', '/F', '/IM', 'JianyingPro.exe'], capture_output=True, timeout=5)
            time.sleep(1.0)
        except Exception:
            pass
        return launch_capcut_app()
    elif sys.platform == 'darwin':
        try:
            subprocess.run(['pkill', '-x', 'CapCut'], capture_output=True, timeout=5)
            subprocess.run(['pkill', '-x', 'JianyingPro'], capture_output=True, timeout=5)
            time.sleep(1.0)
        except Exception:
            pass
        return launch_capcut_app()
    return False


def launch_capcut_app(draft_path: Optional[str] = None) -> bool:
    """
    Launch CapCut application across macOS (Intel/M-series) and Windows.
    On Windows, uses official Start Menu shortcut, URI protocol, or direct versioned binary.
    Drafts appear at the top of CapCut's homepage via root_meta_info.json.
    """
    if sys.platform == 'darwin':
        exe = get_capcut_exe_path()
        if exe and os.path.exists(exe):
            subprocess.Popen(['open', exe])
            return True
        for app_name in ['CapCut', 'JianyingPro']:
            try:
                res = subprocess.run(['open', '-a', app_name], capture_output=True)
                if res.returncode == 0:
                    return True
            except Exception:
                pass
        if draft_path and os.path.exists(draft_path):
            open_path_in_os(draft_path)
            return True
        return False

    elif sys.platform == 'win32':
        # 1. Try launching through Start Menu or Desktop shortcut (most reliable on Windows)
        lnk_candidates = [
            os.path.expanduser(r'~/AppData/Roaming/Microsoft/Windows/Start Menu/Programs/CapCut/CapCut.lnk'),
            os.path.expanduser(r'~/Desktop/CapCut.lnk'),
            r'C:\ProgramData\Microsoft\Windows\Start Menu\Programs\CapCut\CapCut.lnk',
            os.path.expanduser(r'~/AppData/Roaming/Microsoft/Windows/Start Menu/Programs/JianyingPro/JianyingPro.lnk'),
            os.path.expanduser(r'~/Desktop/JianyingPro.lnk'),
            r'C:\ProgramData\Microsoft\Windows\Start Menu\Programs\JianyingPro\JianyingPro.lnk',
        ]
        for lnk in lnk_candidates:
            if os.path.isfile(lnk):
                try:
                    os.startfile(lnk)
                    return True
                except Exception:
                    pass

        # 2. Try URI protocol
        try:
            os.startfile("capcut:")
            return True
        except Exception:
            pass

        # 3. Direct executable launch
        exe = get_capcut_exe_path()
        if exe and os.path.isfile(exe):
            try:
                is_shim = os.path.basename(exe).lower() == 'capcut.exe' and 'apps' in os.path.dirname(exe).lower() and not any(ch.isdigit() for ch in os.path.basename(os.path.dirname(exe)))
                args = [exe, '--src3'] if is_shim else [exe]
                subprocess.Popen(args, cwd=os.path.dirname(exe), creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
                return True
            except Exception:
                try:
                    os.startfile(exe)
                    return True
                except Exception:
                    pass

        if draft_path and os.path.exists(draft_path):
            open_path_in_os(draft_path)
            return True

        return False


def get_default_capcut_draft_path() -> Optional[str]:
    """
    Detect the default CapCut drafts directory across Windows and macOS.
    Supports both Intel and Apple Silicon Macs.
    """
    home = os.path.expanduser('~')

    if sys.platform == 'darwin':
        # macOS paths (Intel & Apple Silicon M1/M2/M3/M4)
        candidates = [
            os.path.join(home, 'Movies', 'CapCut', 'User Data', 'Projects', 'com.lveditor.draft'),
            os.path.join(home, 'Library', 'Containers', 'com.lemon.lvoverseas', 'Data', 'Movies', 'CapCut', 'User Data', 'Projects', 'com.lveditor.draft'),
            os.path.join(home, 'Library', 'Containers', 'com.lemon.cuteditor', 'Data', 'Movies', 'CapCut', 'User Data', 'Projects', 'com.lveditor.draft'),
            os.path.join(home, 'Library', 'Application Support', 'CapCut', 'User Data', 'Projects', 'com.lveditor.draft'),
            os.path.join(home, 'Movies', 'JianyingPro', 'User Data', 'Projects', 'com.lveditor.draft'),
            os.path.join(home, 'Library', 'Containers', 'com.lemon.jianying', 'Data', 'Movies', 'JianyingPro', 'User Data', 'Projects', 'com.lveditor.draft'),
        ]
        for p in candidates:
            if os.path.exists(p):
                return p
        return candidates[0]

    elif sys.platform == 'win32':
        local_app_data = os.environ.get('LOCALAPPDATA', '')
        if not local_app_data:
            user_profile = os.environ.get('USERPROFILE', '')
            local_app_data = os.path.join(user_profile, 'AppData', 'Local')

        candidates = [
            os.path.join(local_app_data, 'CapCut', 'User Data', 'Projects', 'com.lveditor.draft'),
            os.path.join(local_app_data, 'JianyingPro', 'User Data', 'Projects', 'com.lveditor.draft'),
        ]
        for p in candidates:
            if os.path.exists(p):
                return p
        return candidates[0]

    return os.path.join(home, 'CapCut', 'User Data', 'Projects', 'com.lveditor.draft')


def get_capcut_exe_path() -> Optional[str]:
    """
    Detect CapCut or JianYing application location on Windows and macOS.
    Supports both Intel (x86_64) and Apple Silicon (arm64).
    """
    if sys.platform == 'darwin':
        candidates = [
            '/Applications/CapCut.app',
            os.path.expanduser('~/Applications/CapCut.app'),
            '/Applications/JianyingPro.app',
            os.path.expanduser('~/Applications/JianyingPro.app'),
        ]
        for p in candidates:
            if os.path.exists(p):
                return p
        return '/Applications/CapCut.app' if os.path.exists('/Applications/CapCut.app') else None

    elif sys.platform == 'win32':
        local_app_data = os.environ.get('LOCALAPPDATA', '')
        if not local_app_data:
            user_profile = os.environ.get('USERPROFILE', '')
            local_app_data = os.path.join(user_profile, 'AppData', 'Local')

        for app_folder in ['CapCut', 'JianyingPro']:
            apps_dir = os.path.join(local_app_data, app_folder, 'Apps')
            if os.path.isdir(apps_dir):
                # 1. Prefer latest versioned binary (e.g. Apps/9.5.0.4050/CapCut.exe)
                try:
                    subdirs = sorted([d for d in os.listdir(apps_dir) if os.path.isdir(os.path.join(apps_dir, d))], reverse=True)
                    for d in subdirs:
                        for exe_name in ['CapCut.exe', 'JianyingPro.exe']:
                            candidate = os.path.join(apps_dir, d, exe_name)
                            if os.path.isfile(candidate):
                                return candidate
                except Exception:
                    pass

                # 2. Check root Apps launcher
                for exe_name in ['CapCut.exe', 'JianyingPro.exe']:
                    candidate = os.path.join(apps_dir, exe_name)
                    if os.path.isfile(candidate):
                        return candidate

        # 3. Check Program Files
        for pf in [os.environ.get('ProgramFiles'), os.environ.get('ProgramFiles(x86)')]:
            if pf:
                for candidate in [
                    os.path.join(pf, 'CapCut', 'CapCut.exe'),
                    os.path.join(pf, 'ByteDance', 'CapCut', 'CapCut.exe'),
                    os.path.join(pf, 'JianyingPro', 'JianyingPro.exe'),
                ]:
                    if os.path.isfile(candidate):
                        return candidate

        return None
    return None


def get_audio_duration_ms(audio_path: str) -> int:
    """
    Extract accurate audio duration in milliseconds across Windows, macOS, and Linux.
    Tries:
    1. MediaInfo (via pymediainfo)
    2. afinfo (native built-in CoreAudio tool on macOS - Intel & Apple Silicon M)
    3. wave module (standard library for WAV)
    4. ffprobe (if installed)
    """
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"File audio không tồn tại: {audio_path}")

    # 1. MediaInfo
    try:
        media_info = MediaInfo.parse(audio_path)
        for track in media_info.tracks:
            if track.track_type == 'Audio' and track.duration is not None:
                return int(float(track.duration))
            elif track.track_type == 'General' and track.duration is not None:
                return int(float(track.duration))
    except Exception:
        pass

    # 2. Native macOS CoreAudio tool: afinfo (available out-of-the-box on all Macs: Intel + M1/M2/M3/M4)
    if sys.platform == 'darwin':
        try:
            res = subprocess.run(['afinfo', audio_path], capture_output=True, text=True, timeout=5)
            if res.returncode == 0:
                import re
                match = re.search(r'duration:\s*([0-9.]+)\s*sec', res.stdout, re.IGNORECASE)
                if match:
                    return int(float(match.group(1)) * 1000)
        except Exception:
            pass

    # 3. Fallback for WAV files (Python built-in standard library)
    if audio_path.lower().endswith('.wav'):
        try:
            import wave
            with wave.open(audio_path, 'rb') as w:
                frames = w.getnframes()
                rate = w.getframerate()
                return int((frames / float(rate)) * 1000)
        except Exception:
            pass

    # 4. Fallback for ffprobe if available
    try:
        res = subprocess.run(
            ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', audio_path],
            capture_output=True, text=True, timeout=5
        )
        if res.returncode == 0 and res.stdout.strip():
            return int(float(res.stdout.strip()) * 1000)
    except Exception:
        pass

    raise ValueError(f"Không thể đọc thời lượng của file âm thanh: {audio_path}")


def format_time_ms(ms: int) -> str:
    """Format milliseconds into MM:SS.mmm or HH:MM:SS.mmm string."""
    seconds = ms // 1000
    milli = ms % 1000
    minutes = seconds // 60
    sec = seconds % 60
    hours = minutes // 60
    min_rem = minutes % 60
    if hours > 0:
        return f"{hours:02d}:{min_rem:02d}:{sec:02d}.{milli:03d}"
    return f"{min_rem:02d}:{sec:02d}.{milli:03d}"


def register_draft_in_root_meta(
    draft_root: str,
    draft_name: str,
    draft_dir: str,
    duration_us: int,
    cover_image_path: Optional[str] = None
) -> None:
    """
    Update root_meta_info.json in the CapCut drafts directory so that
    the newly generated project appears immediately at the top of CapCut's project list.
    """
    root_meta_file = os.path.join(draft_root, 'root_meta_info.json')
    if not os.path.exists(root_meta_file):
        # Create minimal root_meta_info.json if it doesn't exist yet
        meta_data = {
            'all_draft_store': [],
            'draft_ids': 1,
            'root_path': draft_root.replace('\\', '/')
        }
    else:
        try:
            with open(root_meta_file, 'r', encoding='utf-8') as f:
                meta_data = json.load(f)
        except Exception:
            meta_data = {'all_draft_store': [], 'draft_ids': 1, 'root_path': draft_root.replace('\\', '/')}

    # Read draft_id from draft_meta_info.json if available
    draft_meta_file = os.path.join(draft_dir, 'draft_meta_info.json')
    draft_id = str(uuid.uuid4()).upper()
    if os.path.exists(draft_meta_file):
        try:
            with open(draft_meta_file, 'r', encoding='utf-8') as f:
                d_meta = json.load(f)
                draft_id = d_meta.get('draft_id', draft_id)
        except Exception:
            pass

    # Copy cover image into draft folder if provided
    cover_dest = os.path.join(draft_dir, 'draft_cover.jpg')
    if cover_image_path and os.path.exists(cover_image_path):
        try:
            shutil.copyfile(cover_image_path, cover_dest)
        except Exception:
            pass

    # Ensure both draft_info.json and draft_content.json exist for legacy and modern CapCut versions
    content_file = os.path.join(draft_dir, 'draft_content.json')
    info_file = os.path.join(draft_dir, 'draft_info.json')

    if os.path.exists(content_file) and not os.path.exists(info_file):
        try:
            shutil.copyfile(content_file, info_file)
        except Exception:
            pass
    elif os.path.exists(info_file) and not os.path.exists(content_file):
        try:
            shutil.copyfile(info_file, content_file)
        except Exception:
            pass

    primary_json = info_file if os.path.exists(info_file) else content_file

    now_us = int(time.time() * 1000000)
    all_drafts = meta_data.get('all_draft_store', [])
    # Remove older entry with the same draft name to prevent duplicates
    all_drafts = [d for d in all_drafts if d.get('draft_name') != draft_name]

    new_entry = {
        'cloud_draft_cover': False,
        'cloud_draft_sync': False,
        'draft_cloud_last_action_download': False,
        'draft_cloud_purchase_info': '',
        'draft_cloud_template_id': '',
        'draft_cloud_tutorial_info': '',
        'draft_cloud_videocut_purchase_info': '',
        'draft_cover': cover_dest.replace('\\', '/'),
        'draft_fold_path': draft_dir.replace('\\', '/'),
        'draft_id': draft_id,
        'draft_is_ai_shorts': False,
        'draft_is_cloud_temp_draft': False,
        'draft_is_infinite_canvas_draft': False,
        'draft_is_invisible': False,
        'draft_is_pippit_draft': False,
        'draft_is_web_article_video': False,
        'draft_json_file': primary_json.replace('\\', '/'),
        'draft_name': draft_name,
        'draft_new_version': '',
        'draft_root_path': draft_root.replace('\\', '/'),
        'draft_timeline_materials_size': 0,
        'draft_type': '',
        'draft_web_article_video_enter_from': '',
        'pippit_avatar_url': '',
        'pippit_extra_info': '',
        'pippit_id': '',
        'pippit_user_name': '',
        'streaming_edit_draft_ready': True,
        'tm_draft_cloud_completed': '',
        'tm_draft_cloud_entry_id': -1,
        'tm_draft_cloud_modified': 0,
        'tm_draft_cloud_parent_entry_id': -1,
        'tm_draft_cloud_space_id': -1,
        'tm_draft_cloud_user_id': -1,
        'tm_draft_create': now_us,
        'tm_draft_modified': now_us,
        'tm_draft_removed': 0,
        'tm_duration': duration_us
    }

    # Prepend to the top so it appears as the newest project
    all_drafts.insert(0, new_entry)
    meta_data['all_draft_store'] = all_drafts

    with open(root_meta_file, 'w', encoding='utf-8') as f:
        json.dump(meta_data, f, ensure_ascii=False, indent=2)
