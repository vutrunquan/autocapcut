@echo off
chcp 65001 > nul
title AutoCapCut Studio - Đóng Gói Ứng Dụng (Tạo File ZIP Cho Khách)
cd /d "%~dp0"
echo ========================================================================
echo       AUTOCAPCUT STUDIO - TIẾN TRÌNH ĐÓNG GÓI ỨNG DỤNG CHO KHÁCH
echo ========================================================================
echo.
echo Đang bắt đầu quá trình đóng gói thành ứng dụng độc lập (.exe)...
echo Quá trình này có thể mất từ 1 - 2 phút, vui lòng chờ trong giây lát...
echo.

python tools\build_dist.py
if %errorlevel% neq 0 (
    echo.
    echo [X] Đã xảy ra lỗi trong quá trình đóng gói!
    pause
    exit /b %errorlevel%
)

echo.
echo Đang mở thư mục chứa file ZIP...
explorer "releases"
echo.
echo Hoàn tất! Nhấn phím bất kỳ để đóng cửa sổ này.
pause > nul
