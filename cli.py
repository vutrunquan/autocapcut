"""
Command Line Interface for AutoCapCut.
Run automated video drafting directly from the terminal.
"""

import os
import sys
import argparse
from autocapcut import (
    run_autocapcut,
    get_default_capcut_draft_path,
    get_capcut_exe_path
)

# Ensure console supports UTF-8
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass


def print_banner():
    banner = r"""
========================================================================
     _         _          ____             ____      _   
    / \  _   _| |_ ___   / ___|__ _ _ __  / ___|   _| |_ 
   / _ \| | | | __/ _ \ | |   / _` | '_ \| |  | | | | __|
  / ___ \ |_| | || (_) || |__| (_| | |_) | |__| |_| | |_ 
 /_/   \_\__,_|\__\___/  \____\__,_| .__/ \____\__,_|\__|
                                   |_|                   
       Tự Động Tạo Project CapCut Khớp Ảnh Với Voice & SRT
========================================================================
"""
    print(banner)


def main():
    print_banner()

    parser = argparse.ArgumentParser(
        description="AutoCapCut - Tự động tạo draft CapCut khớp ảnh với voice dựa trên SRT và Kịch bản."
    )
    parser.add_argument("--srt", "-s", help="Đường dẫn file phụ đề .srt")
    parser.add_argument("--script", "-k", help="Đường dẫn file kịch bản .txt (mỗi dòng 1 ảnh)")
    parser.add_argument("--voice", "-v", help="Đường dẫn file âm thanh voice (.wav, .mp3, .m4a)")
    parser.add_argument("--images", "-i", help="Đường dẫn thư mục chứa ảnh (tên ảnh theo số thứ tự)")
    parser.add_argument("--name", "-n", default="AutoCapCut_Project", help="Tên project CapCut (mặc định: AutoCapCut_Project)")
    parser.add_argument("--ratio", choices=["16:9", "9:16", "1:1"], default="16:9", help="Tỷ lệ khung hình (16:9, 9:16, 1:1)")
    parser.add_argument("--fps", type=int, choices=[24, 30, 60], default=30, help="Số khung hình / giây")
    parser.add_argument("--no-subtitles", action="store_true", help="Không import phụ đề SRT vào timeline")
    parser.add_argument("--no-zoom", action="store_true", help="Tắt hiệu ứng zoom nhẹ (Ken Burns)")
    parser.add_argument("--draft-root", help="Thư mục draft của CapCut (nếu muốn chỉ định riêng)")
    parser.add_argument("--open-capcut", action="store_true", help="Tự động mở CapCut sau khi tạo xong")

    args = parser.parse_args()

    # Interactive prompt if required arguments are missing
    srt_path = args.srt
    while not srt_path or not os.path.exists(srt_path):
        if srt_path:
            print(f"[!] File SRT không tồn tại: {srt_path}")
        srt_path = input("Nhập đường dẫn file SRT (.srt): ").strip(' "\'')

    script_path = args.script
    while not script_path or not os.path.exists(script_path):
        if script_path:
            print(f"[!] File kịch bản không tồn tại: {script_path}")
        script_path = input("Nhập đường dẫn file Kịch bản (.txt): ").strip(' "\'')

    voice_path = args.voice
    while not voice_path or not os.path.exists(voice_path):
        if voice_path:
            print(f"[!] File Voice không tồn tại: {voice_path}")
        voice_path = input("Nhập đường dẫn file Voice (.wav, .mp3, .m4a): ").strip(' "\'')

    images_dir = args.images
    while not images_dir or not os.path.isdir(images_dir):
        if images_dir:
            print(f"[!] Thư mục ảnh không tồn tại: {images_dir}")
        images_dir = input("Nhập đường dẫn thư mục Ảnh: ").strip(' "\'')

    # Map aspect ratio to width x height
    ratio_map = {
        "16:9": (1920, 1080),
        "9:16": (1080, 1920),
        "1:1": (1080, 1080)
    }
    width, height = ratio_map[args.ratio]

    print("\n" + "-" * 60)
    print("THÔNG SỐ DỰ ÁN:")
    print(f"  • Tên project:     {args.name}")
    print(f"  • File SRT:        {srt_path}")
    print(f"  • File Kịch bản:   {script_path}")
    print(f"  • File Voice:      {voice_path}")
    print(f"  • Thư mục Ảnh:     {images_dir}")
    print(f"  • Tỷ lệ & FPS:     {args.ratio} ({width}x{height}) @ {args.fps}fps")
    print(f"  • Phụ đề SRT:      {'BẬT' if not args.no_subtitles else 'TẮT'}")
    print(f"  • Ken Burns Zoom:  {'BẬT' if not args.no_zoom else 'TẮT'}")
    print("-" * 60 + "\n")

    def progress_callback(msg: str, pct: float):
        bar_len = 30
        filled = int(bar_len * pct)
        bar = '█' * filled + '-' * (bar_len - filled)
        sys.stdout.write(f"\r[{bar}] {pct * 100:5.1f}% | {msg[:50]:<50}")
        sys.stdout.flush()
        if pct >= 1.0:
            sys.stdout.write("\n")

    try:
        result = run_autocapcut(
            srt_path=srt_path,
            script_path=script_path,
            voice_path=voice_path,
            images_dir=images_dir,
            project_name=args.name,
            draft_root=args.draft_root,
            width=width,
            height=height,
            fps=args.fps,
            import_subtitles=not args.no_subtitles,
            enable_zoom_effect=not args.no_zoom,
            progress_callback=progress_callback
        )

        print("\n" + "=" * 60)
        print("🎉 TẠO PROJECT THÀNH CÔNG!")
        print(f"  • Tên project:   {result['draft_name']}")
        print(f"  • Tổng số cảnh:  {result['total_scenes']} cảnh")
        print(f"  • Thời lượng:    {result['duration_seconds']:.2f} giây ({result['duration_seconds']/60:.2f} phút)")
        print(f"  • Đường dẫn:     {result['draft_dir']}")
        print("=" * 60)
        print("\n👉 Bạn hãy mở phần mềm CapCut Desktop lên, project sẽ xuất hiện ngay ở đầu danh sách!")

        if args.open_capcut:
            capcut_exe = get_capcut_exe_path()
            if capcut_exe and os.path.exists(capcut_exe):
                print(f"[+] Đang khởi chạy CapCut: {capcut_exe}")
                os.startfile(capcut_exe)
            else:
                print("[!] Không tìm thấy CapCut.exe tự động.")

    except Exception as e:
        print(f"\n\n[X] ĐÃ XẢY RA LỖI: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
