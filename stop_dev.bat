@echo off
chcp 65001 >nul
title Workforce Agents 停止工具
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0stop_dev.ps1"
