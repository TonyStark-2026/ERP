@echo off
chcp 65001 > nul
title 复制ERP智能系统到桌面

echo ========================================
echo   ERP智能系统 - 复制到桌面
echo ========================================
echo.

set "SRC=c:\Users\ruancanling\Desktop\ERP VIBE CODING\dist\ERP智能系统"
set "DST=C:\Users\ruancanling\Desktop\ERP智能系统"

echo 正在复制软件到桌面...
echo 源: %SRC%
echo 目标: %DST%
echo.

if exist "%DST%" (
    echo 检测到旧版本，正在删除...
    rmdir /S /Q "%DST%"
)

xcopy "%SRC%" "%DST%\" /E /I /Y /Q

echo.
if exist "%DST%\ERP智能系统.exe" (
    echo ✅ 复制成功！
    echo.
    echo 软件位置: %DST%\ERP智能系统.exe
    echo.
    echo 双击 ERP智能系统.exe 即可启动
    echo.
    echo 是否现在启动？
    set /p choice="(Y/N): "
    if /i "%choice%"=="Y" start "" "%DST%\ERP智能系统.exe"
) else (
    echo ❌ 复制失败！
)

echo.
pause
