# ==============================================================================
# 在桌面创建 Workforce Agents 一键启动与一键停止的快捷方式
# ==============================================================================
$RootDir = $PSScriptRoot
$DesktopPath = [Environment]::GetFolderPath("Desktop")
$WshShell = New-Object -ComObject WScript.Shell

# 1. 启动快捷方式
$s1 = $WshShell.CreateShortcut("$DesktopPath\Start_Workforce.lnk")
$s1.TargetPath = (Join-Path $RootDir "start_dev.bat")
$s1.WorkingDirectory = $RootDir
$s1.Description = "Start Workforce Agents (Podman + Containers + Backend + Frontend)"
$s1.IconLocation = "$env:SystemRoot\System32\shell32.dll,24" # 绿色启动图标
$s1.Save()
Write-Host "[OK] 已创建桌面快捷方式: Start_Workforce.lnk" -ForegroundColor Green

# 2. 停止快捷方式
$s2 = $WshShell.CreateShortcut("$DesktopPath\Stop_Workforce.lnk")
$s2.TargetPath = (Join-Path $RootDir "stop_dev.bat")
$s2.WorkingDirectory = $RootDir
$s2.Description = "Stop Workforce Agents (Podman + Backend + Frontend)"
$s2.IconLocation = "$env:SystemRoot\System32\shell32.dll,27" # 红色停止图标
$s2.Save()
Write-Host "[OK] 已创建桌面快捷方式: Stop_Workforce.lnk" -ForegroundColor Green
