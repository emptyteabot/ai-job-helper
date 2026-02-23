@echo off
chcp 65001 >nul
echo ========================================
echo 重启后端服务
echo ========================================

echo.
echo [1/3] 停止旧的后端进程...
taskkill /F /IM python.exe /FI "WINDOWTITLE eq *main.py*" 2>nul
timeout /t 2 /nobreak >nul

echo.
echo [2/3] 启动新的后端服务...
cd /d "%~dp0backend"
start "AI求职助手后端" cmd /k "python main.py --port 8765"

echo.
echo [3/3] 等待后端启动...
timeout /t 5 /nobreak >nul

echo.
echo ========================================
echo ✅ 后端已重启！
echo 访问: http://localhost:8765/docs
echo ========================================
echo.
pause

