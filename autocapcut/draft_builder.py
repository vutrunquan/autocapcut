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
import sys
import random
from typing import List, Dict, Any, Optional, Callable, Union
import pycapcut as cc
from .utils import register_draft_in_root_meta, get_audio_duration_ms
from .image_loader import remove_gemini_watermark_from_image, batch_remove_gemini_watermarks


# Mapping user transition names to pycapcut TransitionType enums
TRANSITIONS_MAP = {
    "none": None,
    "không transition": None,
    "random": "RANDOM",
    "ngẫu nhiên": "RANDOM",
    "dissolve": getattr(cc.TransitionType, "叠化", None),
    "mờ chồng (dissolve)": getattr(cc.TransitionType, "叠化", None),
    "black fade": getattr(cc.TransitionType, "闪黑", None),
    "mờ đen (black fade)": getattr(cc.TransitionType, "闪黑", None),
    "white flash": getattr(cc.TransitionType, "闪白", None),
    "chớp trắng (white flash)": getattr(cc.TransitionType, "闪白", None),
    "swipe left": getattr(cc.TransitionType, "Swipe_Left", None),
    "gạt sang trái (swipe left)": getattr(cc.TransitionType, "Swipe_Left", None),
    "corner slide": getattr(cc.TransitionType, "Corner_Slide", None),
    "trượt góc (corner slide)": getattr(cc.TransitionType, "Corner_Slide", None),
    "flip zoom": getattr(cc.TransitionType, "Flip_Zoom", None),
    "lật thu phóng (flip zoom)": getattr(cc.TransitionType, "Flip_Zoom", None),
    "zoom transition": getattr(cc.TransitionType, "Zoom_Transition", None),
    "thu phóng nhanh (zoom)": getattr(cc.TransitionType, "Zoom_Transition", None),
    "signal glitch": getattr(cc.TransitionType, "Signal_Glitch_2", None),
    "nhiễu sóng (signal glitch)": getattr(cc.TransitionType, "Signal_Glitch_2", None),
    "slide drop": getattr(cc.TransitionType, "Slide_Drop", None),
    "rơi trượt (slide drop)": getattr(cc.TransitionType, "Slide_Drop", None),
    "slide interface": getattr(cc.TransitionType, "Slide_Interface", None),
    "trượt giao diện (slide interface)": getattr(cc.TransitionType, "Slide_Interface", None),
    "snap zoom": getattr(cc.TransitionType, "Snap_Zoom", None),
    "búng zoom (snap zoom)": getattr(cc.TransitionType, "Snap_Zoom", None),
    "light wipe": getattr(cc.TransitionType, "阳光擦拭", None),
    "vệt sáng quét (light wipe)": getattr(cc.TransitionType, "阳光擦拭", None),
}
AVAILABLE_TRANSITIONS = [v for k, v in TRANSITIONS_MAP.items() if v and v != "RANDOM"]

# Mapping Clip In-Animation names
INTROS_MAP = {
    "none": None,
    "không animation": None,
    "random": "RANDOM",
    "ngẫu nhiên": "RANDOM",
    "zoom in": getattr(cc.IntroType, "放大", None),
    "thu phóng vào (zoom in)": getattr(cc.IntroType, "放大", None),
    "dynamic zoom in": getattr(cc.IntroType, "动感放大", None),
    "phóng to năng động (dynamic zoom in)": getattr(cc.IntroType, "动感放大", None),
    "dynamic zoom out": getattr(cc.IntroType, "动感缩小", None),
    "thu nhỏ năng động (dynamic zoom out)": getattr(cc.IntroType, "动感缩小", None),
    "fade in": getattr(cc.IntroType, "渐显", None),
    "mờ dần xuất hiện (fade in)": getattr(cc.IntroType, "渐显", None),
    "blur fade in": getattr(cc.IntroType, "模糊渐显", None),
    "mờ ảo tỏ dần (blur fade in)": getattr(cc.IntroType, "模糊渐显", None),
    "shake horizontal": getattr(cc.IntroType, "左右抖动", None),
    "lắc ngang nảy (horizontal shake)": getattr(cc.IntroType, "左右抖动", None),
    "shake vertical": getattr(cc.IntroType, "上下抖动", None),
    "lắc dọc nảy (vertical shake)": getattr(cc.IntroType, "上下抖动", None),
    "slide up": getattr(cc.IntroType, "向上滑动", None),
    "trượt từ dưới lên (slide up)": getattr(cc.IntroType, "向上滑动", None),
    "slide down": getattr(cc.IntroType, "向下滑动", None),
    "trượt từ trên xuống (slide down)": getattr(cc.IntroType, "向下滑动", None),
    "slide right": getattr(cc.IntroType, "向右滑动", None),
    "trượt từ trái sang (slide right)": getattr(cc.IntroType, "向右滑动", None),
    "slide left": getattr(cc.IntroType, "向左滑动", None),
    "trượt từ phải sang (slide left)": getattr(cc.IntroType, "向左滑动", None),
    "spin open": getattr(cc.IntroType, "旋转开幕", None),
    "xoay mở màn (spin open)": getattr(cc.IntroType, "旋转开幕", None),
}
AVAILABLE_INTROS = [v for k, v in INTROS_MAP.items() if v and v != "RANDOM"]

# Mapping Video Scene Effects
EFFECTS_MAP = {
    "none": None,
    "không dùng hiệu ứng": None,
    "random": "RANDOM",
    "ngẫu nhiên": "RANDOM",
    "focus shake": getattr(cc.VideoSceneEffectType, "Focus_Shake", None),
    "rung lắc tiêu điểm (focus shake)": getattr(cc.VideoSceneEffectType, "Focus_Shake", None),
    "rgb shake": getattr(cc.VideoSceneEffectType, "RGB_Shake", None),
    "rung tách màu rgb (rgb shake)": getattr(cc.VideoSceneEffectType, "RGB_Shake", None),
    "pixel glitch": getattr(cc.VideoSceneEffectType, "Pixel_Glitch", None),
    "nhiễu hạt pixel (pixel glitch)": getattr(cc.VideoSceneEffectType, "Pixel_Glitch", None),
    "glitch intro": getattr(cc.VideoSceneEffectType, "Glitch_Intro", None),
    "giật sóng mở màn (glitch intro)": getattr(cc.VideoSceneEffectType, "Glitch_Intro", None),
    "bouncing glow": getattr(cc.VideoSceneEffectType, "Bouncing_Glow", None),
    "hào quang nhấp nháy (bouncing glow)": getattr(cc.VideoSceneEffectType, "Bouncing_Glow", None),
    "flash": getattr(cc.VideoSceneEffectType, "Flash", None),
    "chớp sáng kịch tính (flash)": getattr(cc.VideoSceneEffectType, "Flash", None),
    "neon flash": getattr(cc.VideoSceneEffectType, "Neon_Flash", None),
    "ánh đèn neon (neon flash)": getattr(cc.VideoSceneEffectType, "Neon_Flash", None),
    "vintage flash": getattr(cc.VideoSceneEffectType, "Vintage_Flash", None),
    "chớp phim cổ điển (vintage flash)": getattr(cc.VideoSceneEffectType, "Vintage_Flash", None),
}
AVAILABLE_EFFECTS = [v for k, v in EFFECTS_MAP.items() if v and v != "RANDOM"]

# Mapping filter names to pycapcut FilterType enums
FILTERS_MAP = {
    "none": None,
    "không dùng filter": None,
    "soft grain": getattr(cc.FilterType, "Soft_Grain", None),
    "soft grain (hạt phim điện ảnh)": getattr(cc.FilterType, "Soft_Grain", None),
    "vintage 1980": getattr(cc.FilterType, "_1980", None),
    "vintage 1980 (tông màu cổ điển)": getattr(cc.FilterType, "_1980", None),
    "vhs": getattr(cc.FilterType, "VHS_I", None),
    "vhs retro (băng từ vhs)": getattr(cc.FilterType, "VHS_I", None),
    "peach": getattr(cc.FilterType, "Peach_Fuzz", None),
    "peach fuzz (tông ấm điện ảnh)": getattr(cc.FilterType, "Peach_Fuzz", None),
    "lover blue": getattr(cc.FilterType, "Lover_Blue", None),
    "lover blue (tông lạnh điện ảnh)": getattr(cc.FilterType, "Lover_Blue", None),
    "bw": getattr(cc.FilterType, "BW_2", None),
    "bw retro (trắng đen cổ điển)": getattr(cc.FilterType, "BW_2", None),
}

# Subtitle In-Animation
TEXT_INTROS_MAP = {
    "none": None,
    "tĩnh (không animation)": None,
    "bounce": getattr(cc.TextIntro, "向上弹入", None),
    "nảy chữ lên (bounce pop)": getattr(cc.TextIntro, "向上弹入", None),
    "karaoke": getattr(cc.TextIntro, "卡拉OK", None),
    "chạy từng chữ (karaoke reveal)": getattr(cc.TextIntro, "卡拉OK", None),
    "playful": getattr(cc.TextIntro, "可爱悦动", None),
    "nhịp điệu vui nhộn (playful bounce)": getattr(cc.TextIntro, "可爱悦动", None),
    "slide up": getattr(cc.TextIntro, "向上滑动", None),
    "trượt mượt lên (slide up)": getattr(cc.TextIntro, "向上滑动", None),
    "slide right": getattr(cc.TextIntro, "向右滑动", None),
    "quét từ trái sang (slide right)": getattr(cc.TextIntro, "向右滑动", None),
}

# Subtitle color palettes (R, G, B in 0.0 - 1.0)
SUBTITLE_COLORS = {
    "yellow": (0.99, 0.85, 0.21),  # Viral Yellow (#fbbf24)
    "white": (1.0, 1.0, 1.0),      # Classic White (#ffffff)
    "cyan": (0.22, 0.74, 0.97),    # Tech Cyan (#38bdf8)
    "green": (0.29, 0.87, 0.50),   # Finance Green (#4ade80)
    "red": (0.94, 0.27, 0.27),     # Ruby Red (#ef4444)
    "purple": (0.66, 0.33, 0.97),  # Neon Purple (#a855f7)
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
    # Transitions
    transition_name: str = "none",
    transition_duration: float = 0.5,
    transition_mode: str = "all",       # 'all', 'random', 'alternate'
    # Clip In-Animations (Intros)
    clip_intro: str = "none",
    clip_intro_duration: float = 0.8,
    clip_intro_mode: str = "all",       # 'all', 'random', 'first_only'
    # Video Scene Effects
    video_effect: str = "none",
    video_effect_scope: str = "all",    # 'all', 'random', 'intro_outro'
    # Cinematic Filters
    filter_name: str = "none",
    filter_intensity: float = 60.0,
    # Camera Motions (Ken Burns)
    camera_motion: str = "smart_pacing", # 'smart_pacing', 'zoom_in', 'zoom_out', 'pan_left', 'pan_right', 'pan_up', 'pan_down', 'random', 'none'
    zoom_scale: float = 112.0,
    keyframe_config: Optional[Dict[str, Any]] = None,
    smart_pacing: bool = True,
    canvas_blur: bool = True,
    # Subtitles & Typography
    import_subtitles: bool = True,
    subtitle_style: str = "yellow",
    subtitle_animation: str = "bounce",
    subtitle_font_size: float = 8.5,
    subtitle_position: str = "bottom",  # 'bottom', 'center', 'top'
    # Audio Suite
    enable_sfx: bool = True,
    sfx_name: str = "random",           # 'random', 'whoosh', 'swoosh', 'pop', 'ding'
    sfx_volume: float = 0.50,
    bgm_volume: float = 0.15,
    audio_ducking: bool = True,
    audio_fade: bool = True,
    enable_cta_subscribe: bool = True,
    remove_gemini_watermark: bool = False,
    progress_callback: Optional[Callable[[str, float], None]] = None
) -> Dict[str, Any]:
    """
    Build complete CapCut draft project with full pro features and extensive effect controls.
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

    # 2. BGM TRACK (With Built-in Presets, Audio Ducking & Fade)
    assets_dir = os.path.join(getattr(sys, '_MEIPASS', ''), 'assets')
    if not os.path.isdir(assets_dir):
        assets_dir = os.path.join(os.path.dirname(sys.executable), 'assets')
    if not os.path.isdir(assets_dir):
        assets_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'assets')
    if not os.path.isdir(assets_dir):
        assets_dir = os.path.join(os.getcwd(), 'assets')

    bgm_dir = os.path.join(assets_dir, 'bgm')
    preset_map = {
        'cinematic': 'cinematic_storytelling.wav',
        'điện ảnh': 'cinematic_storytelling.wav',
        'sâu lắng': 'cinematic_storytelling.wav',
        'storytelling': 'cinematic_storytelling.wav',
        'news': 'news_finance_tech.wav',
        'tin tức': 'news_finance_tech.wav',
        'tài chính': 'news_finance_tech.wav',
        'finance': 'news_finance_tech.wav',
        'tech': 'news_finance_tech.wav',
        'lofi': 'lofi_chill_podcast.wav',
        'chill': 'lofi_chill_podcast.wav',
        'thư giãn': 'lofi_chill_podcast.wav',
        'podcast': 'lofi_chill_podcast.wav',
        'dramatic': 'dramatic_suspense.wav',
        'kịch tính': 'dramatic_suspense.wav',
        'hồi hộp': 'dramatic_suspense.wav',
        'suspense': 'dramatic_suspense.wav',
        'thriller': 'dramatic_suspense.wav',
        'happy': 'happy_vlog_upbeat.wav',
        'vlog': 'happy_vlog_upbeat.wav',
        'vui tươi': 'happy_vlog_upbeat.wav',
        'năng động': 'happy_vlog_upbeat.wav',
        'upbeat': 'happy_vlog_upbeat.wav',
    }

    resolved_bgm = []
    if bgm_files:
        for b_in in bgm_files:
            b_clean = b_in.strip()
            if not b_clean or b_clean.lower() in ('none', 'không dùng nhạc nền', 'không'):
                continue
            if os.path.exists(b_clean):
                resolved_bgm.append(b_clean)
                continue
            b_lower = b_clean.lower()
            matched_p = None
            for kw, fname in preset_map.items():
                if kw in b_lower:
                    matched_p = fname
                    break
            if matched_p and os.path.isdir(bgm_dir):
                p_file = os.path.join(bgm_dir, matched_p)
                if os.path.exists(p_file):
                    resolved_bgm.append(p_file)

    if resolved_bgm:
        report("Đang cấu hình nhạc nền (BGM) & Audio Ducking...", 0.16)
        script.add_track(cc.TrackType.audio, 'BGM')
        curr_bgm_us = 0
        bgm_idx = 0
        bgm_base_vol = (bgm_volume * 0.75) if audio_ducking else bgm_volume

        while curr_bgm_us < total_audio_us and resolved_bgm:
            bgm_p = resolved_bgm[bgm_idx % len(resolved_bgm)]
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

    # 3. SFX AUDIO TRACK (Rich Transition Sound Effects Suite)
    sfx_dir = os.path.join(assets_dir, 'sfx')
    sfx_files = []
    if enable_sfx and os.path.isdir(sfx_dir):
        all_sfx = [
            os.path.join(sfx_dir, f) for f in os.listdir(sfx_dir)
            if f.lower().endswith(('.wav', '.mp3'))
        ]
        s_target = sfx_name.strip().lower()
        if s_target in ('none', 'không dùng sfx'):
            sfx_files = []
        elif s_target in ('random', 'ngẫu nhiên', ''):
            # Smart random: pool of clean transition whooshes/swooshes/pops/clicks
            sfx_files = [f for f in all_sfx if not os.path.basename(f).lower().startswith(('keyboard', 'ding'))]
            if not sfx_files:
                sfx_files = all_sfx
        else:
            # Keyword matching for specific sound choices
            keywords = []
            if 'deep' in s_target or 'trầm' in s_target:
                keywords = ['whoosh_cinematic_deep', 'whoosh_heavy_bass']
            elif 'fast whoosh' in s_target or 'lướt nhanh' in s_target:
                keywords = ['whoosh_fast', 'whoosh_1']
            elif 'air' in s_target or 'gió' in s_target:
                keywords = ['whoosh_soft_air']
            elif 'bass' in s_target:
                keywords = ['whoosh_heavy_bass']
            elif 'whoosh' in s_target:
                keywords = ['whoosh']
            elif 'whip' in s_target:
                keywords = ['swoosh_fast_whip']
            elif 'slide' in s_target or 'trượt' in s_target:
                keywords = ['swoosh_slide']
            elif 'swoosh' in s_target or 'vút' in s_target:
                keywords = ['swoosh']
            elif 'camera' in s_target or 'chụp' in s_target:
                keywords = ['camera_shutter']
            elif 'click' in s_target or 'chuột' in s_target:
                keywords = ['mouse_click']
            elif 'phím' in s_target or 'keyboard' in s_target or 'typewriter' in s_target:
                keywords = ['keyboard_typing']
            elif 'pop' in s_target or 'bong bóng' in s_target:
                keywords = ['bubble_pop', 'pop']
            elif 'kaching' in s_target or 'tiền' in s_target or 'cash' in s_target:
                keywords = ['cash_register_kaching']
            elif 'boom' in s_target or 'impact' in s_target or 'va đập' in s_target:
                keywords = ['cinematic_boom_impact']
            elif 'ding' in s_target or 'keng' in s_target or 'chuông' in s_target:
                keywords = ['bell_ding_chime', 'ding']
            elif 'rewind' in s_target or 'băng' in s_target:
                keywords = ['tape_rewind']
            elif 'glitch' in s_target or 'nhiễu' in s_target:
                keywords = ['glitch_digital']

            matched = []
            for kw in keywords:
                for f in all_sfx:
                    if kw in os.path.basename(f).lower() and f not in matched:
                        matched.append(f)
            if not matched:
                matched = [f for f in all_sfx if any(p in os.path.basename(f).lower() for p in s_target.split())]
            sfx_files = matched if matched else all_sfx

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
    is_trans_random = t_key in ('random', 'ngẫu nhiên') or transition_mode.lower() == 'random'
    trans_dur_target_us = int(max(0.2, min(2.5, transition_duration)) * 1000000)

    # Resolve clip intro animation
    intro_key = clip_intro.strip().lower()
    intro_anim_type = INTROS_MAP.get(intro_key)
    is_intro_random = intro_key in ('random', 'ngẫu nhiên')
    intro_dur_target_us = int(max(0.2, min(3.0, clip_intro_duration)) * 1000000)

    # Resolve video scene effect
    eff_key = video_effect.strip().lower()
    eff_type = EFFECTS_MAP.get(eff_key)
    is_eff_random = eff_key in ('random', 'ngẫu nhiên')

    # Resolve cinematic filter
    f_key = filter_name.strip().lower()
    cinematic_filter = FILTERS_MAP.get(f_key)

    # Motion scale
    scale_factor = max(1.02, min(1.50, float(zoom_scale) / 100.0))
    cam_mode = camera_motion.strip().lower()
    if not smart_pacing and cam_mode == 'smart_pacing':
        cam_mode = 'zoom_in'

    # Clean watermark if requested using GargantuaX/gemini-watermark-remover
    if remove_gemini_watermark and image_paths:
        report("Đang xóa watermark Gemini (Reverse Alpha Blending)...", 0.24)
        cache_dir = os.path.join(draft_root, draft_name, "_wm_clean")
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

        # 4b. Clip In-Animation (Intro)
        apply_intro = False
        if clip_intro_mode == 'first_only':
            apply_intro = (i == 0)
        elif clip_intro_mode == 'random':
            apply_intro = (i == 0 or random.random() < 0.45)
        else: # 'all'
            apply_intro = True

        if apply_intro:
            cur_intro = random.choice(AVAILABLE_INTROS) if (is_intro_random and AVAILABLE_INTROS) else intro_anim_type
            if cur_intro:
                try:
                    act_intro_dur = min(intro_dur_target_us, dur_us)
                    v_seg.add_animation(cur_intro, duration=act_intro_dur)
                except Exception:
                    pass

        # 4c. Video Scene Effect
        apply_eff = False
        if video_effect_scope == 'intro_outro':
            apply_eff = (i == 0 or i == num_scenes - 1)
        elif video_effect_scope == 'random':
            apply_eff = (i == 0 or (i % 3 == 0) or random.random() < 0.35)
        else: # 'all'
            apply_eff = True

        if apply_eff:
            cur_eff = random.choice(AVAILABLE_EFFECTS) if (is_eff_random and AVAILABLE_EFFECTS) else eff_type
            if cur_eff:
                try:
                    v_seg.add_effect(cur_eff)
                except Exception:
                    pass

        # 4d. Cinematic Filter
        if cinematic_filter:
            try:
                v_seg.add_filter(cinematic_filter, intensity=float(filter_intensity))
            except Exception:
                pass

        # 4e. Camera Motion / Ken Burns
        if cam_mode in ('smart_pacing', 'thông minh'):
            if dur_s < 3.0:
                # Fast zoom-in for punchy energy
                v_seg.add_keyframe(cc.KeyframeProperty.uniform_scale, 0, 1.0)
                v_seg.add_keyframe(cc.KeyframeProperty.uniform_scale, dur_us, scale_factor)
            elif dur_s > 6.0:
                # Long line: Slow Pan across with zoom
                v_seg.add_keyframe(cc.KeyframeProperty.uniform_scale, 0, scale_factor)
                v_seg.add_keyframe(cc.KeyframeProperty.uniform_scale, dur_us, scale_factor)
                v_seg.add_keyframe(cc.KeyframeProperty.position_x, 0, 0.05)
                v_seg.add_keyframe(cc.KeyframeProperty.position_x, dur_us, -0.05)
            else:
                # Alternate zoom in / slow pan
                if i % 2 == 0:
                    v_seg.add_keyframe(cc.KeyframeProperty.uniform_scale, 0, 1.0)
                    v_seg.add_keyframe(cc.KeyframeProperty.uniform_scale, dur_us, scale_factor)
                else:
                    v_seg.add_keyframe(cc.KeyframeProperty.uniform_scale, 0, scale_factor)
                    v_seg.add_keyframe(cc.KeyframeProperty.uniform_scale, dur_us, 1.0)
        elif cam_mode in ('zoom_in', 'phóng to'):
            v_seg.add_keyframe(cc.KeyframeProperty.uniform_scale, 0, 1.0)
            v_seg.add_keyframe(cc.KeyframeProperty.uniform_scale, dur_us, scale_factor)
        elif cam_mode in ('zoom_out', 'thu nhỏ'):
            v_seg.add_keyframe(cc.KeyframeProperty.uniform_scale, 0, scale_factor)
            v_seg.add_keyframe(cc.KeyframeProperty.uniform_scale, dur_us, 1.0)
        elif cam_mode in ('pan_left', 'sang trái'):
            v_seg.add_keyframe(cc.KeyframeProperty.uniform_scale, 0, scale_factor)
            v_seg.add_keyframe(cc.KeyframeProperty.uniform_scale, dur_us, scale_factor)
            v_seg.add_keyframe(cc.KeyframeProperty.position_x, 0, 0.05)
            v_seg.add_keyframe(cc.KeyframeProperty.position_x, dur_us, -0.05)
        elif cam_mode in ('pan_right', 'sang phải'):
            v_seg.add_keyframe(cc.KeyframeProperty.uniform_scale, 0, scale_factor)
            v_seg.add_keyframe(cc.KeyframeProperty.uniform_scale, dur_us, scale_factor)
            v_seg.add_keyframe(cc.KeyframeProperty.position_x, 0, -0.05)
            v_seg.add_keyframe(cc.KeyframeProperty.position_x, dur_us, 0.05)
        elif cam_mode in ('pan_up', 'lên trên'):
            v_seg.add_keyframe(cc.KeyframeProperty.uniform_scale, 0, scale_factor)
            v_seg.add_keyframe(cc.KeyframeProperty.uniform_scale, dur_us, scale_factor)
            v_seg.add_keyframe(cc.KeyframeProperty.position_y, 0, -0.05)
            v_seg.add_keyframe(cc.KeyframeProperty.position_y, dur_us, 0.05)
        elif cam_mode in ('pan_down', 'xuống dưới'):
            v_seg.add_keyframe(cc.KeyframeProperty.uniform_scale, 0, scale_factor)
            v_seg.add_keyframe(cc.KeyframeProperty.uniform_scale, dur_us, scale_factor)
            v_seg.add_keyframe(cc.KeyframeProperty.position_y, 0, 0.05)
            v_seg.add_keyframe(cc.KeyframeProperty.position_y, dur_us, -0.05)
        elif cam_mode in ('random', 'ngẫu nhiên'):
            rand_m = i % 4
            if rand_m == 0:
                v_seg.add_keyframe(cc.KeyframeProperty.uniform_scale, 0, 1.0)
                v_seg.add_keyframe(cc.KeyframeProperty.uniform_scale, dur_us, scale_factor)
            elif rand_m == 1:
                v_seg.add_keyframe(cc.KeyframeProperty.uniform_scale, 0, scale_factor)
                v_seg.add_keyframe(cc.KeyframeProperty.uniform_scale, dur_us, 1.0)
            elif rand_m == 2:
                v_seg.add_keyframe(cc.KeyframeProperty.uniform_scale, 0, scale_factor)
                v_seg.add_keyframe(cc.KeyframeProperty.uniform_scale, dur_us, scale_factor)
                v_seg.add_keyframe(cc.KeyframeProperty.position_x, 0, 0.05)
                v_seg.add_keyframe(cc.KeyframeProperty.position_x, dur_us, -0.05)
            else:
                v_seg.add_keyframe(cc.KeyframeProperty.uniform_scale, 0, scale_factor)
                v_seg.add_keyframe(cc.KeyframeProperty.uniform_scale, dur_us, scale_factor)
                v_seg.add_keyframe(cc.KeyframeProperty.position_x, 0, -0.05)
                v_seg.add_keyframe(cc.KeyframeProperty.position_x, dur_us, 0.05)

        # 4f. Transition at scene boundary
        if i < num_scenes - 1:
            apply_trans = True
            if transition_mode == 'alternate' and (i % 2 != 0):
                apply_trans = False

            if apply_trans:
                cur_trans = random.choice(AVAILABLE_TRANSITIONS) if (is_trans_random and AVAILABLE_TRANSITIONS) else transition_type
                if cur_trans:
                    trans_dur = min(trans_dur_target_us, max(200000, dur_us // 3))
                    try:
                        v_seg.add_transition(cur_trans, duration=trans_dur)
                    except Exception:
                        pass

        script.add_segment(v_seg, 'Images')

        # 4g. SFX Placement at scene boundary
        if enable_sfx and sfx_files and i > 0:
            sfx_p = sfx_files[i % len(sfx_files)]
            try:
                sfx_mat = cc.AudioMaterial(sfx_p)
                sfx_dur = min(sfx_mat.duration, 2500000)
                # Center SFX around cut point
                sfx_st = max(0, st_us - 120000)
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

    # 5. SUBTITLE TRACK (With Animation, Color Palettes & Stroke)
    if import_subtitles and srt_path and os.path.exists(srt_path):
        report("Đang nạp phụ đề phong cách hiện đại...", 0.78)
        color_rgb = SUBTITLE_COLORS.get(subtitle_style.lower(), SUBTITLE_COLORS['yellow'])
        pos_y_map = {'bottom': -0.75, 'dưới cùng': -0.75, 'center': 0.0, 'chính giữa': 0.0, 'top': 0.75, 'trên cùng': 0.75}
        trans_y = pos_y_map.get(subtitle_position.lower(), -0.75)
        f_size = max(5.0, min(16.0, float(subtitle_font_size)))

        try:
            style_template = cc.TextSegment(
                "Template",
                cc.trange(0, 1000),
                style=cc.TextStyle(
                    size=f_size,
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

            # Subtitle In-Animation
            sub_anim_key = subtitle_animation.strip().lower()
            text_intro_enum = TEXT_INTROS_MAP.get(sub_anim_key)
            if text_intro_enum:
                try:
                    style_template.add_animation(text_intro_enum, duration=400000)
                except Exception:
                    pass

            script.import_srt(
                srt_path,
                'Subtitles',
                style_reference=style_template,
                clip_settings=cc.ClipSettings(transform_y=trans_y)
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
