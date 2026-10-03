"""
Automated Build and Packaging Script for AutoCapCut Studio.
Generates a standalone, fully portable application bundle for Windows,
packs it into a clean .ZIP file ready to be uploaded to Google Drive.
"""

import os
import sys
import shutil
import zipfile
import subprocess
from pathlib import Path

if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

DIST_DIR = BASE_DIR / "dist"
BUILD_DIR = BASE_DIR / "build"
RELEASE_DIR = BASE_DIR / "releases"
APP_NAME = "AutoCapCut_Studio"
ZIP_NAME = "AutoCapCut_Studio_Windows.zip"

def log(msg: str):
    print(f"[BUILD] {msg}")

def clean_old_builds():
    log("Cleaning previous build artifacts...")
    if sys.platform == 'win32':
        try:
            subprocess.run(["taskkill", "/F", "/IM", "AutoCapCut.exe"], capture_output=True)
            import time
            time.sleep(1)
        except Exception:
            pass
    for d in [DIST_DIR, BUILD_DIR]:
        if d.exists():
            shutil.rmtree(d, ignore_errors=True)
    RELEASE_DIR.mkdir(parents=True, exist_ok=True)

def build_executable():
    log("Starting PyInstaller build for AutoCapCut...")
    
    icon_path = BASE_DIR / "assets" / "icon.ico"
    if not icon_path.exists():
        from generate_icon import make_icon
        make_icon()

    # Ensure gemini alpha maps npz exists
    npz_path = BASE_DIR / "assets" / "gemini_alpha_maps.npz"
    if not npz_path.exists():
        log("Generating assets/gemini_alpha_maps.npz...")
        subprocess.run([sys.executable, str(BASE_DIR / "tools" / "save_npz.py")], cwd=str(BASE_DIR))

    # PyInstaller arguments
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--clean",
        "--windowed",              # No black console window for end user
        "--name", "AutoCapCut",
        f"--icon={str(icon_path)}",
        "--collect-all", "customtkinter",
        "--collect-all", "pycapcut",
        "--hidden-import", "PIL",
        "--hidden-import", "PIL.Image",
        "--hidden-import", "PIL.ImageTk",
        "--hidden-import", "pymediainfo",
        "--hidden-import", "darkdetect",
        "--hidden-import", "winreg",
        # Exclude unnecessary heavy packages to keep download size small
        "--exclude-module", "torch",
        "--exclude-module", "torchaudio",
        "--exclude-module", "scipy",
        "--exclude-module", "matplotlib",
        "--exclude-module", "pytest",
        "--exclude-module", "whisper",
        "--exclude-module", "openai_whisper",
        # Add assets folder
        f"--add-data={str(BASE_DIR / 'assets')};assets",
        # Entry point
        str(BASE_DIR / "gui.py")
    ]

    log(f"Running command: {' '.join(cmd[:6])} ...")
    res = subprocess.run(cmd, cwd=str(BASE_DIR))
    if res.returncode != 0:
        raise RuntimeError(f"PyInstaller build failed with exit code {res.returncode}")
    log("PyInstaller compilation finished successfully!")

def prepare_dist_folder():
    log("Structuring client distribution package...")
    raw_dist = DIST_DIR / "AutoCapCut"
    target_app_dir = DIST_DIR / APP_NAME

    if target_app_dir.exists():
        shutil.rmtree(target_app_dir, ignore_errors=True)
        import time
        for _ in range(6):
            if not target_app_dir.exists():
                break
            time.sleep(0.5)
            shutil.rmtree(target_app_dir, ignore_errors=True)

    if raw_dist.exists():
        if not target_app_dir.exists():
            try:
                raw_dist.rename(target_app_dir)
            except Exception:
                shutil.copytree(raw_dist, target_app_dir, dirs_exist_ok=True)
                shutil.rmtree(raw_dist, ignore_errors=True)
        else:
            shutil.copytree(raw_dist, target_app_dir, dirs_exist_ok=True)
            shutil.rmtree(raw_dist, ignore_errors=True)

    # 1. Copy assets to app root so both internal and external paths resolve
    assets_dest = target_app_dir / "assets"
    shutil.copytree(BASE_DIR / "assets", assets_dest, dirs_exist_ok=True)

    # 1b. Copy tools/gemini-watermark-remover to app root
    wm_src = BASE_DIR / "tools" / "gemini-watermark-remover"
    wm_dest = target_app_dir / "tools" / "gemini-watermark-remover"
    if wm_src.exists():
        def ignore_heavy(dir, files):
            return [f for f in files if f in {'release', 'public', 'tests', 'docs', '.git', '.github', 'samples', 'video-samples'}]
        shutil.copytree(wm_src, wm_dest, ignore=ignore_heavy, dirs_exist_ok=True)

    # 2. Copy current license_config.json (contains seller banking details)
    cfg_src = BASE_DIR / "license_config.json"
    if cfg_src.exists():
        shutil.copy2(cfg_src, target_app_dir / "license_config.json")
    else:
        # Create default config
        from autocapcut.licensing import DEFAULT_PAYMENT_CONFIG
        import json
        with open(target_app_dir / "license_config.json", "w", encoding="utf-8") as f:
            json.dump(DEFAULT_PAYMENT_CONFIG, f, ensure_ascii=False, indent=2)

    # 3. Copy version.json
    ver_src = BASE_DIR / "version.json"
    if ver_src.exists():
        shutil.copy2(ver_src, target_app_dir / "version.json")

    # 3. Copy user instructions file (Huong_Dan_Su_Dung.txt)
    guide_src = BASE_DIR / "HUONG_DAN_SU_DUNG.txt"
    if guide_src.exists():
        shutil.copy2(guide_src, target_app_dir / "Huong_Dan_Su_Dung.txt")

    # 4. Optional helper launcher .bat (some users prefer clicking a .bat)
    bat_content = """@echo off
start "" "%~dp0AutoCapCut.exe"
"""
    with open(target_app_dir / "Mo_AutoCapCut.bat", "w", encoding="utf-8") as f:
        f.write(bat_content)

    # 5. Security audit: Ensure NO admin keygen files are in the folder
    for root, dirs, files in os.walk(target_app_dir):
        for f in files:
            if "admin_keygen" in f.lower():
                os.remove(os.path.join(root, f))
                log(f"Removed sensitive admin file: {f}")

    log(f"Distribution package prepared at: {target_app_dir}")
    return target_app_dir

def create_zip(target_app_dir: Path):
    log("Compressing package into ZIP archive...")
    zip_path = RELEASE_DIR / ZIP_NAME
    if zip_path.exists():
        zip_path.unlink()

    # Zip the entire APP_NAME directory
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        for root, dirs, files in os.walk(target_app_dir):
            for f in files:
                full_path = Path(root) / f
                rel_path = Path(APP_NAME) / full_path.relative_to(target_app_dir)
                zf.write(full_path, rel_path)

    size_mb = os.path.getsize(zip_path) / (1024 * 1024)
    log(f"ZIP archive created successfully!")
    log(f"File path: {zip_path}")
    log(f"Size: {size_mb:.1f} MB")
    return zip_path

def main():
    print("\n" + "=" * 65)
    print("    AUTOCAPCUT STUDIO - BỘ ĐÓNG GÓI BẢN GIAO CHO KHÁCH HÀNG")
    print("=" * 65 + "\n")
    try:
        clean_old_builds()
        build_executable()
        app_dir = prepare_dist_folder()
        zip_path = create_zip(app_dir)
        print("\n" + "=" * 65)
        print("ĐÓNG GÓI HOÀN TẤT THÀNH CÔNG!")
        print(f"File ZIP để up lên Google Drive:")
        print(f"   {zip_path}")
        print("=" * 65)
        print("\nCách gửi cho khách:")
        print("  1. Up file ZIP trên lên Google Drive.")
        print("  2. Lấy link chia sẻ (Bất kỳ ai có đường liên kết đều có thể xem).")
        print("  3. Gửi link cho khách hàng.")
        print("  4. Khách tải về -> Giải nén -> Bấm AutoCapCut.exe là dùng được ngay!\n")
    except Exception as e:
        print(f"\n[X] LỖI TRONG QUÁ TRÌNH ĐÓNG GÓI: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
