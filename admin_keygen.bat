@echo off
chcp 65001 > nul
title AutoCapCut Studio - Trình Tạo Key Bản Quyền (Admin)
cd /d "%~dp0"
python admin_keygen.py %*
if %errorlevel% neq 0 (
    echo.
    pause
)
