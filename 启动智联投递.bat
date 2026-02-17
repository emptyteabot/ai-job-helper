@echo off
chcp 65001 >nul
echo ========================================
echo 智联招聘自动投递器 - 快速启动
echo ========================================
echo.

echo [1/3] 检查依赖...
python -c "import DrissionPage" 2>nul
if errorlevel 1 (
    echo ❌ DrissionPage 未安装
    echo.
    echo 正在安装 DrissionPage...
    pip install DrissionPage>=4.0.0
    if errorlevel 1 (
        echo ❌ 安装失败，请手动运行: pip install DrissionPage
        pause
        exit /b 1
    )
    echo ✓ DrissionPage 安装成功
) else (
    echo ✓ DrissionPage 已安装
)

echo.
echo [2/3] 检查其他依赖...
pip install -q -r requirements.txt
if errorlevel 1 (
    echo ❌ 依赖安装失败
    pause
    exit /b 1
)
echo ✓ 依赖检查完成

echo.
echo [3/3] 启动测试脚本...
echo.
python test_zhilian.py

echo.
echo ========================================
echo 测试完成
echo ========================================
pause
