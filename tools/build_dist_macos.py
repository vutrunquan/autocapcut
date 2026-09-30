"""
Automated Build and Packaging Script for AutoCapCut Studio on macOS (Intel & Apple Silicon M).
Creates a standalone app bundle and zips it ready for Google Drive.
"""

import os
import sys
import shutil
import zipfile
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

DIST_DIR = BASE_DIR / "dist"
BUILD_DIR = BASE_DIR / "build"
RELEASE_DIR = BASE_DIR / "releases"
APP_NAME = "AutoCapCut_Studio"
ZIP_NAME = "AutoCapCut_Studio_macOS.zip"

def log(msg: str):
    print(f"[BUILD-MACOS] {msg}")

def clean_old_builds():
    log("Cleaning previous build artifacts...")
    for d in [DIST_DIR, BUILD_DIR]:
        if d.exists():
            shutil.rmtree(d, ignore_errors=True)
    RELEASE_DIR.mkdir(parents=True, exist_ok=True)

def build_executable():
    log("Starting PyInstaller build for AutoCapCut on macOS...")

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--clean",
        "--windowed",
        "--name", "AutoCapCut",
        "--collect-all", "customtkinter",
        "--collect-all", "pycapcut",
        "--hidden-import", "PIL",
        "--hidden-import", "PIL.Image",
        "--hidden-import", "PIL.ImageTk",
        "--hidden-import", "pymediainfo",
        "--hidden-import", "darkdetect",
        "--exclude-module", "torch",
        "--exclude-module", "torchaudio",
        "--exclude-module", "scipy",
        "--exclude-module", "matplotlib",
        "--exclude-module", "pytest",
        "--exclude-module", "whisper",
        f"--add-data={str(BASE_DIR / 'assets')}:assets",
        str(BASE_DIR / "gui.py")
    ]

    log(f"Running command: {' '.join(cmd[:6])} ...")
    res = subprocess.run(cmd, cwd=str(BASE_DIR))
    if res.returncode != 0:
        raise RuntimeError(f"PyInstaller build failed with exit code {res.returncode}")
    log("PyInstaller compilation finished successfully!")

def prepare_dist_folder():
    log("Structuring client distribution package for macOS...")
    target_app_dir = DIST_DIR / APP_NAME
    target_app_dir.mkdir(parents=True, exist_ok=True)

    app_bundle = DIST_DIR / "AutoCapCut.app"
    if app_bundle.exists():
        shutil.move(str(app_bundle), str(target_app_dir / "AutoCapCut.app"))

    # Copy license_config.json
    cfg_src = BASE_DIR / "license_config.json"
    if cfg_src.exists():
        shutil.copy2(cfg_src, target_app_dir / "license_config.json")

    # Copy version.json
    ver_src = BASE_DIR / "version.json"
    if ver_src.exists():
        shutil.copy2(ver_src, target_app_dir / "version.json")

    # Copy instructions
    guide_content = """========================================================================
         AUTOCAPCUT STUDIO - HƯỚNG DẪN SỬ DỤNG CHO MACOS
========================================================================

1. CÁCH MỞ PHẦN MỀM TRÊN MAC:
   - Kéo file AutoCapCut.app vào thư mục Applications (hoặc mở trực tiếp).
   - Nếu macOS hỏi xác nhận mở ứng dụng:
     Vào Cài đặt hệ thống (System Settings) -> Quyền riêng tư & Bảo mật (Privacy & Security) -> Bấm "Vẫn mở" (Open Anyway).

2. CHẾ ĐỘ DÙNG THỬ 3 NGÀY:
   - Dùng thử 3 ngày miễn phí toàn bộ tính năng.

3. KÍCH HOẠT BẢN QUYỀN 150.000 VNĐ VĨNH VIỄN:
   - Bấm vào biểu tượng bản quyền trên thanh tiêu đề.
   - Sao chép Mã Thiết Bị (Machine ID).
   - Quét mã VietQR chuyển khoản 150k và gửi mã máy cho Admin qua Zalo.
   - Nhận mã kích hoạt và dán vào app để mở khóa trọn đời.
========================================================================
"""
    with open(target_app_dir / "Huong_Dan_macOS.txt", "w", encoding="utf-8") as f:
        f.write(guide_content)

    return target_app_dir

def create_zip(target_app_dir: Path):
    log("Compressing macOS package into ZIP archive...")
    zip_path = RELEASE_DIR / ZIP_NAME
    if zip_path.exists():
        zip_path.unlink()

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        for root, dirs, files in os.walk(target_app_dir):
            for f in files:
                full_path = Path(root) / f
                rel_path = Path(APP_NAME) / full_path.relative_to(target_app_dir)
                zf.write(full_path, rel_path)

    size_mb = os.path.getsize(zip_path) / (1024 * 1024)
    log(f"macOS ZIP archive created: {zip_path} ({size_mb:.1f} MB)")
    return zip_path

def main():
    try:
        clean_old_builds()
        build_executable()
        app_dir = prepare_dist_folder()
        zip_path = create_zip(app_dir)
        print(f"\n[✓] Hoàn tất đóng gói macOS: {zip_path}\n")
    except Exception as e:
        print(f"\n[X] Lỗi đóng gói macOS: {e}\n")

if __name__ == '__main__':
    main()
