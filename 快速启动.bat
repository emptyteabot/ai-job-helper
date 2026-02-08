@echo off
chcp 65001 >nul
echo.
echo ========================================
echo    AI求职助手 - 快速启动
echo ========================================
echo.

echo [1/3] 检查Python...
python --version
if errorlevel 1 (
    echo ❌ 未找到Python
    pause
    exit /b 1
)
echo ✅ Python正常
echo.

echo [2/3] 检查依赖...
python -c "import fastapi" 2>nul
if errorlevel 1 (
    echo ⚠️  缺少依赖，正在安装...
    call 安装依赖.bat
)
echo ✅ 依赖正常
echo.

echo [3/3] 启动服务...
echo.
echo ========================================
echo    🌐 访问地址
echo ========================================
echo.
echo 📍 官网首页: http://localhost:8000
echo 📍 应用页面: http://localhost:8000/app
echo 📍 API文档: http://localhost:8000/docs
echo.
echo 按 Ctrl+C 停止服务
echo ========================================
echo.

python web_app.py

pause

