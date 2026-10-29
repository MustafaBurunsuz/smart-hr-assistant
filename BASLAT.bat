@echo off
chcp 65001 >nul
title Smart HR Assistant - CLI
echo ===================================================
echo     SMART HR ASSISTANT BASLATILIYOR...
echo ===================================================
cd /d "%~dp0"
python main.py
pause
