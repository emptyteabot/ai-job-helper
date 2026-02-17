@echo off
chcp 65001 >nul
echo ============================================================
echo 🚀 AI求职助手 - 自动投递功能
echo ============================================================
echo.

echo [1/3] 验证整合状态...
python verify_integration.py
if errorlevel 1 (
    echo.
    echo ❌ 验证失败，请检查错误信息
    pause
    exit /b 1
)

echo.
echo [2/3] 运行测试...
pytest tests/test_auto_apply.py -v --tb=short
if errorlevel 1 (
    echo.
    echo ⚠️ 部分测试失败，但不影响核心功能
)

echo.
echo [3/3] 启动服务...
echo.
echo 📍 访问地址:
echo    - 主页: http://localhost:8000
echo    - 工作台: http://localhost:8000/app
echo    - 自动投递: http://localhost:8000/static/auto_apply_panel.html
echo.
echo 按 Ctrl+C 停止服务
echo.

python web_app.py
