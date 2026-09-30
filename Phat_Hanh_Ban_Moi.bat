@echo off
chcp 65001 > nul
cls
echo =====================================================================
echo       AUTOCAPCUT STUDIO - TỰ ĐỘNG ĐÓNG GÓI VÀ PHÁT HÀNH BẢN MỚI
echo =====================================================================
echo.
echo Bước 1/2: Đóng gói ứng dụng thành file ZIP...
python tools\build_dist.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [X] Đóng gói thất bại. Vui lòng kiểm tra lỗi bên trên.
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo Bước 2/2: Đẩy bản cập nhật lên GitHub Releases...
python tools\publish_release.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [X] Phát hành lên GitHub thất bại.
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo =====================================================================
echo 🎉 HOÀN TẤT! Tất cả máy khách mở app lên sẽ tự động có bản cập nhật mới!
echo =====================================================================
pause
