#!/usr/bin/env bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

echo "====================================================================="
echo "      AUTOCAPCUT STUDIO - TỰ ĐỘNG ĐÓNG GÓI VÀ PHÁT HÀNH CHO MACOS"
echo "====================================================================="
echo ""

if [ -f "./venv/bin/python" ]; then
    PYTHON_CMD="./venv/bin/python"
else
    PYTHON_CMD="python3"
fi

echo "Bước 1/2: Đang đóng gói ứng dụng macOS (AutoCapCut.app)..."
$PYTHON_CMD tools/build_dist_macos.py

if [ $? -ne 0 ]; then
    echo ""
    echo "[X] Đóng gói thất bại. Vui lòng kiểm tra lỗi bên trên."
    read -p "Nhấn Enter để thoát..."
    exit 1
fi

echo ""
echo "Bước 2/2: Đang phát hành lên GitHub / mở thư mục releases..."
if [ -f "tools/publish_release.py" ]; then
    $PYTHON_CMD tools/publish_release.py || true
fi

open "releases"

echo ""
echo "====================================================================="
echo "🎉 ĐÓNG GÓI THÀNH CÔNG BẢN CẬP NHẬT MỚI CHO MACOS!"
echo "====================================================================="
echo ""
echo "CÁCH PHÁT HÀNH ĐẾN TOÀN BỘ MÁY KHÁCH:"
echo " 1. Mở Google Drive hoặc GitHub Release."
echo " 2. Tải file AutoCapCut_Studio_macOS.zip trong thư mục releases lên."
echo " 3. Mọi máy Mac của khách khi mở AutoCapCut lên sẽ tự động thông báo"
echo "    có bản mới và tải/cập nhật tự động trực tiếp!"
echo "====================================================================="
read -p "Nhấn Enter để hoàn tất..."
