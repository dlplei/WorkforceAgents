# ==============================================================================
# Workforce Agents 开发环境一键启动脚本 (Windows Terminal 多标签页版)
# ==============================================================================
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

$RootDir = $PSScriptRoot
Set-Location $RootDir
$BackendDir = Join-Path $RootDir "backend"
$BackendBat = Join-Path $RootDir "run_backend.bat"
$FrontendBat = Join-Path $RootDir "run_frontend.bat"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "         Workforce Agents 开发环境一键启动工具               " -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "项目目录: $RootDir" -ForegroundColor Gray
Write-Host ""

# 1. 检查并按需启动 Podman 虚拟机
Write-Host "[1/4] 检查 Podman 虚拟机状态..." -ForegroundColor Yellow
$podmanCmd = Get-Command podman.exe -ErrorAction SilentlyContinue
if (-not $podmanCmd) {
    Write-Host "[ERROR] 系统未找到 podman 命令！" -ForegroundColor Red
    pause
    exit 1
}

try {
    $machineJson = podman machine list --format json 2>$null | ConvertFrom-Json
    $isRunning = $false
    foreach ($m in $machineJson) {
        if ($m.Running -eq $true) { $isRunning = $true; break }
    }
    if (-not $isRunning) {
        Write-Host ">>> Podman 虚拟机未运行，正在启动 (podman machine start)..." -ForegroundColor Cyan
        podman machine start
        Write-Host "[OK] Podman 虚拟机已就绪！" -ForegroundColor Green
    } else {
        Write-Host "[OK] Podman 虚拟机已处于运行状态。" -ForegroundColor Green
    }
} catch {
    Write-Host "[INFO] 虚拟机检测跳过，直接检查容器..." -ForegroundColor Gray
}

# 2. 启动容器组 (podman compose up -d)
Write-Host ""
Write-Host "[2/4] 正在启动后台容器 (Postgres, Chroma, Redis, Ollama, Prometheus, Grafana)..." -ForegroundColor Yellow
if (Test-Path (Join-Path $RootDir "docker-compose.yml")) {
    podman compose up -d
    Write-Host "[OK] 容器服务已启动！" -ForegroundColor Green
}

# 3. 通过 Windows Terminal 启动前端与后端 (多标签页)
Write-Host ""
Write-Host "[3/4] 正在通过 Windows Terminal 启动前端与后端..." -ForegroundColor Yellow
$wtCmd = Get-Command wt.exe -ErrorAction SilentlyContinue

if ($wtCmd) {
    $wtArgs = @(
        '--title', 'Workforce-Backend',
        '-d', $BackendDir,
        'cmd.exe', '/k', "`"$BackendBat`"",
        ';',
        'new-tab',
        '--title', 'Workforce-Frontend',
        '-d', $RootDir,
        'cmd.exe', '/k', "`"$FrontendBat`""
    )
    Start-Process "wt.exe" -ArgumentList $wtArgs
    Write-Host "[OK] Windows Terminal 已成功拉起后端与前端标签页！" -ForegroundColor Green
} else {
    Write-Host "[INFO] 未检测到 wt.exe，使用独立窗口启动..." -ForegroundColor Yellow
    Start-Process cmd.exe -ArgumentList "/k", "`"$BackendBat`""
    Start-Process cmd.exe -ArgumentList "/k", "`"$FrontendBat`""
}

# 4. 健康探测与打开浏览器
Write-Host ""
Write-Host "[4/4] 正在检测服务健康状态 (等待端口就绪)..." -ForegroundColor Yellow

$frontendReady = $false
$backendReady = $false
$frontendPort = 3000
$timeoutSeconds = 30
$sw = [System.Diagnostics.Stopwatch]::StartNew()

while ($sw.Elapsed.TotalSeconds -lt $timeoutSeconds) {
    if (-not $backendReady) {
        $backendConn = Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue
        if ($backendConn) {
            $backendReady = $true
            Write-Host "  -> [OK] 后端服务端口 (8000) 已就绪！" -ForegroundColor Green
        }
    }
    if (-not $frontendReady) {
        $fConn3000 = Get-NetTCPConnection -LocalPort 3000 -State Listen -ErrorAction SilentlyContinue
        $fConn5173 = Get-NetTCPConnection -LocalPort 5173 -State Listen -ErrorAction SilentlyContinue
        if ($fConn3000) {
            $frontendReady = $true
            $frontendPort = 3000
            Write-Host "  -> [OK] 前端服务端口 (3000) 已就绪！" -ForegroundColor Green
        } elseif ($fConn5173) {
            $frontendReady = $true
            $frontendPort = 5173
            Write-Host "  -> [OK] 前端服务端口 (5173) 已就绪！" -ForegroundColor Green
        }
    }
    if ($backendReady -and $frontendReady) {
        break
    }
    Start-Sleep -Milliseconds 1000
}

Write-Host ""
if ($frontendReady) {
    $frontendUrl = "http://localhost:$frontendPort"
    Write-Host "[OK] 前端服务已就绪，正在自动打开浏览器: $frontendUrl" -ForegroundColor Green
    try {
        Start-Process $frontendUrl
    } catch {}
} else {
    Write-Host "[WARNING] 前端服务在 $timeoutSeconds 秒内尚未就绪，请在 Windows Terminal 对应标签页查看报错。" -ForegroundColor Red
    Write-Host "          排查完成后可手动打开浏览器访问: http://localhost:3000" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  常用服务端口导航：" -ForegroundColor Green
Write-Host "  - 前端界面:      http://localhost:$frontendPort" -ForegroundColor White
Write-Host "  - 后端接口:      http://localhost:8000" -ForegroundColor White
Write-Host "  - 后端 API 文档: http://localhost:8000/docs" -ForegroundColor White
Write-Host "  - Grafana 监控:   http://localhost:3002 (admin/admin)" -ForegroundColor White
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "本引导窗口将在 5 秒后自动关闭..." -ForegroundColor Gray
Start-Sleep -Seconds 5
