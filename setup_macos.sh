#!/usr/bin/env bash
# ==============================================================================
# AutoCapCut Studio - Cài đặt môi trường tự động cho macOS
# Tương thích hoàn toàn với cả Apple Silicon (M1/M2/M3/M4) và Intel (x86_64)
# ==============================================================================

set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

echo "=================================================================="
echo "    AUTOCAPCUT STUDIO - TRÌNH CÀI ĐẶT TỰ ĐỘNG CHO MACOS"
echo "=================================================================="

# 1. Phát hiện kiến trúc vi xử lý
ARCH="$(uname -m)"
echo "[-] Kiểm tra phần cứng Mac..."
if [ "$ARCH" = "arm64" ]; then
    echo "    -> Vi xử lý: Apple Silicon (M1/M2/M3/M4 - Kiến trúc ARM64)"
elif [ "$ARCH" = "x86_64" ]; then
    echo "    -> Vi xử lý: Intel Core (Kiến trúc x86_64)"
else
    echo "    -> Vi xử lý: $ARCH"
fi

# 2. Bổ sung đường dẫn Homebrew vào PATH nếu chưa có
if [ -d "/opt/homebrew/bin" ]; then
    export PATH="/opt/homebrew/bin:$PATH"
fi
if [ -d "/usr/local/bin" ]; then
    export PATH="/usr/local/bin:$PATH"
fi

# 3. Kiểm tra Python 3
echo "[-] Kiểm tra Python 3..."
if command -v python3 &>/dev/null; then
    PYTHON_CMD="python3"
elif command -v python &>/dev/null; then
    PYTHON_CMD="python"
else
    echo "[!] Không tìm thấy Python 3 trên máy Mac của bạn."
    echo "    Vui lòng cài đặt Python bằng 1 trong 2 cách:"
    echo "    1. Tải bộ cài chính thức tại: https://www.python.org/downloads/macos/"
    echo "    2. Hoặc qua Homebrew: brew install python python-tk"
    exit 1
fi

PY_VER=$($PYTHON_CMD -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')")
echo "    -> Đã tìm thấy Python: $PY_VER ($PYTHON_CMD)"

# 4. Kiểm tra Tkinter (CustomTkinter cần Tkinter)
echo "[-] Kiểm tra thư viện đồ họa Tkinter..."
if ! $PYTHON_CMD -c "import tkinter" &>/dev/null; then
    echo "[!] Cảnh báo: Python hiện tại chưa có sẵn thư viện Tkinter."
    echo "    Nếu dùng Homebrew, bạn hãy chạy: brew install python-tk"
    echo "    Nếu tải từ python.org, Tkinter đã được tích hợp sẵn."
else
    echo "    -> Tkinter sẵn sàng."
fi

# 5. Khởi tạo Virtual Environment (venv) để tránh xung đột hệ thống
echo "[-] Thiết lập môi trường ảo Python (venv)..."
if [ ! -d "venv" ]; then
    $PYTHON_CMD -m venv venv
    echo "    -> Đã tạo thư mục môi trường ảo 'venv'."
else
    echo "    -> Đã có sẵn thư mục môi trường ảo 'venv'."
fi

# Kích hoạt venv
source venv/bin/activate
VENV_PY="venv/bin/python"
VENV_PIP="venv/bin/pip"

# 6. Nâng cấp pip và cài đặt gói phụ thuộc
echo "[-] Cài đặt các thư viện phụ thuộc từ requirements.txt..."
$VENV_PIP install --upgrade pip
$VENV_PIP install -r requirements.txt

# 7. Kiểm tra Node.js (Cho tính năng xóa Watermark Gemini AI)
echo "[-] Kiểm tra Node.js (dùng cho công cụ xóa Watermark Gemini AI)..."
if command -v node &>/dev/null; then
    NODE_VER=$(node -v)
    echo "    -> Node.js sẵn sàng: $NODE_VER"
else
    echo "    [i] Chưa phát hiện Node.js (tính năng xóa watermark sẽ bỏ qua nếu không có Node)."
    echo "        Bạn có thể cài đặt thêm Node.js nếu cần: brew install node"
fi

# 8. Cấp quyền thực thi cho các file .command và .sh
echo "[-] Cấp quyền thực thi (chmod +x) cho các file khởi chạy..."
chmod +x setup_macos.sh
if [ -f "Chay_AutoCapCut_GUI.command" ]; then
    chmod +x Chay_AutoCapCut_GUI.command
fi
if [ -f "Chay_AutoCapCut_Web.command" ]; then
    chmod +x Chay_AutoCapCut_Web.command
fi

echo ""
echo "=================================================================="
echo "    CHÚC MỪNG! BẠN ĐÃ CÀI ĐẶT THÀNH CÔNG AUTOCAPCUT TRÊN MACOS!"
echo "=================================================================="
echo "Cách khởi động phần mềm trên máy Mac:"
echo "  1. Chạy Desktop GUI:"
echo "     -> Nhấp đúp chuột vào file: Chay_AutoCapCut_GUI.command"
echo "     -> Hoặc trong Terminal: ./venv/bin/python gui.py"
echo ""
echo "  2. Chạy Giao Diện Web:"
echo "     -> Nhấp đúp chuột vào file: Chay_AutoCapCut_Web.command"
echo "     -> Hoặc trong Terminal: ./venv/bin/python web_app.py"
echo "=================================================================="
