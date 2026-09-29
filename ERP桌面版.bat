@echo off
chcp 65001 > nul
title ERP智能系统 - 桌面版
cd /d "%~dp0"

echo.
echo ============================================================
echo    ERP智能系统 企业管理系统 - 桌面窗口版
echo ============================================================
echo.

rem 检查pywebview是否安装
set "NEED_INSTALL=0"
if exist "C:\Users\ruancanling\AppData\Local\Programs\Python\Python38\python.exe" (
    "C:\Users\ruancanling\AppData\Local\Programs\Python\Python38\python.exe" -c "import pywebview" 2>nul
    if errorlevel 1 set "NEED_INSTALL=1"
) else (
    python -c "import pywebview" 2>nul
    if errorlevel 1 set "NEED_INSTALL=1"
)

if "%NEED_INSTALL%"=="1" (
    echo ⚠️  检测到未安装 pywebview，正在自动安装...
    echo.
    if exist "C:\Users\ruancanling\AppData\Local\Programs\Python\Python38\python.exe" (
        "C:\Users\ruancanling\AppData\Local\Programs\Python\Python38\python.exe" -m pip install pywebview
    ) else (
        python -m pip install pywebview
    )
    echo.
    if errorlevel 1 (
        echo ❌ 安装失败，请手动运行: pip install pywebview
        echo 或者使用【启动ERP系统.bat】浏览器版（无需额外安装）
        pause
        exit /b 1
    )
    echo ✅ pywebview 安装完成！即将启动桌面版App...
    echo.
    timeout /t 2 > nul
)

rem 优先使用Python38
set PYEXE=
if exist "C:\Users\ruancanling\AppData\Local\Programs\Python\Python38\python.exe" (
    set "PYEXE=C:\Users\ruancanling\AppData\Local\Programs\Python\Python38\python.exe"
) else if exist ".venv\Scripts\python.exe" (
    set "PYEXE=.venv\Scripts\python.exe"
) else (
    set "PYEXE=python"
)

"%PYEXE%" "%~dp0desktop_app.py"
