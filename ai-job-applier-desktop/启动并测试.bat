@echo off
chcp 65001 >nul
title 修复并启动后端

echo ========================================
echo 修复登录功能并启动后端
echo ========================================

echo.
echo [1/3] 停止旧的后端进程...
taskkill /F /IM python.exe 2>nul
timeout /t 2 /nobreak >nul

echo.
echo [2/3] 启动后端服务...
cd /d "%~dp0backend"
start "AI求职助手后端" cmd /k "python main.py --port 8765"

echo.
echo [3/3] 等待后端启动...
timeout /t 8 /nobreak >nul

echo.
echo ========================================
echo ✅ 后端已启动！
echo.
echo 访问文档: http://localhost:8765/docs
echo ngrok 地址: https://unleisured-polly-welcomingly.ngrok-free.dev
echo.
echo 现在可以在 Streamlit 前端测试登录功能了
echo ========================================
echo.
pause

