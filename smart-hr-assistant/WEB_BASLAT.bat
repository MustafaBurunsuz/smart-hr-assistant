@echo off
chcp 65001 >nul
title Smart HR Assistant - Web UI
echo ===================================================
echo     SMART HR ASSISTANT WEB SUNUCUSU BASLATILIYOR...
echo ===================================================
cd /d "%~dp0"
start "" http://localhost:8080
python web_app.py
pause
