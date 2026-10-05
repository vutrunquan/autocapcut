"""
AutoCapCut Package
Automate CapCut video editing by synchronizing images/videos with voiceover,
guided by SRT subtitles and line-divided scene scripts.
"""

from .engine import run_autocapcut, parse_script_input
from .srt_parser import parse_srt
from .image_loader import (
    load_sorted_media,
    load_sorted_images,
    remove_gemini_watermark_from_image,
    batch_remove_gemini_watermarks
)
from .aligner import read_script_lines, align_scenes_with_srt
from .draft_builder import build_capcut_draft, TRANSITIONS_MAP
from .utils import (
    get_default_capcut_draft_path,
    get_capcut_exe_path,
    get_audio_duration_ms,
    format_time_ms,
    open_path_in_os,
    launch_capcut_app,
    is_capcut_running,
    get_capcut_window_hwnd,
    focus_capcut_window,
    restart_capcut_app,
    ensure_macos_path
)

from .licensing import (
    get_machine_id,
    get_license_info,
    check_license_valid,
    activate_license,
    generate_license_key,
    verify_license_key,
    get_payment_info,
    LicenseExpiredError
)

from .updater import (
    CURRENT_VERSION,
    check_for_updates,
    download_update_file,
    apply_update_package,
    is_newer_version
)

__all__ = [
    'run_autocapcut',
    'parse_script_input',
    'parse_srt',
    'load_sorted_media',
    'load_sorted_images',
    'remove_gemini_watermark_from_image',
    'batch_remove_gemini_watermarks',
    'read_script_lines',
    'align_scenes_with_srt',
    'build_capcut_draft',
    'TRANSITIONS_MAP',
    'get_default_capcut_draft_path',
    'get_capcut_exe_path',
    'get_audio_duration_ms',
    'format_time_ms',
    'open_path_in_os',
    'launch_capcut_app',
    'is_capcut_running',
    'get_capcut_window_hwnd',
    'focus_capcut_window',
    'restart_capcut_app',
    'ensure_macos_path',
    'get_machine_id',
    'get_license_info',
    'check_license_valid',
    'activate_license',
    'generate_license_key',
    'verify_license_key',
    'get_payment_info',
    'LicenseExpiredError',
    'CURRENT_VERSION',
    'check_for_updates',
    'download_update_file',
    'apply_update_package',
    'is_newer_version'
]
