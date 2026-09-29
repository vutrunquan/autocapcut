"""
Draft Builder for AutoCapCut Pro.
Constructs a complete CapCut draft project with full pro features:
- Multi-audio Voice track
- Background music (BGM) track with Audio Ducking & Audio Fade In/Out
- Auto Transition Sound Effects (SFX Whoosh, Swoosh, Pop, Ding)
- Canvas Background Blur (eliminates black bars on mismatched aspect ratios)
- Cinematic Filters (Soft Grain, Vintage 1980, VHS, Peach Warm, Lover Blue, BW)
- Smart Pacing keyframe motions (fast zoom for short lines, pan+zoom for long lines)
- Customizable subtitle colors & styles (Viral Yellow, Tech Cyan, Finance Green, Classic White)
- Auto CTA Subscribe banner with chime SFX
- Seamless transitions (Black Fade, Slow Fade, Swipe, Wipe, Shift, Basic Black, Blink Fade)
- Gemini AI watermark removal
"""

import os
import random
from typing import List, Dict, Any, Optional, Callable, Union
import pycapcut as cc
from .utils import register_draft_in_root_meta, get_audio_duration_ms
from .image_loader import remove_gemini_watermark_from_image, batch_remove_gemini_watermarks


# Mapping user transition names to pycapcut TransitionType enums
TRANSITIONS_MAP = {
    "none": None,
    "không transition": None,
    "black fade": getattr(cc.TransitionType, "闪黑", None),
    "slow fade": getattr(cc.TransitionType, "叠化", None),
    "fade swipe": getattr(cc.TransitionType, "Swipe_Left", getattr(cc.TransitionType, "叠化", None)),
    "fade wipe": getattr(cc.TransitionType, "阳光擦拭", getattr(cc.TransitionType, "叠化", None)),
    "fade shift": getattr(cc.TransitionType, "Push_Away_2", getattr(cc.TransitionType, "叠化", None)),
    "basic black": getattr(cc.TransitionType, "闪黑_II", getattr(cc.TransitionType, "闪黑", None)),
    "blink fade": getattr(cc.TransitionType, "频闪_II", getattr(cc.TransitionType, "叠化", None)),
}

# Mapping filter names to pycapcut FilterType enums
FILTERS_MAP = {
    "none": None,
    "không dùng filter": None,
    "soft grain (hạt phim điện ảnh)": getattr(cc.FilterType, "Soft_Grain", None),
    "vintage 1980 (tông màu cổ điển)": getattr(cc.FilterType, "_1980", None),
    "vhs retro (băng từ vhs)": getattr(cc.FilterType, "VHS_I", None),
    "peach fuzz (tông ấm điện ảnh)": getattr(cc.FilterType, "Peach_Fuzz", None),
    "lover blue (tông lạnh điện ảnh)": getattr(cc.FilterType, "Lover_Blue", None),
    "bw retro (trắng đen cổ điển)": getattr(cc.FilterType, "BW_2", None),
}

# Subtitle color palettes (R, G, B in 0.0 - 1.0)
SUBTITLE_COLORS = {
    "yellow": (0.99, 0.85, 0.21),  # Viral Yellow (#fbbf24)
    "white": (1.0, 1.0, 1.0),      # Classic White
    "cyan": (0.22, 0.74, 0.97),    # Tech Cyan (#38bdf8)
    "green": (0.29, 0.87, 0.50),   # Finance Green (#4ade80)
}


def apply_keyframe_motion(
    seg: cc.VideoSegment,
    motion_type: str,
    params: Dict[str, Any],
    dur_us: int,
    canvas_w: int = 1920,
    canvas_h: int = 1080
):
    """Apply configured motion keyframes to a VideoSegment."""
    scale_val = float(params.get('scale', 110)) / 100.0
    param_x = float(params.get('x', 0))
    param_y = float(params.get('y', 0))

    norm_x = (param_x / float(canvas_w)) * 0.5
    norm_y = (param_y / float(canvas_h)) * 0.5

    if motion_type == 'zoom_in':
        seg.add_keyframe(cc.KeyframeProperty.uniform_scale, 0, 1.0)
        seg.add_keyframe(cc.KeyframeProperty.uniform_scale, dur_us, scale_val)

    elif motion_type == 'zoom_out':
        seg.add_keyframe(cc.KeyframeProperty.uniform_scale, 0, scale_val)
        seg.add_keyframe(cc.KeyframeProperty.uniform_scale, dur_us, 1.0)

    elif motion_type == 'pan_up':
        seg.add_keyframe(cc.KeyframeProperty.uniform_scale, 0, scale_val)
        seg.add_keyframe(cc.KeyframeProperty.uniform_scale, dur_us, scale_val)
        seg.add_keyframe(cc.KeyframeProperty.position_y, 0, 0.0)
        seg.add_keyframe(cc.KeyframeProperty.position_y, dur_us, norm_y)

    elif motion_type == 'pan_down':
        seg.add_keyframe(cc.KeyframeProperty.uniform_scale, 0, scale_val)
        seg.add_keyframe(cc.KeyframeProperty.uniform_scale, dur_us, scale_val)
        seg.add_keyframe(cc.KeyframeProperty.position_y, 0, norm_y)
        seg.add_keyframe(cc.KeyframeProperty.position_y, dur_us, 0.0)

    elif motion_type == 'pan_left':
        seg.add_keyframe(cc.KeyframeProperty.uniform_scale, 0, scale_val)
        seg.add_keyframe(cc.KeyframeProperty.uniform_scale, dur_us, scale_val)
        seg.add_keyframe(cc.KeyframeProperty.position_x, 0, 0.0)
        seg.add_keyframe(cc.KeyframeProperty.position_x, dur_us, -norm_x)

    elif motion_type == 'pan_right':
        seg.add_keyframe(cc.KeyframeProperty.uniform_scale, 0, scale_val)
        seg.add_keyframe(cc.KeyframeProperty.uniform_scale, dur_us, scale_val)
        seg.add_keyframe(cc.KeyframeProperty.position_x, 0, -norm_x)
        seg.add_keyframe(cc.KeyframeProperty.position_x, dur_us, 0.0)


def build_capcut_draft(
    draft_name: str,
    draft_root: str,
    audio_paths: Union[str, List[str]],
    image_paths: List[str],
    scenes: List[Dict[str, Any]],
    srt_path: Optional[str] = None,
    bgm_paths: Optional[Union[str, List[str]]] = None,
    width: int = 1920,
    height: int = 1080,
    fps: int = 30,
    # New Advanced Options
    import_subtitles: bool = True,
    subtitle_style: str = "yellow",
    transition_name: str = "none",
    keyframe_config: Optional[Dict[str, Any]] = None,
    smart_pacing: bool = True,
    canvas_blur: bool = True,
    filter_name: str = "none",
    enable_sfx: bool = True,
    sfx_volume: float = 0.50,
    bgm_volume: float = 0.15,
    audio_ducking: bool = True,
    audio_fade: bool = True,
    enable_cta_subscribe: bool = True,
    remove_gemini_watermark: bool = False,
    progress_callback: Optional[Callable[[str, float], None]] = None
) -> Dict[str, Any]:
    """
    Build complete CapCut draft project with full pro features.
    """
    def report(msg: str, pct: float):
        if progress_callback:
            progress_callback(msg, pct)

    # Normalize audio paths
    voice_files = [audio_paths] if isinstance(audio_paths, str) else list(audio_paths)
    bgm_files = []
    if bgm_paths:
        bgm_files = [bgm_paths] if isinstance(bgm_paths, str) else list(bgm_paths)

    report(f"Khởi tạo dự án CapCut '{draft_name}'...", 0.05)
    os.makedirs(draft_root, exist_ok=True)
    df = cc.DraftFolder(draft_root)
    script = df.create_draft(draft_name, width, height, fps, allow_replace=True)

    # 1. AUDIO TRACK (VOICE)
    report("Đang nạp file voice âm thanh...", 0.10)
    script.add_track(cc.TrackType.audio, 'Voice')
    curr_audio_offset_us = 0
    total_audio_us = 0

    for af in voice_files:
        if not os.path.exists(af):
            continue
        a_mat = cc.AudioMaterial(af)
        dur = a_mat.duration
        script.add_segment(cc.AudioSegment(a_mat, cc.trange(curr_audio_offset_us, dur)), 'Voice')
        curr_audio_offset_us += dur
        total_audio_us += dur

    # 2. BGM TRACK (With Audio Ducking & Fade)
    if bgm_files:
        report("Đang cấu hình nhạc nền (BGM) & Audio Ducking...", 0.16)
        script.add_track(cc.TrackType.audio, 'BGM')
        curr_bgm_us = 0
        bgm_idx = 0
        bgm_base_vol = (bgm_volume * 0.75) if audio_ducking else bgm_volume

        while curr_bgm_us < total_audio_us and bgm_files:
            bgm_p = bgm_files[bgm_idx % len(bgm_files)]
            if not os.path.exists(bgm_p):
                break
            bgm_mat = cc.AudioMaterial(bgm_p)
            needed_us = total_audio_us - curr_bgm_us
            use_dur_us = min(bgm_mat.duration, needed_us)

            bgm_seg = cc.AudioSegment(
                bgm_mat,
                target_timerange=cc.trange(curr_bgm_us, use_dur_us),
                source_timerange=cc.trange(0, use_dur_us),
                volume=bgm_base_vol
            )

            # Apply Audio Fade In & Out
            if audio_fade:
                in_fade = 2000000 if curr_bgm_us == 0 else 0
                out_fade = 3000000 if (curr_bgm_us + use_dur_us >= total_audio_us) else 0
                if in_fade > 0 or out_fade > 0:
                    bgm_seg.add_fade(in_duration=in_fade, out_duration=out_fade)

            script.add_segment(bgm_seg, 'BGM')
            curr_bgm_us += use_dur_us
            bgm_idx += 1

    # 3. SFX AUDIO TRACK (Transition Sound Effects)
    sfx_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets', 'sfx')
    sfx_files = []
    if enable_sfx and os.path.isdir(sfx_dir):
        sfx_files = [
            os.path.join(sfx_dir, f) for f in os.listdir(sfx_dir)
            if f.lower().endswith(('.wav', '.mp3')) and not f.startswith('ding')
        ]

    if enable_sfx and sfx_files:
        report("Đang nạp hiệu ứng âm thanh chuyển cảnh (SFX)...", 0.22)
        script.add_track(cc.TrackType.audio, 'SFX')

    # 4. VIDEO TRACK (IMAGES / CLIPS)
    report(f"Đang đồng bộ {len(scenes)} media vào timeline...", 0.28)
    script.add_track(cc.TrackType.video, 'Images')

    num_scenes = len(scenes)
    num_images = len(image_paths)

    # Resolve transition
    t_key = transition_name.strip().lower()
    transition_type = TRANSITIONS_MAP.get(t_key)

    # Resolve cinematic filter
    f_key = filter_name.strip().lower()
    cinematic_filter = FILTERS_MAP.get(f_key)

    # Resolve active motions
    active_motions = []
    if keyframe_config:
        for m_name in ['zoom_in', 'zoom_out', 'pan_up', 'pan_down', 'pan_left', 'pan_right']:
            m_conf = keyframe_config.get(m_name)
            if m_conf and m_conf.get('enabled', False):
                active_motions.append((m_name, m_conf))

    # Clean watermark if requested using GargantuaX/gemini-watermark-remover
    if remove_gemini_watermark and image_paths:
        report("Đang xóa watermark Gemini (Reverse Alpha Blending)...", 0.24)
        cache_dir = os.path.join(draft_root, draft_name, "_wm_clean")
        # Only clean unique images that are actually used in the scenes
        used_indices = sorted(set(i if i < num_images else (num_images - 1) for i in range(num_scenes)))
        images_to_clean = [image_paths[idx] for idx in used_indices]
        cleaned_subset = batch_remove_gemini_watermarks(
            image_paths=images_to_clean,
            output_cache_dir=cache_dir,
            progress_callback=lambda msg, p: report(f"{msg}", 0.24 + 0.04 * p)
        )
        clean_map = dict(zip(images_to_clean, cleaned_subset))
        image_paths = [clean_map.get(p, p) for p in image_paths]
        num_images = len(image_paths)

    for i, sc in enumerate(scenes):
        img_p = image_paths[i] if i < num_images else image_paths[-1]

        st_us = sc['start_us']
        dur_us = sc['duration_us']
        dur_s = dur_us / 1000000.0

        v_mat = cc.VideoMaterial(img_p)
        v_seg = cc.VideoSegment(v_mat, cc.trange(st_us, dur_us))

        # 4a. Canvas Blur (eliminates black bars)
        if canvas_blur:
            try:
                v_seg.add_background_filling(fill_type='blur', blur=0.0625)
            except Exception:
                pass

        # 4b. Cinematic Filter
        if cinematic_filter:
            try:
                v_seg.add_filter(cinematic_filter, intensity=60.0)
            except Exception:
                pass

        # 4c. Keyframe Motion (Smart Pacing vs Configured Motions)
        if smart_pacing:
            if dur_s < 3.0:
                # Fast zoom-in for high energy
                v_seg.add_keyframe(cc.KeyframeProperty.uniform_scale, 0, 1.0)
                v_seg.add_keyframe(cc.KeyframeProperty.uniform_scale, dur_us, 1.12)
            elif dur_s > 6.0:
                # Long line: Slow Pan across with slight zoom
                v_seg.add_keyframe(cc.KeyframeProperty.uniform_scale, 0, 1.08)
                v_seg.add_keyframe(cc.KeyframeProperty.uniform_scale, dur_us, 1.08)
                v_seg.add_keyframe(cc.KeyframeProperty.position_x, 0, 0.05)
                v_seg.add_keyframe(cc.KeyframeProperty.position_x, dur_us, -0.05)
            else:
                # Medium line: round-robin motion
                if active_motions:
                    m_name, m_params = active_motions[i % len(active_motions)]
                    apply_keyframe_motion(v_seg, m_name, m_params, dur_us, width, height)
                else:
                    v_seg.add_keyframe(cc.KeyframeProperty.uniform_scale, 0, 1.0)
                    v_seg.add_keyframe(cc.KeyframeProperty.uniform_scale, dur_us, 1.07)
        elif active_motions:
            m_name, m_params = active_motions[i % len(active_motions)]
            apply_keyframe_motion(v_seg, m_name, m_params, dur_us, width, height)

        # 4d. Transition
        if transition_type and i < num_scenes - 1:
            trans_dur = min(500000, max(200000, dur_us // 4))
            try:
                v_seg.add_transition(transition_type, duration=trans_dur)
            except Exception:
                pass

        script.add_segment(v_seg, 'Images')

        # 4e. SFX Placement at scene boundary
        if enable_sfx and sfx_files and i > 0:
            sfx_p = sfx_files[i % len(sfx_files)]
            try:
                sfx_mat = cc.AudioMaterial(sfx_p)
                sfx_dur = min(sfx_mat.duration, 600000)
                # Center SFX around cut point
                sfx_st = max(0, st_us - 100000)
                sfx_seg = cc.AudioSegment(
                    sfx_mat,
                    target_timerange=cc.trange(sfx_st, sfx_dur),
                    source_timerange=cc.trange(0, sfx_dur),
                    volume=sfx_volume
                )
                script.add_segment(sfx_seg, 'SFX')
            except Exception:
                pass

        if i % 10 == 0 or i == num_scenes - 1:
            report(f"Đã thêm cảnh {i + 1}/{num_scenes} ({os.path.basename(img_p)})", 0.28 + 0.45 * ((i + 1) / num_scenes))

    # 5. SUBTITLE TRACK (With Color Palettes & Stroke)
    if import_subtitles and srt_path and os.path.exists(srt_path):
        report("Đang nạp phụ đề phong cách hiện đại...", 0.78)
        color_rgb = SUBTITLE_COLORS.get(subtitle_style.lower(), SUBTITLE_COLORS['yellow'])
        try:
            style_template = cc.TextSegment(
                "Template",
                cc.trange(0, 1000),
                style=cc.TextStyle(
                    size=8.5,
                    bold=True,
                    color=color_rgb,
                    align=1,
                    auto_wrapping=True,
                    max_line_width=0.85
                ),
                border=cc.TextBorder(
                    alpha=1.0,
                    color=(0.0, 0.0, 0.0),
                    width=45.0
                )
            )

            script.import_srt(
                srt_path,
                'Subtitles',
                style_reference=style_template,
                clip_settings=cc.ClipSettings(transform_y=-0.75)
            )
            report("Đã hoàn tất nạp phụ đề!", 0.86)
        except Exception as e:
            report(f"Lỗi nạp phụ đề: {e}", 0.86)

    # 6. CTA SUBSCRIBE BANNER & CHIME
    if enable_cta_subscribe and total_audio_us > 10000000:
        report("Đang chèn CTA Kêu gọi Đăng ký (Subscribe)...", 0.90)
        try:
            cta_start_us = max(0, total_audio_us - 8000000)  # Last 8 seconds
            cta_dur_us = 6000000

            script.add_track(cc.TrackType.text, 'CTA_Subscribe')
            cta_seg = cc.TextSegment(
                "🔔 ĐĂNG KÝ KÊNH ĐỂ XEM TIẾP!",
                cc.trange(cta_start_us, cta_dur_us),
                style=cc.TextStyle(
                    size=9.5,
                    bold=True,
                    color=(1.0, 0.9, 0.2),
                    align=1
                ),
                border=cc.TextBorder(alpha=1.0, color=(0.1, 0.1, 0.1), width=45.0),
                clip_settings=cc.ClipSettings(transform_y=-0.50)
            )
            script.add_segment(cta_seg, 'CTA_Subscribe')

            # Chime ding sound for CTA
            ding_p = os.path.join(sfx_dir, 'ding.wav')
            if os.path.exists(ding_p):
                if 'SFX' not in script.tracks:
                    script.add_track(cc.TrackType.audio, 'SFX')
                ding_mat = cc.AudioMaterial(ding_p)
                ding_seg = cc.AudioSegment(
                    ding_mat,
                    target_timerange=cc.trange(cta_start_us, min(ding_mat.duration, 1500000)),
                    source_timerange=cc.trange(0, min(ding_mat.duration, 1500000)),
                    volume=0.55
                )
                script.add_segment(ding_seg, 'SFX')
        except Exception:
            pass

    # 7. SAVE AND REGISTER
    report("Đang lưu dự án và đăng ký vào CapCut...", 0.94)
    script.save()

    draft_dir = os.path.join(draft_root, draft_name)
    cover_image = image_paths[0] if image_paths else None
    register_draft_in_root_meta(
        draft_root=draft_root,
        draft_name=draft_name,
        draft_dir=draft_dir,
        duration_us=total_audio_us,
        cover_image_path=cover_image
    )

    report("Hoàn tất tạo dự án CapCut thành công!", 1.0)

    return {
        'status': 'success',
        'draft_name': draft_name,
        'draft_dir': draft_dir,
        'draft_root': draft_root,
        'total_scenes': num_scenes,
        'total_images': min(num_images, num_scenes),
        'duration_seconds': total_audio_us / 1000000.0,
        'cover_image': cover_image
    }
