#!/usr/bin/env bash
# ==============================================================================
# AutoCapCut Studio - Khởi chạy Desktop App trên macOS (Intel & Apple Silicon)
# Nhấp đúp chuột vào file này trong Finder để mở ứng dụng.
# ==============================================================================

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

# Nạp đường dẫn Homebrew
if [ -d "/opt/homebrew/bin" ]; then
    export PATH="/opt/homebrew/bin:$PATH"
fi
if [ -d "/usr/local/bin" ]; then
    export PATH="/usr/local/bin:$PATH"
fi

echo "=========================================================="
echo "    Đang khởi động AutoCapCut Studio Desktop trên macOS..."
echo "    Phần cứng: $(uname -m) ($(sysctl -n machdep.cpu.brand_string 2>/dev/null || echo 'Apple Silicon / Intel'))"
echo "=========================================================="

# Ưu tiên chạy môi trường ảo venv nếu có
if [ -f "./venv/bin/python" ]; then
    ./venv/bin/python gui.py
elif command -v python3 &>/dev/null; then
    python3 gui.py
elif command -v python &>/dev/null; then
    python gui.py
else
    echo "[!] Lỗi: Không tìm thấy Python 3."
    echo "    Vui lòng chạy file ./setup_macos.sh trước để hoàn tất cài đặt."
    read -p "Nhấn Enter để thoát..."
fi
