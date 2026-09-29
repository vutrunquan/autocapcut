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


def launch_capcut_app() -> bool:
    """Launch CapCut application across macOS (Intel/M-series) and Windows."""
    exe = get_capcut_exe_path()
    if sys.platform == 'darwin':
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
        return False
    elif sys.platform == 'win32':
        if exe and os.path.exists(exe):
            subprocess.Popen([exe])
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
    Detect CapCut application location on Windows and macOS.
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
            return None

        capcut_app = os.path.join(local_app_data, 'CapCut', 'Apps', 'CapCut.exe')
        if os.path.exists(capcut_app):
            return capcut_app

        apps_dir = os.path.join(local_app_data, 'CapCut', 'Apps')
        if os.path.isdir(apps_dir):
            for root, dirs, files in os.walk(apps_dir):
                if 'CapCut.exe' in files:
                    return os.path.join(root, 'CapCut.exe')
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
        'draft_is_invisible': False,
        'draft_is_pippit_draft': False,
        'draft_is_web_article_video': False,
        'draft_json_file': os.path.join(draft_dir, 'draft_content.json').replace('\\', '/'),
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
