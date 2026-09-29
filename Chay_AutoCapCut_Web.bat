@echo off
chcp 65001 > nul
title AutoCapCut Pro - Web App
echo ===================================================
echo     Đang khởi động AutoCapCut Pro Web Server...
echo ===================================================
cd /d "%~dp0"
start "" http://localhost:8000
python web_app.py
pause
