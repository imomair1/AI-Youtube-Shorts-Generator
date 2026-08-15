@echo off
title Vidora Desktop Downloader
cd /d "%~dp0"
start "" ".\venv\Scripts\pythonw.exe" main_desktop.py
exit
