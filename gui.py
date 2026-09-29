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
    get_capcut_exe_path
)


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
        self.geometry("1200x820")
        self.minsize(1080, 720)

        # ------------------------------------------------------------------
        # PROFESSIONAL GRAPHITE & COBALT PALETTE (Gentle on the eyes)
        # ------------------------------------------------------------------
        self.c_bg = "#121316"           # Dark graphite canvas
        self.c_card = "#18191e"         # Studio surface card
        self.c_card_border = "#26272f"  # Subtle 1px border
        self.c_input = "#111215"        # Inset field background
        self.c_input_border = "#2e3039" # Field border
        self.c_text = "#e3e4e8"         # Soft off-white text (no glare)
        self.c_sub = "#888b96"          # Balanced muted slate text
        self.c_accent = "#2563eb"       # Refined cobalt accent
        self.c_accent_hover = "#1d4ed8"
        self.c_btn_sec = "#202127"      # Neutral secondary button
        self.c_btn_sec_h = "#2c2d36"    # Neutral hover
        self.c_success = "#10b981"      # Emerald indicator badge
        self.c_danger = "#ef4444"

        self.configure(fg_color=self.c_bg)

        # ------------------------------------------------------------------
        # STATE VARIABLES
        # ------------------------------------------------------------------
        # Data inputs
        self.audio_files_var = tk.StringVar()
        self.srt_file_var = tk.StringVar()
        self.media_folder_var = tk.StringVar()
        self.bgm_files_var = tk.StringVar()
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
        self.sub_anim_var = tk.StringVar(value="Nảy chữ lên (Bounce Pop)")
        self.sub_size_var = tk.StringVar(value="8.5")
        self.sub_pos_var = tk.StringVar(value="Dưới cùng (Chuẩn Shorts/Reels)")

        self.sfx_var = tk.BooleanVar(value=True)
        self.sfx_name_var = tk.StringVar(value="Ngẫu nhiên phối hợp (Random)")
        self.sfx_vol_var = tk.StringVar(value="50")
        self.ducking_var = tk.BooleanVar(value=True)
        self.fade_var = tk.BooleanVar(value=True)
        self.cta_sub_var = tk.BooleanVar(value=True)

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
        self.last_draft_dir = None

        self.default_init_dir = r"C:\Users\vutru\OneDrive\Desktop\New folder (2)"
        if not os.path.exists(self.default_init_dir):
            self.default_init_dir = os.path.expanduser("~")

        self._build_layout()
        self._auto_detect_sample_files()
        self.after(100, self._process_queue)

    def _build_layout(self):
        # ------------------------------------------------------------------
        # 1. TOP HEADER (Brand & Universal Actions)
        # ------------------------------------------------------------------
        header_frame = ctk.CTkFrame(self, fg_color="transparent", height=50)
        header_frame.pack(fill="x", padx=20, pady=(14, 8))

        # Brand Badge & Title
        title_box = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_box.pack(side="left")

        logo_badge = ctk.CTkLabel(
            title_box, text="AC", font=("Segoe UI", 12, "bold"),
            fg_color=self.c_accent, text_color="#ffffff", corner_radius=6,
            width=30, height=30
        )
        logo_badge.pack(side="left", padx=(0, 10))

        text_sub_box = ctk.CTkFrame(title_box, fg_color="transparent")
        text_sub_box.pack(side="left")

        lbl_title = ctk.CTkLabel(
            text_sub_box, text="AutoCapCut Studio", font=("Segoe UI", 16, "bold"),
            text_color="#ffffff"
        )
        lbl_title.pack(anchor="w")

        lbl_sub = ctk.CTkLabel(
            text_sub_box, text="Đồng bộ media, phụ đề & biên tập timeline CapCut tự động",
            font=("Segoe UI", 11), text_color=self.c_sub
        )
        lbl_sub.pack(anchor="w")

        # Top Right Actions & Quick Preset
        actions_box = ctk.CTkFrame(header_frame, fg_color="transparent")
        actions_box.pack(side="right")

        ctk.CTkLabel(actions_box, text="Mẫu nhanh:", font=("Segoe UI", 11), text_color=self.c_sub).pack(side="left", padx=(0, 6))

        preset_opts = [
            "Tùy chỉnh thủ công (Custom)",
            "Video ngắn dọc TikTok / Shorts (9:16)",
            "Video ngang điện ảnh YouTube (16:9)",
            "Bản tin & Tin tức tài chính (16:9)",
            "Tối giản nhanh (16:9)"
        ]
        self.preset_combo = ctk.CTkComboBox(
            actions_box, variable=self.preset_var, values=preset_opts, width=270, height=32, corner_radius=6,
            fg_color=self.c_input, border_color=self.c_input_border, button_color=self.c_btn_sec,
            font=("Segoe UI", 11), command=self._apply_preset
        )
        self.preset_combo.pack(side="left", padx=(0, 10))

        btn_auto = ctk.CTkButton(
            actions_box, text="Tự động điền", font=("Segoe UI", 11),
            fg_color=self.c_btn_sec, hover_color=self.c_btn_sec_h, text_color=self.c_text,
            corner_radius=6, width=105, height=32, command=self._auto_detect_sample_files
        )
        btn_auto.pack(side="left", padx=4)

        btn_cc = ctk.CTkButton(
            actions_box, text="Mở CapCut", font=("Segoe UI", 11),
            fg_color=self.c_btn_sec, hover_color=self.c_btn_sec_h, text_color=self.c_text,
            corner_radius=6, width=95, height=32, command=self._launch_capcut
        )
        btn_cc.pack(side="left", padx=4)

        btn_settings = ctk.CTkButton(
            actions_box, text="Cài đặt", font=("Segoe UI", 11),
            fg_color=self.c_btn_sec, hover_color=self.c_btn_sec_h, text_color=self.c_text,
            corner_radius=6, width=80, height=32, command=self._open_settings_dialog
        )
        btn_settings.pack(side="left", padx=4)

        # ------------------------------------------------------------------
        # 2. MAIN 2-COLUMN WORKSPACE
        # ------------------------------------------------------------------
        main_body = ctk.CTkFrame(self, fg_color="transparent")
        main_body.pack(fill="both", expand=True, padx=20, pady=(4, 12))

        # LEFT COLUMN: Inputs & Script (46% width)
        left_col = ctk.CTkFrame(main_body, fg_color="transparent")
        left_col.pack(side="left", fill="both", expand=True, padx=(0, 8))

        # RIGHT COLUMN: Studio Controls Tabview & Run Box (54% width)
        right_col = ctk.CTkFrame(main_body, fg_color="transparent")
        right_col.pack(side="right", fill="both", expand=True, padx=(8, 0))

        # ------------------------------------------------------------------
        # LEFT COLUMN CONTENT:
        # Card 1: Dữ liệu đầu vào
        # Card 2: Kịch bản phân cảnh
        # ------------------------------------------------------------------
        card_data = self._create_card(left_col, title="1. DỮ LIỆU ĐẦU VÀO")

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
        bgm_row.pack(fill="x", pady=3)

        lbl_bgm = ctk.CTkLabel(
            bgm_row, text="Nhạc Nền (Tùy chọn):", font=("Segoe UI", 11),
            text_color=self.c_text, width=140, anchor="w"
        )
        lbl_bgm.pack(side="left")

        e_bgm = ctk.CTkEntry(
            bgm_row, textvariable=self.bgm_files_var, placeholder_text="File nhạc nền (nếu có)...",
            corner_radius=6, fg_color=self.c_input, border_color=self.c_input_border, text_color=self.c_text,
            height=30, font=("Segoe UI", 11)
        )
        e_bgm.pack(side="left", fill="x", expand=True, padx=(0, 6))

        ctk.CTkLabel(bgm_row, text="Vol:", font=("Segoe UI", 11), text_color=self.c_sub).pack(side="left", padx=(0, 2))
        ctk.CTkEntry(
            bgm_row, textvariable=self.bgm_vol_var, width=36, height=30, corner_radius=6,
            fg_color=self.c_input, border_color=self.c_input_border, justify="center", font=("Segoe UI", 11)
        ).pack(side="left", padx=(0, 2))
        ctk.CTkLabel(bgm_row, text="%", font=("Segoe UI", 11), text_color=self.c_sub).pack(side="left", padx=(0, 6))

        btn_bgm_clear = ctk.CTkButton(
            bgm_row, text="✕", width=28, height=30, corner_radius=6,
            fg_color=self.c_btn_sec, hover_color=self.c_btn_sec_h, font=("Segoe UI", 11),
            command=lambda: self.bgm_files_var.set("")
        )
        btn_bgm_clear.pack(side="left", padx=(0, 6))

        btn_bgm = ctk.CTkButton(
            bgm_row, text="Chọn BGM", width=95, height=30, corner_radius=6,
            fg_color=self.c_btn_sec, hover_color=self.c_btn_sec_h, font=("Segoe UI", 11),
            command=self._browse_bgm
        )
        btn_bgm.pack(side="right")

        # CapCut Project Name
        name_row = ctk.CTkFrame(card_data, fg_color="transparent")
        name_row.pack(fill="x", pady=3)

        lbl_name = ctk.CTkLabel(
            name_row, text="Tên Dự Án CapCut:", font=("Segoe UI", 11),
            text_color=self.c_text, width=140, anchor="w"
        )
        lbl_name.pack(side="left")

        e_name = ctk.CTkEntry(
            name_row, textvariable=self.capcut_name_var, corner_radius=6,
            fg_color=self.c_input, border_color=self.c_input_border, text_color=self.c_text,
            height=30, font=("Segoe UI", 11)
        )
        e_name.pack(side="left", fill="x", expand=True)

        # Card 2: Kịch bản phân cảnh (Script)
        card_script = self._create_card(left_col, title="2. KỊCH BẢN PHÂN CẢNH (Mỗi dòng 1 media)")

        sc_bar = ctk.CTkFrame(card_script, fg_color="transparent")
        sc_bar.pack(fill="x", pady=(0, 6))

        self.lbl_scenes_count = ctk.CTkLabel(
            sc_bar, text="0 cảnh đã nạp", font=("Segoe UI", 10, "bold"),
            fg_color="#1d2027", text_color=self.c_sub, corner_radius=10, padx=8, pady=2
        )
        self.lbl_scenes_count.pack(side="left")

        sc_tools = ctk.CTkFrame(sc_bar, fg_color="transparent")
        sc_tools.pack(side="right")

        btn_split = ctk.CTkButton(
            sc_tools, text="Tách câu", width=68, height=26, corner_radius=5,
            fg_color=self.c_btn_sec, hover_color=self.c_btn_sec_h, font=("Segoe UI", 10),
            command=self._split_scenes_into_sentences
        )
        btn_split.pack(side="left", padx=2)

        btn_clean = ctk.CTkButton(
            sc_tools, text="Dọn dòng", width=68, height=26, corner_radius=5,
            fg_color=self.c_btn_sec, hover_color=self.c_btn_sec_h, font=("Segoe UI", 10),
            command=self._clean_empty_lines
        )
        btn_clean.pack(side="left", padx=2)

        btn_paste = ctk.CTkButton(
            sc_tools, text="Dán", width=48, height=26, corner_radius=5,
            fg_color=self.c_btn_sec, hover_color=self.c_btn_sec_h, font=("Segoe UI", 10),
            command=self._paste_scenes
        )
        btn_paste.pack(side="left", padx=2)

        btn_copy = ctk.CTkButton(
            sc_tools, text="Copy", width=48, height=26, corner_radius=5,
            fg_color=self.c_btn_sec, hover_color=self.c_btn_sec_h, font=("Segoe UI", 10),
            command=self._copy_scenes
        )
        btn_copy.pack(side="left", padx=2)

        btn_load = ctk.CTkButton(
            sc_tools, text="Đọc .txt", width=68, height=26, corner_radius=5,
            fg_color=self.c_btn_sec, hover_color=self.c_btn_sec_h, font=("Segoe UI", 10),
            command=self._browse_scenes_file
        )
        btn_load.pack(side="left", padx=2)

        btn_clear_sc = ctk.CTkButton(
            sc_tools, text="✕", width=26, height=26, corner_radius=5,
            fg_color=self.c_btn_sec, hover_color=self.c_btn_sec_h, font=("Segoe UI", 10),
            command=self._clear_scenes
        )
        btn_clear_sc.pack(side="left", padx=(2, 0))

        self.scenes_textbox = ctk.CTkTextbox(
            card_script, height=190, corner_radius=8,
            fg_color=self.c_input, border_color=self.c_input_border, border_width=1,
            text_color=self.c_text, font=("Segoe UI", 11)
        )
        self.scenes_textbox.pack(fill="both", expand=True)
        self.scenes_textbox.insert("1.0", SCENES_PLACEHOLDER)
        self.scenes_textbox.bind("<FocusIn>", self._on_scenes_focus_in)
        self.scenes_textbox.bind("<FocusOut>", self._on_scenes_focus_out)
        self.scenes_textbox.bind("<KeyRelease>", self._update_scenes_count)

        # ------------------------------------------------------------------
        # RIGHT COLUMN CONTENT:
        # Tabview (Studio Controls) + Run Box + Progress + Log
        # ------------------------------------------------------------------
        self.tabview = ctk.CTkTabview(
            right_col,
            fg_color=self.c_card,
            segmented_button_fg_color=self.c_input,
            segmented_button_selected_color=self.c_accent,
            segmented_button_selected_hover_color=self.c_accent_hover,
            segmented_button_unselected_color=self.c_input,
            segmented_button_unselected_hover_color=self.c_btn_sec_h,
            text_color=self.c_text,
            corner_radius=10,
            border_color=self.c_card_border,
            border_width=1
        )
        self.tabview.pack(fill="both", expand=True, pady=(0, 10))

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
            cam_bar, text="Chọn tất cả", width=75, height=26, corner_radius=5,
            fg_color=self.c_btn_sec, hover_color=self.c_btn_sec_h, font=("Segoe UI", 10),
            command=lambda: self._select_all_motions(True)
        ).pack(side="right", padx=2)

        ctk.CTkButton(
            cam_bar, text="Bỏ chọn", width=65, height=26, corner_radius=5,
            fg_color=self.c_btn_sec, hover_color=self.c_btn_sec_h, font=("Segoe UI", 10),
            command=lambda: self._select_all_motions(False)
        ).pack(side="right", padx=2)

        # 2 Sub-columns for 6 motion keyframes
        kf_grid = ctk.CTkFrame(tab_cam, fg_color="transparent")
        kf_grid.pack(fill="both", expand=True)

        col_k1 = ctk.CTkFrame(kf_grid, fg_color="#14151a", corner_radius=8, border_color=self.c_card_border, border_width=1)
        col_k1.pack(side="left", fill="both", expand=True, padx=(0, 5), pady=2)
        self._add_motion_zoom(col_k1, "Zoom In (Phóng to)", self.m_zoom_in_var, self.m_zoom_in_scale)
        self._add_motion_pan(col_k1, "Pan Up (Lia lên)", self.m_pan_up_var, self.m_pan_up_x, self.m_pan_up_y, self.m_pan_up_scale)
        self._add_motion_pan(col_k1, "Pan Left (Lia trái)", self.m_pan_left_var, self.m_pan_left_x, self.m_pan_left_y, self.m_pan_left_scale)

        col_k2 = ctk.CTkFrame(kf_grid, fg_color="#14151a", corner_radius=8, border_color=self.c_card_border, border_width=1)
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
            "Nảy chữ lên (Bounce Pop)", "Chạy từng chữ (Karaoke Reveal)", "Nhịp điệu vui nhộn (Playful Bounce)",
            "Trượt mượt lên (Slide Up)", "Quét từ trái sang (Slide Right)", "Tĩnh (Không animation)"
        ]
        ctk.CTkComboBox(
            sub_row2, variable=self.sub_anim_var, values=sub_anim_opts, height=28, corner_radius=6,
            fg_color=self.c_input, border_color=self.c_input_border
        ).pack(side="left", fill="x", expand=True)

        # SFX Row
        sfx_row = ctk.CTkFrame(tab_sub, fg_color="transparent")
        sfx_row.pack(fill="x", pady=(8, 4))

        ctk.CTkCheckBox(
            sfx_row, text=" Âm thanh chuyển cảnh (SFX):",
            variable=self.sfx_var, font=("Segoe UI", 11), corner_radius=5,
            fg_color=self.c_accent, hover_color=self.c_accent_hover, text_color=self.c_text
        ).pack(side="left", padx=(0, 6))

        sfx_opts = ["Ngẫu nhiên phối hợp (Random)", "Whoosh (Lướt gió điện ảnh)", "Swoosh (Vút nhanh)", "Pop (Nảy vui nhộn)", "Ding (Keng chuông)"]
        ctk.CTkComboBox(
            sfx_row, variable=self.sfx_name_var, values=sfx_opts, width=200, height=28, corner_radius=6,
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
        # ACTION BOX & RUN BUTTON
        # ------------------------------------------------------------------
        run_card = ctk.CTkFrame(right_col, fg_color=self.c_card, corner_radius=10, border_color=self.c_card_border, border_width=1)
        run_card.pack(fill="x", pady=(0, 8), padx=2, ipady=4)

        run_inner = ctk.CTkFrame(run_card, fg_color="transparent")
        run_inner.pack(fill="x", padx=12, pady=8)

        self.btn_run = ctk.CTkButton(
            run_inner,
            text="Bắt đầu tạo dự án CapCut",
            font=("Segoe UI", 13, "bold"),
            fg_color=self.c_accent,
            hover_color=self.c_accent_hover,
            corner_radius=8,
            height=40,
            command=self._start_processing
        )
        self.btn_run.pack(fill="x", pady=(0, 6))

        self.progress_bar = ctk.CTkProgressBar(
            run_inner, corner_radius=6, height=6, fg_color="#121316", progress_color=self.c_accent
        )
        self.progress_bar.pack(fill="x")
        self.progress_bar.set(0)

        self.lbl_status = ctk.CTkLabel(
            run_inner, text="Sẵn sàng. Nhấn nút để xuất dự án sang CapCut PC.",
            font=("Segoe UI", 10), text_color=self.c_sub
        )
        self.lbl_status.pack(anchor="w", pady=(3, 0))

        # ------------------------------------------------------------------
        # CONSOLE LOG (Compact & Clean)
        # ------------------------------------------------------------------
        log_card = ctk.CTkFrame(right_col, fg_color=self.c_card, corner_radius=10, border_color=self.c_card_border, border_width=1)
        log_card.pack(fill="both", expand=True, padx=2)

        log_head = ctk.CTkFrame(log_card, fg_color="transparent")
        log_head.pack(fill="x", padx=12, pady=(6, 2))
        ctk.CTkLabel(log_head, text="Nhật ký tiến trình:", font=("Segoe UI", 11, "bold"), text_color=self.c_text).pack(side="left")

        btn_clear_log = ctk.CTkButton(
            log_head, text="Xóa log", width=55, height=22, corner_radius=4,
            fg_color=self.c_btn_sec, hover_color=self.c_btn_sec_h, font=("Segoe UI", 9),
            command=lambda: self.console_textbox.delete("1.0", "end")
        )
        btn_clear_log.pack(side="right")

        self.console_textbox = ctk.CTkTextbox(
            log_card, height=100, corner_radius=6,
            fg_color=self.c_input, border_color=self.c_input_border, border_width=1,
            text_color="#888b96", font=("Consolas", 10)
        )
        self.console_textbox.pack(fill="both", expand=True, padx=12, pady=(0, 10))
        self._log("AutoCapCut Studio sẵn sàng hoạt động.")

    # ------------------------------------------------------------------
    # CARD & ROW HELPERS
    # ------------------------------------------------------------------
    def _create_card(self, parent, title: str) -> ctk.CTkFrame:
        card = ctk.CTkFrame(
            parent, fg_color=self.c_card, corner_radius=10,
            border_color=self.c_card_border, border_width=1
        )
        card.pack(fill="x", pady=(0, 10), ipadx=10, ipady=8)

        lbl = ctk.CTkLabel(
            card, text=title, font=("Segoe UI", 12, "bold"), text_color="#ffffff"
        )
        lbl.pack(anchor="w", padx=4, pady=(0, 6))
        return card

    def _add_row(self, parent, label, var, placeholder, btn_text, cmd):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=3)

        lbl = ctk.CTkLabel(
            row, text=label, font=("Segoe UI", 11), text_color=self.c_text, width=140, anchor="w"
        )
        lbl.pack(side="left")

        entry = ctk.CTkEntry(
            row, textvariable=var, placeholder_text=placeholder, corner_radius=6,
            fg_color=self.c_input, border_color=self.c_input_border, text_color=self.c_text,
            height=30, font=("Segoe UI", 11)
        )
        entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

        btn = ctk.CTkButton(
            row, text=btn_text, font=("Segoe UI", 11), fg_color=self.c_btn_sec,
            hover_color=self.c_btn_sec_h, corner_radius=6, width=110, height=30, command=cmd
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
                text=f"{len(lines)} cảnh đã nạp", text_color="#10b981", fg_color="#064e3b"
            )
        else:
            self.lbl_scenes_count.configure(
                text="0 cảnh", text_color=self.c_sub, fg_color="#1d2027"
            )

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
            self.sub_anim_var.set("Nảy chữ lên (Bounce Pop)")
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
            self.sfx_name_var.set("Whoosh (Lướt gió điện ảnh)")
            self.sfx_vol_var.set("60")
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
            self.sfx_name_var.set("Swoosh (Vút nhanh)")
            self.sfx_vol_var.set("35")
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
            self.sfx_name_var.set("Ding (Keng chuông)")
            self.sfx_vol_var.set("25")
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
            self.blur_var.set(True)
            self.smart_pacing_var.set(False)
            self.ducking_var.set(True)
            self.fade_var.set(True)
            self.cta_sub_var.set(False)
            self._select_all_motions(False)
            self._log("[Preset] Đã áp dụng: Tối giản nhanh (16:9).")

    def _browse_audio(self):
        files = filedialog.askopenfilenames(
            title="Chọn một hoặc nhiều file voice audio",
            initialdir=self.default_init_dir,
            filetypes=[("Audio Files", "*.wav;*.mp3;*.m4a;*.aac;*.flac"), ("All Files", "*.*")]
        )
        if files:
            self.audio_files_var.set("; ".join(files))
            self._auto_detect_from_folder(os.path.dirname(files[0]))

    def _browse_srt(self):
        f = filedialog.askopenfilename(
            title="Chọn file phụ đề SRT",
            initialdir=self.default_init_dir,
            filetypes=[("SRT Subtitles", "*.srt"), ("All Files", "*.*")]
        )
        if f:
            self.srt_file_var.set(f)
            self._auto_detect_from_folder(os.path.dirname(f))

    def _browse_scenes_file(self):
        f = filedialog.askopenfilename(
            title="Chọn file kịch bản (.txt, .csv)",
            initialdir=self.default_init_dir,
            filetypes=[("Text Files", "*.txt"), ("CSV Files", "*.csv"), ("All Files", "*.*")]
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

    def _browse_bgm(self):
        files = filedialog.askopenfilenames(
            title="Chọn file nhạc nền (BGM)",
            initialdir=self.default_init_dir,
            filetypes=[("Audio Files", "*.wav;*.mp3;*.m4a;*.aac;*.flac"), ("All Files", "*.*")]
        )
        if files:
            self.bgm_files_var.set("; ".join(files))

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
        exe = get_capcut_exe_path()
        if exe and os.path.exists(exe):
            self._log(f"[Action] Khởi chạy CapCut: {exe}")
            subprocess.Popen([exe])
        else:
            messagebox.showinfo("Khởi chạy CapCut", "Không tìm thấy CapCut.exe tự động. Vui lòng mở CapCut từ Desktop của bạn.")

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
        btn_row.pack(pady=4)

        def _open_f():
            if os.path.exists(data['draft_dir']):
                os.startfile(data['draft_dir'])
            dlg.destroy()

        def _open_cc():
            exe = get_capcut_exe_path()
            if exe and os.path.exists(exe):
                subprocess.Popen([exe])
            else:
                os.startfile(data['draft_dir'])
            dlg.destroy()

        ctk.CTkButton(btn_row, text="Mở thư mục Draft", fg_color=self.c_btn_sec, hover_color=self.c_btn_sec_h, corner_radius=6, width=140, height=34, command=_open_f).pack(side="left", padx=6)
        ctk.CTkButton(btn_row, text="Mở CapCut ngay", fg_color=self.c_accent, hover_color=self.c_accent_hover, corner_radius=6, width=140, height=34, command=_open_cc).pack(side="left", padx=6)

    # ------------------------------------------------------------------
    # CORE PROCESS EXECUTION
    # ------------------------------------------------------------------
    def _start_processing(self):
        if self.is_running:
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

        self.is_running = True
        self.btn_run.configure(state="disabled", text="Đang xử lý tiến trình...")
        self.progress_bar.set(0)
        self.console_textbox.delete("1.0", "end")

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
                self.cta_sub_var.get(), sub_col, sub_anim, sub_size, sub_pos,
                self.watermark_var.get(), self.subtitles_var.get()
            ),
            daemon=True
        ).start()

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
        enable_cta, sub_col, sub_anim, sub_size, sub_pos,
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
                progress_callback=on_progress
            )
            self.msg_queue.put(('success', res))
        except Exception as e:
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
                    self.last_draft_dir = data['draft_dir']
                    self.lbl_status.configure(text="Tạo project CapCut thành công!")
                    self.progress_bar.set(1.0)
                    self._log("\n" + "=" * 50)
                    self._log(f"TẠO DỰ ÁN CAPCUT THÀNH CÔNG")
                    self._log(f"  Dự án:      {data['draft_name']}")
                    self._log(f"  Tổng cảnh:  {data['total_scenes']} cảnh")
                    self._log(f"  Thời lượng: {data['duration_seconds']:.2f}s ({(data['duration_seconds']/60):.2f} phút)")
                    self._log(f"  Thư mục:    {data['draft_dir']}")
                    self._log("=" * 50)
                    self._show_completed_dialog(data)

                elif msg_type == 'error':
                    self.is_running = False
                    self.btn_run.configure(state="normal", text="Bắt đầu tạo dự án CapCut")
                    self.lbl_status.configure(text=f"Lỗi: {data}")
                    self._log(f"\n[Error] ĐÃ XẢY RA LỖI: {data}")
                    messagebox.showerror("Lỗi Quá Trình", f"Đã xảy ra lỗi:\n{data}")
        except queue.Empty:
            pass

        self.after(100, self._process_queue)


def main():
    app = AutoCapCutApp()
    app.mainloop()


if __name__ == '__main__':
    main()
