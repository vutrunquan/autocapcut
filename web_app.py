"""
Web Interface for AutoCapCut Studio.
Designed with a professional Graphite Studio Dark aesthetic,
ergonomic 2-column layout with tabbed controls,
soothing eye-friendly palette, and real-time WebSocket progress logs.
"""

import os
import sys
import json
import asyncio
import subprocess
from typing import Optional, List, Dict, Any, Union
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect, HTTPException
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
    format_time_ms,
    launch_capcut_app,
    is_capcut_running,
    get_capcut_window_hwnd,
    focus_capcut_window,
    restart_capcut_app,
    open_path_in_os,
    ensure_macos_path,
    get_machine_id,
    get_license_info,
    activate_license,
    get_payment_info,
    check_license_valid,
    LicenseExpiredError,
    CURRENT_VERSION,
    check_for_updates
)

ensure_macos_path()

app = FastAPI(title="AutoCapCut Studio Web")


class PreviewRequest(BaseModel):
    srt_path: str
    script_source: str
    voice_paths: str
    images_dir: str
    sort_mode: str = "abc"


class ActivateRequest(BaseModel):
    license_key: str


@app.get("/api/license")
def api_get_license():
    info = get_license_info()
    pay = get_payment_info()
    return {
        "status": "success",
        "license": info,
        "payment": pay
    }


@app.post("/api/license/activate")
def api_activate_license(req: ActivateRequest):
    ok, msg = activate_license(req.license_key)
    if ok:
        return {"status": "success", "message": msg, "license": get_license_info()}
    raise HTTPException(400, msg)


@app.get("/api/update/check")
def api_check_update():
    return check_for_updates()


@app.get("/api/defaults")
def get_defaults():
    draft_root = get_default_capcut_draft_path()
    sample_dirs = [
        r"C:\Users\vutru\OneDrive\Desktop\New folder (2)",
        os.path.expanduser("~/Desktop"),
        os.path.expanduser("~/Movies")
    ]
    sample_dir = ""
    for sd in sample_dirs:
        if os.path.isdir(sd):
            sample_dir = sd
            break

    defaults = {
        "draft_root": draft_root or "",
        "capcut_installed": bool(draft_root and os.path.exists(draft_root)),
        "srt_path": "",
        "script_content": "",
        "voice_path": "",
        "images_dir": "",
        "bgm_path": ""
    }
    if sample_dir and os.path.exists(sample_dir):
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
async def launch_capcut(request: Request):
    draft_path = None
    force_restart = False
    try:
        body = await request.json()
        if isinstance(body, dict):
            draft_path = body.get("draft_path")
            force_restart = bool(body.get("restart", False))
    except Exception:
        pass

    if is_capcut_running():
        hwnd = get_capcut_window_hwnd()
        if hwnd and not force_restart:
            focus_capcut_window()
            return {
                "status": "already_running",
                "message": "CapCut hiện đang mở trên máy tính. Để dự án mới xuất hiện ngay trên trang chủ CapCut, CapCut cần được khởi động lại.",
                "draft_path": draft_path
            }
        ok = restart_capcut_app()
        if ok:
            return {"status": "success", "message": "Đã khởi động lại CapCut và tải dự án mới thành công!"}
        if draft_path and os.path.exists(draft_path):
            open_path_in_os(draft_path)
            return {"status": "success", "message": "Đã mở thư mục dự án trong File Explorer."}
        return {"status": "error", "message": "Không thể khởi động lại CapCut. Vui lòng mở CapCut thủ công."}

    ok = launch_capcut_app(draft_path)
    if ok:
        return {"status": "success", "message": "Đã khởi chạy CapCut thành công!"}
    if draft_path and os.path.exists(draft_path):
        open_path_in_os(draft_path)
        return {"status": "success", "message": "Đã mở thư mục dự án trong File Explorer."}
    return {"status": "error", "message": "Không tìm thấy CapCut tự động. Vui lòng mở CapCut từ máy tính của bạn."}


@app.post("/api/open-folder")
async def open_folder(request: Request):
    folder_path = None
    try:
        body = await request.json()
        if isinstance(body, dict):
            folder_path = body.get("path")
    except Exception:
        pass
    if folder_path and os.path.exists(folder_path):
        open_path_in_os(folder_path)
        return {"status": "success", "message": f"Đã mở thư mục: {folder_path}"}
    return {"status": "error", "message": "Thư mục không tồn tại."}


@app.get("/api/update-check")
def api_update_check():
    return check_for_updates()


@app.websocket("/ws/build")
async def ws_build(websocket: WebSocket):
    await websocket.accept()
    try:
        # Enforce license check before processing
        try:
            check_license_valid()
        except LicenseExpiredError as e:
            await websocket.send_json({
                "type": "error",
                "message": f"BẢN QUYỀN ĐÃ HẾT HẠN: {str(e)}\nVui lòng kích hoạt gói 150k vĩnh viễn để tiếp tục sử dụng!"
            })
            await websocket.close()
            return

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
                subtitle_box_color=req.get("subtitle_box_color", "black"),
                subtitle_border_color=req.get("subtitle_border_color", "none"),
                subtitle_animation=req.get("subtitle_animation", "word_bounce_box"),
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
  <title>AutoCapCut Studio - Tự Động Biên Tập Video CapCut</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
  <style>
    :root {
      --bg: #15161a;
      --card: #1d1f26;
      --border: #2a2d38;
      --input: #131418;
      --input-border: #303442;
      --text: #e3e5ec;
      --sub: #9499ab;
      --accent: #5356e3;
      --accent-hover: #4447d1;
      --btn-sec: #252833;
      --btn-sec-hover: #323646;
      --success: #10b981;
      --teal: #0d9488;
      --teal-hover: #0f766e;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: 'Plus Jakarta Sans', -apple-system, sans-serif;
      background-color: var(--bg);
      color: var(--text);
      padding: 16px 24px;
      min-height: 100vh;
      font-size: 13px;
    }
    .container { max-width: 1240px; margin: 0 auto; }

    /* Top Header */
    header {
      display: flex; justify-content: space-between; align-items: center;
      margin-bottom: 16px; padding-bottom: 12px; border-bottom: 1px solid var(--border);
    }
    .brand { display: flex; align-items: center; gap: 12px; }
    .brand-badge {
      width: 32px; height: 32px; border-radius: 6px;
      background: var(--accent); color: #fff;
      display: flex; align-items: center; justify-content: center;
      font-size: 13px; font-weight: 700;
    }
    .brand-title h1 { font-size: 17px; font-weight: 700; color: #fff; line-height: 1.2; }
    .brand-title p { font-size: 11px; color: var(--sub); margin-top: 2px; }
    .header-actions { display: flex; align-items: center; gap: 8px; }

    /* Buttons */
    .btn {
      padding: 6px 14px; border-radius: 6px; font-size: 12px; font-weight: 500;
      cursor: pointer; border: 1px solid transparent; transition: all 0.15s;
      display: inline-flex; align-items: center; justify-content: center; gap: 6px;
      font-family: inherit;
    }
    .btn-primary {
      background: var(--accent); color: #fff; border-color: var(--accent);
      font-weight: 600;
    }
    .btn-primary:hover { background: var(--accent-hover); }
    .btn-secondary {
      background: var(--btn-sec); color: var(--text); border-color: var(--border);
    }
    .btn-secondary:hover { background: var(--btn-sec-hover); border-color: #3b3d4a; }

    /* 2-Column Grid Layout */
    .workspace-grid {
      display: grid;
      grid-template-columns: 46% 54%;
      gap: 16px;
      align-items: start;
    }
    @media (max-width: 960px) {
      .workspace-grid { grid-template-columns: 1fr; }
    }

    /* Cards */
    .card {
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 16px;
      margin-bottom: 14px;
    }
    .card-title {
      font-size: 12px; font-weight: 700; color: #ffffff;
      display: flex; align-items: center; justify-content: space-between;
      margin-bottom: 12px; text-transform: uppercase; letter-spacing: 0.5px;
    }

    /* Form Rows */
    .form-row { display: flex; align-items: center; margin-bottom: 8px; gap: 8px; }
    .form-row label { width: 140px; flex-shrink: 0; color: var(--text); font-weight: 500; font-size: 12px; }
    input[type="text"], select, textarea {
      background: var(--input); color: var(--text); border: 1px solid var(--input-border);
      border-radius: 6px; padding: 6px 10px; font-size: 12px; outline: none;
      transition: border-color 0.15s; font-family: inherit;
    }
    input[type="text"]:focus, select:focus, textarea:focus { border-color: var(--accent); }
    input[type="text"] { flex: 1; }

    /* Scenes Box */
    .scenes-box {
      border: 1px solid var(--input-border); border-radius: 8px; background: var(--input);
      padding: 10px; margin-top: 4px;
    }
    .scenes-tools { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
    .scenes-badge {
      background: #1e2027; color: var(--sub); padding: 2px 8px; border-radius: 8px;
      font-size: 10px; font-weight: 600; margin-left: 6px;
    }
    textarea {
      width: 100%; height: 160px; resize: vertical; border: none; padding: 0;
      background: transparent; color: var(--text); line-height: 1.5; font-size: 12px;
    }

    /* Tabs Component */
    .tab-header {
      display: flex; gap: 4px; background: var(--input); border: 1px solid var(--border);
      border-radius: 8px; padding: 3px; margin-bottom: 14px;
    }
    .tab-btn {
      flex: 1; padding: 7px 10px; font-size: 11px; font-weight: 600; color: var(--sub);
      background: transparent; border: none; border-radius: 6px; cursor: pointer;
      transition: all 0.15s; text-align: center; font-family: inherit;
    }
    .tab-btn:hover { color: var(--text); background: var(--btn-sec-hover); }
    .tab-btn.active { background: var(--accent); color: #fff; }

    .tab-content { display: none; }
    .tab-content.active { display: block; }

    /* Checkbox & Motion Cards */
    .checkbox-label {
      display: flex; align-items: center; gap: 6px; cursor: pointer;
      color: var(--text); font-size: 12px;
    }
    .checkbox-label input[type="checkbox"] { accent-color: var(--accent); width: 14px; height: 14px; }

    .motions-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
    .motion-card {
      background: #14151a; border: 1px solid var(--border);
      border-radius: 6px; padding: 8px 10px; display: flex; flex-direction: column; gap: 6px;
    }
    .motion-row { display: flex; align-items: center; gap: 4px; font-size: 11px; }
    .motion-row input[type="text"] { width: 38px; text-align: center; padding: 2px 4px; font-size: 11px; flex: none; height: 22px; }
    .motion-row label { display: flex; align-items: center; gap: 4px; width: 95px; font-weight: 500; cursor: pointer; }
    .motion-row input[type="checkbox"] { accent-color: var(--accent); width: 13px; height: 13px; }

    /* Progress & Console */
    .progress-bar-bg {
      width: 100%; height: 6px; background: var(--input); border-radius: 999px;
      overflow: hidden; margin-top: 8px; border: 1px solid var(--border);
    }
    .progress-bar-fill {
      height: 100%; width: 0%; background: var(--accent); transition: width 0.2s;
    }

    .console-box {
      background: var(--input); border: 1px solid var(--input-border); border-radius: 6px;
      padding: 10px; height: 110px; overflow-y: auto; font-family: 'JetBrains Mono', monospace;
      font-size: 11px; color: var(--sub); white-space: pre-wrap; line-height: 1.45;
    }

    /* License Badge & Activation Modal */
    .license-badge {
      display: inline-flex; align-items: center; gap: 6px; padding: 5px 12px;
      border-radius: 6px; font-size: 11px; font-weight: 700; cursor: pointer;
      transition: all 0.2s; border: 1px solid transparent; user-select: none;
    }
    .license-badge.lifetime {
      background: #065f46; color: #6ee7b7; border-color: #047857;
    }
    .license-badge.lifetime:hover { background: #047857; }
    .license-badge.trial {
      background: #854d0e; color: #fef08a; border-color: #a16207;
    }
    .license-badge.trial:hover { background: #a16207; }
    .license-badge.expired {
      background: #991b1b; color: #fca5a5; border-color: #b91c1c;
      animation: pulse-red 2s infinite;
    }
    .license-badge.expired:hover { background: #b91c1c; }

    @keyframes pulse-red {
      0%, 100% { opacity: 1; }
      50% { opacity: 0.8; }
    }

    .modal-overlay {
      display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%;
      background: rgba(0, 0, 0, 0.75); backdrop-filter: blur(4px);
      z-index: 9999; align-items: center; justify-content: center;
    }
    .modal-overlay.active { display: flex; }
    .modal-card {
      background: #18191e; border: 1px solid #2e3039; border-radius: 12px;
      width: 90%; max-width: 580px; padding: 22px; box-shadow: 0 20px 40px rgba(0,0,0,0.5);
    }
    .modal-header {
      display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;
    }
    .modal-close {
      background: transparent; border: none; color: var(--sub); font-size: 18px;
      cursor: pointer; padding: 4px 8px; border-radius: 4px;
    }
    .modal-close:hover { color: #fff; background: var(--btn-sec-hover); }
    .lic-section { margin-bottom: 12px; }
    .btn-xs {
      background: var(--btn-sec); border: 1px solid var(--border); color: var(--text);
      border-radius: 4px; padding: 2px 7px; font-size: 10px; cursor: pointer;
      margin-left: 6px;
    }
    .btn-xs:hover { background: var(--btn-sec-hover); }
  </style>
</head>
<body>
  <div class="container">
    <!-- Top Header -->
    <header>
      <div class="brand">
        <div class="brand-badge">AC</div>
        <div class="brand-title">
          <div style="display: flex; align-items: center; gap: 8px;">
            <h1>AutoCapCut Studio</h1>
            <span style="font-size: 10px; font-weight: 700; background: #1e293b; color: #94a3b8; padding: 2px 6px; border-radius: 4px; cursor: pointer;" onclick="checkUpdateWeb()" title="Bấm để kiểm tra bản cập nhật">v1.0.0</span>
          </div>
          <p>Đồng bộ media, phụ đề & biên tập timeline CapCut tự động</p>
        </div>
      </div>
      <div class="header-actions">
        <span style="color: var(--sub); font-size: 11px;">Mẫu nhanh:</span>
        <select id="preset_sel" onchange="applyPreset(this.value)" style="width: 250px; font-size: 11px;">
          <option value="custom">Tùy chỉnh thủ công (Custom)</option>
          <option value="tiktok">Video ngắn dọc TikTok / Shorts (9:16)</option>
          <option value="cinematic">Video ngang điện ảnh YouTube (16:9)</option>
          <option value="finance">Bản tin & Tin tức tài chính (16:9)</option>
          <option value="minimal">Tối giản nhanh (16:9)</option>
        </select>
        <button class="btn btn-secondary" onclick="autoLoadSamples()">Tự động điền</button>
        <button class="btn btn-secondary" onclick="launchCapCut()">Mở CapCut</button>
        <div id="licenseBadge" class="license-badge trial" onclick="openLicenseModal()">
          Đang kiểm tra...
        </div>
      </div>
    </header>

    <!-- Update Alert Banner (shown when a newer version is waiting) -->
    <div id="updateBanner" style="display: none; background: #064e3b; border: 1px solid #059669; border-radius: 8px; padding: 10px 16px; margin-bottom: 16px; justify-content: space-between; align-items: center;">
      <div style="display: flex; align-items: center; gap: 10px;">
        <span style="background: #047857; color: #ecfdf5; font-size: 10px; font-weight: 700; padding: 3px 8px; border-radius: 4px;">CẬP NHẬT CHỜ CÀI ĐẶT</span>
        <div>
          <div id="updateTitle" style="font-weight: 700; color: #fff; font-size: 13px;">AutoCapCut Studio có bản cập nhật mới</div>
          <div id="updateSubtitle" style="font-size: 11px; color: #a7f3d0; margin-top: 2px;">Nhấn vào đây để tải và nâng cấp.</div>
        </div>
      </div>
      <div style="display: flex; align-items: center; gap: 8px;">
        <a id="updateBtn" href="#" target="_blank" class="btn btn-primary" style="background: #10b981; border-color: #10b981; font-weight: 600; text-decoration: none;">Cập nhật ngay</a>
        <button class="btn btn-secondary" style="padding: 4px 10px;" onclick="document.getElementById('updateBanner').style.display='none'">✕</button>
      </div>
    </div>

    <!-- Main 2-Column Workspace -->
    <div class="workspace-grid">
      <!-- LEFT COLUMN: Inputs & Script -->
      <div>
        <!-- Card 1: Data inputs -->
        <div class="card">
          <div class="card-title">1. Dữ Liệu Đầu Vào</div>
          <div class="form-row">
            <label>File Voice (Âm thanh):</label>
            <input type="text" id="voice_paths" placeholder="Đường dẫn file audio (.wav, .mp3)...">
          </div>
          <div class="form-row">
            <label>File Phụ Đề (.srt):</label>
            <input type="text" id="srt_path" placeholder="Đường dẫn file phụ đề .srt...">
          </div>
          <div class="form-row">
            <label>Thư Mục Media:</label>
            <input type="text" id="images_dir" placeholder="Thư mục chứa ảnh hoặc video...">
          </div>
          <div class="form-row">
            <label>Nhạc Nền (BGM):</label>
            <select id="bgm_preset" style="flex: 1;" onchange="onBgmPresetChange()">
              <option value="none">Không dùng nhạc nền</option>
              <option value="cinematic">Điện ảnh & Sâu lắng (Cinematic Piano/Strings)</option>
              <option value="news">Tin tức & Tài chính (News / Finance / Tech)</option>
              <option value="lofi">Thư giãn & Lofi Chill (Lofi Beats / Acoustic)</option>
              <option value="dramatic">Kịch tính & Hồi hộp (Suspense Thriller)</option>
              <option value="happy">Vui tươi & Năng động (Happy Vlog / Upbeat)</option>
              <option value="custom">Tự chọn đường dẫn file trên máy...</option>
            </select>
            <input type="text" id="bgm_paths" placeholder="File nhạc nền (tùy chọn)..." style="display: none; flex: 1;">
            <span style="color: var(--sub); font-size: 11px;">Vol:</span>
            <input type="text" id="bgm_volume" value="15" style="width: 36px; text-align: center; flex: none;">
            <span style="color: var(--sub); font-size: 11px;">%</span>
            <button class="btn btn-secondary" style="padding: 4px 8px;" onclick="clearBgm()">✕</button>
          </div>
          <div class="form-row">
            <label>Tên Dự Án CapCut:</label>
            <input type="text" id="project_name" value="AutoCapCut_Project">
          </div>
        </div>

        <!-- Card 2: Script Textarea -->
        <div class="card">
          <div class="card-title">
            <span>2. Kịch Bản Phân Cảnh (Mỗi dòng 1 media)</span>
            <span class="scenes-badge" id="scenes_count">0 cảnh đã nạp</span>
          </div>
          <div class="scenes-box">
            <div class="scenes-tools">
              <div style="display: flex; gap: 4px;">
                <button class="btn btn-secondary" style="padding: 3px 8px; font-size: 11px;" onclick="splitSentences()">Tách câu</button>
                <button class="btn btn-secondary" style="padding: 3px 8px; font-size: 11px;" onclick="cleanEmptyLines()">Dọn dòng</button>
                <button class="btn btn-secondary" style="padding: 3px 8px; font-size: 11px;" onclick="copyScenes()">Copy</button>
                <button class="btn btn-secondary" style="padding: 3px 8px; font-size: 11px;" onclick="clearScenes()">✕</button>
              </div>
            </div>
            <textarea id="scenes_text" oninput="updateScenesCount()" placeholder="Chia kịch bản thành từng câu, mỗi câu một dòng rồi dán vào đây...
• Mỗi dòng tương ứng với 1 ảnh hoặc video.
• Phần mềm sẽ tự động căn thời gian media theo đúng giọng đọc của dòng đó."></textarea>
          </div>
        </div>
      </div>

      <!-- RIGHT COLUMN: Tabbed Controls & Action Box -->
      <div>
        <div class="card" style="padding-bottom: 12px;">
          <!-- Tab Headers -->
          <div class="tab-header">
            <button class="tab-btn active" data-tab="tab_tr" onclick="switchTab('tab_tr')">Chuyển cảnh & Mở đầu</button>
            <button class="tab-btn" data-tab="tab_eff" onclick="switchTab('tab_eff')">Hiệu ứng & Bộ lọc</button>
            <button class="tab-btn" data-tab="tab_cam" onclick="switchTab('tab_cam')">Chuyển động Camera</button>
            <button class="tab-btn" data-tab="tab_sub" onclick="switchTab('tab_sub')">Phụ đề & Âm thanh</button>
          </div>

          <!-- TAB 1: Transitions & Intros -->
          <div id="tab_tr" class="tab-content active">
            <div style="display: flex; flex-direction: column; gap: 10px;">
              <div class="form-row">
                <label>Khung hình & Sắp xếp:</label>
                <select id="aspect_ratio" style="flex: 1;">
                  <option value="16:9">16:9 (Ngang - YouTube, Facebook)</option>
                  <option value="9:16">9:16 (Dọc - TikTok, Reels, Shorts)</option>
                  <option value="1:1">1:1 (Vuông - Instagram, Post)</option>
                </select>
                <select id="sort_mode" style="flex: 1;">
                  <option value="abc">Sắp xếp ABC</option>
                  <option value="oldest_first">Cũ đến Mới</option>
                  <option value="newest_first">Mới đến Cũ</option>
                </select>
              </div>

              <div class="form-row">
                <label>Chuyển cảnh:</label>
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
                <input type="text" id="trans_dur" value="0.5" style="width: 36px; text-align: center; flex: none;">
                <span style="color: var(--sub); font-size: 11px;">s</span>
              </div>
              <div class="form-row">
                <label>Áp dụng chuyển cảnh:</label>
                <select id="trans_mode" style="flex: 1;">
                  <option value="all">Tất cả phân cảnh (All)</option>
                  <option value="random">Ngẫu nhiên đổi hiệu ứng (Random)</option>
                  <option value="alternate">Xen kẽ các cảnh (Alternate)</option>
                </select>
              </div>

              <div class="form-row" style="margin-top: 4px; border-top: 1px solid var(--border); padding-top: 10px;">
                <label>Hoạt ảnh mở đầu (Intro):</label>
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
                <input type="text" id="clip_intro_dur" value="0.8" style="width: 36px; text-align: center; flex: none;">
                <span style="color: var(--sub); font-size: 11px;">s</span>
              </div>
              <div class="form-row">
                <label>Áp dụng hoạt ảnh:</label>
                <select id="clip_intro_mode" style="flex: 1;">
                  <option value="all">Tất cả phân cảnh</option>
                  <option value="random">Ngẫu nhiên xen kẽ</option>
                  <option value="first_only">Chỉ cảnh đầu tiên</option>
                </select>
              </div>
            </div>
          </div>

          <!-- TAB 2: Effects & Filters -->
          <div id="tab_eff" class="tab-content">
            <div style="display: flex; flex-direction: column; gap: 10px;">
              <div class="form-row">
                <label>Hiệu ứng video CapCut:</label>
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
                <select id="video_eff_scope" style="width: 170px; flex: none;">
                  <option value="all">Tất cả phân cảnh</option>
                  <option value="random">Ngẫu nhiên một số cảnh</option>
                  <option value="intro_outro">Chỉ mở đầu & kết thúc</option>
                </select>
              </div>

              <div class="form-row">
                <label>Bộ lọc màu điện ảnh:</label>
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
                <input type="text" id="filter_intensity" value="60" style="width: 36px; text-align: center; flex: none;">
                <span style="color: var(--sub); font-size: 11px;">%</span>
              </div>

              <div style="border-top: 1px solid var(--border); padding-top: 10px; display: flex; flex-direction: column; gap: 8px;">
                <label class="checkbox-label">
                  <input type="checkbox" id="cb_blur" checked>
                  Làm mờ nền Canvas Blur khi ảnh không vừa khung (tránh viền đen)
                </label>
                <label class="checkbox-label">
                  <input type="checkbox" id="cb_wm" checked>
                  Xóa watermark ảnh Gemini AI tự động (Lossless Reverse Alpha Blending)
                </label>
              </div>
            </div>
          </div>

          <!-- TAB 3: Camera Motion -->
          <div id="tab_cam" class="tab-content">
            <div style="display: flex; flex-direction: column; gap: 10px;">
              <div class="form-row">
                <label>Chế độ chuyển động:</label>
                <select id="camera_motion_sel" style="flex: 1;">
                  <option value="smart_pacing">Smart Pacing AI (Tự phân tích nhịp câu)</option>
                  <option value="zoom_in">Zoom In (Phóng to dần)</option>
                  <option value="zoom_out">Zoom Out (Thu nhỏ dần)</option>
                  <option value="pan_left">Pan Left (Lia sang trái)</option>
                  <option value="pan_right">Pan Right (Lia sang phải)</option>
                  <option value="pan_up">Pan Up (Lia lên trên)</option>
                  <option value="pan_down">Pan Down (Lia xuống dưới)</option>
                  <option value="random">Ngẫu nhiên góc quay (Ken Burns)</option>
                  <option value="none">Cố định (Không chuyển động)</option>
                </select>
                <span style="color: var(--sub); font-size: 11px;">Zoom:</span>
                <input type="text" id="zoom_scale" value="112" style="width: 38px; text-align: center; flex: none;">
                <span style="color: var(--sub); font-size: 11px;">%</span>
              </div>

              <div style="display: flex; justify-content: space-between; align-items: center;">
                <span style="color: var(--sub); font-size: 11px;">Tinh chỉnh 6 hướng Keyframe:</span>
                <div style="display: flex; gap: 4px;">
                  <button class="btn btn-secondary" style="padding: 2px 8px; font-size: 10px;" onclick="selectAllMotions(true)">Chọn tất cả</button>
                  <button class="btn btn-secondary" style="padding: 2px 8px; font-size: 10px;" onclick="selectAllMotions(false)">Bỏ chọn</button>
                </div>
              </div>

              <div class="motions-grid">
                <div class="motion-card">
                  <div class="motion-row">
                    <label><input type="checkbox" id="m_zoom_in" checked> Zoom In</label>
                    <span style="color: var(--sub);">S:</span> <input type="text" id="m_zoom_in_s" value="110"> %
                  </div>
                  <div class="motion-row">
                    <label><input type="checkbox" id="m_pan_up" checked> Pan Up</label>
                    <span style="color: var(--sub);">X:</span> <input type="text" id="m_pan_up_x" value="0">
                    <span style="color: var(--sub);">Y:</span> <input type="text" id="m_pan_up_y" value="100">
                    <span style="color: var(--sub);">S:</span> <input type="text" id="m_pan_up_s" value="110">
                  </div>
                  <div class="motion-row">
                    <label><input type="checkbox" id="m_pan_left" checked> Pan Left</label>
                    <span style="color: var(--sub);">X:</span> <input type="text" id="m_pan_left_x" value="190">
                    <span style="color: var(--sub);">Y:</span> <input type="text" id="m_pan_left_y" value="0">
                    <span style="color: var(--sub);">S:</span> <input type="text" id="m_pan_left_s" value="110">
                  </div>
                </div>

                <div class="motion-card">
                  <div class="motion-row">
                    <label><input type="checkbox" id="m_zoom_out" checked> Zoom Out</label>
                    <span style="color: var(--sub);">S:</span> <input type="text" id="m_zoom_out_s" value="110"> %
                  </div>
                  <div class="motion-row">
                    <label><input type="checkbox" id="m_pan_down" checked> Pan Down</label>
                    <span style="color: var(--sub);">X:</span> <input type="text" id="m_pan_down_x" value="0">
                    <span style="color: var(--sub);">Y:</span> <input type="text" id="m_pan_down_y" value="100">
                    <span style="color: var(--sub);">S:</span> <input type="text" id="m_pan_down_s" value="110">
                  </div>
                  <div class="motion-row">
                    <label><input type="checkbox" id="m_pan_right" checked> Pan Right</label>
                    <span style="color: var(--sub);">X:</span> <input type="text" id="m_pan_right_x" value="190">
                    <span style="color: var(--sub);">Y:</span> <input type="text" id="m_pan_right_y" value="0">
                    <span style="color: var(--sub);">S:</span> <input type="text" id="m_pan_right_s" value="110">
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- TAB 4: Subtitles & Audio Suite -->
          <div id="tab_sub" class="tab-content">
            <div style="display: flex; flex-direction: column; gap: 8px;">
              <label class="checkbox-label" style="font-weight: 600;">
                <input type="checkbox" id="cb_subs" checked>
                Tự động chèn phụ đề SRT vào timeline
              </label>

              <div class="form-row">
                <label>Màu chữ & Cỡ:</label>
                <select id="sub_color" style="flex: 1;">
                  <option value="yellow">Vàng Nổi Bật (TikTok / Viral)</option>
                  <option value="white">Trắng Truyền Thống (Classic White)</option>
                  <option value="cyan">Xanh Công Nghệ (Cyan Modern)</option>
                  <option value="green">Xanh Lá Tài Chính (Finance Green)</option>
                  <option value="red">Đỏ Ruby (Dramatic Red)</option>
                  <option value="purple">Tím Neon (Neon Purple)</option>
                </select>
                <span style="color: var(--sub); font-size: 11px;">Cỡ:</span>
                <input type="text" id="sub_size" value="8.5" style="width: 36px; text-align: center; flex: none;">
              </div>

              <div class="form-row">
                <label>Hiệu ứng & Khung hộp:</label>
                <select id="sub_anim" style="flex: 1;" onchange="onSubAnimChange(this.value)">
                  <option value="tiktok_viral">🔥 TikTok Viral (Hộp đen chữ vàng nảy từng từ)</option>
                  <option value="hormozi">⚡ Alex Hormozi (Chữ vàng nảy lò xo từng từ)</option>
                  <option value="mrbeast">🎬 MrBeast Pop (Chữ nảy lò xo theo câu)</option>
                  <option value="breaking_news">🚨 Breaking News (Hộp đỏ chữ trắng kịch tính)</option>
                  <option value="tech_finance">💎 Tech & Finance (Hộp xanh đậm chữ Cyan)</option>
                  <option value="cinematic">✨ Cinematic Clean (Chữ trắng nảy mượt theo câu)</option>
                  <option value="karaoke">🎤 Karaoke Reveal (Chữ đổi màu theo giọng đọc)</option>
                  <option value="classic">📺 Cổ điển (Phụ đề trắng viền đen chuẩn YouTube)</option>
                </select>
                <select id="sub_box" style="width: 140px; flex: none;">
                  <option value="black">Hộp Đen tương phản</option>
                  <option value="red">Hộp Đỏ nổi bật</option>
                  <option value="yellow">Hộp Vàng rực rỡ</option>
                  <option value="dark_blue">Hộp Xanh đậm</option>
                  <option value="purple">Hộp Tím Neon</option>
                  <option value="none">Không hộp nền</option>
                </select>
                <select id="sub_pos" style="width: 110px; flex: none;">
                  <option value="bottom">Dưới cùng</option>
                  <option value="center">Chính giữa</option>
                  <option value="top">Phía trên</option>
                </select>
              </div>

              <div class="form-row" style="border-top: 1px solid var(--border); padding-top: 8px;">
                <label class="checkbox-label">
                  <input type="checkbox" id="cb_sfx" checked>
                  Âm thanh SFX:
                </label>
                <select id="sfx_name_sel" style="flex: 1;">
                  <option value="random">Ngẫu nhiên phối hợp (Smart Random)</option>
                  <option value="whoosh_cinematic_deep">Whoosh Điện ảnh Trầm (Cinematic Deep)</option>
                  <option value="whoosh_fast">Whoosh Lướt Nhanh (Fast Wind)</option>
                  <option value="whoosh_soft_air">Whoosh Gió Nhẹ (Soft Air)</option>
                  <option value="whoosh_heavy_bass">Whoosh Tiếng Bass Dày (Heavy Bass)</option>
                  <option value="swoosh_fast_whip">Swoosh Vung Nhanh (Fast Whip)</option>
                  <option value="swoosh_slide">Swoosh Trượt Mượt (Slide)</option>
                  <option value="camera_shutter">Camera Shutter (Tiếng chụp ảnh)</option>
                  <option value="mouse_click">Mouse Click (Click chuột máy tính)</option>
                  <option value="keyboard_typing">Keyboard Typing (Gõ bàn phím)</option>
                  <option value="bubble_pop">Bubble Pop (Bong bóng vỡ vui nhộn)</option>
                  <option value="cash_register_kaching">Cash Register Kaching (Tiền leng keng)</option>
                  <option value="cinematic_boom_impact">Cinematic Boom (Va đập uy lực)</option>
                  <option value="bell_ding_chime">Bell Ding (Keng chuông báo)</option>
                  <option value="tape_rewind">Tape Rewind (Tua băng cassette)</option>
                  <option value="glitch_digital">Glitch Digital (Nhiễu sóng số)</option>
                </select>
                <span style="color: var(--sub); font-size: 11px;">Vol:</span>
                <input type="text" id="sfx_vol" value="50" style="width: 36px; text-align: center; flex: none;">
                <span style="color: var(--sub); font-size: 11px;">%</span>
              </div>

              <div style="display: flex; flex-direction: column; gap: 6px; padding-top: 4px;">
                <label class="checkbox-label">
                  <input type="checkbox" id="cb_ducking" checked>
                  Audio Ducking (Tự động hạ nhỏ nhạc nền khi có giọng đọc)
                </label>
                <label class="checkbox-label">
                  <input type="checkbox" id="cb_fade" checked>
                  Audio Fade In & Fade Out cho nhạc nền (Mở & tắt êm ái)
                </label>
                <label class="checkbox-label">
                  <input type="checkbox" id="cb_cta" checked>
                  Chèn CTA Kêu gọi Đăng ký (Subscribe) & chuông kết thúc video
                </label>
              </div>
            </div>
          </div>
        </div>

        <!-- Action Box -->
        <div class="card" style="padding: 12px 16px;">
          <button class="btn btn-primary" style="width: 100%; height: 38px; font-size: 13px;" id="btn-run" onclick="startBuild()">
            Bắt đầu tạo dự án CapCut
          </button>
          <div class="progress-bar-bg"><div class="progress-bar-fill" id="p-bar"></div></div>
          <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 6px;">
            <div id="p-status" style="color: var(--sub); font-size: 11px;">Sẵn sàng. Nhấn nút để xuất dự án sang CapCut PC.</div>
            <label class="checkbox-label" style="font-size: 11px; margin: 0;">
              <input type="checkbox" id="cb_auto_open_cc" checked>
              Tự động mở CapCut khi tạo xong
            </label>
          </div>
          <div id="quick_open_banner" style="display: none; margin-top: 10px; background: rgba(5, 150, 105, 0.15); border: 1px solid #059669; border-radius: 8px; padding: 10px 14px; text-align: center;">
            <div id="quick_open_title" style="color: #10b981; font-weight: bold; font-size: 12px; margin-bottom: 6px;">Dự án đã sẵn sàng trong CapCut!</div>
            <div style="display: flex; gap: 8px; justify-content: center; flex-wrap: wrap;">
              <button class="btn btn-primary" style="background: #059669; font-weight: bold; padding: 6px 18px; font-size: 12px;" onclick="openLastDraftCapCut()">Mở Dự Án Trong CapCut Ngay</button>
              <button class="btn btn-secondary" style="font-size: 12px; padding: 6px 14px;" onclick="openLastDraftFolder()">Mở Thư Mục Dự Án</button>
            </div>
          </div>
        </div>

        <!-- Console Log Box -->
        <div class="card">
          <div class="card-title">
            <span>Nhật ký tiến trình</span>
            <button class="btn btn-secondary" style="padding: 2px 8px; font-size: 10px;" onclick="document.getElementById('console').textContent=''">Xóa log</button>
          </div>
          <div class="console-box" id="console">AutoCapCut Studio sẵn sàng hoạt động.</div>
        </div>
      </div>
    </div>
  </div>

  <!-- License Activation Modal -->
  <div id="licenseModal" class="modal-overlay">
    <div class="modal-card">
      <div class="modal-header">
        <div id="modalBadge" class="license-badge trial">Đang tải...</div>
        <button class="modal-close" onclick="closeLicenseModal()">✕</button>
      </div>
      <h2 style="font-size: 16px; margin: 4px 0 2px 0; color: #fff;">Kích Hoạt Bản Quyền AutoCapCut Studio</h2>
      <p id="modalSub" style="color: var(--sub); font-size: 11px; margin-bottom: 12px;">Dùng thử 3 ngày miễn phí hoặc nâng cấp gói 150k vĩnh viễn.</p>

      <!-- Machine ID -->
      <div class="lic-section">
        <label style="font-size: 10px; font-weight: 700; color: var(--sub); text-transform: uppercase;">Mã Máy Của Bạn (Machine ID):</label>
        <div style="display: flex; gap: 8px; margin-top: 5px;">
          <input type="text" id="modalHwid" readonly style="font-family: 'JetBrains Mono', monospace; font-size: 13px; font-weight: 700; color: #60a5fa;" />
          <button class="btn btn-secondary" onclick="copyHwid()" id="btnCopyHwid">Sao chép</button>
        </div>
      </div>

      <!-- Payment info -->
      <div class="lic-section" style="background: #121316; border: 1px solid var(--border); border-radius: 8px; padding: 12px; margin: 10px 0;">
        <div style="font-size: 10px; font-weight: 700; color: #f59e0b; margin-bottom: 6px; text-transform: uppercase;">Thông Tin Thanh Toán (Gói Vĩnh Viễn 150.000 VNĐ)</div>
        <div style="display: flex; gap: 12px; align-items: center;">
          <div style="flex: 1; font-size: 11px; line-height: 1.7; color: var(--text);">
            <div>• Ngân hàng: <b id="payBank">MBBank</b></div>
            <div>• Số tài khoản: <b id="payAcc" style="color: #60a5fa;">...</b> <button class="btn-xs" onclick="copyStk()">Chép STK</button></div>
            <div>• Chủ tài khoản: <b id="payHolder">...</b></div>
            <div>• Số tiền: <b style="color: #10b981;">150.000 VNĐ</b> (Dùng trọn đời máy này)</div>
            <div>• Nội dung CK: <b id="payContent" style="color: #f59e0b;">...</b> <button class="btn-xs" onclick="copyNd()">Chép nội dung</button></div>
          </div>
          <div style="text-align: center;">
            <a id="vietqrLink" href="#" target="_blank" title="Bấm để mở ảnh QR kích thước lớn">
              <img id="vietqrImg" src="" alt="VietQR 150k" style="width: 105px; height: 105px; border-radius: 6px; border: 1px solid var(--border); background: #fff; display: block;" />
            </a>
            <div style="font-size: 9px; color: var(--sub); margin-top: 3px;">Quét VietQR 150k</div>
          </div>
        </div>
      </div>

      <!-- Key Input -->
      <div class="lic-section">
        <label style="font-size: 10px; font-weight: 700; color: var(--sub); text-transform: uppercase;">Nhập Mã Kích Hoạt (License Key):</label>
        <div style="display: flex; gap: 8px; margin-top: 5px;">
          <input type="text" id="modalKeyInput" placeholder="ACCP-XXXX-XXXX-XXXX-XXXX" style="font-family: 'JetBrains Mono', monospace; font-size: 12px;" />
          <button class="btn btn-primary" style="background: #10b981; border-color: #10b981; min-width: 120px;" onclick="doActivateKey()">Kích hoạt ngay</button>
        </div>
        <div id="modalActMsg" style="font-size: 11px; margin-top: 5px; min-height: 16px;"></div>
      </div>

      <div style="font-size: 10px; color: var(--sub); margin-top: 8px; text-align: center;">
        Sau khi chuyển khoản, bạn gửi mã máy qua Zalo/Facebook để nhận mã kích hoạt trong 5 phút.
      </div>
    </div>
  </div>

  <script>
    let sampleData = null;
    let licenseState = null;

    window.addEventListener('DOMContentLoaded', async () => {
      try {
        const res = await fetch('/api/defaults');
        sampleData = await res.json();
        autoLoadSamples();
      } catch (e) { console.error(e); }

      loadLicense();
      setTimeout(() => checkUpdateWeb(true), 2500);
    });

    async function checkUpdateWeb(silent = false) {
      try {
        const res = await fetch('/api/update/check');
        const data = await res.json();
        if (data.has_update) {
          const notes = (data.changelog || []).map(i => '• ' + i).join('\n');
          const ok = confirm(`ĐÃ CÓ BẢN CẬP NHẬT MỚI (v${data.latest_version})!\n\nĐiểm mới:\n${notes}\n\nBạn có muốn mở trang tải bản cập nhật không?`);
          if (ok) {
            window.open(data.manual_url || data.download_url, '_blank');
          }
        } else if (!silent) {
          alert(`Bạn đang sử dụng phiên bản mới nhất (v${data.current_version}).`);
        }
      } catch (e) {
        if (!silent) console.error('Lỗi kiểm tra cập nhật:', e);
      }
    }

    async function loadLicense() {
      try {
        const res = await fetch('/api/license');
        const data = await res.json();
        licenseState = data;
        updateLicenseUI(data.license, data.payment);
      } catch (e) {
        console.error('Không thể kiểm tra bản quyền:', e);
      }
    }

    function updateLicenseUI(lic, pay) {
      const badge = document.getElementById('licenseBadge');
      const mBadge = document.getElementById('modalBadge');
      const mSub = document.getElementById('modalSub');
      const btnRun = document.getElementById('btn-run');

      document.getElementById('modalHwid').value = lic.hwid;
      document.getElementById('payBank').textContent = pay.bank_name || 'MBBank';
      document.getElementById('payAcc').textContent = pay.bank_account || '';
      document.getElementById('payHolder').textContent = pay.account_name || '';
      document.getElementById('payContent').textContent = pay.transfer_content || '';
      document.getElementById('vietqrImg').src = pay.vietqr_url || '';
      document.getElementById('vietqrLink').href = pay.vietqr_url || '#';

      if (lic.status === 'lifetime') {
        badge.className = 'license-badge lifetime';
        badge.textContent = 'Bản quyền vĩnh viễn';
        mBadge.className = 'license-badge lifetime';
        mBadge.textContent = 'ĐÃ KÍCH HOẠT VĨNH VIỄN';
        mSub.textContent = 'Phần mềm đã được kích hoạt bản quyền vĩnh viễn trên máy tính này.';
        if (btnRun) {
          btnRun.disabled = false;
          btnRun.textContent = 'Bắt đầu tạo dự án CapCut';
        }
      } else if (lic.status === 'trial') {
        const d = lic.days_left || 0;
        const h = lic.hours_left || 0;
        const timeStr = d > 0 ? `${d} ngày ${h}h` : `${h} giờ`;
        badge.className = 'license-badge trial';
        badge.textContent = `Dùng thử: Còn ${timeStr}`;
        mBadge.className = 'license-badge trial';
        mBadge.textContent = `DÙNG THỬ (CÒN ${d} NGÀY ${h} GIỜ)`;
        mSub.textContent = 'Bạn đang trong thời gian dùng thử 3 ngày miễn phí. Nâng cấp 150k để dùng trọn đời.';
        if (btnRun) {
          btnRun.disabled = false;
          btnRun.textContent = 'Bắt đầu tạo dự án CapCut';
        }
      } else {
        badge.className = 'license-badge expired';
        badge.textContent = 'Hết hạn (Kích hoạt 150k)';
        mBadge.className = 'license-badge expired';
        mBadge.textContent = 'HẾT HẠN DÙNG THỬ 3 NGÀY';
        mSub.textContent = 'Thời gian dùng thử 3 ngày đã hết. Vui lòng thanh toán 150.000 VNĐ để mở khóa vĩnh viễn.';
        if (btnRun) {
          btnRun.disabled = true;
          btnRun.textContent = 'Đã hết hạn dùng thử 3 ngày (Kích hoạt 150k)';
        }
        openLicenseModal();
      }
    }

    function openLicenseModal() {
      document.getElementById('licenseModal').classList.add('active');
    }

    function closeLicenseModal() {
      document.getElementById('licenseModal').classList.remove('active');
    }

    function copyHwid() {
      const hwid = document.getElementById('modalHwid').value;
      navigator.clipboard.writeText(hwid);
      const btn = document.getElementById('btnCopyHwid');
      btn.textContent = 'Đã chép!';
      setTimeout(() => btn.textContent = 'Sao chép', 1500);
    }

    function copyStk() {
      const acc = document.getElementById('payAcc').textContent;
      navigator.clipboard.writeText(acc);
      alert('Đã sao chép số tài khoản: ' + acc);
    }

    function copyNd() {
      const nd = document.getElementById('payContent').textContent;
      navigator.clipboard.writeText(nd);
      alert('Đã sao chép nội dung chuyển khoản: ' + nd);
    }

    async function doActivateKey() {
      const key = document.getElementById('modalKeyInput').value.trim();
      const msgEl = document.getElementById('modalActMsg');
      if (!key) {
        msgEl.style.color = '#ef4444';
        msgEl.textContent = 'Vui lòng nhập mã kích hoạt!';
        return;
      }
      try {
        const res = await fetch('/api/license/activate', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ license_key: key })
        });
        const data = await res.json();
        if (res.ok && data.status === 'success') {
          msgEl.style.color = '#10b981';
          msgEl.textContent = data.message;
          alert(data.message);
          loadLicense();
          closeLicenseModal();
        } else {
          msgEl.style.color = '#ef4444';
          msgEl.textContent = data.detail || data.message || 'Mã kích hoạt không hợp lệ!';
        }
      } catch (e) {
        msgEl.style.color = '#ef4444';
        msgEl.textContent = 'Lỗi kết nối: ' + e.message;
      }
    }

    function switchTab(tabId) {
      document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
      document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
      const activeBtn = document.querySelector(`[data-tab="${tabId}"]`);
      if (activeBtn) activeBtn.classList.add('active');
      const activeContent = document.getElementById(tabId);
      if (activeContent) activeContent.classList.add('active');
    }

    function updateScenesCount() {
      const text = document.getElementById('scenes_text').value.trim();
      const count = text ? text.split('\\n').filter(l => l.trim().length > 0).length : 0;
      document.getElementById('scenes_count').textContent = count + ' cảnh đã nạp';
    }

    function autoLoadSamples() {
      if (!sampleData) return;
      if (sampleData.srt_path) document.getElementById('srt_path').value = sampleData.srt_path;
      if (sampleData.voice_path) document.getElementById('voice_paths').value = sampleData.voice_path;
      if (sampleData.images_dir) document.getElementById('images_dir').value = sampleData.images_dir;
      if (sampleData.script_content) document.getElementById('scenes_text').value = sampleData.script_content;
      updateScenesCount();
      log('[Info] Đã tự động nạp các tệp mẫu sẵn có từ Desktop.');
    }

    function log(msg) {
      const c = document.getElementById('console');
      c.textContent += '\\n' + msg;
      c.scrollTop = c.scrollHeight;
    }

    function copyScenes() {
      const t = document.getElementById('scenes_text').value;
      if (t.trim()) {
        navigator.clipboard.writeText(t);
        log('[Info] Đã sao chép kịch bản vào clipboard.');
      }
    }

    function splitSentences() {
      const t = document.getElementById('scenes_text').value.trim();
      if (!t) return;
      const sentences = t.replace(/\\r\\n/g, '\\n').split(/(?<=[.!?。！？;])\\s+/);
      const cleaned = sentences.map(s => s.trim()).filter(s => s.length > 0);
      if (cleaned.length > 0) {
        document.getElementById('scenes_text').value = cleaned.join('\\n');
        updateScenesCount();
        log(`[Action] Đã tách kịch bản thành ${cleaned.length} câu (mỗi câu 1 dòng).`);
      }
    }

    function cleanEmptyLines() {
      const t = document.getElementById('scenes_text').value.trim();
      if (!t) return;
      const lines = t.split('\\n').map(l => l.trim()).filter(l => l.length > 0);
      document.getElementById('scenes_text').value = lines.join('\\n');
      updateScenesCount();
      log(`[Action] Đã dọn dẹp dòng trống (${lines.length} dòng hợp lệ).`);
    }

    function clearScenes() {
      document.getElementById('scenes_text').value = '';
      updateScenesCount();
    }

    function selectAllMotions(state) {
      ['m_zoom_in', 'm_zoom_out', 'm_pan_up', 'm_pan_down', 'm_pan_left', 'm_pan_right'].forEach(id => {
        document.getElementById(id).checked = state;
      });
      log(`[Action] ${state ? 'Đã chọn tất cả' : 'Đã bỏ chọn tất cả'} chuyển động keyframe.`);
    }

    function onSubAnimChange(val) {
      const colEl = document.getElementById('sub_color');
      const boxEl = document.getElementById('sub_box');
      const sizeEl = document.getElementById('sub_size');
      if (!colEl || !boxEl || !sizeEl) return;
      if (val === 'tiktok_viral') {
        colEl.value = 'yellow';
        boxEl.value = 'black';
        sizeEl.value = '10.5';
      } else if (val === 'hormozi') {
        colEl.value = 'yellow';
        boxEl.value = 'none';
        sizeEl.value = '10.5';
      } else if (val === 'mrbeast') {
        colEl.value = 'yellow';
        boxEl.value = 'none';
        sizeEl.value = '9.0';
      } else if (val === 'breaking_news') {
        colEl.value = 'white';
        boxEl.value = 'red';
        sizeEl.value = '10.5';
      } else if (val === 'tech_finance') {
        colEl.value = 'cyan';
        boxEl.value = 'dark_blue';
        sizeEl.value = '10.5';
      } else if (val === 'cinematic') {
        colEl.value = 'white';
        boxEl.value = 'none';
        sizeEl.value = '8.5';
      } else if (val === 'karaoke') {
        colEl.value = 'yellow';
        boxEl.value = 'none';
        sizeEl.value = '9.0';
      } else if (val === 'classic') {
        colEl.value = 'white';
        boxEl.value = 'none';
        sizeEl.value = '8.5';
      }
    }

    function applyPreset(preset) {
      if (preset === 'tiktok') {
        document.getElementById('aspect_ratio').value = '9:16';
        document.getElementById('cb_subs').checked = true;
        document.getElementById('sub_anim').value = 'tiktok_viral';
        onSubAnimChange('tiktok_viral');
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
        document.getElementById('sfx_name_sel').value = 'whoosh_fast';
        document.getElementById('sfx_vol').value = '60';
        document.getElementById('bgm_preset').value = 'happy';
        document.getElementById('bgm_volume').value = '15';
        onBgmPresetChange();
        document.getElementById('cb_blur').checked = true;
        document.getElementById('cb_ducking').checked = true;
        document.getElementById('cb_fade').checked = true;
        document.getElementById('cb_cta').checked = true;
        selectAllMotions(true);
        log('[Preset] Đã áp dụng: Video ngắn dọc TikTok / Shorts (9:16).');
      } else if (preset === 'cinematic') {
        document.getElementById('aspect_ratio').value = '16:9';
        document.getElementById('cb_subs').checked = true;
        document.getElementById('sub_anim').value = 'cinematic';
        onSubAnimChange('cinematic');
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
        document.getElementById('sfx_name_sel').value = 'whoosh_cinematic_deep';
        document.getElementById('sfx_vol').value = '35';
        document.getElementById('bgm_preset').value = 'cinematic';
        document.getElementById('bgm_volume').value = '15';
        onBgmPresetChange();
        document.getElementById('cb_blur').checked = true;
        document.getElementById('cb_ducking').checked = true;
        document.getElementById('cb_fade').checked = true;
        document.getElementById('cb_cta').checked = true;
        selectAllMotions(true);
        log('[Preset] Đã áp dụng: Video ngang điện ảnh YouTube (16:9).');
      } else if (preset === 'finance') {
        document.getElementById('aspect_ratio').value = '16:9';
        document.getElementById('cb_subs').checked = true;
        document.getElementById('sub_anim').value = 'tech_finance';
        onSubAnimChange('tech_finance');
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
        document.getElementById('sfx_name_sel').value = 'bell_ding_chime';
        document.getElementById('sfx_vol').value = '25';
        document.getElementById('bgm_preset').value = 'news';
        document.getElementById('bgm_volume').value = '12';
        onBgmPresetChange();
        document.getElementById('cb_blur').checked = true;
        document.getElementById('cb_ducking').checked = true;
        document.getElementById('cb_fade').checked = true;
        document.getElementById('cb_cta').checked = true;
        selectAllMotions(true);
        log('[Preset] Đã áp dụng: Bản tin & Tin tức tài chính (16:9).');
      } else if (preset === 'minimal') {
        document.getElementById('aspect_ratio').value = '16:9';
        document.getElementById('cb_subs').checked = true;
        document.getElementById('sub_anim').value = 'classic';
        onSubAnimChange('classic');
        document.getElementById('transition_sel').value = 'none';
        document.getElementById('clip_intro_sel').value = 'none';
        document.getElementById('video_eff_sel').value = 'none';
        document.getElementById('filter_sel').value = 'none';
        document.getElementById('camera_motion_sel').value = 'none';
        document.getElementById('cb_sfx').checked = false;
        document.getElementById('bgm_preset').value = 'none';
        onBgmPresetChange();
        document.getElementById('cb_blur').checked = true;
        document.getElementById('cb_ducking').checked = true;
        document.getElementById('cb_fade').checked = true;
        document.getElementById('cb_cta').checked = false;
        selectAllMotions(false);
        log('[Preset] Đã áp dụng: Tối giản nhanh (16:9).');
      }
    }

    function onBgmPresetChange() {
      const sel = document.getElementById('bgm_preset').value;
      const pInput = document.getElementById('bgm_paths');
      if (sel === 'custom') {
        pInput.style.display = 'block';
        pInput.focus();
      } else {
        pInput.style.display = 'none';
        pInput.value = '';
      }
    }

    function clearBgm() {
      document.getElementById('bgm_preset').value = 'none';
      const pInput = document.getElementById('bgm_paths');
      pInput.value = '';
      pInput.style.display = 'none';
    }

    let lastDraftDir = null;

    async function launchCapCut(draftPath = null, restart = false) {
      try {
        const payload = { draft_path: draftPath, restart: restart };
        const res = await fetch('/api/launch-capcut', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
        const data = await res.json();
        if (data.status === 'success') {
          log('[Action] ' + data.message);
        } else if (data.status === 'already_running') {
          const ans = confirm(
            "CapCut hiện đang mở trên máy tính.\n\n" +
            "Để dự án mới xuất hiện ngay trên trang chủ CapCut, CapCut cần được khởi động lại.\n\n" +
            "• Bấm [OK]: Khởi động lại CapCut và tải dự án mới ngay.\n" +
            "• Bấm [Cancel/Hủy]: Mở thư mục dự án trong File Explorer."
          );
          if (ans) {
            log('[Action] Đang khởi động lại CapCut...');
            await launchCapCut(draftPath, true);
          } else {
            openLastDraftFolder();
          }
        } else {
          alert('Không thể mở CapCut: ' + data.message);
        }
      } catch (e) { alert(e.message); }
    }

    function openLastDraftCapCut() {
      launchCapCut(lastDraftDir);
    }

    async function openLastDraftFolder() {
      if (!lastDraftDir) return;
      try {
        const res = await fetch('/api/open-folder', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ path: lastDraftDir })
        });
        const data = await res.json();
        if (data.status === 'success') {
          log('[Action] ' + data.message);
        } else {
          alert(data.message);
        }
      } catch (e) { alert(e.message); }
    }

    function startBuild() {
      const bgmPreset = document.getElementById('bgm_preset').value;
      const customBgm = document.getElementById('bgm_paths').value.trim();
      let finalBgm = '';
      if (bgmPreset === 'custom') {
        finalBgm = customBgm;
      } else if (bgmPreset !== 'none') {
        finalBgm = bgmPreset;
      }

      const payload = {
        srt_path: document.getElementById('srt_path').value.trim(),
        script_source: document.getElementById('scenes_text').value.trim(),
        voice_paths: document.getElementById('voice_paths').value.trim(),
        images_dir: document.getElementById('images_dir').value.trim(),
        bgm_paths: finalBgm,
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
        subtitle_box_color: document.getElementById('sub_box').value,
        subtitle_border_color: "none",
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
      btn.textContent = 'Đang xử lý tiến trình...';

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
          pStatus.textContent = 'Hoàn tất 100%!';
          btn.disabled = false;
          btn.textContent = 'Bắt đầu tạo dự án CapCut';
          lastDraftDir = msg.result.draft_dir;
          log('\nTẠO DỰ ÁN CAPCUT THÀNH CÔNG');
          log(`  Dự án:      ${msg.result.draft_name}`);
          log(`  Tổng cảnh:  ${msg.result.total_scenes} cảnh`);
          log(`  Thời lượng: ${(msg.result.duration_seconds/60).toFixed(2)} phút`);
          log(`  Thư mục:    ${msg.result.draft_dir}`);

          const qBanner = document.getElementById('quick_open_banner');
          if (qBanner) {
            document.getElementById('quick_open_title').textContent = `Dự án '${msg.result.draft_name}' đã sẵn sàng!`;
            qBanner.style.display = 'block';
          }

          if (document.getElementById('cb_auto_open_cc').checked) {
            log('[Auto] Tự động khởi chạy CapCut mở dự án...');
            launchCapCut(msg.result.draft_dir);
          }
        } else if (msg.type === 'error') {
          btn.disabled = false;
          btn.textContent = 'Bắt đầu tạo dự án CapCut';
          pStatus.textContent = 'Lỗi: ' + msg.message;
          log('[Error] LỖI: ' + msg.message);
          alert('Lỗi: ' + msg.message);
        }
      };

      ws.onerror = (err) => {
        btn.disabled = false;
        btn.textContent = 'Bắt đầu tạo dự án CapCut';
        log('[Error] Lỗi kết nối WebSocket');
      };
    }

    // Auto-check for updates on load
    fetch('/api/update-check')
      .then(r => r.json())
      .then(data => {
        if (data.has_update) {
          const banner = document.getElementById('updateBanner');
          if (banner) {
            banner.style.display = 'flex';
            document.getElementById('updateTitle').innerText = `AutoCapCut Studio v${data.latest_version} đã sẵn sàng nâng cấp!`;
            if (data.changelog && data.changelog.length > 0) {
              document.getElementById('updateSubtitle').innerText = `• ${data.changelog[0]} (Giữ nguyên bản quyền & dữ liệu)`;
            }
            document.getElementById('updateBtn').href = data.download_url || data.manual_url;
          }
        }
      })
      .catch(() => {});
  </script>
</body>
</html>
"""


def main():
    import uvicorn
    print("\n" + "=" * 60)
    print("AutoCapCut Studio Web đang chạy tại: http://localhost:8000")
    print("=" * 60)
    uvicorn.run(app, host="127.0.0.1", port=8000)


if __name__ == '__main__':
    main()
