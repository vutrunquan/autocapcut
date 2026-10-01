@echo off
chcp 65001 > nul
cls
echo =====================================================================
echo       AUTOCAPCUT STUDIO - TỰ ĐỘNG ĐÓNG GÓI VÀ PHÁT HÀNH BẢN MỚI
echo =====================================================================
echo.
echo Bước 1/2: Đang đóng gói ứng dụng (EXE + Nhạc BGM/SFX + AutoCapCut)...
python tools\build_dist.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [X] Đóng gói thất bại. Vui lòng kiểm tra lỗi bên trên.
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo Bước 2/2: Mở thư mục chứa file ZIP phát hành...
explorer "releases"

echo.
echo =====================================================================
echo 🎉 ĐÓNG GÓI THÀNH CÔNG BẢN CẬP NHẬT MỚI!
echo =====================================================================
echo.
echo CÁCH PHÁT HÀNH ĐẾN TOÀN BỘ MÁY KHÁCH:
echo  1. Mở Google Drive của bạn.
echo  2. Nhấp chuột phải vào file AutoCapCut_Studio_Windows.zip trên Google Drive.
echo  3. Chọn "Quản lý phiên bản" (Manage versions) -^> "Tải phiên bản mới lên" (Upload new version).
echo  4. Chọn file vừa tạo trong thư mục releases.
echo.
echo -^> Toàn bộ máy khách khi mở AutoCapCut lên sẽ tự động thấy thông báo
echo    bản cập nhật mới và tải trực tiếp từ Google Drive tốc độ cao!
echo =====================================================================
pause
