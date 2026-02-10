@echo off
chcp 65001 >nul
echo.
echo ========================================
echo    AI求职助手 - 快速测试
echo ========================================
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误: 未找到Python，请先安装Python 3.8+
    pause
    exit /b 1
)

REM 检查API密钥
if "%DEEPSEEK_API_KEY%"=="" (
    echo ⚠️  警告: 未设置 DEEPSEEK_API_KEY 环境变量
    echo.
    echo 请先设置API密钥:
    echo set DEEPSEEK_API_KEY=你的API密钥
    echo.
    pause
    exit /b 1
)

echo ✓ Python环境检查通过
echo ✓ API密钥已配置
echo.
echo 正在启动多AI协作系统...
echo.

python 快速测试.py

echo.
pause

