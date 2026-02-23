@echo off
chcp 65001 >nul
echo ========================================
echo 修复并测试登录功能
echo ========================================

echo.
echo [1/4] 检查后端是否运行...
curl http://localhost:8765/docs >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ 后端未运行，正在启动...
    start "AI求职助手后端" cmd /k "cd /d %~dp0backend && python main.py --port 8765"
    echo 等待后端启动...
    timeout /t 10 /nobreak >nul
) else (
    echo ✅ 后端已运行
)

echo.
echo [2/4] 安装依赖...
pip install playwright playwright-stealth >nul 2>&1
playwright install chromium >nul 2>&1

echo.
echo [3/4] 运行测试...
python test_login.py

echo.
echo [4/4] 完成！
echo.
pause

