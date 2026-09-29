@echo off
chcp 65001 > nul
title 创建桌面快捷方式
cd /d "%~dp0"

echo.
echo ============================================================
echo    ERP智能系统 - 创建桌面快捷方式
echo ============================================================
echo.

rem 优先使用Python38
set PYEXE=
if exist "C:\Users\ruancanling\AppData\Local\Programs\Python\Python38\python.exe" (
    set "PYEXE=C:\Users\ruancanling\AppData\Local\Programs\Python\Python38\python.exe"
) else if exist ".venv\Scripts\python.exe" (
    set "PYEXE=.venv\Scripts\python.exe"
) else (
    set "PYEXE=python"
)

"%PYEXE%" "%~dp0创建桌面快捷方式.py"
