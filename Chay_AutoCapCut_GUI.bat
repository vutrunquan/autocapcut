@echo off
chcp 65001 > nul
title AutoCapCut Pro - Desktop App
echo ===================================================
echo     Đang khởi động AutoCapCut Pro Desktop GUI...
echo ===================================================
cd /d "%~dp0"
python gui.py
if %errorlevel% neq 0 (
    echo.
    echo [!] Co loi xay ra. Vui long kiem tra lai moi truong Python.
    pause
)
