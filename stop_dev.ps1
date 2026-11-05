# ==============================================================================
# Workforce Agents 开发环境一键停止脚本
# 功能：
#   1. 停止监听在 8000 (FastAPI) 和 5173 (Vite) 端口上的前后端服务进程
#   2. 停止 Podman 容器 (podman compose stop)
#   3. 可选询问是否挂起 Podman 虚拟机 (释放 2GB 内存)
# ==============================================================================
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

$RootDir = $PSScriptRoot
Set-Location $RootDir

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "         Workforce Agents 开发环境一键停止工具               " -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# 1. 停止前后端进程 (按端口 8000 和 5173 查找并停止)
Write-Host "[1/3] 正在停止本地前端 (5173) 与后端 (8000) 进程..." -ForegroundColor Yellow

$targetPorts = @(8000, 3000, 5173)
foreach ($port in $targetPorts) {
    try {
        $conns = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
        if ($conns) {
            foreach ($conn in $conns) {
                $pId = $conn.OwningProcess
                if ($pId -and $pId -gt 0) {
                    $proc = Get-Process -Id $pId -ErrorAction SilentlyContinue
                    if ($proc) {
                        Write-Host "  -> 终止端口 $port 上的进程: $($proc.ProcessName) (PID: $pId)" -ForegroundColor Gray
                        Stop-Process -Id $pId -Force -ErrorAction SilentlyContinue
                    }
                }
            }
        }
    } catch {}
}
Write-Host "[OK] 前后端应用已停止。" -ForegroundColor Green

# 2. 停止后台 Podman 容器
Write-Host ""
Write-Host "[2/3] 正在暂停后台 Podman 容器 (podman compose stop)..." -ForegroundColor Yellow
if (Test-Path (Join-Path $RootDir "docker-compose.yml")) {
    podman compose stop
    Write-Host "[OK] 容器服务已暂停 (数据均完整保留)。" -ForegroundColor Green
}

# 3. 询问是否关闭 Podman 虚拟机
Write-Host ""
Write-Host "[3/3] 释放系统资源" -ForegroundColor Yellow
$response = Read-Host "是否同时停止 Podman 虚拟机以彻底释放 2GB 内存？(y/N, 默认 N)"
if ($response -match "^[yY]$") {
    Write-Host ">>> 正在停止 Podman 虚拟机 (podman machine stop)..." -ForegroundColor Cyan
    podman machine stop
    Write-Host "[OK] Podman 虚拟机已成功停止！" -ForegroundColor Green
} else {
    Write-Host "已保留 Podman 虚拟机运行，下次启动将更加迅速。" -ForegroundColor Gray
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  所有开发服务已安全停止！" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "窗口将在 3 秒后自动关闭..." -ForegroundColor Gray
Start-Sleep -Seconds 3
