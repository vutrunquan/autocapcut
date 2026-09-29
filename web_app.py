"""
Web Interface for AutoCapCut Pro.
Designed with a soothing, eye-friendly Slate & Indigo aesthetic,
balanced cards, intuitive inputs, 1-Click Pro Presets, live scene alignment preview,
and real-time WebSocket progress logs.
"""

import os
import sys
import json
import asyncio
import subprocess
from typing import Optional, List, Dict, Any, Union
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

from autocapcut import (
    run_autocapcut,
    parse_script_input,
    get_default_capcut_draft_path,
    get_capcut_exe_path,
    get_audio_duration_ms,
    parse_srt,
    load_sorted_media,
    align_scenes_with_srt,
    format_time_ms
)

app = FastAPI(title="AutoCapCut Pro Web")


class PreviewRequest(BaseModel):
    srt_path: str
    script_source: str
    voice_paths: str
    images_dir: str
    sort_mode: str = "abc"


@app.get("/api/defaults")
def get_defaults():
    draft_root = get_default_capcut_draft_path()
    sample_dir = r"C:\Users\vutru\OneDrive\Desktop\New folder (2)"
    defaults = {
        "draft_root": draft_root or "",
        "capcut_installed": bool(draft_root and os.path.exists(draft_root)),
        "srt_path": "",
        "script_content": "",
        "voice_path": "",
        "images_dir": "",
        "bgm_path": ""
    }
    if os.path.exists(sample_dir):
        files = os.listdir(sample_dir)
        for f in files:
            p = os.path.join(sample_dir, f)
            if f.lower().endswith(".srt") and not defaults["srt_path"]:
                defaults["srt_path"] = p
            elif f.lower().endswith(".txt") and not defaults["script_content"]:
                try:
                    with open(p, "r", encoding="utf-8-sig", errors="replace") as fo:
                        defaults["script_content"] = fo.read()
                except Exception:
                    pass
            elif f.lower().endswith((".wav", ".mp3", ".m4a")) and not defaults["voice_path"]:
                defaults["voice_path"] = p
            elif os.path.isdir(p) and not defaults["images_dir"]:
                defaults["images_dir"] = p
    return defaults


@app.post("/api/preview")
def preview_alignment(req: PreviewRequest):
    try:
        if not os.path.exists(req.srt_path):
            raise HTTPException(400, f"File SRT không tồn tại: {req.srt_path}")
        if not os.path.isdir(req.images_dir):
            raise HTTPException(400, f"Thư mục media không tồn tại: {req.images_dir}")

        v_list = [p.strip() for p in req.voice_paths.split(';') if p.strip()]
        if not v_list:
            raise HTTPException(400, "Vui lòng nhập đường dẫn file Voice!")

        total_audio_ms = sum(get_audio_duration_ms(vf) for vf in v_list)
        subtitles = parse_srt(req.srt_path)
        script_lines = parse_script_input(req.script_source)
        media_paths = load_sorted_media(req.images_dir, sort_mode=req.sort_mode)
        scenes = align_scenes_with_srt(script_lines, subtitles, total_audio_ms)

        preview_scenes = []
        for i, sc in enumerate(scenes):
            m_file = os.path.basename(media_paths[i]) if i < len(media_paths) else "Lặp lại media cuối"
            preview_scenes.append({
                "scene_num": i + 1,
                "media_file": m_file,
                "start_time": format_time_ms(sc["start_ms"]),
                "end_time": format_time_ms(sc["end_ms"]),
                "duration_s": round(sc["duration_ms"] / 1000, 2),
                "script_text": sc["text"]
            })

        return {
            "status": "success",
            "total_audio_ms": total_audio_ms,
            "total_audio_formatted": format_time_ms(total_audio_ms),
            "total_scenes": len(scenes),
            "total_media": len(media_paths),
            "total_subtitles": len(subtitles),
            "scenes": preview_scenes
        }
    except Exception as e:
        raise HTTPException(500, str(e))


@app.post("/api/launch-capcut")
def launch_capcut():
    exe = get_capcut_exe_path()
    if exe and os.path.exists(exe):
        try:
            subprocess.Popen([exe])
            return {"status": "success", "message": f"Đã khởi chạy CapCut: {exe}"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    return {"status": "error", "message": "Không tìm thấy CapCut.exe"}


@app.websocket("/ws/build")
async def ws_build(websocket: WebSocket):
    await websocket.accept()
    try:
        data_text = await websocket.receive_text()
        req = json.loads(data_text)
        loop = asyncio.get_running_loop()

        def sync_progress(msg: str, pct: float):
            asyncio.run_coroutine_threadsafe(
                websocket.send_json({"type": "progress", "message": msg, "percent": round(pct * 100, 1)}),
                loop
            )

        def run_sync():
            voice_files = [p.strip() for p in req["voice_paths"].split(';') if p.strip()]
            bgm_files = [p.strip() for p in req.get("bgm_paths", "").split(';') if p.strip()] or None

            return run_autocapcut(
                srt_path=req["srt_path"],
                script_source=req["script_source"],
                voice_paths=voice_files,
                images_dir=req["images_dir"],
                project_name=req.get("project_name", "AutoCapCut_Project"),
                draft_root=req.get("draft_root") or None,
                bgm_paths=bgm_files,
                sort_mode=req.get("sort_mode", "abc"),
                # Transitions
                transition=req.get("transition", "none"),
                transition_duration=float(req.get("transition_duration", 0.5)),
                transition_mode=req.get("transition_mode", "all"),
                # Clip In-Animations
                clip_intro=req.get("clip_intro", "none"),
                clip_intro_duration=float(req.get("clip_intro_duration", 0.8)),
                clip_intro_mode=req.get("clip_intro_mode", "all"),
                # Video Scene Effects
                video_effect=req.get("video_effect", "none"),
                video_effect_scope=req.get("video_effect_scope", "all"),
                # Filters
                filter_name=req.get("filter_name", "none"),
                filter_intensity=float(req.get("filter_intensity", 60.0)),
                # Camera Motions
                camera_motion=req.get("camera_motion", "smart_pacing"),
                zoom_scale=float(req.get("zoom_scale", 112.0)),
                keyframe_config=req.get("keyframe_config"),
                aspect_ratio=req.get("aspect_ratio", "16:9"),
                smart_pacing=bool(req.get("smart_pacing", True)),
                canvas_blur=bool(req.get("canvas_blur", True)),
                # Subtitles
                import_subtitles=bool(req.get("import_subtitles", True)),
                subtitle_style=req.get("subtitle_style", "yellow"),
                subtitle_animation=req.get("subtitle_animation", "bounce"),
                subtitle_font_size=float(req.get("subtitle_font_size", 8.5)),
                subtitle_position=req.get("subtitle_position", "bottom"),
                # Audio Suite
                enable_sfx=bool(req.get("enable_sfx", True)),
                sfx_name=req.get("sfx_name", "random"),
                sfx_volume=float(req.get("sfx_volume", 50)) / 100.0,
                bgm_volume=float(req.get("bgm_volume", 15)) / 100.0,
                audio_ducking=bool(req.get("audio_ducking", True)),
                audio_fade=bool(req.get("audio_fade", True)),
                enable_cta_subscribe=bool(req.get("enable_cta_subscribe", True)),
                remove_gemini_watermark=bool(req.get("remove_gemini_watermark", False)),
                progress_callback=sync_progress
            )

        result = await asyncio.to_thread(run_sync)
        res_summary = {k: v for k, v in result.items() if k != "scenes_info"}
        await websocket.send_json({"type": "success", "result": res_summary})

    except WebSocketDisconnect:
        pass
    except Exception as e:
        await websocket.send_json({"type": "error", "message": str(e)})


@app.get("/", response_class=HTMLResponse)
def index_page():
    return """
<!DOCTYPE html>
<html lang="vi">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>AutoCapCut Pro - Tự Động Khớp Media & Âm Thanh Chuyên Nghiệp</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
  <style>
    :root {
      --bg: #0b0f19;
      --card: #161f30;
      --border: #22314a;
      --input: #0d131f;
      --input-border: #2a3b59;
      --text: #f8fafc;
      --sub: #94a3b8;
      --accent: #4f46e5;
      --accent-hover: #4338ca;
      --success: #059669;
      --sky: #0284c7;
      --amber: #d97706;
      --purple: #7c3aed;
      --card-inner: rgba(13, 19, 31, 0.7);
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: 'Plus Jakarta Sans', -apple-system, sans-serif;
      background-color: var(--bg);
      background-image: 
        radial-gradient(at 0% 0%, rgba(79, 70, 229, 0.12) 0px, transparent 40%),
        radial-gradient(at 100% 100%, rgba(2, 132, 199, 0.08) 0px, transparent 40%);
      color: var(--text);
      padding: 24px;
      min-height: 100vh;
      font-size: 13px;
    }
    .container { max-width: 1140px; margin: 0 auto; }
    
    /* Top Header */
    header {
      display: flex; justify-content: space-between; align-items: center;
      margin-bottom: 20px; padding-bottom: 16px; border-bottom: 1px solid var(--border);
    }
    .brand { display: flex; align-items: center; gap: 14px; }
    .brand-icon {
      width: 44px; height: 44px; border-radius: 12px;
      background: linear-gradient(135deg, #4f46e5, #0284c7);
      display: flex; align-items: center; justify-content: center;
      font-size: 22px; box-shadow: 0 4px 16px rgba(79, 70, 229, 0.3);
    }
    .brand-title h1 { font-size: 20px; font-weight: 700; color: #fff; }
    .brand-title p { font-size: 12px; color: var(--sub); margin-top: 2px; }
    .header-actions { display: flex; gap: 8px; }

    /* Preset Banner */
    .preset-card {
      background: #131c2e; border: 1px solid #2b3d5b; border-radius: 12px;
      padding: 12px 18px; margin-bottom: 16px; display: flex; align-items: center; justify-content: space-between; gap: 14px;
      box-shadow: 0 4px 16px rgba(0, 0, 0, 0.25);
    }
    .preset-title { font-weight: 700; color: #fff; display: flex; align-items: center; gap: 8px; white-space: nowrap; }

    /* Cards */
    .card {
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 14px;
      padding: 20px;
      margin-bottom: 18px;
      box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
    }
    .card-title {
      font-size: 14px; font-weight: 700; color: #fff;
      display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px;
    }

    /* Form Rows */
    .form-row { display: flex; align-items: center; margin-bottom: 12px; gap: 12px; }
    .form-row label { width: 175px; flex-shrink: 0; color: var(--text); font-weight: 500; font-size: 13px; }
    input[type="text"], select, textarea {
      background: var(--input); color: var(--text); border: 1px solid var(--input-border);
      border-radius: 8px; padding: 8px 12px; font-size: 13px; outline: none;
      transition: all 0.2s; font-family: inherit;
    }
    input[type="text"]:focus, select:focus, textarea:focus { border-color: var(--accent); }
    input[type="text"] { flex: 1; }
    
    /* Buttons */
    .btn {
      padding: 8px 16px; border-radius: 8px; font-size: 12px; font-weight: 600;
      cursor: pointer; border: none; transition: all 0.2s;
      display: inline-flex; align-items: center; justify-content: center; gap: 6px;
    }
    .btn-primary {
      background: linear-gradient(135deg, var(--accent), var(--accent-hover));
      color: #fff; box-shadow: 0 4px 14px rgba(79, 70, 229, 0.3);
    }
    .btn-primary:hover { transform: translateY(-1px); box-shadow: 0 6px 18px rgba(79, 70, 229, 0.45); }
    .btn-secondary { background: #1e293b; color: var(--text); }
    .btn-secondary:hover { background: #334155; }
    .btn-purple { background: var(--purple); color: #fff; }
    .btn-purple:hover { background: #6d28d9; }

    /* Scenes Area */
    .scenes-box {
      border: 1px solid var(--border); border-radius: 10px; background: var(--input);
      padding: 12px; margin-bottom: 12px;
    }
    .scenes-tools { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
    .scenes-badge { background: #1e293b; color: var(--sub); padding: 3px 8px; border-radius: 10px; font-size: 11px; font-weight: 600; margin-left: 8px; }
    textarea { width: 100%; height: 110px; resize: vertical; border: none; padding: 0; background: transparent; }

    /* Pro Features Grid */
    .pro-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
    .checkbox-label { display: flex; align-items: center; gap: 8px; cursor: pointer; color: var(--text); font-size: 12.5px; }
    .checkbox-label input[type="checkbox"] { accent-color: var(--accent); width: 16px; height: 16px; }

    /* Motions Grid */
    .motions-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 18px; }
    .motion-card {
      background: var(--card-inner); border: 1px solid #1f2c42;
      border-radius: 10px; padding: 12px 14px; display: flex; flex-direction: column; gap: 8px;
    }
    .motion-row { display: flex; align-items: center; gap: 8px; }
    .motion-row input[type="text"] { width: 48px; text-align: center; padding: 4px; font-size: 12px; flex: none; }
    .motion-row label { display: flex; align-items: center; gap: 6px; width: 120px; font-weight: 500; cursor: pointer; }
    .motion-row input[type="checkbox"] { accent-color: var(--accent); width: 15px; height: 15px; }

    /* Console Box */
    .console-box {
      background: #090d16; border: 1px solid var(--border); border-radius: 10px;
      padding: 14px; height: 180px; overflow-y: auto; font-family: 'JetBrains Mono', monospace;
      font-size: 12px; color: #94a3b8; white-space: pre-wrap; line-height: 1.5;
    }

    /* Progress bar */
    .progress-bar-bg { width: 100%; height: 6px; background: #1e293b; border-radius: 999px; overflow: hidden; margin-top: 14px; }
    .progress-bar-fill { height: 100%; width: 0%; background: linear-gradient(90deg, var(--accent), var(--sky)); transition: width 0.3s; }
  </style>
</head>
<body>
  <div class="container">
    <header>
      <div class="brand">
        <div class="brand-icon">⚡</div>
        <div class="brand-title">
          <h1>AutoCapCut Pro v2.5</h1>
          <p>Hệ thống tự động biên tập video AI chuyên nghiệp cho CapCut PC</p>
        </div>
      </div>
      <div class="header-actions">
        <button class="btn btn-secondary" onclick="autoLoadSamples()">✨ Tự Động Điền</button>
        <button class="btn btn-secondary" onclick="launchCapCut()">🎬 Mở CapCut</button>
      </div>
    </header>

    <!-- Card 1: Data inputs -->
    <div class="card">
      <div class="card-title"><span>📁 1. NGUỒN DỮ LIỆU ĐẦU VÀO</span></div>
      <div class="form-row">
        <label>File Voice (Âm thanh):</label>
        <input type="text" id="voice_paths" placeholder="Đường dẫn 1 hoặc nhiều file audio (.wav, .mp3, .m4a)...">
      </div>
      <div class="form-row">
        <label>File Phụ Đề (.srt):</label>
        <input type="text" id="srt_path" placeholder="Đường dẫn đến file phụ đề .srt...">
      </div>

      <!-- Scenes Textarea -->
      <div class="scenes-box">
        <div class="scenes-tools">
          <div style="display: flex; align-items: center;">
            <span style="font-weight: 600; color: #fff;">Kịch Bản Phân Cảnh (Mỗi dòng 1 ảnh/video):</span>
            <span class="scenes-badge" id="scenes_count">0 dòng</span>
          </div>
          <div style="display: flex; gap: 5px;">
            <button class="btn btn-secondary" style="padding: 4px 10px;" onclick="copyScenes()">📋 Copy</button>
            <button class="btn btn-secondary" style="padding: 4px 10px;" onclick="splitSentences()">✂️ Tách Câu</button>
            <button class="btn btn-secondary" style="padding: 4px 10px;" onclick="cleanEmptyLines()">🧹 Dọn Dòng</button>
            <button class="btn btn-secondary" style="padding: 4px 8px;" onclick="clearScenes()">✕</button>
          </div>
        </div>
        <textarea id="scenes_text" oninput="updateScenesCount()" placeholder="Chia kịch bản thành từng câu, mỗi câu một dòng rồi dán vào đây...
• Mỗi dòng tương ứng với 1 ảnh hoặc video.
• Tool sẽ tự động căn thời gian media theo đúng giọng đọc của dòng đó."></textarea>
      </div>

      <div class="form-row">
        <label>Thư Mục Chứa Media:</label>
        <input type="text" id="images_dir" placeholder="Thư mục chứa ảnh hoặc video (001.jpg, 002.jpg...)...">
      </div>

      <div class="form-row">
        <label>Nhạc Nền (BGM - Tùy chọn):</label>
        <input type="text" id="bgm_paths" placeholder="File nhạc nền (BGM)...">
        <span style="color: var(--sub); font-size: 12px; margin-left: 4px;">Âm lượng:</span>
        <input type="text" id="bgm_volume" value="15" style="width: 44px; text-align: center; flex: none;">
        <span style="color: var(--sub); font-size: 12px;">%</span>
        <button class="btn btn-secondary" style="padding: 6px 12px;" onclick="document.getElementById('bgm_paths').value=''">✕ Xóa</button>
      </div>

      <div class="form-row">
        <label>Tên Dự Án CapCut:</label>
        <input type="text" id="project_name" value="AutoCapCut_Project">
      </div>
    </div>

    <!-- 1-Click Pro Preset Banner -->
    <div class="preset-card">
      <div class="preset-title">🎯 BỘ THIẾT LẬP NHANH (1-CLICK PRO PRESETS):</div>
      <select id="preset_sel" onchange="applyPreset(this.value)" style="flex: 1; max-width: 580px; border-color: var(--accent);">
        <option value="custom">⚙️ Tùy Chỉnh Thủ Công (Custom)</option>
        <option value="tiktok">🔥 TikTok / Reels / Shorts Siêu Cuốn (9:16, Nhanh, SFX, Chữ Vàng)</option>
        <option value="cinematic">🎬 YouTube Kể Chuyện Điện Ảnh (16:9, Tông Ấm, Hạt Phim, Chữ Trắng)</option>
        <option value="finance">💼 Tin Tức & Phân Tích Tài Chính (16:9, Chữ Xanh Lá, Fade Wipe)</option>
        <option value="minimal">⚡ Tối Giản Siêu Tốc (16:9, Không SFX, Không Filter)</option>
      </select>
    </div>

    <!-- Card 2: Subtitles & Transitions -->
    <div class="card">
      <div class="card-title"><span>⚙️ 2. PHỤ ĐỀ, CHUYỂN CẢNH & KHUNG HÌNH</span></div>
      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
        <!-- Left: Subtitles & Watermark -->
        <div style="display: flex; flex-direction: column; gap: 10px;">
          <label class="checkbox-label" style="font-weight: 600;">
            <input type="checkbox" id="cb_subs" checked>
            Tự động chèn phụ đề SRT vào video
          </label>
          <div style="display: flex; align-items: center; gap: 8px;">
            <span style="color: var(--sub); font-size: 12px; width: 75px;">Màu chữ:</span>
            <select id="sub_color" style="flex: 1;">
              <option value="yellow">Vàng Nổi Bật (TikTok / Viral)</option>
              <option value="white">Trắng Truyền Thống (Classic White)</option>
              <option value="cyan">Xanh Công Nghệ (Cyan Modern)</option>
              <option value="green">Xanh Lá Tài Chính (Finance Green)</option>
              <option value="red">Đỏ Ruby (Dramatic Red)</option>
              <option value="purple">Tím Neon (Neon Purple)</option>
            </select>
            <span style="color: var(--sub); font-size: 12px;">Cỡ:</span>
            <input type="text" id="sub_size" value="8.5" style="width: 44px; text-align: center; flex: none;">
          </div>
          <div style="display: flex; align-items: center; gap: 8px;">
            <span style="color: var(--sub); font-size: 12px; width: 75px;">Hiệu ứng:</span>
            <select id="sub_anim" style="flex: 1;">
              <option value="bounce">Nảy chữ lên (Bounce Pop)</option>
              <option value="karaoke">Chạy từng chữ (Karaoke Reveal)</option>
              <option value="playful">Nhịp điệu vui nhộn (Playful Bounce)</option>
              <option value="slide up">Trượt mượt lên (Slide Up)</option>
              <option value="slide right">Quét từ trái sang (Slide Right)</option>
              <option value="none">Tĩnh (Không animation)</option>
            </select>
            <select id="sub_pos" style="width: 140px; flex: none;">
              <option value="bottom">Dưới cùng</option>
              <option value="center">Chính giữa</option>
              <option value="top">Phía trên</option>
            </select>
          </div>
          <label class="checkbox-label" style="margin-top: 4px;">
            <input type="checkbox" id="cb_wm" checked>
            Xóa watermark Gemini AI (Reverse Alpha Blending - Lossless)
          </label>
        </div>

        <!-- Right: Format & Transitions -->
        <div style="display: flex; flex-direction: column; gap: 10px;">
          <div style="display: flex; align-items: center; gap: 10px;">
            <span style="color: var(--sub); width: 110px;">Tỉ lệ & Sắp xếp:</span>
            <select id="aspect_ratio" style="flex: 1;">
              <option value="16:9">16:9 (Ngang)</option>
              <option value="9:16">9:16 (Dọc - TikTok/Reels)</option>
              <option value="1:1">1:1 (Vuông)</option>
            </select>
            <select id="sort_mode" style="flex: 1;">
              <option value="abc">Sắp xếp ABC</option>
              <option value="oldest_first">Cũ đến Mới</option>
              <option value="newest_first">Mới đến Cũ</option>
            </select>
          </div>
          <div style="display: flex; align-items: center; gap: 10px;">
            <span style="color: var(--sub); width: 110px;">Chuyển cảnh:</span>
            <select id="transition_sel" style="flex: 1;">
              <option value="none">Không transition</option>
              <option value="random">Ngẫu nhiên (Random)</option>
              <option value="dissolve">Mờ chồng (Dissolve)</option>
              <option value="black fade">Mờ đen (Black Fade)</option>
              <option value="white flash">Chớp trắng (White Flash)</option>
              <option value="swipe left">Gạt sang trái (Swipe Left)</option>
              <option value="corner slide">Trượt góc (Corner Slide)</option>
              <option value="flip zoom">Lật thu phóng (Flip Zoom)</option>
              <option value="zoom">Thu phóng nhanh (Zoom)</option>
              <option value="signal glitch">Nhiễu sóng (Signal Glitch)</option>
              <option value="slide drop">Rơi trượt (Slide Drop)</option>
              <option value="slide interface">Trượt giao diện (Slide Interface)</option>
              <option value="snap zoom">Búng zoom (Snap Zoom)</option>
              <option value="light wipe">Vệt sáng quét (Light Wipe)</option>
            </select>
            <span style="color: var(--sub); font-size: 11px;">Thời lượng:</span>
            <input type="text" id="trans_dur" value="0.5" style="width: 40px; text-align: center; flex: none;">
            <span style="color: var(--sub); font-size: 11px;">s</span>
          </div>
          <div style="display: flex; align-items: center; gap: 10px;">
            <span style="color: var(--sub); width: 110px;">Áp dụng:</span>
            <select id="trans_mode" style="flex: 1;">
              <option value="all">Tất cả phân cảnh (All)</option>
              <option value="random">Ngẫu nhiên đổi hiệu ứng (Random)</option>
              <option value="alternate">Xen kẽ các cảnh (Alternate)</option>
            </select>
          </div>
        </div>
      </div>
    </div>

    <!-- Card 3: Pro Video Effects, Intros & Filters -->
    <div class="card">
      <div class="card-title"><span>✨ 3. HIỆU ỨNG CAPCUT, HOẠT ẢNH & BỘ LỌC ĐIỆN ẢNH</span></div>
      
      <div style="display: flex; flex-direction: column; gap: 12px; margin-bottom: 14px;">
        <!-- Row 1: Clip In-Animation -->
        <div style="display: flex; align-items: center; gap: 10px;">
          <span style="color: var(--text); font-weight: 500; width: 180px;">Hoạt ảnh mở đầu (Intro):</span>
          <select id="clip_intro_sel" style="flex: 1;">
            <option value="none">Không animation</option>
            <option value="random">Ngẫu nhiên (Random)</option>
            <option value="zoom in">Thu phóng vào (Zoom In)</option>
            <option value="dynamic zoom in">Phóng to năng động (Dynamic Zoom In)</option>
            <option value="dynamic zoom out">Thu nhỏ năng động (Dynamic Zoom Out)</option>
            <option value="fade in">Mờ dần xuất hiện (Fade In)</option>
            <option value="blur fade in">Mờ ảo tỏ dần (Blur Fade In)</option>
            <option value="shake horizontal">Lắc ngang nảy (Horizontal Shake)</option>
            <option value="shake vertical">Lắc dọc nảy (Vertical Shake)</option>
            <option value="slide up">Trượt từ dưới lên (Slide Up)</option>
            <option value="slide down">Trượt từ trên xuống (Slide Down)</option>
            <option value="slide right">Trượt từ trái sang (Slide Right)</option>
            <option value="slide left">Trượt từ phải sang (Slide Left)</option>
            <option value="spin open">Xoay mở màn (Spin Open)</option>
          </select>
          <span style="color: var(--sub); font-size: 11px;">Thời lượng:</span>
          <input type="text" id="clip_intro_dur" value="0.8" style="width: 40px; text-align: center; flex: none;">
          <span style="color: var(--sub); font-size: 11px;">s</span>
          <select id="clip_intro_mode" style="width: 170px; flex: none;">
            <option value="all">Tất cả phân cảnh</option>
            <option value="random">Ngẫu nhiên xen kẽ</option>
            <option value="first_only">Chỉ cảnh đầu tiên</option>
          </select>
        </div>

        <!-- Row 2: Video Scene Effect -->
        <div style="display: flex; align-items: center; gap: 10px;">
          <span style="color: var(--text); font-weight: 500; width: 180px;">Hiệu ứng video (Effect):</span>
          <select id="video_eff_sel" style="flex: 1;">
            <option value="none">Không dùng hiệu ứng</option>
            <option value="random">Ngẫu nhiên (Random)</option>
            <option value="focus shake">Rung lắc tiêu điểm (Focus Shake)</option>
            <option value="rgb shake">Rung tách màu RGB (RGB Shake)</option>
            <option value="pixel glitch">Nhiễu hạt Pixel (Pixel Glitch)</option>
            <option value="glitch intro">Giật sóng mở màn (Glitch Intro)</option>
            <option value="bouncing glow">Hào quang nhấp nháy (Bouncing Glow)</option>
            <option value="flash">Chớp sáng kịch tính (Flash)</option>
            <option value="neon flash">Ánh đèn Neon (Neon Flash)</option>
            <option value="vintage flash">Chớp phim cổ điển (Vintage Flash)</option>
          </select>
          <span style="color: var(--sub); font-size: 11px;">Phạm vi:</span>
          <select id="video_eff_scope" style="width: 250px; flex: none;">
            <option value="all">Tất cả phân cảnh</option>
            <option value="random">Ngẫu nhiên một số cảnh</option>
            <option value="intro_outro">Chỉ cảnh mở đầu & kết thúc</option>
          </select>
        </div>

        <!-- Row 3: Cinematic Filter -->
        <div style="display: flex; align-items: center; gap: 10px;">
          <span style="color: var(--text); font-weight: 500; width: 180px;">Bộ lọc màu (Filter):</span>
          <select id="filter_sel" style="flex: 1;">
            <option value="none">Không dùng filter</option>
            <option value="soft grain">Soft Grain (Hạt phim điện ảnh)</option>
            <option value="vintage 1980">Vintage 1980 (Tông màu cổ điển)</option>
            <option value="vhs retro">VHS Retro (Băng từ VHS)</option>
            <option value="peach fuzz">Peach Fuzz (Tông ấm điện ảnh)</option>
            <option value="lover blue">Lover Blue (Tông lạnh điện ảnh)</option>
            <option value="bw retro">BW Retro (Trắng đen cổ điển)</option>
          </select>
          <span style="color: var(--sub); font-size: 11px;">Độ đậm:</span>
          <input type="text" id="filter_intensity" value="60" style="width: 40px; text-align: center; flex: none;">
          <span style="color: var(--sub); font-size: 11px;">%</span>
        </div>

        <!-- Row 4: SFX Audio Suite -->
        <div style="display: flex; align-items: center; gap: 10px;">
          <label class="checkbox-label" style="width: 180px;">
            <input type="checkbox" id="cb_sfx" checked>
            Âm thanh chuyển cảnh (SFX):
          </label>
          <select id="sfx_name_sel" style="flex: 1;">
            <option value="random">Ngẫu nhiên phối hợp (Random)</option>
            <option value="whoosh">Whoosh (Lướt gió điện ảnh)</option>
            <option value="swoosh">Swoosh (Vút nhanh)</option>
            <option value="pop">Pop (Nảy vui nhộn)</option>
            <option value="ding">Ding (Keng chuông)</option>
          </select>
          <span style="color: var(--sub); font-size: 11px;">Âm lượng:</span>
          <input type="text" id="sfx_vol" value="50" style="width: 40px; text-align: center; flex: none;">
          <span style="color: var(--sub); font-size: 11px;">%</span>
        </div>
      </div>

      <!-- Row 5: Pro Audio & Visual Toggles -->
      <div class="pro-grid" style="border-top: 1px solid var(--border); padding-top: 12px;">
        <div style="display: flex; flex-direction: column; gap: 8px;">
          <label class="checkbox-label">
            <input type="checkbox" id="cb_blur" checked>
            Canvas Blur (Làm mờ nền khi ảnh không vừa khung - chống viền đen)
          </label>
          <label class="checkbox-label">
            <input type="checkbox" id="cb_ducking" checked>
            Audio Ducking (Tự động hạ nhạc nền khi có tiếng giọng đọc)
          </label>
        </div>
        <div style="display: flex; flex-direction: column; gap: 8px;">
          <label class="checkbox-label">
            <input type="checkbox" id="cb_fade" checked>
            Audio Fade In & Fade Out cho nhạc nền (Mở & tắt êm ái)
          </label>
          <label class="checkbox-label">
            <input type="checkbox" id="cb_cta" checked>
            Chèn CTA Kêu gọi Đăng ký (Subscribe) & tiếng chuông ở cuối video
          </label>
        </div>
      </div>
    </div>

    <!-- Card 4: Camera Motion & Ken Burns -->
    <div class="card">
      <div class="card-title">
        <span>🎥 4. GÓC QUAY & CHUYỂN ĐỘNG CAMERA (CAMERA MOTION & KEN BURNS)</span>
        <div style="display: flex; gap: 6px;">
          <button class="btn btn-secondary" style="padding: 4px 10px; font-size: 11px;" onclick="selectAllMotions(true)">✓ Chọn Tất Cả</button>
          <button class="btn btn-secondary" style="padding: 4px 10px; font-size: 11px;" onclick="selectAllMotions(false)">✕ Bỏ Chọn</button>
        </div>
      </div>

      <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 12px;">
        <span style="color: var(--text); font-weight: 500;">Chế độ Camera:</span>
        <select id="camera_motion_sel" style="flex: 1; max-width: 320px;">
          <option value="smart_pacing">Smart Pacing AI (Tự phân tích nhịp câu)</option>
          <option value="zoom_in">Zoom In (Phóng to dần)</option>
          <option value="zoom_out">Zoom Out (Thu nhỏ dần)</option>
          <option value="pan_left">Pan Left (Lia sang trái)</option>
          <option value="pan_right">Pan Right (Lia sang phải)</option>
          <option value="pan_up">Pan Up (Lia lên trên)</option>
          <option value="pan_down">Pan Down (Lia xuống dưới)</option>
          <option value="random">Ngẫu nhiên góc quay (Dynamic Ken Burns)</option>
          <option value="none">Cố định (Không chuyển động)</option>
        </select>
        <span style="color: var(--sub); font-size: 12px;">Tỷ lệ zoom:</span>
        <input type="text" id="zoom_scale" value="112" style="width: 44px; text-align: center; flex: none;">
        <span style="color: var(--sub); font-size: 12px;">%</span>
      </div>
      <div class="motions-grid">
        <!-- Col 1 -->
        <div class="motion-card">
          <div class="motion-row">
            <label><input type="checkbox" id="m_zoom_in" checked> Zoom In</label>
            <span style="color: var(--sub);">Scale:</span>
            <input type="text" id="m_zoom_in_s" value="110"> %
          </div>
          <div class="motion-row">
            <label><input type="checkbox" id="m_pan_up" checked> Pan Up</label>
            <span style="color: var(--sub);">X:</span> <input type="text" id="m_pan_up_x" value="0">
            <span style="color: var(--sub);">Y:</span> <input type="text" id="m_pan_up_y" value="100">
            <span style="color: var(--sub);">Scale:</span> <input type="text" id="m_pan_up_s" value="110"> %
          </div>
          <div class="motion-row">
            <label><input type="checkbox" id="m_pan_left" checked> Pan Left</label>
            <span style="color: var(--sub);">X:</span> <input type="text" id="m_pan_left_x" value="190">
            <span style="color: var(--sub);">Y:</span> <input type="text" id="m_pan_left_y" value="0">
            <span style="color: var(--sub);">Scale:</span> <input type="text" id="m_pan_left_s" value="110"> %
          </div>
        </div>
        <!-- Col 2 -->
        <div class="motion-card">
          <div class="motion-row">
            <label><input type="checkbox" id="m_zoom_out" checked> Zoom Out</label>
            <span style="color: var(--sub);">Scale:</span>
            <input type="text" id="m_zoom_out_s" value="110"> %
          </div>
          <div class="motion-row">
            <label><input type="checkbox" id="m_pan_down" checked> Pan Down</label>
            <span style="color: var(--sub);">X:</span> <input type="text" id="m_pan_down_x" value="0">
            <span style="color: var(--sub);">Y:</span> <input type="text" id="m_pan_down_y" value="100">
            <span style="color: var(--sub);">Scale:</span> <input type="text" id="m_pan_down_s" value="110"> %
          </div>
          <div class="motion-row">
            <label><input type="checkbox" id="m_pan_right" checked> Pan Right</label>
            <span style="color: var(--sub);">X:</span> <input type="text" id="m_pan_right_x" value="190">
            <span style="color: var(--sub);">Y:</span> <input type="text" id="m_pan_right_y" value="0">
            <span style="color: var(--sub);">Scale:</span> <input type="text" id="m_pan_right_s" value="110"> %
          </div>
        </div>
      </div>
    </div>

    <!-- Center Action -->
    <div style="text-align: center; margin: 24px 0 16px;">
      <button class="btn btn-primary" style="padding: 14px 48px; font-size: 15px; font-weight: 700;" id="btn-run" onclick="startBuild()">
        🚀 TẠO PROJECT CAPCUT NGAY
      </button>
      <div class="progress-bar-bg"><div class="progress-bar-fill" id="p-bar"></div></div>
      <div id="p-status" style="color: var(--sub); font-size: 12px; margin-top: 8px;">Sẵn sàng.</div>
    </div>

    <!-- Card 5: Console Output -->
    <div class="card">
      <div class="card-title"><span>📊 NHẬT KÝ TIẾN TRÌNH CHI TIẾT</span></div>
      <div class="console-box" id="console">Hệ thống sẵn sàng. Nhấn 'TẠO PROJECT CAPCUT NGAY' để thực hiện.</div>
    </div>
  </div>

  <script>
    let sampleData = null;

    window.addEventListener('DOMContentLoaded', async () => {
      try {
        const res = await fetch('/api/defaults');
        sampleData = await res.json();
        autoLoadSamples();
      } catch (e) { console.error(e); }
    });

    function updateScenesCount() {
      const text = document.getElementById('scenes_text').value.trim();
      const count = text ? text.split('\\n').filter(l => l.trim().length > 0).length : 0;
      document.getElementById('scenes_count').textContent = count + ' dòng';
    }

    function autoLoadSamples() {
      if (!sampleData) return;
      if (sampleData.srt_path) document.getElementById('srt_path').value = sampleData.srt_path;
      if (sampleData.voice_path) document.getElementById('voice_paths').value = sampleData.voice_path;
      if (sampleData.images_dir) document.getElementById('images_dir').value = sampleData.images_dir;
      if (sampleData.script_content) document.getElementById('scenes_text').value = sampleData.script_content;
      updateScenesCount();
      log('[✨] Đã tự động nạp các tệp mẫu sẵn có!');
    }

    function log(msg) {
      const c = document.getElementById('console');
      c.textContent += '\\n' + msg;
      c.scrollTop = c.scrollHeight;
    }

    function copyScenes() {
      const t = document.getElementById('scenes_text').value;
      navigator.clipboard.writeText(t);
      log('[✓] Đã sao chép kịch bản vào clipboard!');
    }

    function splitSentences() {
      const t = document.getElementById('scenes_text').value.trim();
      if (!t) return;
      // Split on sentence boundary
      const sentences = t.replace(/\\r\\n/g, '\\n').split(/(?<=[.!?。！？;])\\s+/);
      const cleaned = sentences.map(s => s.trim()).filter(s => s.length > 0);
      if (cleaned.length > 0) {
        document.getElementById('scenes_text').value = cleaned.join('\\n');
        updateScenesCount();
        log(`[✂️] Đã tự động tách thành ${cleaned.length} câu (mỗi câu 1 dòng)!`);
      }
    }

    function cleanEmptyLines() {
      const t = document.getElementById('scenes_text').value.trim();
      if (!t) return;
      const lines = t.split('\\n').map(l => l.trim()).filter(l => l.length > 0);
      document.getElementById('scenes_text').value = lines.join('\\n');
      updateScenesCount();
      log(`[🧹] Đã dọn sạch các dòng trống (${lines.length} dòng hợp lệ)!`);
    }

    function clearScenes() {
      document.getElementById('scenes_text').value = '';
      updateScenesCount();
    }

    function selectAllMotions(state) {
      ['m_zoom_in', 'm_zoom_out', 'm_pan_up', 'm_pan_down', 'm_pan_left', 'm_pan_right'].forEach(id => {
        document.getElementById(id).checked = state;
      });
      log(`[🎥] ${state ? 'Đã chọn tất cả' : 'Đã bỏ chọn tất cả'} chuyển động keyframe.`);
    }

    function applyPreset(preset) {
      if (preset === 'tiktok') {
        document.getElementById('aspect_ratio').value = '9:16';
        document.getElementById('cb_subs').checked = true;
        document.getElementById('sub_color').value = 'yellow';
        document.getElementById('sub_anim').value = 'bounce';
        document.getElementById('sub_size').value = '9.5';
        document.getElementById('sub_pos').value = 'bottom';
        document.getElementById('transition_sel').value = 'flip zoom';
        document.getElementById('trans_dur').value = '0.4';
        document.getElementById('trans_mode').value = 'all';
        document.getElementById('clip_intro_sel').value = 'dynamic zoom in';
        document.getElementById('clip_intro_dur').value = '0.5';
        document.getElementById('clip_intro_mode').value = 'all';
        document.getElementById('video_eff_sel').value = 'focus shake';
        document.getElementById('video_eff_scope').value = 'random';
        document.getElementById('filter_sel').value = 'none';
        document.getElementById('camera_motion_sel').value = 'smart_pacing';
        document.getElementById('zoom_scale').value = '115';
        document.getElementById('cb_sfx').checked = true;
        document.getElementById('sfx_name_sel').value = 'whoosh';
        document.getElementById('sfx_vol').value = '60';
        document.getElementById('cb_blur').checked = true;
        document.getElementById('cb_ducking').checked = true;
        document.getElementById('cb_fade').checked = true;
        document.getElementById('cb_cta').checked = true;
        selectAllMotions(true);
        log('[🎯] Đã áp dụng Preset: TikTok / Reels / Shorts Siêu Cuốn (9:16, Nhanh, SFX, Chữ Vàng)!');
      } else if (preset === 'cinematic') {
        document.getElementById('aspect_ratio').value = '16:9';
        document.getElementById('cb_subs').checked = true;
        document.getElementById('sub_color').value = 'white';
        document.getElementById('sub_anim').value = 'slide up';
        document.getElementById('sub_size').value = '8.5';
        document.getElementById('sub_pos').value = 'bottom';
        document.getElementById('transition_sel').value = 'dissolve';
        document.getElementById('trans_dur').value = '0.8';
        document.getElementById('trans_mode').value = 'all';
        document.getElementById('clip_intro_sel').value = 'fade in';
        document.getElementById('clip_intro_dur').value = '1.0';
        document.getElementById('clip_intro_mode').value = 'all';
        document.getElementById('video_eff_sel').value = 'none';
        document.getElementById('filter_sel').value = 'soft grain';
        document.getElementById('filter_intensity').value = '65';
        document.getElementById('camera_motion_sel').value = 'smart_pacing';
        document.getElementById('zoom_scale').value = '110';
        document.getElementById('cb_sfx').checked = true;
        document.getElementById('sfx_name_sel').value = 'swoosh';
        document.getElementById('sfx_vol').value = '35';
        document.getElementById('cb_blur').checked = true;
        document.getElementById('cb_ducking').checked = true;
        document.getElementById('cb_fade').checked = true;
        document.getElementById('cb_cta').checked = true;
        selectAllMotions(true);
        log('[🎯] Đã áp dụng Preset: YouTube Kể Chuyện Điện Ảnh (16:9, Tông Ấm, Hạt Phim, Chữ Trắng)!');
      } else if (preset === 'finance') {
        document.getElementById('aspect_ratio').value = '16:9';
        document.getElementById('cb_subs').checked = true;
        document.getElementById('sub_color').value = 'green';
        document.getElementById('sub_anim').value = 'karaoke';
        document.getElementById('sub_size').value = '8.5';
        document.getElementById('sub_pos').value = 'bottom';
        document.getElementById('transition_sel').value = 'corner slide';
        document.getElementById('trans_dur').value = '0.5';
        document.getElementById('trans_mode').value = 'all';
        document.getElementById('clip_intro_sel').value = 'slide right';
        document.getElementById('clip_intro_dur').value = '0.6';
        document.getElementById('clip_intro_mode').value = 'all';
        document.getElementById('video_eff_sel').value = 'none';
        document.getElementById('filter_sel').value = 'none';
        document.getElementById('camera_motion_sel').value = 'pan_left';
        document.getElementById('zoom_scale').value = '108';
        document.getElementById('cb_sfx').checked = true;
        document.getElementById('sfx_name_sel').value = 'ding';
        document.getElementById('sfx_vol').value = '25';
        document.getElementById('cb_blur').checked = true;
        document.getElementById('cb_ducking').checked = true;
        document.getElementById('cb_fade').checked = true;
        document.getElementById('cb_cta').checked = true;
        selectAllMotions(true);
        log('[🎯] Đã áp dụng Preset: Tin Tức & Phân Tích Tài Chính (16:9, Chữ Xanh Lá)!');
      } else if (preset === 'minimal') {
        document.getElementById('aspect_ratio').value = '16:9';
        document.getElementById('cb_subs').checked = true;
        document.getElementById('sub_color').value = 'white';
        document.getElementById('sub_anim').value = 'none';
        document.getElementById('transition_sel').value = 'none';
        document.getElementById('clip_intro_sel').value = 'none';
        document.getElementById('video_eff_sel').value = 'none';
        document.getElementById('filter_sel').value = 'none';
        document.getElementById('camera_motion_sel').value = 'none';
        document.getElementById('cb_sfx').checked = false;
        document.getElementById('cb_blur').checked = true;
        document.getElementById('cb_ducking').checked = true;
        document.getElementById('cb_fade').checked = true;
        document.getElementById('cb_cta').checked = false;
        selectAllMotions(false);
        document.getElementById('m_zoom_in').checked = true;
        log('[🎯] Đã áp dụng Preset: Tối Giản Siêu Tốc (16:9, Không SFX, Không Filter)!');
      }
    }

    async function launchCapCut() {
      try {
        const res = await fetch('/api/launch-capcut', { method: 'POST' });
        const data = await res.json();
        if (data.status === 'success') {
          log('[+] Đã khởi chạy CapCut!');
        } else {
          alert('Không thể mở CapCut: ' + data.message);
        }
      } catch (e) { alert(e.message); }
    }

    function startBuild() {
      const payload = {
        srt_path: document.getElementById('srt_path').value.trim(),
        script_source: document.getElementById('scenes_text').value.trim(),
        voice_paths: document.getElementById('voice_paths').value.trim(),
        images_dir: document.getElementById('images_dir').value.trim(),
        bgm_paths: document.getElementById('bgm_paths').value.trim(),
        bgm_volume: document.getElementById('bgm_volume').value.trim() || '15',
        project_name: document.getElementById('project_name').value.trim() || 'AutoCapCut_Project',
        aspect_ratio: document.getElementById('aspect_ratio').value,
        sort_mode: document.getElementById('sort_mode').value,
        // Transitions
        transition: document.getElementById('transition_sel').value,
        transition_duration: parseFloat(document.getElementById('trans_dur').value) || 0.5,
        transition_mode: document.getElementById('trans_mode').value,
        // Clip In-Animations
        clip_intro: document.getElementById('clip_intro_sel').value,
        clip_intro_duration: parseFloat(document.getElementById('clip_intro_dur').value) || 0.8,
        clip_intro_mode: document.getElementById('clip_intro_mode').value,
        // Video Scene Effects
        video_effect: document.getElementById('video_eff_sel').value,
        video_effect_scope: document.getElementById('video_eff_scope').value,
        // Filters
        filter_name: document.getElementById('filter_sel').value,
        filter_intensity: parseFloat(document.getElementById('filter_intensity').value) || 60.0,
        // Camera Motions
        camera_motion: document.getElementById('camera_motion_sel').value,
        zoom_scale: parseFloat(document.getElementById('zoom_scale').value) || 112.0,
        // Subtitles
        import_subtitles: document.getElementById('cb_subs').checked,
        subtitle_style: document.getElementById('sub_color').value,
        subtitle_animation: document.getElementById('sub_anim').value,
        subtitle_font_size: parseFloat(document.getElementById('sub_size').value) || 8.5,
        subtitle_position: document.getElementById('sub_pos').value,
        // Audio Suite
        enable_sfx: document.getElementById('cb_sfx').checked,
        sfx_name: document.getElementById('sfx_name_sel').value,
        sfx_volume: document.getElementById('sfx_vol').value || '50',
        canvas_blur: document.getElementById('cb_blur').checked,
        audio_ducking: document.getElementById('cb_ducking').checked,
        audio_fade: document.getElementById('cb_fade').checked,
        enable_cta_subscribe: document.getElementById('cb_cta').checked,
        remove_gemini_watermark: document.getElementById('cb_wm').checked,
        keyframe_config: {
          zoom_in: { enabled: document.getElementById('m_zoom_in').checked, scale: document.getElementById('m_zoom_in_s').value },
          zoom_out: { enabled: document.getElementById('m_zoom_out').checked, scale: document.getElementById('m_zoom_out_s').value },
          pan_up: { enabled: document.getElementById('m_pan_up').checked, x: document.getElementById('m_pan_up_x').value, y: document.getElementById('m_pan_up_y').value, scale: document.getElementById('m_pan_up_s').value },
          pan_down: { enabled: document.getElementById('m_pan_down').checked, x: document.getElementById('m_pan_down_x').value, y: document.getElementById('m_pan_down_y').value, scale: document.getElementById('m_pan_down_s').value },
          pan_left: { enabled: document.getElementById('m_pan_left').checked, x: document.getElementById('m_pan_left_x').value, y: document.getElementById('m_pan_left_y').value, scale: document.getElementById('m_pan_left_s').value },
          pan_right: { enabled: document.getElementById('m_pan_right').checked, x: document.getElementById('m_pan_right_x').value, y: document.getElementById('m_pan_right_y').value, scale: document.getElementById('m_pan_right_s').value },
        }
      };

      if (!payload.srt_path || !payload.script_source || !payload.voice_paths || !payload.images_dir) {
        alert('Vui lòng điền đủ các trường Audio, SRT, Kịch bản và Thư mục Media!');
        return;
      }

      const btn = document.getElementById('btn-run');
      const pBar = document.getElementById('p-bar');
      const pStatus = document.getElementById('p-status');

      btn.disabled = true;
      btn.textContent = '⏳ ĐANG XỬ LÝ TIẾN TRÌNH...';

      const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const ws = new WebSocket(`${proto}//${window.location.host}/ws/build`);

      ws.onopen = () => {
        log('[*] Đang kết nối tạo CapCut project...');
        ws.send(JSON.stringify(payload));
      };

      ws.onmessage = (evt) => {
        const msg = JSON.parse(evt.data);
        if (msg.type === 'progress') {
          pBar.style.width = msg.percent + '%';
          pStatus.textContent = `[${msg.percent}%] ${msg.message}`;
          log(`[${msg.percent}%] ${msg.message}`);
        } else if (msg.type === 'success') {
          pBar.style.width = '100%';
          pStatus.textContent = '🎉 Hoàn tất 100%!';
          btn.disabled = false;
          btn.textContent = '🚀 TẠO PROJECT CAPCUT NGAY';
          log('\\n🎉 TẠO PROJECT CAPCUT THÀNH CÔNG!');
          log(`  • Dự án:      ${msg.result.draft_name}`);
          log(`  • Tổng cảnh:  ${msg.result.total_scenes} cảnh`);
          log(`  • Thời lượng: ${(msg.result.duration_seconds/60).toFixed(2)} phút`);
          log(`  • Thư mục:    ${msg.result.draft_dir}`);
          alert(`🎉 Đã tạo project CapCut '${msg.result.draft_name}' thành công!\\nBạn có thể mở CapCut ngay bây giờ.`);
        } else if (msg.type === 'error') {
          btn.disabled = false;
          btn.textContent = '🚀 TẠO PROJECT CAPCUT NGAY';
          pStatus.textContent = '❌ Lỗi: ' + msg.message;
          log('[!] LỖI: ' + msg.message);
          alert('Lỗi: ' + msg.message);
        }
      };

      ws.onerror = (err) => {
        btn.disabled = false;
        btn.textContent = '🚀 TẠO PROJECT CAPCUT NGAY';
        log('[!] Lỗi kết nối WebSocket');
      };
    }
  </script>
</body>
</html>
"""


def main():
    import uvicorn
    print("\n" + "=" * 60)
    print("🎬 AutoCapCut Web Interface đang chạy tại: http://localhost:8000")
    print("=" * 60)
    uvicorn.run(app, host="127.0.0.1", port=8000)


if __name__ == '__main__':
    main()
