$ErrorActionPreference = "Stop"

# 使用Unicode转义字符构建文件路径
$txtPath = "C:\Users\ruancanling\Desktop\`u5927`u6570`u636e`u5728`u8d22`u52a1`u7ba1`u7406`u4e2d`u7684`u5e94`u7528`u7814`u7a76`u8bba`u6587.txt"
$docxPath = "C:\Users\ruancanling\Desktop\`u5927`u6570`u636e`u5728`u8d22`u52a1`u7ba1`u7406`u4e2d`u7684`u5e94`u7528`u7814`u7a76`u8bba`u6587.docx"

Write-Output "Txt path: $txtPath"
Write-Output "Docx path: $docxPath"

# 检查文件是否存在
if (-not (Test-Path $txtPath)) {
    Write-Error "Source file not found: $txtPath"
    Get-ChildItem "C:\Users\ruancanling\Desktop\*.txt" | ForEach-Object { Write-Output $_.Name }
    exit 1
}

# 使用Word COM对象
try {
    $word = New-Object -ComObject Word.Application
    $word.Visible = $false
    Write-Output "Word application started"
    
    $doc = $word.Documents.Open($txtPath)
    Write-Output "Document opened"
    
    $doc.SaveAs2($docxPath, 16)
    Write-Output "Document saved as docx"
    
    $doc.Close()
    Write-Output "Document closed"
    
    $word.Quit()
    Write-Output "Word application closed"
    
    [System.Runtime.Interopservices.Marshal]::ReleaseComObject($word) | Out-Null
    
    Write-Output "Conversion completed successfully"
} catch {
    Write-Error "Error: $_"
    exit 1
}