@echo off
chcp 65001 >nul
echo.
echo ========================================
echo    AI求职助手 - 启动Web服务
echo ========================================
echo.

REM 检查Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误: 未找到Python
    pause
    exit /b 1
)

echo ✓ Python环境检查通过
echo.
echo 正在安装依赖...
pip install fastapi uvicorn python-dotenv openai -q

echo.
echo ✓ 依赖安装完成
echo.
echo 🚀 启动Web服务...
echo.
echo 📍 请在浏览器中打开: http://localhost:8000
echo.

python web_app.py

pause

