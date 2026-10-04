# ERP 云服务器一键部署脚本
# 在服务器上以管理员身份运行 PowerShell，粘贴此脚本执行

Write-Host "===== ERP 部署开始 =====" -ForegroundColor Cyan

# 1. 安装 Python（如果未安装）
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "[1/6] 下载 Python..." -ForegroundColor Yellow
    $pyUrl = "https://www.python.org/ftp/python/3.8.10/python-3.8.10-amd64.exe"
    $pyInstaller = "$env:TEMP\python_installer.exe"
    Invoke-WebRequest -Uri $pyUrl -OutFile $pyInstaller -UseBasicParsing
    Write-Host "[1/6] 安装 Python（静默模式）..." -ForegroundColor Yellow
    Start-Process -FilePath $pyInstaller -ArgumentList "/quiet InstallAllUsers=1 PrependPath=1" -Wait
    # 刷新环境变量
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
    Write-Host "[1/6] Python 安装完成" -ForegroundColor Green
} else {
    Write-Host "[1/6] Python 已安装，跳过" -ForegroundColor Green
}

# 2. 安装 Git（如果未安装）
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Host "[2/6] 下载 Git..." -ForegroundColor Yellow
    $gitUrl = "https://github.com/git-for-windows/git/releases/download/v2.47.0.windows.1/Git-2.47.0-64-bit.exe"
    $gitInstaller = "$env:TEMP\git_installer.exe"
    Invoke-WebRequest -Uri $gitUrl -OutFile $gitInstaller -UseBasicParsing
    Write-Host "[2/6] 安装 Git（静默模式）..." -ForegroundColor Yellow
    Start-Process -FilePath $gitInstaller -ArgumentList "/VERYSILENT /NORESTART" -Wait
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
    Write-Host "[2/6] Git 安装完成" -ForegroundColor Green
} else {
    Write-Host "[2/6] Git 已安装，跳过" -ForegroundColor Green
}

# 3. 克隆 ERP 代码
$erpDir = "C:\ERP"
if (-not (Test-Path $erpDir)) {
    Write-Host "[3/6] 克隆 ERP 代码..." -ForegroundColor Yellow
    git clone https://github.com/TonyStark-2026/ERP.git $erpDir
    Write-Host "[3/6] 代码克隆完成" -ForegroundColor Green
} else {
    Write-Host "[3/6] ERP 目录已存在，跳过克隆" -ForegroundColor Green
}

# 4. 安装 Python 依赖
Write-Host "[4/6] 安装 Python 依赖..." -ForegroundColor Yellow
Set-Location $erpDir
pip install -r requirements.txt --quiet
Write-Host "[4/6] 依赖安装完成" -ForegroundColor Green

# 5. 开放防火墙端口
Write-Host "[5/6] 配置防火墙..." -ForegroundColor Yellow
New-NetFirewallRule -DisplayName "ERP 8000" -Direction Inbound -LocalPort 8000 -Protocol TCP -Action Allow -ErrorAction SilentlyContinue
Write-Host "[5/6] 防火墙已开放 8000 端口" -ForegroundColor Green

# 6. 创建启动脚本
Write-Host "[6/6] 创建启动脚本..." -ForegroundColor Yellow
$startScript = @"
@echo off
cd /d C:\ERP
python -m uvicorn backend.app:app --host 0.0.0.0 --port 8000
"@
$startScript | Out-File -FilePath "C:\ERP\启动ERP.bat" -Encoding ASCII
Write-Host "[6/6] 启动脚本已创建：C:\ERP\启动ERP.bat" -ForegroundColor Green

Write-Host "`n===== 部署完成！=====" -ForegroundColor Green
Write-Host "ERP 代码位置：C:\ERP" -ForegroundColor Cyan
Write-Host "启动方式：双击运行 C:\ERP\启动ERP.bat" -ForegroundColor Cyan
Write-Host "访问地址：http://47.107.104.0:8000" -ForegroundColor Cyan
Write-Host "`n注意：还需要上传数据库文件 erp_data.db 到 C:\ERP 目录" -ForegroundColor Yellow
