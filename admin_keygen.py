#!/usr/bin/env python3
"""
Admin License Key Generator for AutoCapCut Studio.
For the tool creator / administrator to generate lifetime license keys
for customers after receiving the 150,000 VND payment.
"""

import sys
import os

if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

from autocapcut.licensing import (
    generate_license_key,
    verify_license_key,
    get_payment_info,
    update_payment_config,
    get_machine_id
)


def run_cli(hwid: str):
    try:
        key = generate_license_key(hwid)
        pay_info = get_payment_info()
        print("\n" + "=" * 60)
        print("    AUTOCAPCUT STUDIO - TRÌNH TẠO KEY BẢN QUYỀN (ADMIN)")
        print("=" * 60)
        print(f"  • Mã thiết bị khách gửi: {hwid.upper()}")
        print(f"  • Gói bản quyền:         Vĩnh viễn (150.000 VNĐ)")
        print("-" * 60)
        print(f"  MÃ KÍCH HOẠT:             {key}")
        print("=" * 60)

        # Copy to clipboard if possible
        try:
            import tkinter as tk
            r = tk.Tk()
            r.withdraw()
            r.clipboard_clear()
            r.clipboard_append(key)
            r.update()
            r.destroy()
            print("  [OK] Đã tự động sao chép mã kích hoạt vào Clipboard!")
            print("      Bạn có thể dán (Ctrl+V) gửi ngay cho khách hàng.")
        except Exception:
            pass
        print("")
    except Exception as e:
        print(f"\n[!] Lỗi: {e}\n")


def run_gui():
    try:
        import customtkinter as ctk
        from tkinter import messagebox
    except ImportError:
        print("[!] Thiếu thư viện customtkinter. Vui lòng chạy ở chế độ dòng lệnh: python admin_keygen.py <HWID>")
        sys.exit(1)

    ctk.set_appearance_mode("Dark")
    ctk.set_default_color_theme("blue")

    app = ctk.CTk()
    app.title("AutoCapCut Studio - Trình Tạo Key Bản Quyền (Admin)")
    app.geometry("640x540")
    app.minsize(600, 480)
    app.configure(fg_color="#121316")

    # Header
    head = ctk.CTkFrame(app, fg_color="#18191e", corner_radius=10, border_color="#26272f", border_width=1)
    head.pack(fill="x", padx=16, pady=12)

    ctk.CTkLabel(
        head, text="AutoCapCut Studio - Quản Lý Bản Quyền",
        font=("Segoe UI", 16, "bold"), text_color="#ffffff"
    ).pack(anchor="w", padx=16, pady=(12, 2))

    ctk.CTkLabel(
        head, text="Tạo mã kích hoạt vĩnh viễn (150k) theo Mã Thiết Bị (HWID) của khách hàng",
        font=("Segoe UI", 11), text_color="#888b96"
    ).pack(anchor="w", padx=16, pady=(0, 12))

    # Tabview for Generator vs Payment Settings
    tabs = ctk.CTkTabview(
        app, fg_color="#18191e",
        segmented_button_selected_color="#2563eb",
        segmented_button_fg_color="#111215",
        text_color="#e3e4e8", corner_radius=10,
        border_color="#26272f", border_width=1
    )
    tabs.pack(fill="both", expand=True, padx=16, pady=(0, 14))

    tab_gen = tabs.add("Tạo Key Cho Khách")
    tab_pay = tabs.add("Cài Đặt Thanh Toán (150k)")

    # TAB 1: Generator
    ctk.CTkLabel(
        tab_gen, text="1. Nhập Mã Thiết Bị (Machine ID) khách hàng gửi:",
        font=("Segoe UI", 12, "bold"), text_color="#ffffff"
    ).pack(anchor="w", padx=10, pady=(10, 4))

    hwid_row = ctk.CTkFrame(tab_gen, fg_color="transparent")
    hwid_row.pack(fill="x", padx=10, pady=(0, 8))

    hwid_var = ctk.StringVar()
    e_hwid = ctk.CTkEntry(
        hwid_row, textvariable=hwid_var, placeholder_text="Ví dụ: AC-3635-81C2-BEC2...",
        height=36, corner_radius=6, fg_color="#111215", border_color="#2e3039",
        font=("Segoe UI", 13, "bold"), text_color="#ffffff"
    )
    e_hwid.pack(side="left", fill="x", expand=True, padx=(0, 6))

    def _paste_hwid():
        try:
            cb = app.clipboard_get().strip()
            if cb:
                hwid_var.set(cb)
        except Exception:
            pass

    btn_paste = ctk.CTkButton(
        hwid_row, text="Dán", width=60, height=36, corner_radius=6,
        fg_color="#202127", hover_color="#2c2d36", font=("Segoe UI", 11),
        command=_paste_hwid
    )
    btn_paste.pack(side="right")

    key_var = ctk.StringVar()

    def _do_generate():
        val = hwid_var.get().strip()
        if not val:
            messagebox.showwarning("Thiếu Mã Máy", "Vui lòng nhập Mã Thiết Bị của khách hàng!")
            return
        try:
            res_key = generate_license_key(val)
            key_var.set(res_key)
            app.clipboard_clear()
            app.clipboard_append(res_key)
            lbl_noti.configure(text=f"Đã tạo key và sao chép vào Clipboard: {res_key}", text_color="#10b981")
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể tạo key: {e}")

    btn_gen = ctk.CTkButton(
        tab_gen, text="Tạo Key Vĩnh Viễn (150.000đ)",
        font=("Segoe UI", 13, "bold"), fg_color="#2563eb", hover_color="#1d4ed8",
        height=40, corner_radius=8, command=_do_generate
    )
    btn_gen.pack(fill="x", padx=10, pady=(6, 12))

    ctk.CTkLabel(
        tab_gen, text="2. Mã Kích Hoạt Bản Quyền (Gửi mã này cho khách):",
        font=("Segoe UI", 12, "bold"), text_color="#ffffff"
    ).pack(anchor="w", padx=10, pady=(4, 4))

    key_row = ctk.CTkFrame(tab_gen, fg_color="transparent")
    key_row.pack(fill="x", padx=10, pady=(0, 6))

    e_key = ctk.CTkEntry(
        key_row, textvariable=key_var, height=38, corner_radius=6,
        fg_color="#111215", border_color="#2563eb", font=("Consolas", 14, "bold"),
        text_color="#10b981", justify="center"
    )
    e_key.pack(side="left", fill="x", expand=True, padx=(0, 6))

    def _copy_key():
        k = key_var.get().strip()
        if k:
            app.clipboard_clear()
            app.clipboard_append(k)
            lbl_noti.configure(text="Đã sao chép mã kích hoạt vào Clipboard!", text_color="#10b981")

    btn_copy = ctk.CTkButton(
        key_row, text="Sao Chép", width=80, height=38, corner_radius=6,
        fg_color="#202127", hover_color="#2c2d36", font=("Segoe UI", 11, "bold"),
        command=_copy_key
    )
    btn_copy.pack(side="right")

    lbl_noti = ctk.CTkLabel(tab_gen, text="", font=("Segoe UI", 11))
    lbl_noti.pack(anchor="w", padx=12, pady=4)

    # TAB 2: Payment Settings
    p_info = get_payment_info()
    bank_var = ctk.StringVar(value=p_info.get("bank_name", "MBBank"))
    acc_var = ctk.StringVar(value=p_info.get("bank_account", ""))
    name_var = ctk.StringVar(value=p_info.get("account_name", ""))
    price_var = ctk.StringVar(value=str(p_info.get("price_vnd", 150000)))
    zalo_var = ctk.StringVar(value=p_info.get("zalo_contact", ""))

    def _add_p_row(label, var):
        r = ctk.CTkFrame(tab_pay, fg_color="transparent")
        r.pack(fill="x", padx=10, pady=4)
        ctk.CTkLabel(r, text=label, width=150, anchor="w", font=("Segoe UI", 11), text_color="#e3e4e8").pack(side="left")
        ctk.CTkEntry(r, textvariable=var, height=30, corner_radius=6, fg_color="#111215", border_color="#2e3039", font=("Segoe UI", 11)).pack(side="left", fill="x", expand=True)

    _add_p_row("Ngân hàng (VietQR code):", bank_var)
    _add_p_row("Số tài khoản nhận tiền:", acc_var)
    _add_p_row("Tên chủ tài khoản:", name_var)
    _add_p_row("Giá tiền gói vĩnh viễn (VNĐ):", price_var)
    _add_p_row("Số Zalo hỗ trợ khách:", zalo_var)

    def _save_payment():
        try:
            update_payment_config({
                "bank_name": bank_var.get().strip(),
                "bank_account": acc_var.get().strip(),
                "account_name": name_var.get().strip().upper(),
                "price_vnd": int(price_var.get().strip() or 150000),
                "zalo_contact": zalo_var.get().strip()
            })
            messagebox.showinfo("Thành Công", "Đã lưu thông tin tài khoản thanh toán thành công!\nKhách hàng khi mở bảng thanh toán sẽ tự động nhận đúng STK và QR Code này.")
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể lưu: {e}")

    btn_save = ctk.CTkButton(
        tab_pay, text="Lưu Cấu Hình Thanh Toán",
        font=("Segoe UI", 12, "bold"), fg_color="#2563eb", hover_color="#1d4ed8",
        height=36, corner_radius=6, command=_save_payment
    )
    btn_save.pack(fill="x", padx=10, pady=(16, 0))

    app.mainloop()


if __name__ == '__main__':
    if len(sys.argv) > 1:
        run_cli(sys.argv[1])
    else:
        run_gui()
