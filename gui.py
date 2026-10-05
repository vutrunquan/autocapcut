"""
Desktop GUI for AutoCapCut Studio.
Designed with a professional Graphite Studio Dark aesthetic,
ergonomic 2-column layout with tabbed effect controls,
soothing eye-friendly palette, and extensive pro video automation features.
"""

import os
import sys
import threading
import queue
import time
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox

if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

import customtkinter as ctk

from autocapcut import (
    run_autocapcut,
    get_default_capcut_draft_path,
    get_capcut_exe_path,
    open_path_in_os,
    launch_capcut_app,
    ensure_macos_path,
    get_machine_id,
    get_license_info,
    activate_license,
    get_payment_info,
    check_license_valid,
    LicenseExpiredError,
    CURRENT_VERSION,
    check_for_updates,
    download_update_file,
    apply_update_package
)

ensure_macos_path()


SCENES_PLACEHOLDER = (
    "Chia kịch bản thành từng câu, mỗi câu một dòng rồi dán vào đây...\n"
    "• Mỗi dòng tương ứng với 1 ảnh hoặc video.\n"
    "• Phần mềm sẽ tự động căn thời gian media theo đúng giọng đọc của dòng đó.\n"
    "• Bạn có thể nhấn 'Đọc .txt' để nạp file sẵn có hoặc dán trực tiếp."
)


class AutoCapCutApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")

        self.title("AutoCapCut Studio - Tự Động Biên Tập Video CapCut")
        self.geometry("1280x900")
        self.minsize(1160, 780)

        # Application Icon
        for p in [
            os.path.join(getattr(sys, '_MEIPASS', ''), "assets", "icon.ico"),
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "icon.ico"),
            os.path.join(os.path.dirname(sys.executable), "assets", "icon.ico"),
            "assets/icon.ico"
        ]:
            if p and os.path.exists(p):
                try:
                    self.iconbitmap(p)
                    break
                except Exception:
                    pass

        # ------------------------------------------------------------------
        # BESPOKE HORIZON HOMES DASHBOARD PALETTE
        # Warm Slate Charcoal Canvas, Elevated Surface Cards & Vibrant Coral Orange
        # ------------------------------------------------------------------
        self.c_bg = "#222227"           # Deep warm slate obsidian canvas
        self.c_card = "#2c2d34"         # Smooth elevated card surface
        self.c_card_border = "#3a3b45"  # Subtle crisp card boundary
        self.c_input = "#24252b"        # Inset container for text & inputs
        self.c_input_border = "#383944" # Clean input border
        self.c_text = "#f4f4f6"         # Crisp pearl white text
        self.c_sub = "#9ca3af"          # Soothing neutral gray helper text
        self.c_accent = "#ff5a36"       # Vibrant terracotta coral orange accent
        self.c_accent_hover = "#ff6e4d" # Energetic warm hover glow
        self.c_btn_sec = "#383944"      # Refined slate pill button
        self.c_btn_sec_h = "#464754"    # Natural hover
        self.c_btn_sec_text = "#f4f4f6" # Secondary button text
        self.c_success = "#22c55e"      # Emerald green indicator
        self.c_danger = "#ef4444"       # Soft rose red
        self.c_amber = "#f59e0b"        # Warm amber indicator

        self.configure(fg_color=self.c_bg)

        # ------------------------------------------------------------------
        # STATE VARIABLES
        # ------------------------------------------------------------------
        # Data inputs
        self.audio_files_var = tk.StringVar()
        self.srt_file_var = tk.StringVar()
        self.media_folder_var = tk.StringVar()
        self.bgm_files_var = tk.StringVar()
        self.bgm_preset_var = tk.StringVar(value="Không dùng nhạc nền")
        self.bgm_vol_var = tk.StringVar(value="15")
        self.capcut_name_var = tk.StringVar(value=f"AutoCapCut_{time.strftime('%Y%m%d_%H%M')}")
        self.draft_root_var = tk.StringVar(value=get_default_capcut_draft_path() or "")

        # Presets & Format
        self.preset_var = tk.StringVar(value="Tùy chỉnh thủ công (Custom)")
        self.aspect_ratio_var = tk.StringVar(value="16:9 (Ngang - YouTube, Facebook)")
        self.sort_mode_var = tk.StringVar(value="Sắp xếp media theo ABC (Số tự nhiên)")

        # Transitions & Clip Intro
        self.transition_var = tk.StringVar(value="Không transition")
        self.trans_dur_var = tk.StringVar(value="0.5")
        self.trans_mode_var = tk.StringVar(value="Tất cả phân cảnh (All)")

        self.clip_intro_var = tk.StringVar(value="Không animation")
        self.clip_intro_dur_var = tk.StringVar(value="0.8")
        self.clip_intro_mode_var = tk.StringVar(value="Tất cả phân cảnh (All)")

        # Video Effects & Filters
        self.video_effect_var = tk.StringVar(value="Không dùng hiệu ứng")
        self.video_effect_scope_var = tk.StringVar(value="Tất cả phân cảnh (All)")
        self.filter_var = tk.StringVar(value="Không dùng filter")
        self.filter_intensity_var = tk.StringVar(value="60")
        self.blur_var = tk.BooleanVar(value=True)
        self.watermark_var = tk.BooleanVar(value=True)

        # Subtitles & Audio Suite
        self.subtitles_var = tk.BooleanVar(value=True)
        self.subtitle_color_var = tk.StringVar(value="Vàng Nổi Bật (TikTok / Viral)")
        self.subtitle_box_var = tk.StringVar(value="Hộp Đen tương phản (Black Box)")
        self.sub_anim_var = tk.StringVar(value="Chữ nảy hộp chữ nhật từng từ (Word Bounce Box)")
        self.sub_size_var = tk.StringVar(value="9.5")
        self.sub_pos_var = tk.StringVar(value="Dưới cùng (Chuẩn Shorts/Reels)")

        self.sfx_var = tk.BooleanVar(value=True)
        self.sfx_name_var = tk.StringVar(value="Ngẫu nhiên phối hợp (Smart Random)")
        self.sfx_vol_var = tk.StringVar(value="50")
        self.ducking_var = tk.BooleanVar(value=True)
        self.fade_var = tk.BooleanVar(value=True)
        self.cta_sub_var = tk.BooleanVar(value=True)
        self.auto_open_capcut_var = tk.BooleanVar(value=True)

        # Camera Motion & Ken Burns
        self.camera_motion_var = tk.StringVar(value="Smart Pacing AI (Tự phân tích nhịp câu)")
        self.zoom_scale_var = tk.StringVar(value="112")
        self.smart_pacing_var = tk.BooleanVar(value=True)

        self.m_zoom_in_var = tk.BooleanVar(value=True)
        self.m_zoom_in_scale = tk.StringVar(value="110")

        self.m_zoom_out_var = tk.BooleanVar(value=True)
        self.m_zoom_out_scale = tk.StringVar(value="110")

        self.m_pan_up_var = tk.BooleanVar(value=True)
        self.m_pan_up_x = tk.StringVar(value="0")
        self.m_pan_up_y = tk.StringVar(value="100")
        self.m_pan_up_scale = tk.StringVar(value="110")

        self.m_pan_down_var = tk.BooleanVar(value=True)
        self.m_pan_down_x = tk.StringVar(value="0")
        self.m_pan_down_y = tk.StringVar(value="100")
        self.m_pan_down_scale = tk.StringVar(value="110")

        self.m_pan_left_var = tk.BooleanVar(value=True)
        self.m_pan_left_x = tk.StringVar(value="190")
        self.m_pan_left_y = tk.StringVar(value="0")
        self.m_pan_left_scale = tk.StringVar(value="110")

        self.m_pan_right_var = tk.BooleanVar(value=True)
        self.m_pan_right_x = tk.StringVar(value="190")
        self.m_pan_right_y = tk.StringVar(value="0")
        self.m_pan_right_scale = tk.StringVar(value="110")

        self.msg_queue = queue.Queue()
        self.is_running = False
        self.cancel_event = threading.Event()
        self.last_draft_dir = None
        self.pending_update_data = None

        sample_dirs = [
            r"C:\Users\vutru\OneDrive\Desktop\New folder (2)",
            os.path.expanduser("~/Desktop"),
            os.path.expanduser("~/Movies"),
            os.path.expanduser("~")
        ]
        self.default_init_dir = os.path.expanduser("~")
        for sd in sample_dirs:
            if os.path.isdir(sd):
                self.default_init_dir = sd
                break

        self._build_layout()
        self._auto_detect_sample_files()
        self._update_preset_pills_ui()
        self._update_stat_cards()
        self._update_license_ui()
        self.after(100, self._process_queue)
        if not get_license_info().get("is_valid", False):
            self.after(600, self._open_license_dialog)
        # Background check for updates after 2s
        self.after(2000, self._start_background_update_check)

    def _build_layout(self):
        # ------------------------------------------------------------------
        # 1. TOP FLOATING NAVBAR (Horizon Homes Architecture)
        # ------------------------------------------------------------------
        nav_card = ctk.CTkFrame(
            self, fg_color=self.c_card, corner_radius=14,
            border_color=self.c_card_border, border_width=1
        )
        nav_card.pack(fill="x", padx=22, pady=(14, 8))

        nav_inner = ctk.CTkFrame(nav_card, fg_color="transparent")
        nav_inner.pack(fill="x", padx=16, pady=8)

        # Brand Badge & Title
        brand_box = ctk.CTkFrame(nav_inner, fg_color="transparent")
        brand_box.pack(side="left")

        title_box = ctk.CTkFrame(brand_box, fg_color="transparent")
        title_box.pack(side="left")

        title_row = ctk.CTkFrame(title_box, fg_color="transparent")
        title_row.pack(anchor="w")

        lbl_title = ctk.CTkLabel(
            title_row, text="AutoCapCut Studio", font=("Segoe UI", 15, "bold"),
            text_color="#ffffff"
        )
        lbl_title.pack(side="left")

        self.btn_ver = ctk.CTkButton(
            title_row, text=f"v{CURRENT_VERSION}", font=("Segoe UI", 9, "bold"),
            fg_color=self.c_btn_sec, hover_color=self.c_btn_sec_h, text_color=self.c_text,
            corner_radius=10, height=22, width=54, command=self._manual_check_update
        )
        self.btn_ver.pack(side="left", padx=(8, 0))

        lbl_sub = ctk.CTkLabel(
            title_box, text="Đồng bộ media, phụ đề & biên tập timeline CapCut tự động",
            font=("Segoe UI", 10), text_color=self.c_sub
        )
        lbl_sub.pack(anchor="w")

        # Preset Selector in Navbar
        preset_box = ctk.CTkFrame(nav_inner, fg_color="transparent")
        preset_box.pack(side="left", padx=(28, 0))

        ctk.CTkLabel(preset_box, text="Mẫu:", font=("Segoe UI", 11, "bold"), text_color=self.c_sub).pack(side="left", padx=(0, 8))

        preset_opts = [
            "Tùy chỉnh thủ công (Custom)",
            "Video ngắn dọc TikTok / Shorts (9:16)",
            "Video ngang điện ảnh YouTube (16:9)",
            "Bản tin & Tin tức tài chính (16:9)",
            "Tối giản nhanh (16:9)"
        ]
        self.preset_combo = ctk.CTkComboBox(
            preset_box, variable=self.preset_var, values=preset_opts, width=270, height=32, corner_radius=8,
            fg_color=self.c_input, border_color=self.c_input_border, button_color=self.c_btn_sec,
            font=("Segoe UI", 11), command=self._apply_preset
        )
        self.preset_combo.pack(side="left")

        self.preset_pill_buttons = {}
        self.preset_pill_map = []

        # Right Actions on Navbar
        nav_actions = ctk.CTkFrame(nav_inner, fg_color="transparent")
        nav_actions.pack(side="right")

        btn_auto = ctk.CTkButton(
            nav_actions, text="Tự động điền", font=("Segoe UI", 11, "bold"),
            fg_color=self.c_btn_sec, hover_color=self.c_btn_sec_h, text_color=self.c_text,
            corner_radius=10, width=105, height=32, command=self._auto_detect_sample_files
        )
        btn_auto.pack(side="left", padx=3)

        btn_cc = ctk.CTkButton(
            nav_actions, text="Mở CapCut", font=("Segoe UI", 11, "bold"),
            fg_color=self.c_btn_sec, hover_color=self.c_btn_sec_h, text_color=self.c_text,
            corner_radius=10, width=100, height=32, command=self._launch_capcut
        )
        btn_cc.pack(side="left", padx=3)

        btn_settings = ctk.CTkButton(
            nav_actions, text="Cài đặt", font=("Segoe UI", 11),
            fg_color=self.c_btn_sec, hover_color=self.c_btn_sec_h, text_color=self.c_text,
            corner_radius=10, width=80, height=32, command=self._open_settings_dialog
        )
        btn_settings.pack(side="left", padx=3)

        # License Pill
        self.btn_license = ctk.CTkButton(
            nav_actions, text="Đang kiểm tra...", font=("Segoe UI", 11, "bold"),
            fg_color="#3e2810", hover_color="#543716", text_color="#fbbf24",
            corner_radius=10, height=32, command=self._open_license_dialog
        )
        self.btn_license.pack(side="left", padx=(6, 0))

        # ------------------------------------------------------------------
        # 4. MAIN BODY — Balanced 2-Column Grid Layout (50/50)
        # ------------------------------------------------------------------
        # Update Alert Banner (shown when update is available)
        self.update_banner_frame = ctk.CTkFrame(
            self, fg_color="#142b23", border_color="#1e4d3b", border_width=1, corner_radius=8
        )

        self.main_body = ctk.CTkFrame(self, fg_color="transparent")
        self.main_body.pack(fill="both", expand=True, padx=22, pady=(0, 14))

        # Use grid for precise 50/50 split
        self.main_body.columnconfigure(0, weight=1, uniform="col")
        self.main_body.columnconfigure(1, weight=1, uniform="col")
        self.main_body.rowconfigure(0, weight=1)

        # LEFT COLUMN: Inputs & Script
        left_col = ctk.CTkFrame(self.main_body, fg_color="transparent")
        left_col.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        # RIGHT COLUMN: Studio Controls Tabview & Run Box
        right_col = ctk.CTkFrame(self.main_body, fg_color="transparent")
        right_col.grid(row=0, column=1, sticky="nsew", padx=(8, 0))


        # ------------------------------------------------------------------
        # LEFT COLUMN CONTENT:
        # Card 1: Dữ liệu đầu vào (fixed height)
        # Card 2: Kịch bản phân cảnh (fills remaining space)
        # ------------------------------------------------------------------
        # Use grid in left_col so card_script can expand
        left_col.rowconfigure(0, weight=0)  # card_data: fixed
        left_col.rowconfigure(1, weight=1)  # card_script: expand
        left_col.columnconfigure(0, weight=1)

        card_data = self._create_card(left_col, title="1. DỮ LIỆU ĐẦU VÀO", grid_row=0)

        self._add_row(
            card_data, label="File Voice (Âm thanh):", var=self.audio_files_var,
            placeholder="Chọn 1 hoặc nhiều file audio (.wav, .mp3)...",
            btn_text="Chọn audio", cmd=self._browse_audio
        )

        self._add_row(
            card_data, label="File Phụ Đề (.srt):", var=self.srt_file_var,
            placeholder="Chọn file phụ đề SRT khớp với giọng đọc...",
            btn_text="Chọn SRT", cmd=self._browse_srt
        )

        self._add_row(
            card_data, label="Thư Mục Media:", var=self.media_folder_var,
            placeholder="Thư mục chứa ảnh hoặc video...",
            btn_text="Chọn thư mục", cmd=self._browse_media_folder
        )

        # BGM (Nhạc nền) row
        bgm_row = ctk.CTkFrame(card_data, fg_color="transparent")
        bgm_row.pack(fill="x", pady=4)

        lbl_bgm = ctk.CTkLabel(
            bgm_row, text="Nhạc Nền (CapCut BGM):", font=("Segoe UI", 11),
            text_color=self.c_text, width=140, anchor="w"
        )
        lbl_bgm.pack(side="left")

        bgm_presets = [
            "Không dùng nhạc nền",
            "Điện ảnh & Sâu lắng (Cinematic)",
            "Tin tức & Tài chính (News / Tech)",
            "Thư giãn & Lofi Chill (Lofi Beats)",
            "Kịch tính & Hồi hộp (Suspense)",
            "Vui tươi & Năng động (Happy Vlog)",
            "Chọn file nhạc từ máy tính..."
        ]
        self.cb_bgm_preset = ctk.CTkComboBox(
            bgm_row, variable=self.bgm_preset_var, values=bgm_presets,
            command=self._on_bgm_preset_change,
            corner_radius=8, fg_color=self.c_input, border_color=self.c_input_border, text_color=self.c_text,
            button_color=self.c_btn_sec, height=32, font=("Segoe UI", 11)
        )
        self.cb_bgm_preset.pack(side="left", fill="x", expand=True, padx=(0, 6))

        ctk.CTkLabel(bgm_row, text="Vol:", font=("Segoe UI", 11), text_color=self.c_sub).pack(side="left", padx=(0, 2))
        ctk.CTkEntry(
            bgm_row, textvariable=self.bgm_vol_var, width=38, height=32, corner_radius=8,
            fg_color=self.c_input, border_color=self.c_input_border, justify="center", font=("Segoe UI", 11)
        ).pack(side="left", padx=(0, 2))
        ctk.CTkLabel(bgm_row, text="%", font=("Segoe UI", 11), text_color=self.c_sub).pack(side="left", padx=(0, 6))

        btn_bgm_clear = ctk.CTkButton(
            bgm_row, text="Xóa", width=38, height=32, corner_radius=8,
            fg_color=self.c_btn_sec, hover_color=self.c_btn_sec_h, text_color=self.c_sub, font=("Segoe UI", 10),
            command=self._clear_bgm
        )
        btn_bgm_clear.pack(side="left", padx=(0, 6))

        btn_bgm = ctk.CTkButton(
            bgm_row, text="Chọn BGM", width=95, height=32, corner_radius=8,
            fg_color=self.c_btn_sec, hover_color=self.c_btn_sec_h, text_color=self.c_text,
            font=("Segoe UI", 11, "bold"),
            command=self._browse_bgm
        )
        btn_bgm.pack(side="right")

        # CapCut Project Name
        name_row = ctk.CTkFrame(card_data, fg_color="transparent")
        name_row.pack(fill="x", pady=4)

        lbl_name = ctk.CTkLabel(
            name_row, text="Tên Dự Án CapCut:", font=("Segoe UI", 11),
            text_color=self.c_text, width=140, anchor="w"
        )
        lbl_name.pack(side="left")

        e_name = ctk.CTkEntry(
            name_row, textvariable=self.capcut_name_var, corner_radius=8,
            fg_color=self.c_input, border_color=self.c_input_border, text_color=self.c_text,
            height=32, font=("Segoe UI", 11)
        )
        e_name.pack(side="left", fill="x", expand=True)

        # Card 2: Kịch bản phân cảnh (Script) — fills remaining vertical space
        card_script = self._create_card(left_col, title="2. KỊCH BẢN PHÂN CẢNH", grid_row=1, expand=True)

        sc_bar = ctk.CTkFrame(card_script, fg_color="transparent")
        sc_bar.pack(fill="x", pady=(0, 8))

        self.lbl_scenes_count = ctk.CTkLabel(
            sc_bar, text="0 cảnh đã nạp", font=("Segoe UI", 10, "bold"),
            fg_color="#212227", text_color=self.c_sub, corner_radius=10, padx=10, pady=3
        )
        self.lbl_scenes_count.pack(side="left")

        sc_tools = ctk.CTkFrame(sc_bar, fg_color="transparent")
        sc_tools.pack(side="right")

        btn_split = ctk.CTkButton(
            sc_tools, text="Tách câu", width=70, height=28, corner_radius=6,
            fg_color=self.c_btn_sec, hover_color=self.c_btn_sec_h, text_color=self.c_text, font=("Segoe UI", 10, "bold"),
            command=self._split_scenes_into_sentences
        )
        btn_split.pack(side="left", padx=2)

        btn_clean = ctk.CTkButton(
            sc_tools, text="Dọn dòng", width=70, height=28, corner_radius=6,
            fg_color=self.c_btn_sec, hover_color=self.c_btn_sec_h, text_color=self.c_text, font=("Segoe UI", 10),
            command=self._clean_empty_lines
        )
        btn_clean.pack(side="left", padx=2)

        btn_paste = ctk.CTkButton(
            sc_tools, text="Dán", width=50, height=28, corner_radius=6,
            fg_color=self.c_btn_sec, hover_color=self.c_btn_sec_h, text_color=self.c_text, font=("Segoe UI", 10, "bold"),
            command=self._paste_scenes
        )
        btn_paste.pack(side="left", padx=2)

        btn_copy = ctk.CTkButton(
            sc_tools, text="Sao chép", width=68, height=28, corner_radius=6,
            fg_color=self.c_btn_sec, hover_color=self.c_btn_sec_h, text_color=self.c_text, font=("Segoe UI", 10),
            command=self._copy_scenes
        )
        btn_copy.pack(side="left", padx=2)

        btn_load = ctk.CTkButton(
            sc_tools, text="Đọc .txt", width=72, height=28, corner_radius=6,
            fg_color=self.c_btn_sec, hover_color=self.c_btn_sec_h, text_color=self.c_text, font=("Segoe UI", 10, "bold"),
            command=self._browse_scenes_file
        )
        btn_load.pack(side="left", padx=2)

        btn_clear_sc = ctk.CTkButton(
            sc_tools, text="Xóa", width=45, height=28, corner_radius=6,
            fg_color=self.c_btn_sec, hover_color=self.c_btn_sec_h, text_color=self.c_sub, font=("Segoe UI", 10),
            command=self._clear_scenes
        )
        btn_clear_sc.pack(side="left", padx=(2, 0))

        self.scenes_textbox = ctk.CTkTextbox(
            card_script, height=220, corner_radius=10,
            fg_color=self.c_input, border_color=self.c_input_border, border_width=1,
            text_color=self.c_text, font=("Segoe UI", 11)
        )
        self.scenes_textbox.pack(fill="both", expand=True, pady=(0, 2))
        self.scenes_textbox.insert("1.0", SCENES_PLACEHOLDER)
        self.scenes_textbox.bind("<FocusIn>", self._on_scenes_focus_in)
        self.scenes_textbox.bind("<FocusOut>", self._on_scenes_focus_out)
        self.scenes_textbox.bind("<KeyRelease>", self._update_scenes_count)

        # RIGHT COLUMN: use grid so tabview expands and run/log cards have fixed sizes
        right_col.rowconfigure(0, weight=1)  # tabview: expand
        right_col.rowconfigure(1, weight=0)  # run card: fixed
        right_col.rowconfigure(2, weight=0)  # log card: fixed
        right_col.columnconfigure(0, weight=1)

        self.tabview = ctk.CTkTabview(
            right_col,
            fg_color=self.c_card,
            segmented_button_fg_color="#212228",
            segmented_button_selected_color=self.c_accent,
            segmented_button_selected_hover_color=self.c_accent_hover,
            segmented_button_unselected_color="#2d2f3a",
            segmented_button_unselected_hover_color=self.c_btn_sec_h,
            text_color=self.c_text,
            corner_radius=12,
            border_color=self.c_card_border,
            border_width=1
        )
        self.tabview.grid(row=0, column=0, sticky="nsew", pady=(0, 8))
        self.tabview.grid(row=0, column=0, sticky="nsew", pady=(0, 8))

        tab_tr = self.tabview.add("Chuyển cảnh & Mở đầu")
        tab_eff = self.tabview.add("Hiệu ứng & Bộ lọc")
        tab_cam = self.tabview.add("Chuyển động Camera")
        tab_sub = self.tabview.add("Phụ đề & Âm thanh")

        # ------------------------------------------------------------------
        # TAB 1: CHUYỂN CẢNH & MỞ ĐẦU
        # ------------------------------------------------------------------
        # Khung hình & Sắp xếp
        fmt_box = ctk.CTkFrame(tab_tr, fg_color="transparent")
        fmt_box.pack(fill="x", pady=(4, 8))

        ctk.CTkLabel(fmt_box, text="Khung hình & Sắp xếp:", font=("Segoe UI", 11, "bold"), text_color=self.c_text).pack(anchor="w", pady=(0, 4))
        fmt_row = ctk.CTkFrame(fmt_box, fg_color="transparent")
        fmt_row.pack(fill="x")

        ar_opts = [
            "16:9 (Ngang - YouTube, Facebook)",
            "9:16 (Dọc - TikTok, Reels, Shorts)",
            "1:1 (Vuông - Instagram, Post)"
        ]
        ctk.CTkComboBox(
            fmt_row, variable=self.aspect_ratio_var, values=ar_opts, height=30, corner_radius=6,
            fg_color=self.c_input, border_color=self.c_input_border, button_color=self.c_btn_sec
        ).pack(side="left", fill="x", expand=True, padx=(0, 6))

        sort_opts = [
            "Sắp xếp media theo ABC (Số tự nhiên)",
            "Sắp xếp media theo thời gian Cũ đến Mới",
            "Sắp xếp media theo thời gian Mới đến Cũ"
        ]
        ctk.CTkComboBox(
            fmt_row, variable=self.sort_mode_var, values=sort_opts, height=30, corner_radius=6,
            fg_color=self.c_input, border_color=self.c_input_border, button_color=self.c_btn_sec
        ).pack(side="left", fill="x", expand=True)

        # Chuyển cảnh (Transitions)
        tr_box = ctk.CTkFrame(tab_tr, fg_color="transparent")
        tr_box.pack(fill="x", pady=6)
        ctk.CTkLabel(tr_box, text="Hiệu ứng chuyển cảnh giữa các phân cảnh:", font=("Segoe UI", 11, "bold"), text_color=self.c_text).pack(anchor="w", pady=(0, 4))

        tr_row = ctk.CTkFrame(tr_box, fg_color="transparent")
        tr_row.pack(fill="x")

        trans_opts = [
            "Không transition", "Ngẫu nhiên (Random)", "Mờ chồng (Dissolve)", "Mờ đen (Black Fade)",
            "Chớp trắng (White Flash)", "Gạt sang trái (Swipe Left)", "Trượt góc (Corner Slide)",
            "Lật thu phóng (Flip Zoom)", "Thu phóng nhanh (Zoom)", "Nhiễu sóng (Signal Glitch)",
            "Rơi trượt (Slide Drop)", "Trượt giao diện (Slide Interface)", "Búng zoom (Snap Zoom)",
            "Vệt sáng quét (Light Wipe)"
        ]
        ctk.CTkComboBox(
            tr_row, variable=self.transition_var, values=trans_opts, width=220, height=30, corner_radius=6,
            fg_color=self.c_input, border_color=self.c_input_border, button_color=self.c_btn_sec
        ).pack(side="left", padx=(0, 8))

        ctk.CTkLabel(tr_row, text="Thời lượng:", font=("Segoe UI", 11), text_color=self.c_sub).pack(side="left", padx=(0, 2))
        ctk.CTkEntry(
            tr_row, textvariable=self.trans_dur_var, width=38, height=30, corner_radius=6,
            fg_color=self.c_input, border_color=self.c_input_border, justify="center"
        ).pack(side="left", padx=(0, 2))
        ctk.CTkLabel(tr_row, text="s", font=("Segoe UI", 11), text_color=self.c_sub).pack(side="left", padx=(0, 8))

        trans_mode_opts = ["Tất cả phân cảnh (All)", "Ngẫu nhiên đổi hiệu ứng (Random)", "Xen kẽ các cảnh (Alternate)"]
        ctk.CTkComboBox(
            tr_row, variable=self.trans_mode_var, values=trans_mode_opts, height=30, corner_radius=6,
            fg_color=self.c_input, border_color=self.c_input_border, button_color=self.c_btn_sec
        ).pack(side="left", fill="x", expand=True)

        # Hoạt ảnh mở đầu Clip Intro
        intro_box = ctk.CTkFrame(tab_tr, fg_color="transparent")
        intro_box.pack(fill="x", pady=6)
        ctk.CTkLabel(intro_box, text="Hoạt ảnh mở đầu phân cảnh (Clip In-Animation):", font=("Segoe UI", 11, "bold"), text_color=self.c_text).pack(anchor="w", pady=(0, 4))

        intro_row = ctk.CTkFrame(intro_box, fg_color="transparent")
        intro_row.pack(fill="x")

        intro_opts = [
            "Không animation", "Ngẫu nhiên (Random)", "Thu phóng vào (Zoom In)", "Phóng to năng động (Dynamic Zoom In)",
            "Thu nhỏ năng động (Dynamic Zoom Out)", "Mờ dần xuất hiện (Fade In)", "Mờ ảo tỏ dần (Blur Fade In)",
            "Lắc ngang nảy (Horizontal Shake)", "Lắc dọc nảy (Vertical Shake)", "Trượt từ dưới lên (Slide Up)",
            "Trượt từ trên xuống (Slide Down)", "Trượt từ trái sang (Slide Right)", "Trượt từ phải sang (Slide Left)",
            "Xoay mở màn (Spin Open)"
        ]
        ctk.CTkComboBox(
            intro_row, variable=self.clip_intro_var, values=intro_opts, width=220, height=30, corner_radius=6,
            fg_color=self.c_input, border_color=self.c_input_border, button_color=self.c_btn_sec
        ).pack(side="left", padx=(0, 8))

        ctk.CTkLabel(intro_row, text="Thời lượng:", font=("Segoe UI", 11), text_color=self.c_sub).pack(side="left", padx=(0, 2))
        ctk.CTkEntry(
            intro_row, textvariable=self.clip_intro_dur_var, width=38, height=30, corner_radius=6,
            fg_color=self.c_input, border_color=self.c_input_border, justify="center"
        ).pack(side="left", padx=(0, 2))
        ctk.CTkLabel(intro_row, text="s", font=("Segoe UI", 11), text_color=self.c_sub).pack(side="left", padx=(0, 8))

        intro_mode_opts = ["Tất cả phân cảnh (All)", "Ngẫu nhiên xen kẽ (Random)", "Chỉ cảnh đầu tiên (Intro)"]
        ctk.CTkComboBox(
            intro_row, variable=self.clip_intro_mode_var, values=intro_mode_opts, height=30, corner_radius=6,
            fg_color=self.c_input, border_color=self.c_input_border, button_color=self.c_btn_sec
        ).pack(side="left", fill="x", expand=True)

        # ------------------------------------------------------------------
        # TAB 2: HIỆU ỨNG & BỘ LỌC
        # ------------------------------------------------------------------
        eff_box = ctk.CTkFrame(tab_eff, fg_color="transparent")
        eff_box.pack(fill="x", pady=(4, 6))

        ctk.CTkLabel(eff_box, text="Hiệu ứng video CapCut (Scene Effects):", font=("Segoe UI", 11, "bold"), text_color=self.c_text).pack(anchor="w", pady=(0, 4))
        eff_row = ctk.CTkFrame(eff_box, fg_color="transparent")
        eff_row.pack(fill="x")

        effect_opts = [
            "Không dùng hiệu ứng", "Ngẫu nhiên (Random)", "Rung lắc tiêu điểm (Focus Shake)", "Rung tách màu RGB (RGB Shake)",
            "Nhiễu hạt Pixel (Pixel Glitch)", "Giật sóng mở màn (Glitch Intro)", "Hào quang nhấp nháy (Bouncing Glow)",
            "Chớp sáng kịch tính (Flash)", "Ánh đèn Neon (Neon Flash)", "Chớp phim cổ điển (Vintage Flash)"
        ]
        ctk.CTkComboBox(
            eff_row, variable=self.video_effect_var, values=effect_opts, width=240, height=30, corner_radius=6,
            fg_color=self.c_input, border_color=self.c_input_border, button_color=self.c_btn_sec
        ).pack(side="left", padx=(0, 8))

        ctk.CTkLabel(eff_row, text="Phạm vi:", font=("Segoe UI", 11), text_color=self.c_sub).pack(side="left", padx=(0, 4))
        effect_scope_opts = ["Tất cả phân cảnh (All)", "Ngẫu nhiên một số cảnh (Random)", "Chỉ cảnh mở đầu & kết thúc"]
        ctk.CTkComboBox(
            eff_row, variable=self.video_effect_scope_var, values=effect_scope_opts, height=30, corner_radius=6,
            fg_color=self.c_input, border_color=self.c_input_border, button_color=self.c_btn_sec
        ).pack(side="left", fill="x", expand=True)

        # Bộ lọc màu Filter
        filt_box = ctk.CTkFrame(tab_eff, fg_color="transparent")
        filt_box.pack(fill="x", pady=6)

        ctk.CTkLabel(filt_box, text="Bộ lọc màu điện ảnh (Filters):", font=("Segoe UI", 11, "bold"), text_color=self.c_text).pack(anchor="w", pady=(0, 4))
        filt_row = ctk.CTkFrame(filt_box, fg_color="transparent")
        filt_row.pack(fill="x")

        filt_opts = [
            "Không dùng filter", "Soft Grain (Hạt phim điện ảnh)", "Vintage 1980 (Tông màu cổ điển)", "VHS Retro (Băng từ VHS)",
            "Peach Fuzz (Tông ấm điện ảnh)", "Lover Blue (Tông lạnh điện ảnh)", "BW Retro (Trắng đen cổ điển)"
        ]
        ctk.CTkComboBox(
            filt_row, variable=self.filter_var, values=filt_opts, width=240, height=30, corner_radius=6,
            fg_color=self.c_input, border_color=self.c_input_border, button_color=self.c_btn_sec
        ).pack(side="left", padx=(0, 8))

        ctk.CTkLabel(filt_row, text="Độ đậm:", font=("Segoe UI", 11), text_color=self.c_sub).pack(side="left", padx=(0, 4))
        ctk.CTkEntry(
            filt_row, textvariable=self.filter_intensity_var, width=44, height=30, corner_radius=6,
            fg_color=self.c_input, border_color=self.c_input_border, justify="center"
        ).pack(side="left", padx=(0, 2))
        ctk.CTkLabel(filt_row, text="%", font=("Segoe UI", 11), text_color=self.c_sub).pack(side="left")

        # Tùy chọn nâng cao (Canvas Blur & Gemini Watermark Remover)
        adv_box = ctk.CTkFrame(tab_eff, fg_color="transparent")
        adv_box.pack(fill="x", pady=(10, 0))

        ctk.CTkCheckBox(
            adv_box, text=" Làm mờ nền Canvas Blur khi ảnh không vừa khung hình (tránh viền đen)",
            variable=self.blur_var, font=("Segoe UI", 11), corner_radius=5,
            fg_color=self.c_accent, hover_color=self.c_accent_hover, text_color=self.c_text
        ).pack(anchor="w", pady=3)

        ctk.CTkCheckBox(
            adv_box, text=" Xóa watermark ảnh Gemini AI tự động (Lossless Reverse Alpha Blending)",
            variable=self.watermark_var, font=("Segoe UI", 11), corner_radius=5,
            fg_color=self.c_accent, hover_color=self.c_accent_hover, text_color=self.c_text
        ).pack(anchor="w", pady=3)

        # ------------------------------------------------------------------
        # TAB 3: CHUYỂN ĐỘNG CAMERA & KEYFRAMES
        # ------------------------------------------------------------------
        cam_bar = ctk.CTkFrame(tab_cam, fg_color="transparent")
        cam_bar.pack(fill="x", pady=(4, 8))

        ctk.CTkLabel(cam_bar, text="Chế độ chuyển động:", font=("Segoe UI", 11, "bold"), text_color=self.c_text).pack(side="left", padx=(0, 6))
        cam_opts = [
            "Smart Pacing AI (Tự phân tích nhịp câu)", "Zoom In (Phóng to dần)", "Zoom Out (Thu nhỏ dần)",
            "Pan Left (Lia sang trái)", "Pan Right (Lia sang phải)", "Pan Up (Lia lên trên)", "Pan Down (Lia xuống dưới)",
            "Ngẫu nhiên góc quay (Dynamic Ken Burns)", "Cố định (Không chuyển động)"
        ]
        ctk.CTkComboBox(
            cam_bar, variable=self.camera_motion_var, values=cam_opts, width=260, height=28, corner_radius=6,
            fg_color=self.c_input, border_color=self.c_input_border
        ).pack(side="left", padx=(0, 8))

        ctk.CTkLabel(cam_bar, text="Zoom:", font=("Segoe UI", 11), text_color=self.c_sub).pack(side="left", padx=(0, 2))
        ctk.CTkEntry(
            cam_bar, textvariable=self.zoom_scale_var, width=42, height=28, corner_radius=6,
            fg_color=self.c_input, border_color=self.c_input_border, justify="center"
        ).pack(side="left", padx=(0, 2))
        ctk.CTkLabel(cam_bar, text="%", font=("Segoe UI", 11), text_color=self.c_sub).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            cam_bar, text="Chọn tất cả", width=80, height=28, corner_radius=8,
            fg_color=self.c_btn_sec, hover_color=self.c_btn_sec_h, text_color=self.c_text, font=("Segoe UI", 10, "bold"),
            command=lambda: self._select_all_motions(True)
        ).pack(side="right", padx=2)

        ctk.CTkButton(
            cam_bar, text="Bỏ chọn", width=70, height=28, corner_radius=8,
            fg_color=self.c_btn_sec, hover_color=self.c_btn_sec_h, text_color=self.c_sub, font=("Segoe UI", 10),
            command=lambda: self._select_all_motions(False)
        ).pack(side="right", padx=2)

        # 2 Sub-columns for 6 motion keyframes
        kf_grid = ctk.CTkFrame(tab_cam, fg_color="transparent")
        kf_grid.pack(fill="both", expand=True)

        col_k1 = ctk.CTkFrame(kf_grid, fg_color="#212228", corner_radius=10, border_color=self.c_card_border, border_width=1)
        col_k1.pack(side="left", fill="both", expand=True, padx=(0, 5), pady=2)
        self._add_motion_zoom(col_k1, "Zoom In (Phóng to)", self.m_zoom_in_var, self.m_zoom_in_scale)
        self._add_motion_pan(col_k1, "Pan Up (Lia lên)", self.m_pan_up_var, self.m_pan_up_x, self.m_pan_up_y, self.m_pan_up_scale)
        self._add_motion_pan(col_k1, "Pan Left (Lia trái)", self.m_pan_left_var, self.m_pan_left_x, self.m_pan_left_y, self.m_pan_left_scale)

        col_k2 = ctk.CTkFrame(kf_grid, fg_color="#212228", corner_radius=10, border_color=self.c_card_border, border_width=1)
        col_k2.pack(side="left", fill="both", expand=True, padx=(5, 0), pady=2)
        self._add_motion_zoom(col_k2, "Zoom Out (Thu nhỏ)", self.m_zoom_out_var, self.m_zoom_out_scale)
        self._add_motion_pan(col_k2, "Pan Down (Lia xuống)", self.m_pan_down_var, self.m_pan_down_x, self.m_pan_down_y, self.m_pan_down_scale)
        self._add_motion_pan(col_k2, "Pan Right (Lia phải)", self.m_pan_right_var, self.m_pan_right_x, self.m_pan_right_y, self.m_pan_right_scale)

        # ------------------------------------------------------------------
        # TAB 4: PHỤ ĐỀ & ÂM THANH
        # ------------------------------------------------------------------
        sub_top = ctk.CTkFrame(tab_sub, fg_color="transparent")
        sub_top.pack(fill="x", pady=(4, 4))

        ctk.CTkCheckBox(
            sub_top, text=" Tự động chèn phụ đề SRT vào timeline",
            variable=self.subtitles_var, font=("Segoe UI", 11, "bold"), corner_radius=5,
            fg_color=self.c_accent, hover_color=self.c_accent_hover, text_color=self.c_text
        ).pack(side="left")

        sub_row1 = ctk.CTkFrame(tab_sub, fg_color="transparent")
        sub_row1.pack(fill="x", pady=2)

        ctk.CTkLabel(sub_row1, text="Màu chữ:", font=("Segoe UI", 11), text_color=self.c_sub, width=65, anchor="w").pack(side="left")
        sub_col_opts = [
            "Vàng Nổi Bật (TikTok / Viral)", "Trắng Truyền Thống (Classic White)", "Xanh Công Nghệ (Cyan Modern)",
            "Xanh Lá Tài Chính (Finance Green)", "Đỏ Ruby (Dramatic Red)", "Tím Neon (Neon Purple)"
        ]
        ctk.CTkComboBox(
            sub_row1, variable=self.subtitle_color_var, values=sub_col_opts, width=200, height=28, corner_radius=6,
            fg_color=self.c_input, border_color=self.c_input_border
        ).pack(side="left", padx=(0, 8))

        ctk.CTkLabel(sub_row1, text="Cỡ:", font=("Segoe UI", 11), text_color=self.c_sub).pack(side="left", padx=(0, 2))
        ctk.CTkEntry(
            sub_row1, textvariable=self.sub_size_var, width=38, height=28, corner_radius=6,
            fg_color=self.c_input, border_color=self.c_input_border, justify="center"
        ).pack(side="left", padx=(0, 8))

        sub_pos_opts = ["Dưới cùng (Chuẩn Shorts/Reels)", "Chính giữa màn hình", "Phía trên cùng"]
        ctk.CTkComboBox(
            sub_row1, variable=self.sub_pos_var, values=sub_pos_opts, height=28, corner_radius=6,
            fg_color=self.c_input, border_color=self.c_input_border
        ).pack(side="left", fill="x", expand=True)

        sub_row2 = ctk.CTkFrame(tab_sub, fg_color="transparent")
        sub_row2.pack(fill="x", pady=2)

        ctk.CTkLabel(sub_row2, text="Hiệu ứng:", font=("Segoe UI", 11), text_color=self.c_sub, width=65, anchor="w").pack(side="left")
        sub_anim_opts = [
            "Chữ nảy hộp chữ nhật từng từ (Word Bounce Box)",
            "Chữ nảy hộp chữ nhật theo câu (Sentence Bounce Box)",
            "Nảy chữ lên (Bounce Pop không hộp)",
            "Chạy từng chữ (Karaoke Reveal)",
            "Nhịp điệu vui nhộn (Playful Bounce)",
            "Trượt mượt lên (Slide Up)",
            "Quét từ trái sang (Slide Right)",
            "Tĩnh (Không animation)"
        ]
        ctk.CTkComboBox(
            sub_row2, variable=self.sub_anim_var, values=sub_anim_opts, height=28, corner_radius=6,
            fg_color=self.c_input, border_color=self.c_input_border
        ).pack(side="left", fill="x", expand=True, padx=(0, 8))

        ctk.CTkLabel(sub_row2, text="Khung hộp:", font=("Segoe UI", 11), text_color=self.c_sub).pack(side="left", padx=(0, 4))
        box_opts = [
            "Hộp Đen tương phản (Black Box)",
            "Hộp Đỏ nổi bật (Red Box)",
            "Hộp Vàng rực rỡ (Yellow Box)",
            "Hộp Xanh đậm (Deep Blue Box)",
            "Hộp Tím Neon (Purple Box)",
            "Không hộp nền (Trong suốt)"
        ]
        ctk.CTkComboBox(
            sub_row2, variable=self.subtitle_box_var, values=box_opts, width=175, height=28, corner_radius=6,
            fg_color=self.c_input, border_color=self.c_input_border
        ).pack(side="left")

        # SFX Row
        sfx_row = ctk.CTkFrame(tab_sub, fg_color="transparent")
        sfx_row.pack(fill="x", pady=(8, 4))

        ctk.CTkCheckBox(
            sfx_row, text=" Âm thanh chuyển cảnh (SFX):",
            variable=self.sfx_var, font=("Segoe UI", 11), corner_radius=5,
            fg_color=self.c_accent, hover_color=self.c_accent_hover, text_color=self.c_text
        ).pack(side="left", padx=(0, 6))

        sfx_opts = [
            "Ngẫu nhiên phối hợp (Smart Random)",
            "Whoosh Điện ảnh Trầm (Cinematic Deep)",
            "Whoosh Lướt Nhanh (Fast Wind)",
            "Whoosh Gió Nhẹ (Soft Air)",
            "Whoosh Tiếng Bass Dày (Heavy Bass)",
            "Swoosh Vung Nhanh (Fast Whip)",
            "Swoosh Trượt Mượt (Slide)",
            "Camera Shutter (Tiếng chụp ảnh)",
            "Mouse Click (Click chuột máy tính)",
            "Keyboard Typing (Gõ bàn phím)",
            "Bubble Pop (Bong bóng vỡ vui nhộn)",
            "Cash Register Kaching (Tiền leng keng)",
            "Cinematic Boom (Va đập uy lực)",
            "Bell Ding (Keng chuông báo)",
            "Tape Rewind (Tua băng cassette)",
            "Glitch Digital (Nhiễu sóng số)"
        ]
        ctk.CTkComboBox(
            sfx_row, variable=self.sfx_name_var, values=sfx_opts, width=260, height=28, corner_radius=6,
            fg_color=self.c_input, border_color=self.c_input_border
        ).pack(side="left", padx=(0, 8))

        ctk.CTkLabel(sfx_row, text="Âm lượng:", font=("Segoe UI", 11), text_color=self.c_sub).pack(side="left", padx=(0, 2))
        ctk.CTkEntry(
            sfx_row, textvariable=self.sfx_vol_var, width=38, height=28, corner_radius=6,
            fg_color=self.c_input, border_color=self.c_input_border, justify="center"
        ).pack(side="left", padx=(0, 2))
        ctk.CTkLabel(sfx_row, text="%", font=("Segoe UI", 11), text_color=self.c_sub).pack(side="left")

        # Audio enhancements checkboxes
        aud_box = ctk.CTkFrame(tab_sub, fg_color="transparent")
        aud_box.pack(fill="x", pady=(4, 0))

        ctk.CTkCheckBox(
            aud_box, text=" Audio Ducking (Tự động hạ nhỏ nhạc nền khi có tiếng voice)",
            variable=self.ducking_var, font=("Segoe UI", 11), corner_radius=5,
            fg_color=self.c_accent, hover_color=self.c_accent_hover, text_color=self.c_text
        ).pack(anchor="w", pady=2)

        ctk.CTkCheckBox(
            aud_box, text=" Audio Fade In & Fade Out cho nhạc nền (Mở và tắt êm ái)",
            variable=self.fade_var, font=("Segoe UI", 11), corner_radius=5,
            fg_color=self.c_accent, hover_color=self.c_accent_hover, text_color=self.c_text
        ).pack(anchor="w", pady=2)

        ctk.CTkCheckBox(
            aud_box, text=" Chèn CTA Kêu gọi Đăng ký (Subscribe) & chuông kết thúc video",
            variable=self.cta_sub_var, font=("Segoe UI", 11), corner_radius=5,
            fg_color=self.c_accent, hover_color=self.c_accent_hover, text_color=self.c_text
        ).pack(anchor="w", pady=2)

        # ------------------------------------------------------------------
        # ACTION BOX & RUN BUTTON — fixed height card
        # ------------------------------------------------------------------
        run_card = ctk.CTkFrame(right_col, fg_color=self.c_card, corner_radius=14, border_color=self.c_card_border, border_width=1)
        run_card.grid(row=1, column=0, sticky="ew", pady=(0, 8), ipady=4)

        run_inner = ctk.CTkFrame(run_card, fg_color="transparent")
        run_inner.pack(fill="x", padx=14, pady=10)

        self.run_btn_row = ctk.CTkFrame(run_inner, fg_color="transparent")
        self.run_btn_row.pack(fill="x", pady=(0, 8))

        self.btn_run = ctk.CTkButton(
            self.run_btn_row,
            text="Bắt đầu tạo dự án CapCut",
            font=("Segoe UI", 13, "bold"),
            fg_color=self.c_accent,
            hover_color=self.c_accent_hover,
            corner_radius=12,
            height=44,
            command=self._start_processing
        )
        self.btn_run.pack(side="left", fill="x", expand=True)

        self.btn_stop = ctk.CTkButton(
            self.run_btn_row,
            text="Dừng lại",
            font=("Segoe UI", 12, "bold"),
            fg_color=self.c_danger,
            hover_color="#dc2626",
            text_color="#ffffff",
            corner_radius=12,
            width=110,
            height=44,
            command=self._stop_processing
        )
        self.btn_stop.pack_forget()

        self.progress_bar = ctk.CTkProgressBar(
            run_inner, corner_radius=6, height=6, fg_color="#212228", progress_color=self.c_accent
        )
        self.progress_bar.pack(fill="x")
        self.progress_bar.set(0)

        status_row = ctk.CTkFrame(run_inner, fg_color="transparent")
        status_row.pack(fill="x", pady=(6, 0))

        self.lbl_status = ctk.CTkLabel(
            status_row, text="Sẵn sàng. Nhấn nút để xuất dự án sang CapCut PC.",
            font=("Segoe UI", 10), text_color=self.c_sub
        )
        self.lbl_status.pack(side="left")

        cb_auto_open = ctk.CTkCheckBox(
            status_row, text=" Tự động mở CapCut",
            variable=self.auto_open_capcut_var, font=("Segoe UI", 10),
            text_color=self.c_sub, fg_color=self.c_accent, hover_color=self.c_accent_hover,
            corner_radius=4
        )
        cb_auto_open.pack(side="right")

        # Dynamic Action Buttons (Shown after project creation)
        self.complete_action_frame = ctk.CTkFrame(run_inner, fg_color="transparent")

        self.btn_open_now = ctk.CTkButton(
            self.complete_action_frame,
            text="Mở Dự Án Trong CapCut Ngay",
            font=("Segoe UI", 11, "bold"),
            fg_color="#10b981",
            hover_color="#059669",
            text_color="#ffffff",
            corner_radius=10,
            height=36,
            command=self._launch_last_draft
        )
        self.btn_open_now.pack(side="left", fill="x", expand=True, padx=(0, 8))

        self.btn_open_folder = ctk.CTkButton(
            self.complete_action_frame,
            text="Mở Thư Mục",
            font=("Segoe UI", 11),
            fg_color=self.c_btn_sec,
            hover_color=self.c_btn_sec_h,
            text_color=self.c_text,
            corner_radius=10,
            height=36,
            width=120,
            command=self._open_last_draft_folder
        )
        self.btn_open_folder.pack(side="left")

        # ------------------------------------------------------------------
        # CONSOLE LOG — compact fixed-height card
        # ------------------------------------------------------------------
        log_card = ctk.CTkFrame(right_col, fg_color=self.c_card, corner_radius=14, border_color=self.c_card_border, border_width=1)
        log_card.grid(row=2, column=0, sticky="ew")

        log_head = ctk.CTkFrame(log_card, fg_color="transparent")
        log_head.pack(fill="x", padx=14, pady=(8, 4))
        ctk.CTkLabel(log_head, text="Nhật ký tiến trình:", font=("Segoe UI", 11, "bold"), text_color=self.c_text).pack(side="left")

        btn_clear_log = ctk.CTkButton(
            log_head, text="Xóa log", width=60, height=24, corner_radius=6,
            fg_color=self.c_btn_sec, hover_color=self.c_btn_sec_h, text_color=self.c_sub, font=("Segoe UI", 9),
            command=lambda: self.console_textbox.delete("1.0", "end")
        )
        btn_clear_log.pack(side="right")

        self.console_textbox = ctk.CTkTextbox(
            log_card, height=120, corner_radius=8,
            fg_color=self.c_input, border_color=self.c_input_border, border_width=1,
            text_color="#cbd5e1", font=("Consolas", 10)
        )
        self.console_textbox.pack(fill="x", padx=14, pady=(0, 12))
        self._log("AutoCapCut Studio sẵn sàng hoạt động.")

    # ------------------------------------------------------------------
    # CARD & ROW HELPERS
    # ------------------------------------------------------------------
    def _create_card(self, parent, title: str, grid_row: int = None, expand: bool = False) -> ctk.CTkFrame:
        card = ctk.CTkFrame(
            parent, fg_color=self.c_card, corner_radius=14,
            border_color=self.c_card_border, border_width=1
        )
        if grid_row is not None:
            sticky = "nsew" if expand else "ew"
            card.grid(row=grid_row, column=0, sticky=sticky, pady=(0, 10))
        else:
            card.pack(fill="x", pady=(0, 10))

        lbl = ctk.CTkLabel(
            card, text=title, font=("Segoe UI", 12, "bold"), text_color="#ffffff"
        )
        lbl.pack(anchor="w", padx=16, pady=(12, 6))

        # Inner content frame for consistent left/right padding
        content = ctk.CTkFrame(card, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=16, pady=(0, 12))
        return content

    def _select_preset_pill(self, full_name: str):
        self.preset_var.set(full_name)
        self._apply_preset(full_name)
        self._update_preset_pills_ui()

    def _update_preset_pills_ui(self):
        cur = self.preset_var.get()
        if hasattr(self, "preset_combo") and self.preset_combo.get() != cur:
            self.preset_combo.set(cur)
        for short_name, full_name in getattr(self, "preset_pill_map", []):
            btn = self.preset_pill_buttons.get(full_name)
            if not btn:
                continue
            if cur == full_name or (full_name in cur) or (short_name in cur):
                btn.configure(
                    fg_color=self.c_accent,
                    hover_color=self.c_accent_hover,
                    text_color="#ffffff",
                    border_width=0
                )
            else:
                btn.configure(
                    fg_color=self.c_card,
                    hover_color=self.c_btn_sec,
                    text_color=self.c_sub,
                    border_color=self.c_card_border,
                    border_width=1
                )

    def _update_stat_cards(self):
        pass

    def _add_row(self, parent, label, var, placeholder, btn_text, cmd, btn_color=None, btn_hover=None, btn_text_color=None):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=4)

        lbl = ctk.CTkLabel(
            row, text=label, font=("Segoe UI", 11), text_color=self.c_text, width=140, anchor="w"
        )
        lbl.pack(side="left")

        entry = ctk.CTkEntry(
            row, textvariable=var, placeholder_text=placeholder, corner_radius=8,
            fg_color=self.c_input, border_color=self.c_input_border, text_color=self.c_text,
            height=32, font=("Segoe UI", 11)
        )
        entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

        btn = ctk.CTkButton(
            row, text=btn_text, font=("Segoe UI", 11, "bold"),
            fg_color=btn_color or self.c_btn_sec,
            hover_color=btn_hover or self.c_btn_sec_h,
            text_color=btn_text_color or self.c_btn_sec_text,
            corner_radius=8, width=110, height=32, command=cmd
        )
        btn.pack(side="right")

    def _add_motion_zoom(self, parent, title, var, scale_var):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=10, pady=4)

        cb = ctk.CTkCheckBox(
            row, text=f" {title}", variable=var, font=("Segoe UI", 11),
            corner_radius=5, fg_color=self.c_accent, hover_color=self.c_accent_hover,
            text_color=self.c_text, width=150
        )
        cb.pack(side="left")

        ctk.CTkLabel(row, text="Scale:", font=("Segoe UI", 10), text_color=self.c_sub).pack(side="left", padx=(4, 2))
        e = ctk.CTkEntry(
            row, textvariable=scale_var, width=44, height=24, corner_radius=5,
            fg_color=self.c_input, border_color=self.c_input_border, justify="center", font=("Segoe UI", 10)
        )
        e.pack(side="left", padx=2)
        ctk.CTkLabel(row, text="%", font=("Segoe UI", 10), text_color=self.c_sub).pack(side="left")

    def _add_motion_pan(self, parent, title, var, x_var, y_var, scale_var):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=10, pady=4)

        cb = ctk.CTkCheckBox(
            row, text=f" {title}", variable=var, font=("Segoe UI", 11),
            corner_radius=5, fg_color=self.c_accent, hover_color=self.c_accent_hover,
            text_color=self.c_text, width=150
        )
        cb.pack(side="left")

        ctk.CTkLabel(row, text="X:", font=("Segoe UI", 10), text_color=self.c_sub).pack(side="left", padx=(2, 2))
        e_x = ctk.CTkEntry(row, textvariable=x_var, width=38, height=24, corner_radius=5, fg_color=self.c_input, border_color=self.c_input_border, justify="center", font=("Segoe UI", 10))
        e_x.pack(side="left", padx=1)

        ctk.CTkLabel(row, text="Y:", font=("Segoe UI", 10), text_color=self.c_sub).pack(side="left", padx=(3, 2))
        e_y = ctk.CTkEntry(row, textvariable=y_var, width=38, height=24, corner_radius=5, fg_color=self.c_input, border_color=self.c_input_border, justify="center", font=("Segoe UI", 10))
        e_y.pack(side="left", padx=1)

        ctk.CTkLabel(row, text="S:", font=("Segoe UI", 10), text_color=self.c_sub).pack(side="left", padx=(3, 2))
        e_s = ctk.CTkEntry(row, textvariable=scale_var, width=42, height=24, corner_radius=5, fg_color=self.c_input, border_color=self.c_input_border, justify="center", font=("Segoe UI", 10))
        e_s.pack(side="left", padx=1)
        ctk.CTkLabel(row, text="%", font=("Segoe UI", 10), text_color=self.c_sub).pack(side="left")

    # ------------------------------------------------------------------
    # ACTIONS & EVENT HANDLERS
    # ------------------------------------------------------------------
    def _on_scenes_focus_in(self, event):
        text = self.scenes_textbox.get("1.0", "end").strip()
        if text == SCENES_PLACEHOLDER.strip():
            self.scenes_textbox.delete("1.0", "end")

    def _on_scenes_focus_out(self, event):
        text = self.scenes_textbox.get("1.0", "end").strip()
        if not text:
            self.scenes_textbox.insert("1.0", SCENES_PLACEHOLDER)
        self._update_scenes_count()

    def _update_scenes_count(self, event=None):
        text = self.scenes_textbox.get("1.0", "end").strip()
        if text and text != SCENES_PLACEHOLDER.strip():
            lines = [l for l in text.splitlines() if l.strip()]
            self.lbl_scenes_count.configure(
                text=f"{len(lines)} cảnh đã nạp", text_color="#4ade80", fg_color="#143b2a"
            )
        else:
            self.lbl_scenes_count.configure(
                text="0 cảnh", text_color=self.c_sub, fg_color="#212227"
            )
        self._update_stat_cards()

    def _copy_scenes(self):
        text = self.scenes_textbox.get("1.0", "end").strip()
        if text and text != SCENES_PLACEHOLDER.strip():
            self.clipboard_clear()
            self.clipboard_append(text)
            self._log("[Info] Đã sao chép kịch bản vào clipboard.")
        else:
            self._log("[Warn] Kịch bản hiện đang rỗng.")

    def _paste_scenes(self):
        try:
            cb_text = self.clipboard_get()
            if cb_text:
                self.scenes_textbox.delete("1.0", "end")
                self.scenes_textbox.insert("1.0", cb_text)
                self._update_scenes_count()
                lines = [l for l in cb_text.splitlines() if l.strip()]
                self._log(f"[Info] Đã dán {len(lines)} cảnh từ clipboard.")
        except Exception:
            self._log("[Warn] Clipboard không chứa văn bản hợp lệ.")

    def _clear_scenes(self):
        self.scenes_textbox.delete("1.0", "end")
        self._update_scenes_count()

    def _split_scenes_into_sentences(self):
        text = self.scenes_textbox.get("1.0", "end").strip()
        if not text or text == SCENES_PLACEHOLDER.strip():
            return
        import re
        sentences = re.split(r'(?<=[.!?。！？;])\s+', text.replace('\r\n', '\n'))
        cleaned = [s.strip() for s in sentences if s.strip()]
        if cleaned:
            self.scenes_textbox.delete("1.0", "end")
            self.scenes_textbox.insert("1.0", "\n".join(cleaned))
            self._update_scenes_count()
            self._log(f"[Action] Đã tách kịch bản thành {len(cleaned)} câu (mỗi câu 1 dòng).")

    def _clean_empty_lines(self):
        text = self.scenes_textbox.get("1.0", "end").strip()
        if not text or text == SCENES_PLACEHOLDER.strip():
            return
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        self.scenes_textbox.delete("1.0", "end")
        self.scenes_textbox.insert("1.0", "\n".join(lines))
        self._update_scenes_count()
        self._log(f"[Action] Đã dọn dẹp dòng trống ({len(lines)} dòng hợp lệ).")

    def _select_all_motions(self, state: bool):
        self.m_zoom_in_var.set(state)
        self.m_zoom_out_var.set(state)
        self.m_pan_up_var.set(state)
        self.m_pan_down_var.set(state)
        self.m_pan_left_var.set(state)
        self.m_pan_right_var.set(state)
        self._log(f"[Action] {'Đã chọn tất cả' if state else 'Đã bỏ chọn tất cả'} chuyển động keyframe.")

    def _apply_preset(self, choice: str):
        if "TikTok" in choice or "Shorts" in choice:
            self.aspect_ratio_var.set("9:16 (Dọc - TikTok, Reels, Shorts)")
            self.subtitles_var.set(True)
            self.subtitle_color_var.set("Vàng Nổi Bật (TikTok / Viral)")
            self.subtitle_box_var.set("Hộp Đen tương phản (Black Box)")
            self.sub_anim_var.set("Chữ nảy hộp chữ nhật từng từ (Word Bounce Box)")
            self.sub_size_var.set("9.5")
            self.sub_pos_var.set("Dưới cùng (Chuẩn Shorts/Reels)")
            self.transition_var.set("Lật thu phóng (Flip Zoom)")
            self.trans_dur_var.set("0.4")
            self.trans_mode_var.set("Tất cả phân cảnh (All)")
            self.clip_intro_var.set("Phóng to năng động (Dynamic Zoom In)")
            self.clip_intro_dur_var.set("0.5")
            self.clip_intro_mode_var.set("Tất cả phân cảnh (All)")
            self.video_effect_var.set("Rung lắc tiêu điểm (Focus Shake)")
            self.video_effect_scope_var.set("Ngẫu nhiên một số cảnh (Random)")
            self.filter_var.set("Không dùng filter")
            self.camera_motion_var.set("Smart Pacing AI (Tự phân tích nhịp câu)")
            self.zoom_scale_var.set("115")
            self.sfx_var.set(True)
            self.sfx_name_var.set("Whoosh Lướt Nhanh (Fast Wind)")
            self.sfx_vol_var.set("60")
            self.bgm_preset_var.set("Vui tươi & Năng động (Happy Vlog)")
            self.bgm_files_var.set("Vui tươi & Năng động (Happy Vlog)")
            self.bgm_vol_var.set("15")
            self.blur_var.set(True)
            self.smart_pacing_var.set(True)
            self.ducking_var.set(True)
            self.fade_var.set(True)
            self.cta_sub_var.set(True)
            self._select_all_motions(True)
            self._log("[Preset] Đã áp dụng: Video ngắn dọc TikTok / Shorts (9:16).")
        elif "Điện ảnh" in choice or "YouTube" in choice:
            self.aspect_ratio_var.set("16:9 (Ngang - YouTube, Facebook)")
            self.subtitles_var.set(True)
            self.subtitle_color_var.set("Trắng Truyền Thống (Classic White)")
            self.sub_anim_var.set("Trượt mượt lên (Slide Up)")
            self.sub_size_var.set("8.5")
            self.sub_pos_var.set("Dưới cùng (Chuẩn Shorts/Reels)")
            self.transition_var.set("Mờ chồng (Dissolve)")
            self.trans_dur_var.set("0.8")
            self.trans_mode_var.set("Tất cả phân cảnh (All)")
            self.clip_intro_var.set("Mờ dần xuất hiện (Fade In)")
            self.clip_intro_dur_var.set("1.0")
            self.clip_intro_mode_var.set("Tất cả phân cảnh (All)")
            self.video_effect_var.set("Không dùng hiệu ứng")
            self.filter_var.set("Soft Grain (Hạt phim điện ảnh)")
            self.filter_intensity_var.set("65")
            self.camera_motion_var.set("Smart Pacing AI (Tự phân tích nhịp câu)")
            self.zoom_scale_var.set("110")
            self.sfx_var.set(True)
            self.sfx_name_var.set("Whoosh Điện ảnh Trầm (Cinematic Deep)")
            self.sfx_vol_var.set("35")
            self.bgm_preset_var.set("Điện ảnh & Sâu lắng (Cinematic)")
            self.bgm_files_var.set("Điện ảnh & Sâu lắng (Cinematic)")
            self.bgm_vol_var.set("15")
            self.blur_var.set(True)
            self.smart_pacing_var.set(True)
            self.ducking_var.set(True)
            self.fade_var.set(True)
            self.cta_sub_var.set(True)
            self._select_all_motions(True)
            self._log("[Preset] Đã áp dụng: Video ngang điện ảnh YouTube (16:9).")
        elif "Tài chính" in choice or "Bản tin" in choice:
            self.aspect_ratio_var.set("16:9 (Ngang - YouTube, Facebook)")
            self.subtitles_var.set(True)
            self.subtitle_color_var.set("Xanh Lá Tài Chính (Finance Green)")
            self.sub_anim_var.set("Chạy từng chữ (Karaoke Reveal)")
            self.sub_size_var.set("8.5")
            self.sub_pos_var.set("Dưới cùng (Chuẩn Shorts/Reels)")
            self.transition_var.set("Trượt góc (Corner Slide)")
            self.trans_dur_var.set("0.5")
            self.trans_mode_var.set("Tất cả phân cảnh (All)")
            self.clip_intro_var.set("Trượt từ trái sang (Slide Right)")
            self.clip_intro_dur_var.set("0.6")
            self.clip_intro_mode_var.set("Tất cả phân cảnh (All)")
            self.video_effect_var.set("Không dùng hiệu ứng")
            self.filter_var.set("Không dùng filter")
            self.camera_motion_var.set("Pan Left (Lia sang trái)")
            self.zoom_scale_var.set("108")
            self.sfx_var.set(True)
            self.sfx_name_var.set("Bell Ding (Keng chuông báo)")
            self.sfx_vol_var.set("25")
            self.bgm_preset_var.set("Tin tức & Tài chính (News / Tech)")
            self.bgm_files_var.set("Tin tức & Tài chính (News / Tech)")
            self.bgm_vol_var.set("12")
            self.blur_var.set(True)
            self.smart_pacing_var.set(True)
            self.ducking_var.set(True)
            self.fade_var.set(True)
            self.cta_sub_var.set(True)
            self._select_all_motions(True)
            self._log("[Preset] Đã áp dụng: Bản tin & Tin tức tài chính (16:9).")
        elif "Tối giản" in choice:
            self.aspect_ratio_var.set("16:9 (Ngang - YouTube, Facebook)")
            self.subtitles_var.set(True)
            self.subtitle_color_var.set("Trắng Truyền Thống (Classic White)")
            self.sub_anim_var.set("Tĩnh (Không animation)")
            self.transition_var.set("Không transition")
            self.clip_intro_var.set("Không animation")
            self.video_effect_var.set("Không dùng hiệu ứng")
            self.filter_var.set("Không dùng filter")
            self.camera_motion_var.set("Cố định (Không chuyển động)")
            self.sfx_var.set(False)
            self.bgm_preset_var.set("Không dùng nhạc nền")
            self.bgm_files_var.set("")
            self.blur_var.set(True)
            self.smart_pacing_var.set(False)
            self.ducking_var.set(True)
            self.fade_var.set(True)
            self.cta_sub_var.set(False)
            self._select_all_motions(False)
            self._log("[Preset] Đã áp dụng: Tối giản nhanh (16:9).")
        self._update_preset_pills_ui()
        self._update_stat_cards()

    def _browse_audio(self):
        files = filedialog.askopenfilenames(
            title="Chọn một hoặc nhiều file voice audio",
            initialdir=self.default_init_dir,
            filetypes=[
                ("Audio Files", "*.wav *.mp3 *.m4a *.aac *.flac *.WAV *.MP3 *.M4A *.AAC *.FLAC"),
                ("WAV Audio", "*.wav *.WAV"),
                ("MP3 Audio", "*.mp3 *.MP3"),
                ("M4A Audio", "*.m4a *.M4A"),
                ("All Files", "*.*")
            ]
        )
        if files:
            self.audio_files_var.set("; ".join(files))
            self._auto_detect_from_folder(os.path.dirname(files[0]))
            self._update_stat_cards()

    def _browse_srt(self):
        f = filedialog.askopenfilename(
            title="Chọn file phụ đề SRT",
            initialdir=self.default_init_dir,
            filetypes=[("SRT Subtitles", "*.srt *.SRT"), ("All Files", "*.*")]
        )
        if f:
            self.srt_file_var.set(f)
            self._auto_detect_from_folder(os.path.dirname(f))

    def _browse_scenes_file(self):
        f = filedialog.askopenfilename(
            title="Chọn file kịch bản (.txt, .csv)",
            initialdir=self.default_init_dir,
            filetypes=[("Text Files", "*.txt *.TXT"), ("CSV Files", "*.csv *.CSV"), ("All Files", "*.*")]
        )
        if f:
            try:
                for enc in ['utf-8-sig', 'utf-8', 'cp1252', 'latin-1']:
                    try:
                        with open(f, 'r', encoding=enc) as file_obj:
                            content = file_obj.read()
                        break
                    except Exception:
                        continue
                self.scenes_textbox.delete("1.0", "end")
                self.scenes_textbox.insert("1.0", content)
                self._update_scenes_count()
                lines = [l for l in content.splitlines() if l.strip()]
                self._log(f"[Info] Đã nạp {len(lines)} cảnh từ file: {os.path.basename(f)}")
            except Exception as e:
                messagebox.showerror("Lỗi Đọc File", f"Không thể đọc file kịch bản: {e}")

    def _browse_media_folder(self):
        d = filedialog.askdirectory(title="Chọn thư mục chứa ảnh hoặc video", initialdir=self.default_init_dir)
        if d:
            self.media_folder_var.set(d)

    def _on_bgm_preset_change(self, choice: str):
        if choice == "Không dùng nhạc nền":
            self.bgm_files_var.set("")
        elif "Tự chọn file" in choice:
            self._browse_bgm()
        else:
            self.bgm_files_var.set(choice)

    def _clear_bgm(self):
        self.bgm_files_var.set("")
        self.bgm_preset_var.set("Không dùng nhạc nền")

    def _browse_bgm(self):
        files = filedialog.askopenfilenames(
            title="Chọn file nhạc nền (BGM)",
            initialdir=self.default_init_dir,
            filetypes=[
                ("Audio Files", "*.wav *.mp3 *.m4a *.aac *.flac *.WAV *.MP3 *.M4A *.AAC *.FLAC"),
                ("WAV Audio", "*.wav *.WAV"),
                ("MP3 Audio", "*.mp3 *.MP3"),
                ("M4A Audio", "*.m4a *.M4A"),
                ("All Files", "*.*")
            ]
        )
        if files:
            self.bgm_files_var.set("; ".join(files))
            first_name = os.path.basename(files[0])
            self.bgm_preset_var.set(f"File: {first_name}")

    def _auto_detect_from_folder(self, folder: str):
        if not os.path.isdir(folder):
            return
        files = os.listdir(folder)
        if not self.srt_file_var.get():
            srts = [os.path.join(folder, f) for f in files if f.lower().endswith('.srt')]
            if srts:
                self.srt_file_var.set(srts[0])

        curr_text = self.scenes_textbox.get("1.0", "end").strip()
        if not curr_text or curr_text == SCENES_PLACEHOLDER.strip():
            txts = [os.path.join(folder, f) for f in files if f.lower().endswith('.txt')]
            if txts:
                try:
                    with open(txts[0], 'r', encoding='utf-8-sig', errors='replace') as fo:
                        self.scenes_textbox.delete("1.0", "end")
                        self.scenes_textbox.insert("1.0", fo.read())
                        self._update_scenes_count()
                except Exception:
                    pass

        if not self.media_folder_var.get():
            subdirs = [os.path.join(folder, d) for d in files if os.path.isdir(os.path.join(folder, d))]
            for sd in subdirs:
                has_imgs = any(f.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.webp', '.mp4'] for f in os.listdir(sd)[:5])
                if has_imgs:
                    self.media_folder_var.set(sd)
                    break

    def _auto_detect_sample_files(self):
        if os.path.isdir(self.default_init_dir):
            self._auto_detect_from_folder(self.default_init_dir)
            files = os.listdir(self.default_init_dir)
            voices = [os.path.join(self.default_init_dir, f) for f in files if f.lower().endswith(('.wav', '.mp3'))]
            if voices and not self.audio_files_var.get():
                self.audio_files_var.set(voices[0])
            self._update_scenes_count()
            self._log("[Info] Đã tự động nạp các tệp mẫu sẵn có từ Desktop.")

    def _log(self, text: str):
        self.console_textbox.insert("end", text + "\n")
        self.console_textbox.see("end")

    def _launch_capcut(self):
        ok = launch_capcut_app()
        if ok:
            self._log("[Action] Đã khởi chạy CapCut.")
        else:
            messagebox.showinfo("Khởi chạy CapCut", "Không tìm thấy CapCut tự động. Vui lòng mở CapCut từ máy tính của bạn.")

    def _launch_last_draft(self):
        draft_p = getattr(self, 'last_draft_dir', None)
        ok = launch_capcut_app(draft_p)
        if ok:
            self._log(f"[Action] Đã khởi chạy CapCut mở dự án thành công.")
        else:
            if draft_p:
                open_path_in_os(draft_p)

    def _open_last_draft_folder(self):
        draft_p = getattr(self, 'last_draft_dir', None)
        if draft_p and os.path.exists(draft_p):
            open_path_in_os(draft_p)

    def _open_settings_dialog(self):
        dlg = ctk.CTkToplevel(self)
        dlg.title("Cài Đặt Thư Mục CapCut")
        dlg.geometry("540x200")
        dlg.configure(fg_color=self.c_bg)
        dlg.transient(self)
        dlg.grab_set()

        ctk.CTkLabel(dlg, text="Cài Đặt Thư Mục CapCut Drafts", font=("Segoe UI", 13, "bold"), text_color="#fff").pack(anchor="w", padx=20, pady=(16, 6))
        ctk.CTkLabel(dlg, text="Đường dẫn lưu dự án CapCut (com.lveditor.draft):", font=("Segoe UI", 11), text_color=self.c_sub).pack(anchor="w", padx=20, pady=(0, 4))

        e = ctk.CTkEntry(dlg, textvariable=self.draft_root_var, height=34, corner_radius=6, fg_color=self.c_input, border_color=self.c_input_border)
        e.pack(fill="x", padx=20, pady=(0, 10))

        def _pick_d():
            d = filedialog.askdirectory(title="Chọn thư mục com.lveditor.draft", initialdir=self.draft_root_var.get())
            if d:
                self.draft_root_var.set(d)

        btn_row = ctk.CTkFrame(dlg, fg_color="transparent")
        btn_row.pack(fill="x", padx=20, pady=6)

        ctk.CTkButton(btn_row, text="Duyệt thư mục...", fg_color=self.c_btn_sec, hover_color=self.c_btn_sec_h, command=_pick_d).pack(side="left")
        ctk.CTkButton(btn_row, text="Lưu lại", fg_color=self.c_accent, hover_color=self.c_accent_hover, command=dlg.destroy).pack(side="right")

    def _show_completed_dialog(self, data):
        dlg = ctk.CTkToplevel(self)
        dlg.title("Thành Công")
        dlg.geometry("480x220")
        dlg.configure(fg_color=self.c_bg)
        dlg.transient(self)
        dlg.grab_set()

        ctk.CTkLabel(dlg, text="TẠO DỰ ÁN CAPCUT THÀNH CÔNG", font=("Segoe UI", 14, "bold"), text_color=self.c_success).pack(pady=(18, 6))

        ctk.CTkLabel(
            dlg,
            text=f"Dự án '{data['draft_name']}' ({data['total_scenes']} cảnh, {data['duration_seconds']/60:.2f} phút) đã sẵn sàng trong CapCut.",
            font=("Segoe UI", 11), text_color=self.c_text, wraplength=420, justify="center"
        ).pack(pady=(0, 16))

        btn_row = ctk.CTkFrame(dlg, fg_color="transparent")
        btn_row.pack(pady=8)

        def _open_f():
            open_path_in_os(data['draft_dir'])
            dlg.destroy()

        def _open_cc():
            ok = launch_capcut_app(data.get('draft_dir'))
            if not ok:
                open_path_in_os(data['draft_dir'])
            dlg.destroy()

        ctk.CTkButton(
            btn_row, text="Mở thư mục Draft", fg_color=self.c_btn_sec, hover_color=self.c_btn_sec_h,
            text_color=self.c_text, corner_radius=10, width=150, height=36, font=("Segoe UI", 11), command=_open_f
        ).pack(side="left", padx=6)

        ctk.CTkButton(
            btn_row, text="Mở CapCut xem ngay", fg_color=self.c_accent, hover_color=self.c_accent_hover,
            text_color="#ffffff", corner_radius=10, width=180, height=36, font=("Segoe UI", 12, "bold"), command=_open_cc
        ).pack(side="left", padx=6)

    def _update_license_ui(self):
        info = get_license_info()
        status = info.get("status")
        if status == "lifetime":
            self.btn_license.configure(
                text="Bản quyền vĩnh viễn",
                fg_color="#143b2a",
                hover_color="#1d5039",
                text_color="#4ade80"
            )
            if hasattr(self, "btn_run") and not self.is_running:
                self.btn_run.configure(state="normal", text="Bắt đầu tạo dự án CapCut")
        elif status == "trial":
            d = info.get("days_left", 0)
            h = info.get("hours_left", 0)
            t_str = f"{d} ngày {h}h" if d > 0 else f"{h} giờ"
            self.btn_license.configure(
                text=f"Dùng thử: Còn {t_str}",
                fg_color="#3e2810",
                hover_color="#543716",
                text_color="#fbbf24"
            )
            if hasattr(self, "btn_run") and not self.is_running:
                self.btn_run.configure(state="normal", text="Bắt đầu tạo dự án CapCut")
        else:
            self.btn_license.configure(
                text="Kích hoạt bản quyền",
                fg_color="#40181d",
                hover_color="#572127",
                text_color="#f87171"
            )
            if hasattr(self, "btn_run") and not self.is_running:
                self.btn_run.configure(state="disabled", text="Hết hạn dùng thử 3 ngày (Kích hoạt 150k)")
        self._update_stat_cards()

    def _open_license_dialog(self):
        info = get_license_info()
        pay = get_payment_info()
        hwid = info["hwid"]

        dlg = ctk.CTkToplevel(self)
        dlg.title("Bản Quyền & Kích Hoạt AutoCapCut Studio")
        dlg.geometry("640x630")
        dlg.minsize(580, 580)
        dlg.configure(fg_color=self.c_bg)
        dlg.transient(self)
        dlg.grab_set()

        # Dialog Header
        top_bar = ctk.CTkFrame(dlg, fg_color=self.c_card, corner_radius=14, border_width=1, border_color=self.c_card_border)
        top_bar.pack(fill="x", padx=20, pady=(18, 10))

        if info["status"] == "lifetime":
            badge_text = "ĐÃ KÍCH HOẠT VĨNH VIỄN"
            badge_color = "#143b2a"
            badge_fg = "#4ade80"
            sub_text = "Phần mềm đã được kích hoạt bản quyền vĩnh viễn trên máy tính này."
        elif info["status"] == "trial":
            badge_text = f"ĐANG DÙNG THỬ (CÒN {info['days_left']} NGÀY {info['hours_left']} GIỜ)"
            badge_color = "#3e2810"
            badge_fg = "#fbbf24"
            sub_text = "Bạn đang trong 3 ngày trải nghiệm miễn phí toàn bộ tính năng. Nâng cấp 150k để dùng trọn đời."
        else:
            badge_text = "HẾT HẠN DÙNG THỬ 3 NGÀY"
            badge_color = "#40181d"
            badge_fg = "#f87171"
            sub_text = "Thời gian dùng thử 3 ngày đã kết thúc. Vui lòng thanh toán 150.000 VNĐ để mở khóa vĩnh viễn."

        header_inner = ctk.CTkFrame(top_bar, fg_color="transparent")
        header_inner.pack(fill="x", padx=16, pady=12)

        lbl_b = ctk.CTkLabel(header_inner, text=badge_text, font=("Segoe UI", 11, "bold"),
                             fg_color=badge_color, text_color=badge_fg, corner_radius=8, height=26, padx=10)
        lbl_b.pack(anchor="w", pady=(0, 6))

        ctk.CTkLabel(header_inner, text="Kích Hoạt Bản Quyền AutoCapCut Studio", font=("Segoe UI", 15, "bold"),
                     text_color="#ffffff").pack(anchor="w")
        ctk.CTkLabel(header_inner, text=sub_text, font=("Segoe UI", 11),
                     text_color=self.c_sub).pack(anchor="w", pady=(2, 0))

        # Card 1: Machine ID (HWID)
        hwid_card = ctk.CTkFrame(dlg, fg_color=self.c_card, corner_radius=14, border_width=1, border_color=self.c_card_border)
        hwid_card.pack(fill="x", padx=20, pady=5)

        hwid_inner = ctk.CTkFrame(hwid_card, fg_color="transparent")
        hwid_inner.pack(fill="x", padx=16, pady=10)

        ctk.CTkLabel(hwid_inner, text="MÃ THIẾT BỊ CỦA BẠN (MACHINE ID):", font=("Segoe UI", 10, "bold"),
                     text_color=self.c_sub).pack(anchor="w")

        id_row = ctk.CTkFrame(hwid_inner, fg_color="transparent")
        id_row.pack(fill="x", pady=(6, 0))

        ent_hwid = ctk.CTkEntry(id_row, font=("Consolas", 13, "bold"), fg_color=self.c_input,
                                border_color=self.c_accent, text_color=self.c_text, height=34, corner_radius=8)
        ent_hwid.insert(0, hwid)
        ent_hwid.configure(state="readonly")
        ent_hwid.pack(side="left", fill="x", expand=True, padx=(0, 8))

        def _copy_hwid():
            self.clipboard_clear()
            self.clipboard_append(hwid)
            btn_copy_hwid.configure(text="Đã chép!", fg_color=self.c_success)
            self.after(1500, lambda: btn_copy_hwid.configure(text="Sao chép", fg_color=self.c_btn_sec))

        btn_copy_hwid = ctk.CTkButton(id_row, text="Sao chép", font=("Segoe UI", 11, "bold"),
                                     fg_color=self.c_btn_sec, hover_color=self.c_btn_sec_h, text_color=self.c_text,
                                     width=90, height=34, corner_radius=8, command=_copy_hwid)
        btn_copy_hwid.pack(side="left")

        # Card 2: Payment Details (150k Lifetime)
        pay_card = ctk.CTkFrame(dlg, fg_color=self.c_card, corner_radius=14, border_width=1, border_color=self.c_card_border)
        pay_card.pack(fill="x", padx=20, pady=5)

        pay_inner = ctk.CTkFrame(pay_card, fg_color="transparent")
        pay_inner.pack(fill="x", padx=16, pady=10)

        ctk.CTkLabel(pay_inner, text="THÔNG TIN THANH TOÁN (GÓI VĨNH VIỄN 150.000 VNĐ):",
                     font=("Segoe UI", 10, "bold"), text_color=self.c_sub).pack(anchor="w", pady=(0, 4))

        p_info = (
            f"• Ngân hàng: {pay.get('bank_name', 'MBBank')}\n"
            f"• Số tài khoản: {pay.get('bank_account', '')} ({pay.get('account_name', '')})\n"
            f"• Số tiền: 150.000 VNĐ (Sử dụng trọn đời trên máy này, cập nhật miễn phí)\n"
            f"• Nội dung chuyển khoản: {pay.get('transfer_content', '')}"
        )
        ctk.CTkLabel(pay_inner, text=p_info, font=("Segoe UI", 11), text_color=self.c_text,
                     justify="left").pack(anchor="w", pady=(0, 8))

        p_btn_row = ctk.CTkFrame(pay_inner, fg_color="transparent")
        p_btn_row.pack(fill="x")

        def _open_qr():
            import webbrowser
            qr_url = pay.get("vietqr_url", "")
            if qr_url:
                webbrowser.open(qr_url)

        def _copy_stk():
            self.clipboard_clear()
            self.clipboard_append(pay.get('bank_account', ''))
            btn_stk.configure(text="Đã chép STK!")
            self.after(1500, lambda: btn_stk.configure(text="Chép STK"))

        def _copy_nd():
            self.clipboard_clear()
            self.clipboard_append(pay.get('transfer_content', ''))
            btn_nd.configure(text="Đã chép cú pháp!")
            self.after(1500, lambda: btn_nd.configure(text="Chép nội dung CK"))

        btn_stk = ctk.CTkButton(p_btn_row, text="Chép STK", font=("Segoe UI", 11, "bold"),
                                fg_color=self.c_btn_sec, hover_color=self.c_btn_sec_h, text_color=self.c_text,
                                corner_radius=8, width=105, height=32, command=_copy_stk)
        btn_stk.pack(side="left", padx=(0, 6))

        btn_nd = ctk.CTkButton(p_btn_row, text="Chép nội dung CK", font=("Segoe UI", 11, "bold"),
                               fg_color=self.c_btn_sec, hover_color=self.c_btn_sec_h, text_color=self.c_text,
                               corner_radius=8, width=135, height=32, command=_copy_nd)
        btn_nd.pack(side="left", padx=(0, 6))

        btn_qr = ctk.CTkButton(p_btn_row, text="Mở mã QR VietQR", font=("Segoe UI", 11, "bold"),
                               fg_color=self.c_accent, hover_color=self.c_accent_hover, text_color="#ffffff",
                               corner_radius=8, width=135, height=32, command=_open_qr)
        btn_qr.pack(side="left")

        # Card 3: Key Activation Entry
        act_card = ctk.CTkFrame(dlg, fg_color=self.c_card, corner_radius=14, border_width=1, border_color=self.c_card_border)
        act_card.pack(fill="x", padx=20, pady=5)

        act_inner = ctk.CTkFrame(act_card, fg_color="transparent")
        act_inner.pack(fill="x", padx=16, pady=10)

        ctk.CTkLabel(act_inner, text="NHẬP MÃ KÍCH HOẠT (LICENSE KEY):", font=("Segoe UI", 10, "bold"),
                     text_color=self.c_sub).pack(anchor="w")

        key_row = ctk.CTkFrame(act_inner, fg_color="transparent")
        key_row.pack(fill="x", pady=(6, 4))

        ent_key = ctk.CTkEntry(key_row, font=("Consolas", 12), placeholder_text="ACCP-XXXX-XXXX-XXXX-XXXX",
                               fg_color=self.c_input, border_color=self.c_input_border, height=34, corner_radius=8)
        ent_key.pack(side="left", fill="x", expand=True, padx=(0, 8))

        lbl_msg = ctk.CTkLabel(act_inner, text="", font=("Segoe UI", 11), text_color=self.c_text)
        lbl_msg.pack(anchor="w")

        def _do_activate():
            key_val = ent_key.get().strip()
            ok, msg = activate_license(key_val)
            if ok:
                lbl_msg.configure(text=msg, text_color=self.c_success)
                messagebox.showinfo("Kích Hoạt Thành Công", msg)
                self._update_license_ui()
                dlg.destroy()
            else:
                lbl_msg.configure(text=msg, text_color=self.c_danger)
                messagebox.showerror("Kích Hoạt Thất Bại", msg)

        btn_act = ctk.CTkButton(key_row, text="Kích hoạt ngay", font=("Segoe UI", 11, "bold"),
                                fg_color=self.c_accent, hover_color=self.c_accent_hover, text_color="#ffffff",
                                corner_radius=8, width=120, height=34, command=_do_activate)
        btn_act.pack(side="left")

        # Bottom help note
        note_text = "Lưu ý: Sau khi chuyển khoản, gửi mã máy (Machine ID) để Admin kích hoạt ngay trong 5-10 phút."
        ctk.CTkLabel(dlg, text=note_text, font=("Segoe UI", 10), text_color=self.c_sub).pack(pady=(6, 12))

    # ------------------------------------------------------------------
    # IN-APP AUTO-UPDATER
    # ------------------------------------------------------------------
    def _start_background_update_check(self):
        def _bg():
            try:
                info = check_for_updates(timeout=6)
                if info.get("has_update"):
                    self.msg_queue.put(('update_available', info))
            except Exception:
                pass
        threading.Thread(target=_bg, daemon=True).start()

    def _manual_check_update(self):
        if self.pending_update_data:
            self._show_update_dialog(self.pending_update_data)
            return

        self._log("[Update] Đang kiểm tra bản cập nhật mới...")
        def _bg():
            try:
                info = check_for_updates(timeout=6)
                if info.get("has_update"):
                    self.msg_queue.put(('update_available', info))
                else:
                    self.msg_queue.put(('update_none', info))
            except Exception as e:
                self.msg_queue.put(('update_check_error', str(e)))
        threading.Thread(target=_bg, daemon=True).start()

    def _show_update_banner(self, data):
        self.pending_update_data = data
        latest = data.get("latest_version", "Mới")
        curr = data.get("current_version", CURRENT_VERSION)
        changelog = data.get("changelog", [])
        highlight = changelog[0] if changelog else "Cập nhật và tối ưu hoá tính năng mới."

        # 1. Update title row version badge to an eye-catching update indicator
        self.btn_ver.configure(
            text=f"Bản v{latest} mới!",
            fg_color="#143b2a",
            hover_color="#1d5039",
            text_color="#4ade80",
            width=120,
            command=lambda: self._show_update_dialog(data)
        )

        # 2. Clear previous banner content if any
        for w in self.update_banner_frame.winfo_children():
            w.destroy()

        # 3. Build inner content
        inner = ctk.CTkFrame(self.update_banner_frame, fg_color="transparent")
        inner.pack(fill="x", padx=14, pady=8)

        # Left Info
        left_box = ctk.CTkFrame(inner, fg_color="transparent")
        left_box.pack(side="left", fill="x", expand=True)

        top_row = ctk.CTkFrame(left_box, fg_color="transparent")
        top_row.pack(anchor="w")

        ctk.CTkLabel(
            top_row, text="BẢN CẬP NHẬT MỚI",
            font=("Segoe UI", 10, "bold"),
            fg_color="#143b2a", text_color="#4ade80",
            corner_radius=6, height=22, padx=8
        ).pack(side="left", padx=(0, 8))

        ctk.CTkLabel(
            top_row, text=f"AutoCapCut Studio v{latest} đã sẵn sàng (Đang dùng: v{curr})",
            font=("Segoe UI", 12, "bold"), text_color="#ffffff"
        ).pack(side="left")

        ctk.CTkLabel(
            left_box, text=f"• Điểm mới: {highlight} — Nhấn 'Cập nhật ngay' để nâng cấp tự động (giữ nguyên bản quyền)",
            font=("Segoe UI", 11), text_color="#a7f3d0"
        ).pack(anchor="w", pady=(3, 0))

        # Right Actions
        btn_box = ctk.CTkFrame(inner, fg_color="transparent")
        btn_box.pack(side="right")

        btn_act = ctk.CTkButton(
            btn_box, text="Cập nhật ngay", font=("Segoe UI", 11, "bold"),
            fg_color=self.c_accent, hover_color=self.c_accent_hover, text_color="#ffffff",
            height=32, width=120, corner_radius=8,
            command=lambda: self._show_update_dialog(data, auto_start=True)
        )
        btn_act.pack(side="left", padx=(0, 6))

        btn_detail = ctk.CTkButton(
            btn_box, text="Xem chi tiết", font=("Segoe UI", 11),
            fg_color=self.c_btn_sec, hover_color=self.c_btn_sec_h, text_color=self.c_text,
            height=32, width=95, corner_radius=8,
            command=lambda: self._show_update_dialog(data, auto_start=False)
        )
        btn_detail.pack(side="left", padx=(0, 6))

        btn_hide = ctk.CTkButton(
            btn_box, text="✕", font=("Segoe UI", 11, "bold"),
            fg_color="transparent", hover_color=self.c_btn_sec_h, text_color=self.c_sub,
            height=32, width=32, corner_radius=8,
            command=self.update_banner_frame.pack_forget
        )
        btn_hide.pack(side="left")

        # Pack banner right above main_body
        self.update_banner_frame.pack(fill="x", padx=20, pady=(0, 8), before=self.main_body)

    def _show_update_dialog(self, data, auto_start: bool = False):
        latest = data.get("latest_version", "Mới")
        curr = data.get("current_version", CURRENT_VERSION)
        changelog = data.get("changelog", [])
        dl_url = data.get("download_url", "")
        manual_url = data.get("manual_url", "https://github.com/vutrunquan/autocapcut/releases/latest")

        dlg = ctk.CTkToplevel(self)
        dlg.title("Cập Nhật AutoCapCut Studio")
        dlg.geometry("560x490")
        dlg.minsize(520, 430)
        dlg.configure(fg_color=self.c_bg)
        dlg.transient(self)
        dlg.grab_set()

        # Top banner card
        card_top = ctk.CTkFrame(dlg, fg_color=self.c_card, corner_radius=14, border_color=self.c_card_border, border_width=1)
        card_top.pack(fill="x", padx=18, pady=(16, 10))

        head_inner = ctk.CTkFrame(card_top, fg_color="transparent")
        head_inner.pack(fill="x", padx=16, pady=12)

        ctk.CTkLabel(
            head_inner, text=f"BẢN CẬP NHẬT MỚI: v{latest}", font=("Segoe UI", 11, "bold"),
            fg_color="#143b2a", text_color="#4ade80", corner_radius=6, height=24, padx=8
        ).pack(anchor="w", pady=(0, 6))

        ctk.CTkLabel(
            head_inner, text="Nâng Cấp AutoCapCut Studio", font=("Segoe UI", 15, "bold"),
            text_color="#ffffff"
        ).pack(anchor="w")

        rel_date = f" ({data.get('release_date')})" if data.get('release_date') else ""
        ctk.CTkLabel(
            head_inner, text=f"Phiên bản đang dùng: v{curr}  →  Phiên bản mới: v{latest}{rel_date}",
            font=("Segoe UI", 11), text_color=self.c_sub
        ).pack(anchor="w", pady=(2, 0))

        # Changelog card
        card_change = ctk.CTkFrame(dlg, fg_color=self.c_card, corner_radius=10, border_color=self.c_card_border, border_width=1)
        card_change.pack(fill="both", expand=True, padx=18, pady=6)

        c_inner = ctk.CTkFrame(card_change, fg_color="transparent")
        c_inner.pack(fill="both", expand=True, padx=14, pady=12)

        ctk.CTkLabel(
            c_inner, text="NHỮNG ĐIỂM MỚI TRONG BẢN CẬP NHẬT:", font=("Segoe UI", 10, "bold"),
            text_color=self.c_sub
        ).pack(anchor="w", pady=(0, 6))

        txt_box = ctk.CTkTextbox(
            c_inner, fg_color=self.c_input, border_color=self.c_input_border, border_width=1,
            text_color=self.c_text, font=("Segoe UI", 11), corner_radius=6
        )
        txt_box.pack(fill="both", expand=True)

        if changelog:
            cl_text = "\n".join(f"• {item}" for item in changelog)
        else:
            cl_text = "• Cập nhật và tối ưu hoá tính năng AutoCapCut Studio mới nhất."
        txt_box.insert("1.0", cl_text)
        txt_box.configure(state="disabled")

        # Progress UI (initially hidden)
        prog_frame = ctk.CTkFrame(dlg, fg_color="transparent")
        lbl_p_status = ctk.CTkLabel(prog_frame, text="", font=("Segoe UI", 11), text_color=self.c_text)
        lbl_p_status.pack(anchor="w", padx=2, pady=(0, 4))
        p_bar = ctk.CTkProgressBar(prog_frame, height=8, corner_radius=4, progress_color=self.c_accent)
        p_bar.pack(fill="x")
        p_bar.set(0)

        # Bottom buttons
        btn_row = ctk.CTkFrame(dlg, fg_color="transparent")
        btn_row.pack(fill="x", padx=18, pady=(10, 16))

        btn_cancel = ctk.CTkButton(
            btn_row, text="Để sau", font=("Segoe UI", 11),
            fg_color=self.c_btn_sec, hover_color=self.c_btn_sec_h, text_color=self.c_text,
            width=100, height=36, corner_radius=6, command=dlg.destroy
        )
        btn_cancel.pack(side="left")

        def _do_update():
            if not dl_url:
                import webbrowser
                webbrowser.open(manual_url)
                dlg.destroy()
                return

            btn_update.configure(state="disabled", text="Đang tải về...")
            btn_cancel.configure(state="disabled")
            btn_row.pack_forget()
            prog_frame.pack(fill="x", padx=18, pady=(8, 16))
            lbl_p_status.configure(text="Đang kết nối tải bản cập nhật...")

            import tempfile
            target_zip = os.path.join(tempfile.gettempdir(), f"autocapcut_update_v{latest}.zip")

            def _dl_worker():
                def _prog(pct, dl_bytes, tot_bytes):
                    dl_mb = dl_bytes / (1024 * 1024)
                    tot_mb = tot_bytes / (1024 * 1024) if tot_bytes else 0
                    if tot_mb > 0:
                        msg = f"Đang tải bản cập nhật: {pct*100:4.1f}% ({dl_mb:.1f} MB / {tot_mb:.1f} MB)..."
                    else:
                        msg = f"Đang tải bản cập nhật: {dl_mb:.1f} MB..."
                    self.msg_queue.put(('update_progress_ui', (dlg, p_bar, lbl_p_status, pct, msg)))

                try:
                    download_update_file(dl_url, target_zip, progress_callback=_prog)
                    self.msg_queue.put(('update_apply_ui', (dlg, lbl_p_status, target_zip)))
                except Exception as e:
                    self.msg_queue.put(('update_err_ui', (dlg, lbl_p_status, btn_row, btn_cancel, btn_update, str(e), manual_url)))

            threading.Thread(target=_dl_worker, daemon=True).start()

        btn_update = ctk.CTkButton(
            btn_row, text="Cập nhật ngay (Tự động)", font=("Segoe UI", 11, "bold"),
            fg_color=self.c_accent, hover_color=self.c_accent_hover, text_color="#ffffff",
            width=180, height=36, corner_radius=6, command=_do_update
        )
        btn_update.pack(side="right")

        if auto_start:
            self.after(200, _do_update)

    # ------------------------------------------------------------------
    # CORE PROCESS EXECUTION
    # ------------------------------------------------------------------
    def _start_processing(self):
        if self.is_running:
            return

        # Hard License check before starting processing
        try:
            check_license_valid()
        except LicenseExpiredError as e:
            self._update_license_ui()
            self._open_license_dialog()
            messagebox.showwarning("Bản Quyền Đã Hết Hạn", str(e))
            return

        audio_str = self.audio_files_var.get().strip()
        srt_path = self.srt_file_var.get().strip()
        scenes_content = self.scenes_textbox.get("1.0", "end").strip()
        media_dir = self.media_folder_var.get().strip()
        capcut_name = self.capcut_name_var.get().strip()
        bgm_str = self.bgm_files_var.get().strip()
        draft_root = self.draft_root_var.get().strip()

        # Validation
        if not audio_str:
            messagebox.showerror("Thiếu File Audio", "Vui lòng chọn ít nhất một file Audio voice!")
            return
        if not srt_path or not os.path.exists(srt_path):
            messagebox.showerror("Thiếu File SRT", "Vui lòng chọn file phụ đề SRT hợp lệ!")
            return
        if not scenes_content or scenes_content == SCENES_PLACEHOLDER.strip():
            messagebox.showerror("Thiếu Kịch Bản", "Vui lòng dán kịch bản vào khung văn bản hoặc nhấn 'Đọc .txt'!")
            return
        if not media_dir or not os.path.isdir(media_dir):
            messagebox.showerror("Thiếu Thư Mục Media", "Vui lòng chọn thư mục chứa ảnh hoặc video!")
            return
        if not capcut_name:
            messagebox.showerror("Thiếu Tên Dự Án", "Vui lòng nhập tên cho dự án CapCut!")
            return

        voice_files = [p.strip() for p in audio_str.split(';') if p.strip()]
        bgm_files = [p.strip() for p in bgm_str.split(';') if p.strip()] if bgm_str else None

        sort_label = self.sort_mode_var.get()
        if "Cũ đến Mới" in sort_label:
            sort_mode = "oldest_first"
        elif "Mới đến Cũ" in sort_label:
            sort_mode = "newest_first"
        else:
            sort_mode = "abc"

        trans_label = self.transition_var.get()
        try:
            trans_dur = float(self.trans_dur_var.get() or 0.5)
        except ValueError:
            trans_dur = 0.5
        trans_mode = 'all' if 'Tất cả' in self.trans_mode_var.get() else ('random' if 'Ngẫu nhiên' in self.trans_mode_var.get() else 'alternate')

        clip_intro = self.clip_intro_var.get()
        try:
            clip_intro_dur = float(self.clip_intro_dur_var.get() or 0.8)
        except ValueError:
            clip_intro_dur = 0.8
        clip_intro_mode = 'all' if 'Tất cả' in self.clip_intro_mode_var.get() else ('random' if 'Ngẫu nhiên' in self.clip_intro_mode_var.get() else 'first_only')

        video_effect = self.video_effect_var.get()
        video_effect_scope = 'all' if 'Tất cả' in self.video_effect_scope_var.get() else ('random' if 'Ngẫu nhiên' in self.video_effect_scope_var.get() else 'intro_outro')

        filter_name = self.filter_var.get()
        try:
            filter_intensity = float(self.filter_intensity_var.get() or 60.0)
        except ValueError:
            filter_intensity = 60.0

        cam_motion = self.camera_motion_var.get()
        try:
            zoom_scale = float(self.zoom_scale_var.get() or 112.0)
        except ValueError:
            zoom_scale = 112.0

        sub_anim = self.sub_anim_var.get()
        try:
            sub_size = float(self.sub_size_var.get() or 8.5)
        except ValueError:
            sub_size = 8.5
        sub_pos = 'bottom' if 'Dưới' in self.sub_pos_var.get() else ('center' if 'giữa' in self.sub_pos_var.get() else 'top')

        sfx_name = self.sfx_name_var.get()

        sub_col = "yellow"
        if "Trắng" in self.subtitle_color_var.get():
            sub_col = "white"
        elif "Cyan" in self.subtitle_color_var.get() or "Công Nghệ" in self.subtitle_color_var.get():
            sub_col = "cyan"
        elif "Xanh Lá" in self.subtitle_color_var.get():
            sub_col = "green"
        elif "Đỏ" in self.subtitle_color_var.get() or "Red" in self.subtitle_color_var.get():
            sub_col = "red"
        elif "Tím" in self.subtitle_color_var.get() or "Purple" in self.subtitle_color_var.get():
            sub_col = "purple"

        sub_box = "black"
        raw_box = self.subtitle_box_var.get()
        if "Đỏ" in raw_box or "Red" in raw_box:
            sub_box = "red"
        elif "Vàng" in raw_box or "Yellow" in raw_box:
            sub_box = "yellow"
        elif "Xanh" in raw_box or "Blue" in raw_box:
            sub_box = "dark_blue"
        elif "Tím" in raw_box or "Purple" in raw_box:
            sub_box = "purple"
        elif "Không" in raw_box or "None" in raw_box:
            sub_box = "none"
        elif "Trắng" in raw_box or "White" in raw_box:
            sub_box = "white"

        sfx_vol = float(self.sfx_vol_var.get() or 50) / 100.0
        bgm_vol = float(self.bgm_vol_var.get() or 15) / 100.0
        aspect_ratio = self.aspect_ratio_var.get()

        keyframe_config = {
            'zoom_in': {'enabled': self.m_zoom_in_var.get(), 'scale': self.m_zoom_in_scale.get()},
            'zoom_out': {'enabled': self.m_zoom_out_var.get(), 'scale': self.m_zoom_out_scale.get()},
            'pan_up': {'enabled': self.m_pan_up_var.get(), 'x': self.m_pan_up_x.get(), 'y': self.m_pan_up_y.get(), 'scale': self.m_pan_up_scale.get()},
            'pan_down': {'enabled': self.m_pan_down_var.get(), 'x': self.m_pan_down_x.get(), 'y': self.m_pan_down_y.get(), 'scale': self.m_pan_down_scale.get()},
            'pan_left': {'enabled': self.m_pan_left_var.get(), 'x': self.m_pan_left_x.get(), 'y': self.m_pan_left_y.get(), 'scale': self.m_pan_left_scale.get()},
            'pan_right': {'enabled': self.m_pan_right_var.get(), 'x': self.m_pan_right_x.get(), 'y': self.m_pan_right_y.get(), 'scale': self.m_pan_right_scale.get()},
        }

        self.cancel_event.clear()
        self.is_running = True
        self.btn_run.configure(state="disabled", text="Đang xử lý tiến trình...")
        if hasattr(self, 'btn_stop'):
            self.btn_stop.pack(side="right", padx=(8, 0))
            self.btn_stop.configure(state="normal", text="Dừng lại")
        self.progress_bar.set(0)
        self.console_textbox.delete("1.0", "end")
        self._update_stat_cards()
        if hasattr(self, 'complete_action_frame'):
            self.complete_action_frame.pack_forget()

        threading.Thread(
            target=self._worker_thread,
            args=(
                srt_path, scenes_content, voice_files, media_dir, capcut_name, draft_root,
                bgm_files, sort_mode,
                trans_label, trans_dur, trans_mode,
                clip_intro, clip_intro_dur, clip_intro_mode,
                video_effect, video_effect_scope,
                filter_name, filter_intensity,
                cam_motion, zoom_scale, keyframe_config,
                aspect_ratio, self.smart_pacing_var.get(), self.blur_var.get(),
                self.sfx_var.get(), sfx_name, sfx_vol, bgm_vol, self.ducking_var.get(), self.fade_var.get(),
                self.cta_sub_var.get(), sub_col, sub_box, sub_anim, sub_size, sub_pos,
                self.watermark_var.get(), self.subtitles_var.get()
            ),
            daemon=True
        ).start()

    def _stop_processing(self):
        if not self.is_running:
            return
        self.cancel_event.set()
        if hasattr(self, 'btn_stop'):
            self.btn_stop.configure(state="disabled", text="Đang dừng...")
        self.lbl_status.configure(text="Đang dừng tiến trình...", text_color=self.c_amber)
        self._log("\n[Hủy] Người dùng đã nhấn nút dừng tiến trình...")

    def _worker_thread(
        self, srt_path, script_source, voice_files, media_dir, capcut_name, draft_root,
        bgm_files, sort_mode,
        trans_label, trans_dur, trans_mode,
        clip_intro, clip_intro_dur, clip_intro_mode,
        video_effect, video_effect_scope,
        filter_name, filter_intensity,
        cam_motion, zoom_scale, keyframe_config,
        aspect_ratio, smart_pacing, canvas_blur,
        enable_sfx, sfx_name, sfx_volume, bgm_volume, audio_ducking, audio_fade,
        enable_cta, sub_col, sub_box, sub_anim, sub_size, sub_pos,
        remove_wm, import_subs
    ):
        def on_progress(msg, pct):
            self.msg_queue.put(('progress', (msg, pct)))

        try:
            res = run_autocapcut(
                srt_path=srt_path,
                script_source=script_source,
                voice_paths=voice_files,
                images_dir=media_dir,
                project_name=capcut_name,
                draft_root=draft_root or None,
                bgm_paths=bgm_files,
                sort_mode=sort_mode,
                transition=trans_label,
                transition_duration=trans_dur,
                transition_mode=trans_mode,
                clip_intro=clip_intro,
                clip_intro_duration=clip_intro_dur,
                clip_intro_mode=clip_intro_mode,
                video_effect=video_effect,
                video_effect_scope=video_effect_scope,
                filter_name=filter_name,
                filter_intensity=filter_intensity,
                camera_motion=cam_motion,
                zoom_scale=zoom_scale,
                keyframe_config=keyframe_config,
                smart_pacing=smart_pacing,
                canvas_blur=canvas_blur,
                import_subtitles=import_subs,
                subtitle_style=sub_col,
                subtitle_box_color=sub_box,
                subtitle_border_color="none",
                subtitle_animation=sub_anim,
                subtitle_font_size=sub_size,
                subtitle_position=sub_pos,
                enable_sfx=enable_sfx,
                sfx_name=sfx_name,
                sfx_volume=sfx_volume,
                bgm_volume=bgm_volume,
                audio_ducking=audio_ducking,
                audio_fade=audio_fade,
                enable_cta_subscribe=enable_cta,
                remove_gemini_watermark=remove_wm,
                aspect_ratio=aspect_ratio,
                progress_callback=on_progress,
                cancel_event=self.cancel_event
            )
            self.msg_queue.put(('success', res))
        except (InterruptedError, KeyboardInterrupt):
            self.msg_queue.put(('cancelled', None))
        except Exception as e:
            if self.cancel_event and self.cancel_event.is_set():
                self.msg_queue.put(('cancelled', None))
            else:
                self.msg_queue.put(('error', str(e)))

    def _process_queue(self):
        try:
            while True:
                msg_type, data = self.msg_queue.get_nowait()
                if msg_type == 'progress':
                    msg, pct = data
                    self.lbl_status.configure(text=f"[{pct*100:5.1f}%]  {msg}")
                    self.progress_bar.set(pct)
                    self._log(f"[{pct*100:5.1f}%] {msg}")
                elif msg_type == 'success':
                    self.is_running = False
                    self.btn_run.configure(state="normal", text="Bắt đầu tạo dự án CapCut")
                    if hasattr(self, 'btn_stop'):
                        self.btn_stop.pack_forget()
                        self.btn_stop.configure(state="normal", text="Dừng lại")
                    self._update_stat_cards()
                    self.last_draft_dir = data['draft_dir']
                    self.last_draft_name = data.get('draft_name', 'Dự án CapCut')
                    self.lbl_status.configure(text=f"Hoàn tất: Đã tạo xong '{self.last_draft_name}'!", text_color=self.c_success)
                    self.progress_bar.set(1.0)
                    self._log("\n" + "=" * 50)
                    self._log(f"TẠO DỰ ÁN CAPCUT THÀNH CÔNG")
                    self._log(f"  Dự án:      {data['draft_name']}")
                    self._log(f"  Tổng cảnh:  {data['total_scenes']} cảnh")
                    self._log(f"  Thời lượng: {data['duration_seconds']:.2f}s ({(data['duration_seconds']/60):.2f} phút)")
                    self._log(f"  Thư mục:    {data['draft_dir']}")
                    self._log("=" * 50)

                    # Show quick action buttons
                    if hasattr(self, 'complete_action_frame'):
                        self.btn_open_now.configure(text=f"Mở '{self.last_draft_name}' Trong CapCut")
                        self.complete_action_frame.pack(fill="x", pady=(6, 0))

                    if self.auto_open_capcut_var.get():
                        self._log("[Action] Tự động khởi chạy CapCut mở dự án...")
                        launch_capcut_app(data.get('draft_dir'))

                    self._show_completed_dialog(data)

                elif msg_type == 'cancelled':
                    self.is_running = False
                    self.btn_run.configure(state="normal", text="Bắt đầu tạo dự án CapCut")
                    if hasattr(self, 'btn_stop'):
                        self.btn_stop.pack_forget()
                        self.btn_stop.configure(state="normal", text="Dừng lại")
                    self._update_stat_cards()
                    self.lbl_status.configure(text="Đã dừng tiến trình.", text_color=self.c_amber)
                    self.progress_bar.set(0)
                    self._log("\n[Đã dừng] Tiến trình đã được dừng lại thành công.")
                    messagebox.showinfo("Đã Dừng", "Tiến trình tạo dự án CapCut đã được dừng lại.")

                elif msg_type == 'error':
                    self.is_running = False
                    self.btn_run.configure(state="normal", text="Bắt đầu tạo dự án CapCut")
                    if hasattr(self, 'btn_stop'):
                        self.btn_stop.pack_forget()
                        self.btn_stop.configure(state="normal", text="Dừng lại")
                    self._update_stat_cards()
                    self.lbl_status.configure(text=f"Lỗi: {data}", text_color=self.c_danger)
                    self._log(f"\n[Error] ĐÃ XẢY RA LỖI: {data}")
                    messagebox.showerror("Lỗi Quá Trình", f"Đã xảy ra lỗi:\n{data}")

                elif msg_type == 'update_available':
                    self.pending_update_data = data
                    self._show_update_banner(data)
                    self._show_update_dialog(data)

                elif msg_type == 'update_none':
                    messagebox.showinfo("Cập Nhật", f"Bạn đang sử dụng phiên bản mới nhất (v{CURRENT_VERSION}).")

                elif msg_type == 'update_check_error':
                    self._log(f"[Update] Không thể kiểm tra bản cập nhật: {data}")

                elif msg_type == 'update_progress_ui':
                    dlg, p_bar, lbl_p, pct, msg = data
                    if dlg.winfo_exists():
                        p_bar.set(pct)
                        lbl_p.configure(text=msg)

                elif msg_type == 'update_apply_ui':
                    dlg, lbl_p, zip_path = data
                    if dlg.winfo_exists():
                        lbl_p.configure(text="Đã tải xong! Đang cài đặt và khởi động lại ứng dụng...")
                    ok, msg = apply_update_package(zip_path)
                    if ok:
                        self.after(1000, lambda: os._exit(0))
                    else:
                        messagebox.showerror("Lỗi Cập Nhật", msg)

                elif msg_type == 'update_err_ui':
                    dlg, lbl_p, btn_row, btn_cancel, btn_update, err_msg, man_url = data
                    if dlg.winfo_exists():
                        lbl_p.configure(text=f"Lỗi tải về: {err_msg}", text_color=self.c_danger)
                        btn_row.pack(fill="x", padx=18, pady=(10, 16))
                        btn_cancel.configure(state="normal")
                        btn_update.configure(
                            state="normal", text="Mở trang tải thủ công",
                            command=lambda: [__import__('webbrowser').open(man_url), dlg.destroy()]
                        )
        except queue.Empty:
            pass

        self.after(100, self._process_queue)


def main():
    app = AutoCapCutApp()
    app.mainloop()


if __name__ == '__main__':
    main()
