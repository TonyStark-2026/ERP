@echo off
chcp 65001 > nul
title ERP系统 - 云服务器版
cd /d "%~dp0"

echo.
echo ============================================================
echo    ERP系统 - 云服务器启动脚本
echo ============================================================
echo.

rem 检查Python
where python >nul 2>nul
if errorlevel 1 (
    echo ❌ 未检测到 Python，请先安装 Python 3.8+
    echo 下载地址：https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [1/3] 检查依赖...
python -c "import fastapi" 2>nul
if errorlevel 1 (
    echo 正在安装依赖，请稍候...
    pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
    if errorlevel 1 (
        echo ❌ 依赖安装失败
        pause
        exit /b 1
    )
    echo ✅ 依赖安装完成
) else (
    echo ✅ 依赖已就绪
)

echo.
echo [2/3] 检查数据库...
if exist "erp_data.db" (
    echo ✅ 数据库已就绪
) else (
    echo ⚠️  未找到数据库文件，首次启动将自动创建
)

echo.
echo [3/3] 启动服务...
echo.
echo ============================================================
echo    服务启动中，请稍候...
echo    访问地址：http://服务器公网IP:8000
echo    按 Ctrl+C 停止服务
echo ============================================================
echo.

python -m uvicorn backend.app:app --host 0.0.0.0 --port 8000

if errorlevel 1 (
    echo.
    echo ❌ 启动失败，请检查上面的错误信息
    pause
)
