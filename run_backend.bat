@echo off
chcp 65001 >nul
title Workforce Backend (:8000)
cd /d "%~dp0backend"
echo ============================================================
echo   Workforce Backend 服务启动中 (FastAPI :8000)
echo ============================================================
echo 正在激活虚拟环境并启动 Python 后端...
call "%~dp0backend\venv\Scripts\activate.bat"
python main.py
if errorlevel 1 (
    echo.
    echo [ERROR] 后端服务异常退出，请检查上方报错日志。
    pause
)
