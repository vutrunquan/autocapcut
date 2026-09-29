"""
Main Engine for AutoCapCut Pro.
Orchestrates the entire pipeline: validation -> parsing -> alignment -> pro draft construction.
"""

import os
from typing import Dict, Any, Optional, Callable, List, Union
from .srt_parser import parse_srt
from .image_loader import load_sorted_media
from .aligner import read_script_lines, align_scenes_with_srt
from .draft_builder import build_capcut_draft
from .utils import (
    get_default_capcut_draft_path,
    get_audio_duration_ms,
    format_time_ms
)


def parse_script_input(script_source: str) -> List[str]:
    """Parse script lines either from a file path or from raw text pasted by user."""
    if os.path.exists(script_source):
        return read_script_lines(script_source)
    else:
        lines = [line.strip() for line in script_source.splitlines() if line.strip()]
        if not lines:
            raise ValueError("Kịch bản rỗng hoặc không có dòng nội dung nào!")
        return lines


def run_autocapcut(
    srt_path: str,
    script_source: Optional[str] = None,
    voice_paths: Optional[Union[str, List[str]]] = None,
    images_dir: str = "",
    project_name: str = "AutoCapCut_Project",
    draft_root: Optional[str] = None,
    bgm_paths: Optional[Union[str, List[str]]] = None,
    sort_mode: str = "abc",
    # Transitions
    transition: str = "none",
    transition_duration: float = 0.5,
    transition_mode: str = "all",
    # Clip In-Animations
    clip_intro: str = "none",
    clip_intro_duration: float = 0.8,
    clip_intro_mode: str = "all",
    # Video Scene Effects
    video_effect: str = "none",
    video_effect_scope: str = "all",
    # Cinematic Filters
    filter_name: str = "none",
    filter_intensity: float = 60.0,
    # Camera Motions
    camera_motion: str = "smart_pacing",
    zoom_scale: float = 112.0,
    keyframe_config: Optional[Dict[str, Any]] = None,
    smart_pacing: bool = True,
    canvas_blur: bool = True,
    # Subtitles
    import_subtitles: bool = True,
    subtitle_style: str = "yellow",
    subtitle_animation: str = "bounce",
    subtitle_font_size: float = 8.5,
    subtitle_position: str = "bottom",
    # Audio Suite
    enable_sfx: bool = True,
    sfx_name: str = "random",
    sfx_volume: float = 0.50,
    bgm_volume: float = 0.15,
    audio_ducking: bool = True,
    audio_fade: bool = True,
    enable_cta_subscribe: bool = True,
    remove_gemini_watermark: bool = False,
    width: Optional[int] = None,
    height: Optional[int] = None,
    fps: int = 30,
    aspect_ratio: str = "16:9",
    progress_callback: Optional[Callable[[str, float], None]] = None,
    # Fallback aliases
    script_path: Optional[str] = None,
    voice_path: Optional[Union[str, List[str]]] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Run full automated CapCut video project creation with all pro features.
    """
    def log(msg: str, pct: float = 0.0):
        if progress_callback:
            progress_callback(msg, pct)

    # Resolve aliases
    actual_script = script_source or script_path
    if not actual_script:
        raise ValueError("Vui lòng cung cấp kịch bản phân cảnh!")

    actual_voice = voice_paths if voice_paths is not None else voice_path
    if actual_voice is None:
        raise ValueError("Vui lòng cung cấp ít nhất 1 file Voice âm thanh!")

    # Resolve resolution from aspect ratio
    if width is None or height is None:
        ar_str = str(aspect_ratio).strip().lower()
        if "9:16" in ar_str or "dọc" in ar_str or "tiktok" in ar_str or "shorts" in ar_str:
            width, height = 1080, 1920
        elif "1:1" in ar_str or "vuông" in ar_str:
            width, height = 1080, 1080
        else:
            width, height = 1920, 1080

    log("Đang kiểm tra tính hợp lệ của các file đầu vào...", 0.02)
    if not os.path.exists(srt_path):
        raise FileNotFoundError(f"Không tìm thấy file SRT: {srt_path}")

    if isinstance(actual_voice, str):
        v_list = [p.strip() for p in actual_voice.replace(';', '\n').splitlines() if p.strip()]
    else:
        v_list = list(actual_voice)

    if not v_list:
        raise ValueError("Vui lòng chọn ít nhất 1 file Voice âm thanh!")
    for vf in v_list:
        if not os.path.exists(vf):
            raise FileNotFoundError(f"Không tìm thấy file Voice: {vf}")

    if not os.path.isdir(images_dir):
        raise NotADirectoryError(f"Không tìm thấy thư mục Media/Ảnh: {images_dir}")

    if not draft_root:
        draft_root = get_default_capcut_draft_path()

    # Audio duration
    log("Đang phân tích thời lượng file Voice...", 0.05)
    total_audio_ms = 0
    for vf in v_list:
        dur = get_audio_duration_ms(vf)
        total_audio_ms += dur
    log(f"Tổng thời lượng voice ({len(v_list)} file): {format_time_ms(total_audio_ms)} ({total_audio_ms / 1000:.2f}s)", 0.08)

    # Parse SRT
    log("Đang phân tích file phụ đề SRT...", 0.10)
    subtitles = parse_srt(srt_path)
    log(f"Đã đọc thành công {len(subtitles)} đoạn phụ đề từ SRT.", 0.14)

    # Parse Script
    log("Đang phân tích các cảnh trong kịch bản...", 0.18)
    script_lines = parse_script_input(actual_script)
    log(f"Đã đọc thành công {len(script_lines)} dòng kịch bản (cảnh phim).", 0.22)

    # Media loading & sorting
    sort_desc = "theo tên ABC" if sort_mode == 'abc' else ("Cũ đến Mới" if sort_mode == 'oldest_first' else "Mới đến Cũ")
    log(f"Đang nạp và sắp xếp media {sort_desc}...", 0.25)
    media_paths = load_sorted_media(images_dir, sort_mode=sort_mode)
    log(f"Đã nạp {len(media_paths)} file media (Từ '{os.path.basename(media_paths[0])}' đến '{os.path.basename(media_paths[-1])}').", 0.28)

    # Align scenes
    log("Đang khớp nội dung kịch bản với thời gian của phụ đề SRT...", 0.32)
    scenes = align_scenes_with_srt(
        script_lines=script_lines,
        srt_subtitles=subtitles,
        total_audio_ms=total_audio_ms
    )
    log(f"Khớp thành công {len(scenes)} cảnh liên tục (Gapless timeline).", 0.35)

    # Build CapCut draft with full pro options
    result = build_capcut_draft(
        draft_name=project_name,
        draft_root=draft_root,
        audio_paths=v_list,
        image_paths=media_paths,
        scenes=scenes,
        srt_path=srt_path,
        bgm_paths=bgm_paths,
        width=width,
        height=height,
        fps=fps,
        # Transitions
        transition_name=transition,
        transition_duration=transition_duration,
        transition_mode=transition_mode,
        # Clip In-Animations
        clip_intro=clip_intro,
        clip_intro_duration=clip_intro_duration,
        clip_intro_mode=clip_intro_mode,
        # Video Scene Effects
        video_effect=video_effect,
        video_effect_scope=video_effect_scope,
        # Filters
        filter_name=filter_name,
        filter_intensity=filter_intensity,
        # Motions
        camera_motion=camera_motion,
        zoom_scale=zoom_scale,
        keyframe_config=keyframe_config,
        smart_pacing=smart_pacing,
        canvas_blur=canvas_blur,
        # Subtitles
        import_subtitles=import_subtitles,
        subtitle_style=subtitle_style,
        subtitle_animation=subtitle_animation,
        subtitle_font_size=subtitle_font_size,
        subtitle_position=subtitle_position,
        # Audio
        enable_sfx=enable_sfx,
        sfx_name=sfx_name,
        sfx_volume=sfx_volume,
        bgm_volume=bgm_volume,
        audio_ducking=audio_ducking,
        audio_fade=audio_fade,
        enable_cta_subscribe=enable_cta_subscribe,
        remove_gemini_watermark=remove_gemini_watermark,
        progress_callback=progress_callback
    )

    result['scenes_info'] = scenes
    return result
