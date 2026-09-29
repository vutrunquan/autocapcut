"""
Desktop GUI for AutoCapCut Pro.
Built with CustomTkinter for native rounded contours, soothing Obsidian Navy palette,
balanced visual hierarchy, and an extensive suite of easy-to-use pro video editing features.
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
    "• Tool sẽ tự động căn thời gian media theo đúng giọng đọc của dòng đó.\n"
    "• Bạn có thể nhấn 'Đọc File .txt' để nạp file hoặc dán trực tiếp."
)


class AutoCapCutApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")

        self.title("AutoCapCut Pro - Tự Động Khớp Media & Âm Thanh Chuyên Nghiệp")
        self.geometry("1120x920")
        self.minsize(980, 760)

        # ------------------------------------------------------------------
        # HARMONIOUS COLOR SYSTEM (Obsidian Navy & Indigo)
        # ------------------------------------------------------------------
        self.c_bg = "#0b0f19"         # Deep Obsidian (Eye-friendly)
        self.c_card = "#161f30"       # Dark Slate Card
        self.c_card_border = "#22314a"# Subtle card border
        self.c_input = "#0d131f"      # Input field background
        self.c_input_border = "#2a3b59"
        self.c_text = "#f8fafc"       # Pure soft white
        self.c_sub = "#94a3b8"        # Slate 400 muted text
        
        # Accents
        self.c_indigo = "#4f46e5"     # Primary action
        self.c_indigo_hover = "#4338ca"
        self.c_amber = "#d97706"      # Audio button
        self.c_amber_hover = "#b45309"
        self.c_sky = "#0284c7"        # SRT button
        self.c_sky_hover = "#0369a1"
        self.c_emerald = "#059669"    # Media button
        self.c_emerald_hover = "#047857"
        self.c_purple = "#7c3aed"     # Script tools
        self.c_purple_hover = "#6d28d9"
        self.c_rose = "#e11d48"       # BGM & Delete
        self.c_btn_sec = "#1e293b"    # Secondary buttons
        self.c_btn_sec_h = "#334155"

        self.configure(fg_color=self.c_bg)

        # ------------------------------------------------------------------
        # STATE VARIABLES
        # ------------------------------------------------------------------
        # Card 1: Data inputs
        self.audio_files_var = tk.StringVar()
        self.srt_file_var = tk.StringVar()
        self.media_folder_var = tk.StringVar()
        self.bgm_files_var = tk.StringVar()
        self.bgm_vol_var = tk.StringVar(value="15")
        self.capcut_name_var = tk.StringVar(value=f"AutoCapCut_{time.strftime('%Y%m%d_%H%M')}")
        self.draft_root_var = tk.StringVar(value=get_default_capcut_draft_path() or "")

        # Presets & Format
        self.preset_var = tk.StringVar(value="⚙️ Tùy Chỉnh Thủ Công (Custom)")
        self.aspect_ratio_var = tk.StringVar(value="16:9 (Ngang - YouTube, Facebook)")

        # Card 2: Config, Subtitles & Transitions
        self.subtitles_var = tk.BooleanVar(value=True)
        self.subtitle_color_var = tk.StringVar(value="Vàng Nổi Bật (TikTok / Viral)")
        self.sub_anim_var = tk.StringVar(value="Nảy chữ lên (Bounce Pop)")
        self.sub_size_var = tk.StringVar(value="8.5")
        self.sub_pos_var = tk.StringVar(value="Dưới cùng (Chuẩn Shorts/Reels)")
        self.watermark_var = tk.BooleanVar(value=True)
        self.sort_mode_var = tk.StringVar(value="Sắp xếp media theo ABC (Số tự nhiên)")

        # Transitions
        self.transition_var = tk.StringVar(value="Không transition")
        self.trans_dur_var = tk.StringVar(value="0.5")
        self.trans_mode_var = tk.StringVar(value="Tất cả phân cảnh (All)")

        # Card 3: Clip In-Animation, Scene Effects, Filters & Audio
        self.clip_intro_var = tk.StringVar(value="Không animation")
        self.clip_intro_dur_var = tk.StringVar(value="0.8")
        self.clip_intro_mode_var = tk.StringVar(value="Tất cả phân cảnh (All)")

        self.video_effect_var = tk.StringVar(value="Không dùng hiệu ứng")
        self.video_effect_scope_var = tk.StringVar(value="Tất cả phân cảnh (All)")

        self.filter_var = tk.StringVar(value="Không dùng filter")
        self.filter_intensity_var = tk.StringVar(value="60")

        self.sfx_var = tk.BooleanVar(value=True)
        self.sfx_name_var = tk.StringVar(value="Ngẫu nhiên phối hợp (Random)")
        self.sfx_vol_var = tk.StringVar(value="50")
        self.ducking_var = tk.BooleanVar(value=True)
        self.fade_var = tk.BooleanVar(value=True)
        self.blur_var = tk.BooleanVar(value=True)
        self.cta_sub_var = tk.BooleanVar(value=True)

        # Card 4: Camera Motion & Ken Burns
        self.camera_motion_var = tk.StringVar(value="Smart Pacing AI (Tự phân tích nhịp câu)")
        self.zoom_scale_var = tk.StringVar(value="112")
        self.smart_pacing_var = tk.BooleanVar(value=True)

        # Card 4: Motions
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
        # 1. TOP HEADER
        header_frame = ctk.CTkFrame(self, fg_color="transparent", height=60)
        header_frame.pack(fill="x", padx=24, pady=(16, 12))

        # Brand Title & Icon
        title_box = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_box.pack(side="left")

        app_icon = ctk.CTkLabel(title_box, text="⚡", font=("Segoe UI Emoji", 26))
        app_icon.pack(side="left", padx=(0, 10))

        text_sub_box = ctk.CTkFrame(title_box, fg_color="transparent")
        text_sub_box.pack(side="left")

        lbl_title = ctk.CTkLabel(
            text_sub_box, text="AutoCapCut Pro v2.5", font=("Segoe UI", 18, "bold"),
            text_color="#ffffff"
        )
        lbl_title.pack(anchor="w")

        lbl_sub = ctk.CTkLabel(
            text_sub_box, text="Hệ thống tự động biên tập video AI chuyên nghiệp cho CapCut PC",
            font=("Segoe UI", 11), text_color=self.c_sub
        )
        lbl_sub.pack(anchor="w")

        # Top Toolbar Actions
        actions_box = ctk.CTkFrame(header_frame, fg_color="transparent")
        actions_box.pack(side="right")

        btn_auto = ctk.CTkButton(
            actions_box, text="✨ Tự Động Điền", font=("Segoe UI", 12, "bold"),
            fg_color=self.c_btn_sec, hover_color=self.c_btn_sec_h, text_color=self.c_text,
            corner_radius=8, width=125, height=34, command=self._auto_detect_sample_files
        )
        btn_auto.pack(side="left", padx=4)

        btn_cc = ctk.CTkButton(
            actions_box, text="🎬 Mở CapCut", font=("Segoe UI", 12, "bold"),
            fg_color=self.c_btn_sec, hover_color=self.c_btn_sec_h, text_color=self.c_text,
            corner_radius=8, width=110, height=34, command=self._launch_capcut
        )
        btn_cc.pack(side="left", padx=4)

        btn_settings = ctk.CTkButton(
            actions_box, text="⚙️ Cài Đặt", font=("Segoe UI", 12, "bold"),
            fg_color=self.c_btn_sec, hover_color=self.c_btn_sec_h, text_color=self.c_text,
            corner_radius=8, width=90, height=34, command=self._open_settings_dialog
        )
        btn_settings.pack(side="left", padx=4)

        # 2. MAIN SCROLLABLE CONTENT (Card containers)
        self.scroll_frame = ctk.CTkScrollableFrame(
            self, fg_color="transparent", corner_radius=14
        )
        self.scroll_frame.pack(fill="both", expand=True, padx=20, pady=(0, 10))

        content = self.scroll_frame

        # ------------------------------------------------------------------
        # CARD 1: 📁  1. NGUỒN DỮ LIỆU ĐẦU VÀO
        # ------------------------------------------------------------------
        card_data = self._create_card(content, title="📁  1. NGUỒN DỮ LIỆU ĐẦU VÀO")

        # Voice Audio
        self._add_row(
            card_data, label="File Voice (Âm thanh):", var=self.audio_files_var,
            placeholder="Chọn 1 hoặc nhiều file audio (.wav, .mp3, .m4a)...",
            btn_text="🎵 Chọn Audio", btn_color=self.c_amber, btn_hover=self.c_amber_hover,
            cmd=self._browse_audio
        )

        # SRT File
        self._add_row(
            card_data, label="File Phụ Đề (.srt):", var=self.srt_file_var,
            placeholder="Chọn file phụ đề SRT khớp với giọng đọc...",
            btn_text="📄 Chọn SRT", btn_color=self.c_sky, btn_hover=self.c_sky_hover,
            cmd=self._browse_srt
        )

        # Scenes Textarea
        sc_container = ctk.CTkFrame(card_data, fg_color="transparent")
        sc_container.pack(fill="x", pady=(8, 10))

        sc_bar = ctk.CTkFrame(sc_container, fg_color="transparent")
        sc_bar.pack(fill="x", pady=(0, 6))

        sc_lbl = ctk.CTkLabel(
            sc_bar, text="Kịch Bản Phân Cảnh (Mỗi dòng 1 ảnh/video):",
            font=("Segoe UI", 12, "bold"), text_color="#ffffff"
        )
        sc_lbl.pack(side="left")

        # Line counter pill badge
        self.lbl_scenes_count = ctk.CTkLabel(
            sc_bar, text="0 dòng", font=("Segoe UI", 10, "bold"),
            fg_color="#1e293b", text_color=self.c_sub, corner_radius=12, padx=10, pady=2
        )
        self.lbl_scenes_count.pack(side="left", padx=8)

        sc_tools = ctk.CTkFrame(sc_bar, fg_color="transparent")
        sc_tools.pack(side="right")

        btn_paste = ctk.CTkButton(
            sc_tools, text="📋 Dán", width=55, height=28, corner_radius=6,
            fg_color=self.c_btn_sec, hover_color=self.c_btn_sec_h, font=("Segoe UI", 11),
            command=self._paste_scenes
        )
        btn_paste.pack(side="left", padx=2)

        btn_copy = ctk.CTkButton(
            sc_tools, text="📄 Copy", width=55, height=28, corner_radius=6,
            fg_color=self.c_btn_sec, hover_color=self.c_btn_sec_h, font=("Segoe UI", 11),
            command=self._copy_scenes
        )
        btn_copy.pack(side="left", padx=2)

        btn_split = ctk.CTkButton(
            sc_tools, text="✂️ Tách Câu", width=80, height=28, corner_radius=6,
            fg_color=self.c_btn_sec, hover_color=self.c_btn_sec_h, font=("Segoe UI", 11),
            command=self._split_scenes_into_sentences
        )
        btn_split.pack(side="left", padx=2)

        btn_clean = ctk.CTkButton(
            sc_tools, text="🧹 Dọn Dòng", width=80, height=28, corner_radius=6,
            fg_color=self.c_btn_sec, hover_color=self.c_btn_sec_h, font=("Segoe UI", 11),
            command=self._clean_empty_lines
        )
        btn_clean.pack(side="left", padx=2)

        btn_load = ctk.CTkButton(
            sc_tools, text="📂 Đọc File .txt", width=100, height=28, corner_radius=6,
            fg_color=self.c_purple, hover_color=self.c_purple_hover, font=("Segoe UI", 11, "bold"),
            command=self._browse_scenes_file
        )
        btn_load.pack(side="left", padx=2)

        btn_clear_sc = ctk.CTkButton(
            sc_tools, text="✕", width=30, height=28, corner_radius=6,
            fg_color="#334155", hover_color="#475569", font=("Segoe UI", 11, "bold"),
            command=self._clear_scenes
        )
        btn_clear_sc.pack(side="left", padx=(2, 0))

        # Modern Textbox
        self.scenes_textbox = ctk.CTkTextbox(
            sc_container, height=110, corner_radius=10,
            fg_color=self.c_input, border_color=self.c_input_border, border_width=1,
            text_color=self.c_text, font=("Segoe UI", 12)
        )
        self.scenes_textbox.pack(fill="x")
        self.scenes_textbox.insert("1.0", SCENES_PLACEHOLDER)
        self.scenes_textbox.bind("<FocusIn>", self._on_scenes_focus_in)
        self.scenes_textbox.bind("<FocusOut>", self._on_scenes_focus_out)
        self.scenes_textbox.bind("<KeyRelease>", self._update_scenes_count)

        # Media Folder
        self._add_row(
            card_data, label="Thư Mục Chứa Media:", var=self.media_folder_var,
            placeholder="Thư mục chứa ảnh hoặc video (001.jpg, 002.jpg...)...",
            btn_text="📁 Chọn Thư Mục", btn_color=self.c_emerald, btn_hover=self.c_emerald_hover,
            cmd=self._browse_media_folder
        )

        # BGM (Nhạc Nền)
        bgm_row = ctk.CTkFrame(card_data, fg_color="transparent")
        bgm_row.pack(fill="x", pady=4)

        lbl_bgm = ctk.CTkLabel(
            bgm_row, text="Nhạc Nền (BGM - Tùy chọn):", font=("Segoe UI", 12),
            text_color=self.c_text, width=190, anchor="w"
        )
        lbl_bgm.pack(side="left")

        e_bgm = ctk.CTkEntry(
            bgm_row, textvariable=self.bgm_files_var, placeholder_text="Có thể chọn 1 hoặc nhiều file nhạc nền...",
            corner_radius=8, fg_color=self.c_input, border_color=self.c_input_border, text_color=self.c_text,
            height=34
        )
        e_bgm.pack(side="left", fill="x", expand=True, padx=(0, 6))

        # BGM Volume
        ctk.CTkLabel(bgm_row, text="Âm lượng:", font=("Segoe UI", 11), text_color=self.c_sub).pack(side="left", padx=(0, 2))
        ctk.CTkEntry(
            bgm_row, textvariable=self.bgm_vol_var, width=38, height=34, corner_radius=8,
            fg_color=self.c_input, border_color=self.c_input_border, justify="center"
        ).pack(side="left", padx=(0, 2))
        ctk.CTkLabel(bgm_row, text="%", font=("Segoe UI", 11), text_color=self.c_sub).pack(side="left", padx=(0, 6))

        btn_bgm_clear = ctk.CTkButton(
            bgm_row, text="✕ Xóa", width=60, height=34, corner_radius=8,
            fg_color="#334155", hover_color="#475569", font=("Segoe UI", 11),
            command=lambda: self.bgm_files_var.set("")
        )
        btn_bgm_clear.pack(side="left", padx=(0, 6))

        btn_bgm = ctk.CTkButton(
            bgm_row, text="🎵 Chọn BGM", width=115, height=34, corner_radius=8,
            fg_color=self.c_btn_sec, hover_color=self.c_btn_sec_h, font=("Segoe UI", 11, "bold"),
            command=self._browse_bgm
        )
        btn_bgm.pack(side="right")
        btn_bgm.pack(side="right")

        # CapCut Name
        name_row = ctk.CTkFrame(card_data, fg_color="transparent")
        name_row.pack(fill="x", pady=4)

        lbl_name = ctk.CTkLabel(
            name_row, text="Tên Dự Án CapCut:", font=("Segoe UI", 12),
            text_color=self.c_text, width=190, anchor="w"
        )
        lbl_name.pack(side="left")

        e_name = ctk.CTkEntry(
            name_row, textvariable=self.capcut_name_var, corner_radius=8,
            fg_color=self.c_input, border_color=self.c_input_border, text_color=self.c_text,
            height=34
        )
        e_name.pack(side="left", fill="x", expand=True)

        # ------------------------------------------------------------------
        # PRESET BANNER (1-CLICK QUICK SETUP)
        # ------------------------------------------------------------------
        preset_card = ctk.CTkFrame(content, fg_color="#131c2e", corner_radius=12, border_color="#2b3d5b", border_width=1)
        preset_card.pack(fill="x", pady=(0, 14), padx=2, ipady=4)

        p_row = ctk.CTkFrame(preset_card, fg_color="transparent")
        p_row.pack(fill="x", padx=14, pady=6)

        p_icon_lbl = ctk.CTkLabel(p_row, text="🎯  BỘ THIẾT LẬP NHANH (1-CLICK PRO PRESETS):", font=("Segoe UI", 12, "bold"), text_color="#ffffff")
        p_icon_lbl.pack(side="left", padx=(0, 12))

        preset_opts = [
            "⚙️ Tùy Chỉnh Thủ Công (Custom)",
            "🔥 TikTok / Reels / Shorts Siêu Cuốn (9:16, Nhanh, SFX, Chữ Vàng)",
            "🎬 YouTube Kể Chuyện Điện Ảnh (16:9, Tông Ấm, Hạt Phim, Chữ Trắng)",
            "💼 Tin Tức & Phân Tích Tài Chính (16:9, Chữ Xanh Lá, Fade Wipe)",
            "⚡ Tối Giản Siêu Tốc (16:9, Không SFX, Không Filter)"
        ]
        self.preset_combo = ctk.CTkComboBox(
            p_row, variable=self.preset_var, values=preset_opts, width=480, height=34, corner_radius=8,
            fg_color=self.c_input, border_color=self.c_indigo, button_color=self.c_indigo,
            command=self._apply_preset
        )
        self.preset_combo.pack(side="left", fill="x", expand=True)

        # ------------------------------------------------------------------
        # CARD 2: ⚙️  2. PHỤ ĐỀ, CHUYỂN CẢNH & KHUNG HÌNH (SUBTITLES & TRANSITIONS)
        # ------------------------------------------------------------------
        card_cfg = self._create_card(content, title="⚙️  2. PHỤ ĐỀ, CHUYỂN CẢNH & KHUNG HÌNH")

        cfg_grid = ctk.CTkFrame(card_cfg, fg_color="transparent")
        cfg_grid.pack(fill="x")

        # Left Column: Subtitles & Watermark
        col_cb = ctk.CTkFrame(cfg_grid, fg_color="transparent")
        col_cb.pack(side="left", fill="both", expand=True, padx=(0, 10))

        cb1 = ctk.CTkCheckBox(
            col_cb, text=" Tự động chèn phụ đề SRT vào video",
            variable=self.subtitles_var, font=("Segoe UI", 12, "bold"), corner_radius=6,
            fg_color=self.c_indigo, hover_color=self.c_indigo_hover, text_color=self.c_text
        )
        cb1.pack(anchor="w", pady=(0, 4))

        # Subtitle Color Palette & Font Size
        sub_style_row = ctk.CTkFrame(col_cb, fg_color="transparent")
        sub_style_row.pack(fill="x", pady=2)
        ctk.CTkLabel(sub_style_row, text="Màu chữ:", font=("Segoe UI", 11), text_color=self.c_sub, width=60, anchor="w").pack(side="left")
        sub_col_opts = [
            "Vàng Nổi Bật (TikTok / Viral)",
            "Trắng Truyền Thống (Classic White)",
            "Xanh Công Nghệ (Cyan Modern)",
            "Xanh Lá Tài Chính (Finance Green)",
            "Đỏ Ruby (Dramatic Red)",
            "Tím Neon (Neon Purple)"
        ]
        ctk.CTkComboBox(
            sub_style_row, variable=self.subtitle_color_var, values=sub_col_opts, width=200, height=28, corner_radius=6,
            fg_color=self.c_input, border_color=self.c_input_border
        ).pack(side="left", padx=(0, 6))

        ctk.CTkLabel(sub_style_row, text="Cỡ:", font=("Segoe UI", 11), text_color=self.c_sub).pack(side="left", padx=(2, 2))
        ctk.CTkEntry(
            sub_style_row, textvariable=self.sub_size_var, width=38, height=28, corner_radius=6,
            fg_color=self.c_input, border_color=self.c_input_border, justify="center"
        ).pack(side="left")

        # Subtitle In-Animation & Position
        sub_anim_row = ctk.CTkFrame(col_cb, fg_color="transparent")
        sub_anim_row.pack(fill="x", pady=2)
        ctk.CTkLabel(sub_anim_row, text="Hiệu ứng:", font=("Segoe UI", 11), text_color=self.c_sub, width=60, anchor="w").pack(side="left")
        sub_anim_opts = [
            "Nảy chữ lên (Bounce Pop)",
            "Chạy từng chữ (Karaoke Reveal)",
            "Nhịp điệu vui nhộn (Playful Bounce)",
            "Trượt mượt lên (Slide Up)",
            "Quét từ trái sang (Slide Right)",
            "Tĩnh (Không animation)"
        ]
        ctk.CTkComboBox(
            sub_anim_row, variable=self.sub_anim_var, values=sub_anim_opts, width=200, height=28, corner_radius=6,
            fg_color=self.c_input, border_color=self.c_input_border
        ).pack(side="left", padx=(0, 6))

        sub_pos_opts = [
            "Dưới cùng (Chuẩn Shorts/Reels)",
            "Chính giữa màn hình",
            "Phía trên cùng"
        ]
        ctk.CTkComboBox(
            sub_anim_row, variable=self.sub_pos_var, values=sub_pos_opts, width=150, height=28, corner_radius=6,
            fg_color=self.c_input, border_color=self.c_input_border
        ).pack(side="left")

        cb2 = ctk.CTkCheckBox(
            col_cb, text=" Xóa watermark Gemini AI (Reverse Alpha Blending - Lossless)",
            variable=self.watermark_var, font=("Segoe UI", 11), corner_radius=6,
            fg_color=self.c_indigo, hover_color=self.c_indigo_hover, text_color=self.c_text
        )
        cb2.pack(anchor="w", pady=(6, 2))

        # Right Column: Format & Transitions
        col_dd = ctk.CTkFrame(cfg_grid, fg_color="transparent")
        col_dd.pack(side="right", fill="both", expand=True, padx=(10, 0))

        # Tỉ lệ khung hình (Aspect Ratio) & Sắp xếp
        ar_row = ctk.CTkFrame(col_dd, fg_color="transparent")
        ar_row.pack(fill="x", pady=2)
        ctk.CTkLabel(ar_row, text="Tỉ lệ & Sắp xếp:", font=("Segoe UI", 11), text_color=self.c_sub, width=95, anchor="w").pack(side="left")
        ar_opts = [
            "16:9 (Ngang - YouTube, Facebook)",
            "9:16 (Dọc - TikTok, Reels, Shorts)",
            "1:1 (Vuông - Instagram, Post)"
        ]
        ctk.CTkComboBox(
            ar_row, variable=self.aspect_ratio_var, values=ar_opts, width=175, height=28, corner_radius=6,
            fg_color=self.c_input, border_color=self.c_input_border, button_color=self.c_btn_sec
        ).pack(side="left", padx=(0, 6))

        sort_opts = [
            "Sắp xếp media theo ABC (Số tự nhiên)",
            "Sắp xếp media theo thời gian Cũ đến Mới",
            "Sắp xếp media theo thời gian Mới đến Cũ"
        ]
        ctk.CTkComboBox(
            ar_row, variable=self.sort_mode_var, values=sort_opts, width=195, height=28, corner_radius=6,
            fg_color=self.c_input, border_color=self.c_input_border, button_color=self.c_btn_sec
        ).pack(side="left")

        # Transition Type & Duration
        tr_row = ctk.CTkFrame(col_dd, fg_color="transparent")
        tr_row.pack(fill="x", pady=2)
        ctk.CTkLabel(tr_row, text="Chuyển cảnh:", font=("Segoe UI", 11), text_color=self.c_sub, width=95, anchor="w").pack(side="left")
        trans_opts = [
            "Không transition",
            "Ngẫu nhiên (Random)",
            "Mờ chồng (Dissolve)",
            "Mờ đen (Black Fade)",
            "Chớp trắng (White Flash)",
            "Gạt sang trái (Swipe Left)",
            "Trượt góc (Corner Slide)",
            "Lật thu phóng (Flip Zoom)",
            "Thu phóng nhanh (Zoom)",
            "Nhiễu sóng (Signal Glitch)",
            "Rơi trượt (Slide Drop)",
            "Trượt giao diện (Slide Interface)",
            "Búng zoom (Snap Zoom)",
            "Vệt sáng quét (Light Wipe)"
        ]
        ctk.CTkComboBox(
            tr_row, variable=self.transition_var, values=trans_opts, width=225, height=28, corner_radius=6,
            fg_color=self.c_input, border_color=self.c_input_border, button_color=self.c_btn_sec
        ).pack(side="left", padx=(0, 6))

        ctk.CTkLabel(tr_row, text="Thời lượng:", font=("Segoe UI", 11), text_color=self.c_sub).pack(side="left", padx=(2, 2))
        ctk.CTkEntry(
            tr_row, textvariable=self.trans_dur_var, width=38, height=28, corner_radius=6,
            fg_color=self.c_input, border_color=self.c_input_border, justify="center"
        ).pack(side="left")
        ctk.CTkLabel(tr_row, text="s", font=("Segoe UI", 11), text_color=self.c_sub).pack(side="left", padx=(2, 0))

        # Transition Mode
        tr_mode_row = ctk.CTkFrame(col_dd, fg_color="transparent")
        tr_mode_row.pack(fill="x", pady=2)
        ctk.CTkLabel(tr_mode_row, text="Áp dụng chuyển cảnh:", font=("Segoe UI", 11), text_color=self.c_sub, width=125, anchor="w").pack(side="left")
        trans_mode_opts = [
            "Tất cả phân cảnh (All)",
            "Ngẫu nhiên đổi hiệu ứng (Random)",
            "Xen kẽ các cảnh (Alternate)"
        ]
        ctk.CTkComboBox(
            tr_mode_row, variable=self.trans_mode_var, values=trans_mode_opts, width=245, height=28, corner_radius=6,
            fg_color=self.c_input, border_color=self.c_input_border
        ).pack(side="left")

        # ------------------------------------------------------------------
        # CARD 3: ✨  3. HIỆU ỨNG CAPCUT, HOẠT ẢNH & BỘ LỌC ĐIỆN ẢNH (EFFECTS & FILTERS)
        # ------------------------------------------------------------------
        card_pro = self._create_card(content, title="✨  3. HIỆU ỨNG CAPCUT, HOẠT ẢNH & BỘ LỌC ĐIỆN ẢNH")

        # Row 1: Clip In-Animation (Intro)
        r_intro = ctk.CTkFrame(card_pro, fg_color="transparent")
        r_intro.pack(fill="x", pady=3)
        ctk.CTkLabel(r_intro, text="Hoạt ảnh mở đầu (Intro):", font=("Segoe UI", 12), text_color=self.c_text, width=180, anchor="w").pack(side="left")
        intro_opts = [
            "Không animation",
            "Ngẫu nhiên (Random)",
            "Thu phóng vào (Zoom In)",
            "Phóng to năng động (Dynamic Zoom In)",
            "Thu nhỏ năng động (Dynamic Zoom Out)",
            "Mờ dần xuất hiện (Fade In)",
            "Mờ ảo tỏ dần (Blur Fade In)",
            "Lắc ngang nảy (Horizontal Shake)",
            "Lắc dọc nảy (Vertical Shake)",
            "Trượt từ dưới lên (Slide Up)",
            "Trượt từ trên xuống (Slide Down)",
            "Trượt từ trái sang (Slide Right)",
            "Trượt từ phải sang (Slide Left)",
            "Xoay mở màn (Spin Open)"
        ]
        ctk.CTkComboBox(
            r_intro, variable=self.clip_intro_var, values=intro_opts, width=260, height=28, corner_radius=6,
            fg_color=self.c_input, border_color=self.c_input_border
        ).pack(side="left", padx=(0, 10))

        ctk.CTkLabel(r_intro, text="Thời lượng:", font=("Segoe UI", 11), text_color=self.c_sub).pack(side="left", padx=(0, 2))
        ctk.CTkEntry(
            r_intro, textvariable=self.clip_intro_dur_var, width=40, height=28, corner_radius=6,
            fg_color=self.c_input, border_color=self.c_input_border, justify="center"
        ).pack(side="left")
        ctk.CTkLabel(r_intro, text="s", font=("Segoe UI", 11), text_color=self.c_sub).pack(side="left", padx=(2, 10))

        intro_mode_opts = ["Tất cả phân cảnh (All)", "Ngẫu nhiên xen kẽ (Random)", "Chỉ cảnh đầu tiên (Intro)"]
        ctk.CTkComboBox(
            r_intro, variable=self.clip_intro_mode_var, values=intro_mode_opts, width=200, height=28, corner_radius=6,
            fg_color=self.c_input, border_color=self.c_input_border
        ).pack(side="left")

        # Row 2: Video Scene Effect
        r_eff = ctk.CTkFrame(card_pro, fg_color="transparent")
        r_eff.pack(fill="x", pady=3)
        ctk.CTkLabel(r_eff, text="Hiệu ứng video (Effect):", font=("Segoe UI", 12), text_color=self.c_text, width=180, anchor="w").pack(side="left")
        effect_opts = [
            "Không dùng hiệu ứng",
            "Ngẫu nhiên (Random)",
            "Rung lắc tiêu điểm (Focus Shake)",
            "Rung tách màu RGB (RGB Shake)",
            "Nhiễu hạt Pixel (Pixel Glitch)",
            "Giật sóng mở màn (Glitch Intro)",
            "Hào quang nhấp nháy (Bouncing Glow)",
            "Chớp sáng kịch tính (Flash)",
            "Ánh đèn Neon (Neon Flash)",
            "Chớp phim cổ điển (Vintage Flash)"
        ]
        ctk.CTkComboBox(
            r_eff, variable=self.video_effect_var, values=effect_opts, width=260, height=28, corner_radius=6,
            fg_color=self.c_input, border_color=self.c_input_border
        ).pack(side="left", padx=(0, 10))

        ctk.CTkLabel(r_eff, text="Phạm vi:", font=("Segoe UI", 11), text_color=self.c_sub).pack(side="left", padx=(0, 6))
        effect_scope_opts = ["Tất cả phân cảnh (All)", "Ngẫu nhiên một số cảnh (Random)", "Chỉ cảnh mở đầu & kết thúc"]
        ctk.CTkComboBox(
            r_eff, variable=self.video_effect_scope_var, values=effect_scope_opts, width=250, height=28, corner_radius=6,
            fg_color=self.c_input, border_color=self.c_input_border
        ).pack(side="left")

        # Row 3: Cinematic Filter & Intensity
        r_filt = ctk.CTkFrame(card_pro, fg_color="transparent")
        r_filt.pack(fill="x", pady=3)
        ctk.CTkLabel(r_filt, text="Bộ lọc màu (Filter):", font=("Segoe UI", 12), text_color=self.c_text, width=180, anchor="w").pack(side="left")
        filt_opts = [
            "Không dùng filter",
            "Soft Grain (Hạt phim điện ảnh)",
            "Vintage 1980 (Tông màu cổ điển)",
            "VHS Retro (Băng từ VHS)",
            "Peach Fuzz (Tông ấm điện ảnh)",
            "Lover Blue (Tông lạnh điện ảnh)",
            "BW Retro (Trắng đen cổ điển)"
        ]
        ctk.CTkComboBox(
            r_filt, variable=self.filter_var, values=filt_opts, width=260, height=28, corner_radius=6,
            fg_color=self.c_input, border_color=self.c_input_border
        ).pack(side="left", padx=(0, 10))

        ctk.CTkLabel(r_filt, text="Độ đậm:", font=("Segoe UI", 11), text_color=self.c_sub).pack(side="left", padx=(0, 2))
        ctk.CTkEntry(
            r_filt, textvariable=self.filter_intensity_var, width=40, height=28, corner_radius=6,
            fg_color=self.c_input, border_color=self.c_input_border, justify="center"
        ).pack(side="left")
        ctk.CTkLabel(r_filt, text="%", font=("Segoe UI", 11), text_color=self.c_sub).pack(side="left", padx=(2, 10))

        # Row 4: SFX Suite
        r_sfx = ctk.CTkFrame(card_pro, fg_color="transparent")
        r_sfx.pack(fill="x", pady=4)
        ctk.CTkCheckBox(
            r_sfx, text=" Âm thanh chuyển cảnh (SFX):",
            variable=self.sfx_var, font=("Segoe UI", 12), corner_radius=6,
            fg_color=self.c_indigo, hover_color=self.c_indigo_hover, text_color=self.c_text, width=180
        ).pack(side="left")

        sfx_opts = [
            "Ngẫu nhiên phối hợp (Random)",
            "Whoosh (Lướt gió điện ảnh)",
            "Swoosh (Vút nhanh)",
            "Pop (Nảy vui nhộn)",
            "Ding (Keng chuông)"
        ]
        ctk.CTkComboBox(
            r_sfx, variable=self.sfx_name_var, values=sfx_opts, width=260, height=28, corner_radius=6,
            fg_color=self.c_input, border_color=self.c_input_border
        ).pack(side="left", padx=(0, 10))

        ctk.CTkLabel(r_sfx, text="Âm lượng:", font=("Segoe UI", 11), text_color=self.c_sub).pack(side="left", padx=(0, 2))
        ctk.CTkEntry(
            r_sfx, textvariable=self.sfx_vol_var, width=40, height=28, corner_radius=6,
            fg_color=self.c_input, border_color=self.c_input_border, justify="center"
        ).pack(side="left")
        ctk.CTkLabel(r_sfx, text="%", font=("Segoe UI", 11), text_color=self.c_sub).pack(side="left")

        # Row 5: Pro Audio & Visual Toggles (2 columns)
        r_toggles = ctk.CTkFrame(card_pro, fg_color="transparent")
        r_toggles.pack(fill="x", pady=(4, 0))

        tog_left = ctk.CTkFrame(r_toggles, fg_color="transparent")
        tog_left.pack(side="left", fill="x", expand=True)
        ctk.CTkCheckBox(
            tog_left, text=" Canvas Blur (Làm mờ nền khi ảnh không vừa khung - chống viền đen)",
            variable=self.blur_var, font=("Segoe UI", 11), corner_radius=6,
            fg_color=self.c_indigo, hover_color=self.c_indigo_hover, text_color=self.c_text
        ).pack(anchor="w", pady=2)
        ctk.CTkCheckBox(
            tog_left, text=" Audio Ducking (Tự động hạ nhạc nền khi có tiếng voice đọc)",
            variable=self.ducking_var, font=("Segoe UI", 11), corner_radius=6,
            fg_color=self.c_indigo, hover_color=self.c_indigo_hover, text_color=self.c_text
        ).pack(anchor="w", pady=2)

        tog_right = ctk.CTkFrame(r_toggles, fg_color="transparent")
        tog_right.pack(side="left", fill="x", expand=True)
        ctk.CTkCheckBox(
            tog_right, text=" Audio Fade In & Fade Out cho nhạc nền (Mở & tắt êm ái)",
            variable=self.fade_var, font=("Segoe UI", 11), corner_radius=6,
            fg_color=self.c_indigo, hover_color=self.c_indigo_hover, text_color=self.c_text
        ).pack(anchor="w", pady=2)
        ctk.CTkCheckBox(
            tog_right, text=" Chèn CTA Kêu gọi Đăng ký (Subscribe) & tiếng chuông ở cuối",
            variable=self.cta_sub_var, font=("Segoe UI", 11), corner_radius=6,
            fg_color=self.c_indigo, hover_color=self.c_indigo_hover, text_color=self.c_text
        ).pack(anchor="w", pady=2)

        # ------------------------------------------------------------------
        # CARD 4: 🎥  4. GÓC QUAY & CHUYỂN ĐỘNG CAMERA (CAMERA MOTION & KEN BURNS)
        # ------------------------------------------------------------------
        card_kf = self._create_card(content, title="🎥  4. GÓC QUAY & CHUYỂN ĐỘNG CAMERA (CAMERA MOTION & KEN BURNS)")

        cam_bar = ctk.CTkFrame(card_kf, fg_color="transparent")
        cam_bar.pack(fill="x", pady=(0, 8))

        ctk.CTkLabel(cam_bar, text="Chế độ camera:", font=("Segoe UI", 12, "bold"), text_color=self.c_text).pack(side="left", padx=(0, 8))
        cam_opts = [
            "Smart Pacing AI (Tự phân tích nhịp câu)",
            "Zoom In (Phóng to dần)",
            "Zoom Out (Thu nhỏ dần)",
            "Pan Left (Lia sang trái)",
            "Pan Right (Lia sang phải)",
            "Pan Up (Lia lên trên)",
            "Pan Down (Lia xuống dưới)",
            "Ngẫu nhiên góc quay (Dynamic Ken Burns)",
            "Cố định (Không chuyển động)"
        ]
        ctk.CTkComboBox(
            cam_bar, variable=self.camera_motion_var, values=cam_opts, width=310, height=30, corner_radius=6,
            fg_color=self.c_input, border_color=self.c_input_border
        ).pack(side="left", padx=(0, 14))

        ctk.CTkLabel(cam_bar, text="Tỷ lệ zoom:", font=("Segoe UI", 11), text_color=self.c_sub).pack(side="left", padx=(0, 4))
        ctk.CTkEntry(
            cam_bar, textvariable=self.zoom_scale_var, width=44, height=30, corner_radius=6,
            fg_color=self.c_input, border_color=self.c_input_border, justify="center"
        ).pack(side="left")
        ctk.CTkLabel(cam_bar, text="%", font=("Segoe UI", 11), text_color=self.c_sub).pack(side="left", padx=(2, 10))

        kf_tools = ctk.CTkFrame(cam_bar, fg_color="transparent")
        kf_tools.pack(side="right")
        ctk.CTkButton(
            kf_tools, text="✓ Chọn Tất Cả", width=95, height=26, corner_radius=6,
            fg_color=self.c_btn_sec, hover_color=self.c_btn_sec_h, font=("Segoe UI", 10, "bold"),
            command=lambda: self._select_all_motions(True)
        ).pack(side="left", padx=2)
        ctk.CTkButton(
            kf_tools, text="✕ Bỏ Chọn", width=75, height=26, corner_radius=6,
            fg_color=self.c_btn_sec, hover_color=self.c_btn_sec_h, font=("Segoe UI", 10),
            command=lambda: self._select_all_motions(False)
        ).pack(side="left", padx=2)

        kf_grid = ctk.CTkFrame(card_kf, fg_color="transparent")
        kf_grid.pack(fill="x")

        # Column 1
        col_k1 = ctk.CTkFrame(kf_grid, fg_color="#101726", corner_radius=10, border_color="#1f2c42", border_width=1)
        col_k1.pack(side="left", fill="both", expand=True, padx=(0, 10), pady=4, ipady=4)

        self._add_motion_zoom(col_k1, "Zoom In (Phóng to)", self.m_zoom_in_var, self.m_zoom_in_scale)
        self._add_motion_pan(col_k1, "Pan Up (Lia lên)", self.m_pan_up_var, self.m_pan_up_x, self.m_pan_up_y, self.m_pan_up_scale)
        self._add_motion_pan(col_k1, "Pan Left (Lia trái)", self.m_pan_left_var, self.m_pan_left_x, self.m_pan_left_y, self.m_pan_left_scale)

        # Column 2
        col_k2 = ctk.CTkFrame(kf_grid, fg_color="#101726", corner_radius=10, border_color="#1f2c42", border_width=1)
        col_k2.pack(side="left", fill="both", expand=True, padx=(10, 0), pady=4, ipady=4)

        self._add_motion_zoom(col_k2, "Zoom Out (Thu nhỏ)", self.m_zoom_out_var, self.m_zoom_out_scale)
        self._add_motion_pan(col_k2, "Pan Down (Lia xuống)", self.m_pan_down_var, self.m_pan_down_x, self.m_pan_down_y, self.m_pan_down_scale)
        self._add_motion_pan(col_k2, "Pan Right (Lia phải)", self.m_pan_right_var, self.m_pan_right_x, self.m_pan_right_y, self.m_pan_right_scale)

        # ------------------------------------------------------------------
        # CENTER ACTION BUTTON & PROGRESS BAR
        # ------------------------------------------------------------------
        act_box = ctk.CTkFrame(content, fg_color="transparent")
        act_box.pack(fill="x", pady=(18, 12))

        self.btn_run = ctk.CTkButton(
            act_box,
            text="🚀  TẠO PROJECT CAPCUT NGAY",
            font=("Segoe UI", 14, "bold"),
            fg_color=self.c_indigo,
            hover_color=self.c_indigo_hover,
            corner_radius=12,
            height=48,
            width=340,
            command=self._start_processing
        )
        self.btn_run.pack(anchor="center")

        # Smooth Progress Bar
        p_frame = ctk.CTkFrame(act_box, fg_color="transparent")
        p_frame.pack(fill="x", padx=10, pady=(12, 0))

        self.progress_bar = ctk.CTkProgressBar(
            p_frame, corner_radius=8, height=8, fg_color="#1e293b", progress_color=self.c_indigo
        )
        self.progress_bar.pack(fill="x")
        self.progress_bar.set(0)

        self.lbl_status = ctk.CTkLabel(
            p_frame, text="Hệ thống sẵn sàng. Nhấn nút để bắt đầu tạo project CapCut.",
            font=("Segoe UI", 11), text_color=self.c_sub
        )
        self.lbl_status.pack(anchor="w", pady=(4, 0))

        # ------------------------------------------------------------------
        # CARD 5: 📊 NHẬT KÝ TIẾN TRÌNH CHI TIẾT
        # ------------------------------------------------------------------
        card_log = self._create_card(content, title="📊  5. NHẬT KÝ TIẾN TRÌNH CHI TIẾT")

        self.console_textbox = ctk.CTkTextbox(
            card_log, height=130, corner_radius=10,
            fg_color=self.c_input, border_color=self.c_input_border, border_width=1,
            text_color="#94a3b8", font=("Consolas", 11)
        )
        self.console_textbox.pack(fill="both", expand=True)
        self._log("AutoCapCut Pro v2.5 sẵn sàng hoạt động với trọn bộ tính năng nâng cao.")
        self._log("Vui lòng nạp thông tin và nhấn 'TẠO PROJECT CAPCUT NGAY'.")

    # ------------------------------------------------------------------
    # CARD & ROW HELPERS
    # ------------------------------------------------------------------
    def _create_card(self, parent, title: str) -> ctk.CTkFrame:
        card = ctk.CTkFrame(
            parent, fg_color=self.c_card, corner_radius=14,
            border_color=self.c_card_border, border_width=1
        )
        card.pack(fill="x", pady=(0, 14), padx=4, ipadx=14, ipady=12)

        lbl = ctk.CTkLabel(
            card, text=title, font=("Segoe UI", 13, "bold"), text_color="#ffffff"
        )
        lbl.pack(anchor="w", pady=(0, 8))
        return card

    def _add_row(self, parent, label, var, placeholder, btn_text, btn_color, btn_hover, cmd):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=4)

        lbl = ctk.CTkLabel(
            row, text=label, font=("Segoe UI", 12), text_color=self.c_text, width=190, anchor="w"
        )
        lbl.pack(side="left")

        entry = ctk.CTkEntry(
            row, textvariable=var, placeholder_text=placeholder, corner_radius=8,
            fg_color=self.c_input, border_color=self.c_input_border, text_color=self.c_text,
            height=34
        )
        entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

        btn = ctk.CTkButton(
            row, text=btn_text, font=("Segoe UI", 11, "bold"), fg_color=btn_color,
            hover_color=btn_hover, corner_radius=8, width=125, height=34, command=cmd
        )
        btn.pack(side="right")

    def _add_motion_zoom(self, parent, title, var, scale_var):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=12, pady=6)

        cb = ctk.CTkCheckBox(
            row, text=f" {title}", variable=var, font=("Segoe UI", 12),
            corner_radius=6, fg_color=self.c_indigo, hover_color=self.c_indigo_hover,
            text_color=self.c_text, width=170
        )
        cb.pack(side="left")

        ctk.CTkLabel(row, text="Scale:", font=("Segoe UI", 11), text_color=self.c_sub).pack(side="left", padx=(4, 2))
        e = ctk.CTkEntry(
            row, textvariable=scale_var, width=54, height=28, corner_radius=6,
            fg_color=self.c_input, border_color=self.c_input_border, justify="center"
        )
        e.pack(side="left", padx=2)
        ctk.CTkLabel(row, text="%", font=("Segoe UI", 11), text_color=self.c_sub).pack(side="left")

    def _add_motion_pan(self, parent, title, var, x_var, y_var, scale_var):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=12, pady=6)

        cb = ctk.CTkCheckBox(
            row, text=f" {title}", variable=var, font=("Segoe UI", 12),
            corner_radius=6, fg_color=self.c_indigo, hover_color=self.c_indigo_hover,
            text_color=self.c_text, width=170
        )
        cb.pack(side="left")

        # X
        ctk.CTkLabel(row, text="X:", font=("Segoe UI", 11), text_color=self.c_sub).pack(side="left", padx=(2, 2))
        e_x = ctk.CTkEntry(row, textvariable=x_var, width=44, height=28, corner_radius=6, fg_color=self.c_input, border_color=self.c_input_border, justify="center")
        e_x.pack(side="left", padx=2)

        # Y
        ctk.CTkLabel(row, text="Y:", font=("Segoe UI", 11), text_color=self.c_sub).pack(side="left", padx=(4, 2))
        e_y = ctk.CTkEntry(row, textvariable=y_var, width=44, height=28, corner_radius=6, fg_color=self.c_input, border_color=self.c_input_border, justify="center")
        e_y.pack(side="left", padx=2)

        # Scale
        ctk.CTkLabel(row, text="Scale:", font=("Segoe UI", 11), text_color=self.c_sub).pack(side="left", padx=(4, 2))
        e_s = ctk.CTkEntry(row, textvariable=scale_var, width=48, height=28, corner_radius=6, fg_color=self.c_input, border_color=self.c_input_border, justify="center")
        e_s.pack(side="left", padx=2)

        ctk.CTkLabel(row, text="%", font=("Segoe UI", 11), text_color=self.c_sub).pack(side="left")

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
                text="0 cảnh", text_color=self.c_sub, fg_color="#1e293b"
            )

    def _copy_scenes(self):
        text = self.scenes_textbox.get("1.0", "end").strip()
        if text and text != SCENES_PLACEHOLDER.strip():
            self.clipboard_clear()
            self.clipboard_append(text)
            self._log("[✓] Đã copy kịch bản vào clipboard!")
        else:
            self._log("[!] Kịch bản hiện đang rỗng.")

    def _paste_scenes(self):
        try:
            cb_text = self.clipboard_get()
            if cb_text:
                self.scenes_textbox.delete("1.0", "end")
                self.scenes_textbox.insert("1.0", cb_text)
                self._update_scenes_count()
                lines = [l for l in cb_text.splitlines() if l.strip()]
                self._log(f"[✓] Đã dán {len(lines)} cảnh từ clipboard!")
        except Exception:
            self._log("[!] Clipboard không chứa văn bản hợp lệ.")

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
            self._log(f"[✂️] Đã tự động tách kịch bản thành {len(cleaned)} câu (mỗi câu 1 dòng/cảnh)!")

    def _clean_empty_lines(self):
        text = self.scenes_textbox.get("1.0", "end").strip()
        if not text or text == SCENES_PLACEHOLDER.strip():
            return
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        self.scenes_textbox.delete("1.0", "end")
        self.scenes_textbox.insert("1.0", "\n".join(lines))
        self._update_scenes_count()
        self._log(f"[🧹] Đã dọn dẹp các dòng trống ({len(lines)} dòng hợp lệ)!")

    def _select_all_motions(self, state: bool):
        self.m_zoom_in_var.set(state)
        self.m_zoom_out_var.set(state)
        self.m_pan_up_var.set(state)
        self.m_pan_down_var.set(state)
        self.m_pan_left_var.set(state)
        self.m_pan_right_var.set(state)
        self._log(f"[🎥] {'Đã chọn tất cả' if state else 'Đã bỏ chọn tất cả'} chuyển động keyframe.")

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
            self._log("[🎯] Đã áp dụng Preset: TikTok / Reels / Shorts Siêu Cuốn (9:16, Nhanh, SFX, Chữ Vàng)!")
        elif "Điện Ảnh" in choice:
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
            self._log("[🎯] Đã áp dụng Preset: YouTube Kể Chuyện Điện Ảnh (16:9, Tông Ấm, Hạt Phim, Chữ Trắng)!")
        elif "Tài Chính" in choice or "Tin Tức" in choice:
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
            self._log("[🎯] Đã áp dụng Preset: Tin Tức & Phân Tích Tài Chính (16:9, Chữ Xanh Lá)!")
        elif "Tối Giản" in choice:
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
            self._log("[🎯] Đã áp dụng Preset: Tối Giản Siêu Tốc (16:9, Không SFX, Không Filter)!")

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
                self._log(f"[✓] Đã nạp {len(lines)} cảnh từ file: {os.path.basename(f)}")
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
            self._log("[✨] Đã tự động nạp các tệp mẫu sẵn có từ Desktop!")

    def _log(self, text: str):
        self.console_textbox.insert("end", text + "\n")
        self.console_textbox.see("end")

    def _launch_capcut(self):
        exe = get_capcut_exe_path()
        if exe and os.path.exists(exe):
            self._log(f"[+] Khởi chạy CapCut: {exe}")
            subprocess.Popen([exe])
        else:
            messagebox.showinfo("Khởi chạy CapCut", "Không tìm thấy CapCut.exe tự động. Vui lòng mở CapCut từ Desktop của bạn.")

    def _open_settings_dialog(self):
        dlg = ctk.CTkToplevel(self)
        dlg.title("Cài Đặt Thư Mục CapCut")
        dlg.geometry("560x220")
        dlg.configure(fg_color=self.c_bg)
        dlg.transient(self)
        dlg.grab_set()

        ctk.CTkLabel(dlg, text="⚙️ Cài Đặt Thư Mục CapCut Drafts", font=("Segoe UI", 14, "bold"), text_color="#fff").pack(anchor="w", padx=20, pady=(16, 8))
        ctk.CTkLabel(dlg, text="Đường dẫn lưu dự án CapCut (com.lveditor.draft):", font=("Segoe UI", 11), text_color=self.c_sub).pack(anchor="w", padx=20, pady=(0, 4))

        e = ctk.CTkEntry(dlg, textvariable=self.draft_root_var, height=36, corner_radius=8, fg_color=self.c_input, border_color=self.c_input_border)
        e.pack(fill="x", padx=20, pady=(0, 10))

        def _pick_d():
            d = filedialog.askdirectory(title="Chọn thư mục com.lveditor.draft", initialdir=self.draft_root_var.get())
            if d:
                self.draft_root_var.set(d)

        btn_row = ctk.CTkFrame(dlg, fg_color="transparent")
        btn_row.pack(fill="x", padx=20, pady=8)

        ctk.CTkButton(btn_row, text="📁 Duyệt Thư Mục...", fg_color=self.c_btn_sec, hover_color=self.c_btn_sec_h, command=_pick_d).pack(side="left")
        ctk.CTkButton(btn_row, text="✓ Lưu Lại", fg_color=self.c_indigo, hover_color=self.c_indigo_hover, command=dlg.destroy).pack(side="right")

    def _show_completed_dialog(self, data):
        dlg = ctk.CTkToplevel(self)
        dlg.title("Thành Công")
        dlg.geometry("500x240")
        dlg.configure(fg_color=self.c_bg)
        dlg.transient(self)
        dlg.grab_set()

        ctk.CTkLabel(dlg, text="🎉 TẠO PROJECT CAPCUT THÀNH CÔNG!", font=("Segoe UI", 15, "bold"), text_color=self.c_emerald).pack(pady=(20, 8))
        ctk.CTkLabel(
            dlg,
            text=f"Dự án '{data['draft_name']}' ({data['total_scenes']} cảnh, {data['duration_seconds']/60:.2f} phút) đã được tạo sẵn trong CapCut với trọn bộ hiệu ứng Pro.",
            font=("Segoe UI", 11), text_color=self.c_text, wraplength=440, justify="center"
        ).pack(pady=(0, 16))

        btn_row = ctk.CTkFrame(dlg, fg_color="transparent")
        btn_row.pack(pady=6)

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

        ctk.CTkButton(btn_row, text="📂 Mở Thư Mục Draft", fg_color=self.c_btn_sec, hover_color=self.c_btn_sec_h, corner_radius=8, width=150, height=36, command=_open_f).pack(side="left", padx=8)
        ctk.CTkButton(btn_row, text="🎬 Mở CapCut Ngay", fg_color=self.c_emerald, hover_color=self.c_emerald_hover, corner_radius=8, width=150, height=36, command=_open_cc).pack(side="left", padx=8)

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
            messagebox.showerror("Thiếu Kịch Bản", "Vui lòng dán kịch bản vào khung văn bản hoặc nhấn 'Đọc File .txt'!")
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

        # Map subtitle color
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
        self.btn_run.configure(state="disabled", text="⏳  ĐANG XỬ LÝ TIẾN TRÌNH...")
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
                # Transitions
                transition=trans_label,
                transition_duration=trans_dur,
                transition_mode=trans_mode,
                # Clip In-Animations
                clip_intro=clip_intro,
                clip_intro_duration=clip_intro_dur,
                clip_intro_mode=clip_intro_mode,
                # Video Scene Effects
                video_effect=video_effect,
                video_effect_scope=video_effect_scope,
                # Filters
                filter_name=filter_name,
                filter_intensity=filter_intensity,
                # Camera Motions
                camera_motion=cam_motion,
                zoom_scale=zoom_scale,
                keyframe_config=keyframe_config,
                smart_pacing=smart_pacing,
                canvas_blur=canvas_blur,
                # Subtitles
                import_subtitles=import_subs,
                subtitle_style=sub_col,
                subtitle_animation=sub_anim,
                subtitle_font_size=sub_size,
                subtitle_position=sub_pos,
                # Audio Suite
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
                    self.btn_run.configure(state="normal", text="🚀  TẠO PROJECT CAPCUT NGAY")
                    self.last_draft_dir = data['draft_dir']
                    self.lbl_status.configure(text="🎉 Tạo project CapCut thành công!")
                    self.progress_bar.set(1.0)
                    self._log("\n" + "=" * 60)
                    self._log(f"🎉 TẠO PROJECT CAPCUT THÀNH CÔNG!")
                    self._log(f"  • Dự án:       {data['draft_name']}")
                    self._log(f"  • Tổng cảnh:   {data['total_scenes']} cảnh")
                    self._log(f"  • Thời lượng:  {data['duration_seconds']:.2f}s ({(data['duration_seconds']/60):.2f} phút)")
                    self._log(f"  • Thư mục:     {data['draft_dir']}")
                    self._log("=" * 60)
                    self._show_completed_dialog(data)

                elif msg_type == 'error':
                    self.is_running = False
                    self.btn_run.configure(state="normal", text="🚀  TẠO PROJECT CAPCUT NGAY")
                    self.lbl_status.configure(text=f"❌ Lỗi: {data}")
                    self._log(f"\n[X] ĐÃ XẢY RA LỖI: {data}")
                    messagebox.showerror("Lỗi Quá Trình", f"Đã xảy ra lỗi:\n{data}")
        except queue.Empty:
            pass

        self.after(100, self._process_queue)


def main():
    app = AutoCapCutApp()
    app.mainloop()


if __name__ == '__main__':
    main()
