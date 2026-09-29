@echo off
chcp 65001 > nul
title ERP智能系统 - 启动器
cd /d "%~dp0"

echo.
echo ============================================================
echo    ERP智能系统 企业管理系统 - 一键启动
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

"%PYEXE%" "%~dp0app_launcher.py"

if errorlevel 1 (
    echo.
    echo ❌ 启动失败，请检查上面的错误信息
    pause
)
