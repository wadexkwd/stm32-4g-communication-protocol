# PowerShell 脚本用于运行地图测试
Write-Host "===== 开始运行地图测试 =====" -ForegroundColor Green

# 获取当前目录
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Definition
Write-Host "脚本路径: $scriptPath"
Set-Location $scriptPath

# 运行测试
Write-Host "`n1. 运行 test_map_fixed.py" -ForegroundColor Yellow
try {
    $startTime = Get-Date
    Write-Host "运行时间: $($startTime.ToString('yyyy-MM-dd HH:mm:ss'))"
    $output = & python test_map_fixed.py 2>&1
    
    Write-Host "输出:" -ForegroundColor Cyan
    $output
} catch {
    Write-Host "错误: $_" -ForegroundColor Red
}

Write-Host "`n===== 测试完成 =====" -ForegroundColor Green