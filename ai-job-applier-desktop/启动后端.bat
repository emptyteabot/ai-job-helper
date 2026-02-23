@echo off
chcp 65001 >nul
title AI求职助手后端

cd /d "%~dp0backend"

echo ========================================
echo 启动 AI求职助手后端服务
echo ========================================
echo.
echo 端口: 8765
echo 文档: http://localhost:8765/docs
echo.

python main.py --port 8765

pause

