@echo off
chcp 65001 >nul
title Workforce Frontend (:3000)
cd /d "%~dp0"
echo ============================================================
echo   Workforce Frontend 服务启动中 (Vite :3000)
echo ============================================================
echo 正在启动 Vite 前端开发服务器...
call npm.cmd run dev
if errorlevel 1 (
    echo.
    echo [ERROR] 前端服务异常退出，请检查上方报错日志。
    pause
)
