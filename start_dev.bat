@echo off
chcp 65001 >nul
title Workforce Agents 启动器
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0start_dev.ps1"
