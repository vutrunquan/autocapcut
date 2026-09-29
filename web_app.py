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
                transition=req.get("transition", "none"),
                keyframe_config=req.get("keyframe_config"),
                aspect_ratio=req.get("aspect_ratio", "16:9"),
                smart_pacing=bool(req.get("smart_pacing", True)),
                canvas_blur=bool(req.get("canvas_blur", True)),
                filter_name=req.get("filter_name", "none"),
                enable_sfx=bool(req.get("enable_sfx", True)),
                sfx_volume=float(req.get("sfx_volume", 50)) / 100.0,
                bgm_volume=float(req.get("bgm_volume", 15)) / 100.0,
                audio_ducking=bool(req.get("audio_ducking", True)),
                audio_fade=bool(req.get("audio_fade", True)),
                enable_cta_subscribe=bool(req.get("enable_cta_subscribe", True)),
                subtitle_style=req.get("subtitle_style", "yellow"),
                remove_gemini_watermark=bool(req.get("remove_gemini_watermark", False)),
                import_subtitles=bool(req.get("import_subtitles", True)),
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

    <!-- Card 2: Configuration & Transitions -->
    <div class="card">
      <div class="card-title"><span>⚙️ 2. CẤU HÌNH & CHUYỂN CẢNH</span></div>
      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
        <div style="display: flex; flex-direction: column; gap: 12px;">
          <label class="checkbox-label">
            <input type="checkbox" id="cb_subs" checked>
            Tự động chèn phụ đề SRT vào video
          </label>
          <div style="display: flex; align-items: center; gap: 8px; margin-left: 24px;">
            <span style="color: var(--sub); font-size: 12px;">Màu sắc phụ đề:</span>
            <select id="sub_color" style="flex: 1;">
              <option value="yellow">Vàng Nổi Bật (TikTok / Viral)</option>
              <option value="white">Trắng Truyền Thống (Classic White)</option>
              <option value="cyan">Xanh Công Nghệ (Cyan Modern)</option>
              <option value="green">Xanh Lá Tài Chính (Finance Green)</option>
            </select>
          </div>
          <label class="checkbox-label">
            <input type="checkbox" id="cb_wm" checked>
            Xóa watermark Gemini AI (Reverse Alpha Blending - Lossless)
          </label>
        </div>

        <div style="display: flex; flex-direction: column; gap: 10px;">
          <div style="display: flex; align-items: center; gap: 10px;">
            <span style="color: var(--sub); width: 110px;">Tỉ lệ video:</span>
            <select id="aspect_ratio" style="flex: 1;">
              <option value="16:9">16:9 (Ngang - YouTube, Facebook)</option>
              <option value="9:16">9:16 (Dọc - TikTok, Reels, Shorts)</option>
              <option value="1:1">1:1 (Vuông - Instagram, Post)</option>
            </select>
          </div>
          <div style="display: flex; align-items: center; gap: 10px;">
            <span style="color: var(--sub); width: 110px;">Sắp xếp media:</span>
            <select id="sort_mode" style="flex: 1;">
              <option value="abc">Sắp xếp media theo ABC (Số tự nhiên)</option>
              <option value="oldest_first">Sắp xếp media theo thời gian Cũ đến Mới</option>
              <option value="newest_first">Sắp xếp media theo thời gian Mới đến Cũ</option>
            </select>
          </div>
          <div style="display: flex; align-items: center; gap: 10px;">
            <span style="color: var(--sub); width: 110px;">Chuyển cảnh:</span>
            <select id="transition_sel" style="flex: 1;">
              <option value="none">Không transition</option>
              <option value="black fade">Black Fade</option>
              <option value="slow fade">Slow Fade</option>
              <option value="fade swipe">Fade Swipe</option>
              <option value="fade wipe">Fade Wipe</option>
              <option value="fade shift">Fade Shift</option>
              <option value="basic black">Basic Black</option>
              <option value="blink fade">Blink Fade</option>
            </select>
          </div>
        </div>
      </div>
    </div>

    <!-- Card 3: Pro Video Effects -->
    <div class="card">
      <div class="card-title"><span>✨ 3. TÍNH NĂNG BIÊN TẬP NÂNG CAO (PRO VIDEO EFFECTS)</span></div>
      <div class="pro-grid">
        <div style="display: flex; flex-direction: column; gap: 10px;">
          <div style="display: flex; align-items: center; gap: 8px;">
            <label class="checkbox-label">
              <input type="checkbox" id="cb_sfx" checked>
              Âm thanh chuyển cảnh (SFX Whoosh/Swoosh)
            </label>
            <span style="color: var(--sub); font-size: 11px;">Âm lượng:</span>
            <input type="text" id="sfx_vol" value="50" style="width: 40px; text-align: center; padding: 2px 4px; font-size: 11px; flex: none;">
            <span style="color: var(--sub); font-size: 11px;">%</span>
          </div>

          <label class="checkbox-label">
            <input type="checkbox" id="cb_blur" checked>
            Tự động làm mờ nền khi ảnh không vừa khung (Canvas Blur)
          </label>

          <label class="checkbox-label">
            <input type="checkbox" id="cb_pacing" checked>
            Điều nhịp thông minh (Smart Pacing: câu ngắn zoom nhanh, câu dài lia chậm)
          </label>
        </div>

        <div style="display: flex; flex-direction: column; gap: 10px;">
          <label class="checkbox-label">
            <input type="checkbox" id="cb_ducking" checked>
            Audio Ducking (Tự hạ nhạc nền khi có tiếng giọng đọc)
          </label>

          <label class="checkbox-label">
            <input type="checkbox" id="cb_fade" checked>
            Audio Fade In & Fade Out cho nhạc nền (Mở & tắt êm ái)
          </label>

          <label class="checkbox-label">
            <input type="checkbox" id="cb_cta" checked>
            Tự động chèn CTA Đăng ký kênh (Subscribe) & tiếng chuông cuối video
          </label>
        </div>
      </div>

      <div style="display: flex; align-items: center; gap: 12px; margin-top: 14px; padding-top: 12px; border-top: 1px solid var(--border);">
        <span style="font-weight: 600; color: #fff;">Bộ lọc màu điện ảnh (Cinematic Filter):</span>
        <select id="filter_sel" style="width: 280px;">
          <option value="none">Không dùng filter</option>
          <option value="soft grain">Soft Grain (Hạt phim điện ảnh)</option>
          <option value="vintage 1980">Vintage 1980 (Tông màu cổ điển)</option>
          <option value="vhs retro">VHS Retro (Băng từ VHS)</option>
          <option value="peach fuzz">Peach Fuzz (Tông ấm điện ảnh)</option>
          <option value="lover blue">Lover Blue (Tông lạnh điện ảnh)</option>
          <option value="bw retro">BW Retro (Trắng đen cổ điển)</option>
        </select>
      </div>
    </div>

    <!-- Card 4: Keyframe Motions -->
    <div class="card">
      <div class="card-title">
        <span>🎥 4. KEYFRAME CHUYỂN ĐỘNG (PAN & ZOOM TÙY CHỈNH)</span>
        <div style="display: flex; gap: 6px;">
          <button class="btn btn-secondary" style="padding: 4px 10px; font-size: 11px;" onclick="selectAllMotions(true)">✓ Chọn Tất Cả</button>
          <button class="btn btn-secondary" style="padding: 4px 10px; font-size: 11px;" onclick="selectAllMotions(false)">✕ Bỏ Chọn</button>
        </div>
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
        document.getElementById('transition_sel').value = 'fade swipe';
        document.getElementById('cb_sfx').checked = true;
        document.getElementById('sfx_vol').value = '60';
        document.getElementById('cb_blur').checked = true;
        document.getElementById('cb_pacing').checked = true;
        document.getElementById('cb_ducking').checked = true;
        document.getElementById('cb_fade').checked = true;
        document.getElementById('cb_cta').checked = true;
        document.getElementById('filter_sel').value = 'none';
        selectAllMotions(true);
        log('[🎯] Đã áp dụng Preset: TikTok / Reels / Shorts Siêu Cuốn (9:16, Nhanh, SFX, Chữ Vàng)!');
      } else if (preset === 'cinematic') {
        document.getElementById('aspect_ratio').value = '16:9';
        document.getElementById('cb_subs').checked = true;
        document.getElementById('sub_color').value = 'white';
        document.getElementById('transition_sel').value = 'slow fade';
        document.getElementById('cb_sfx').checked = true;
        document.getElementById('sfx_vol').value = '35';
        document.getElementById('cb_blur').checked = true;
        document.getElementById('cb_pacing').checked = true;
        document.getElementById('cb_ducking').checked = true;
        document.getElementById('cb_fade').checked = true;
        document.getElementById('cb_cta').checked = true;
        document.getElementById('filter_sel').value = 'soft grain';
        selectAllMotions(true);
        log('[🎯] Đã áp dụng Preset: YouTube Kể Chuyện Điện Ảnh (16:9, Tông Ấm, Hạt Phim, Chữ Trắng)!');
      } else if (preset === 'finance') {
        document.getElementById('aspect_ratio').value = '16:9';
        document.getElementById('cb_subs').checked = true;
        document.getElementById('sub_color').value = 'green';
        document.getElementById('transition_sel').value = 'fade wipe';
        document.getElementById('cb_sfx').checked = true;
        document.getElementById('sfx_vol').value = '25';
        document.getElementById('cb_blur').checked = true;
        document.getElementById('cb_pacing').checked = true;
        document.getElementById('cb_ducking').checked = true;
        document.getElementById('cb_fade').checked = true;
        document.getElementById('cb_cta').checked = true;
        document.getElementById('filter_sel').value = 'none';
        selectAllMotions(true);
        log('[🎯] Đã áp dụng Preset: Tin Tức & Phân Tích Tài Chính (16:9, Chữ Xanh Lá)!');
      } else if (preset === 'minimal') {
        document.getElementById('aspect_ratio').value = '16:9';
        document.getElementById('cb_subs').checked = true;
        document.getElementById('sub_color').value = 'white';
        document.getElementById('transition_sel').value = 'none';
        document.getElementById('cb_sfx').checked = false;
        document.getElementById('cb_blur').checked = true;
        document.getElementById('cb_pacing').checked = false;
        document.getElementById('cb_ducking').checked = true;
        document.getElementById('cb_fade').checked = true;
        document.getElementById('cb_cta').checked = false;
        document.getElementById('filter_sel').value = 'none';
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
        transition: document.getElementById('transition_sel').value,
        import_subtitles: document.getElementById('cb_subs').checked,
        subtitle_style: document.getElementById('sub_color').value,
        remove_gemini_watermark: document.getElementById('cb_wm').checked,
        enable_sfx: document.getElementById('cb_sfx').checked,
        sfx_volume: document.getElementById('sfx_vol').value || '50',
        canvas_blur: document.getElementById('cb_blur').checked,
        smart_pacing: document.getElementById('cb_pacing').checked,
        audio_ducking: document.getElementById('cb_ducking').checked,
        audio_fade: document.getElementById('cb_fade').checked,
        enable_cta_subscribe: document.getElementById('cb_cta').checked,
        filter_name: document.getElementById('filter_sel').value,
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
