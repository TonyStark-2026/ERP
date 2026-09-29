# PowerShell 脚本：scripts/new_daily_log.ps1
# 用途：在 dev-logs 目录下创建当日日志文件并注入模板内容

$today = Get-Date -Format yyyy-MM-dd
$logDir = Join-Path -Path (Resolve-Path ..\) -ChildPath "dev-logs"
# 如果脚本在项目根 scripts 下运行，则调整路径
$logDir = Join-Path -Path (Get-Location) -ChildPath "..\dev-logs"
$logDir = Resolve-Path $logDir
$target = Join-Path -Path $logDir -ChildPath ("$today.md")

if (Test-Path $target) {
    Write-Host "Log for $today already exists: $target"
    exit 0
}

$templatePath = Join-Path -Path $logDir -ChildPath "template.md"

if (Test-Path $templatePath) {
    Copy-Item -Path $templatePath -Destination $target
    Write-Host "Created new daily log: $target"
} else {
    $content = "# 开发日志 - $today`n`n- 今日完成：`n  - `n- 待办：`n  - `n- 阻塞/风险：`n  - `n- 关联提交/PR：`n  - `n- 备注：`n  - `n"
    $content | Out-File -FilePath $target -Encoding UTF8
    Write-Host "Created new daily log with default template: $target"
}
