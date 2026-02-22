@echo off
echo ========================================
echo 一人公司 AI Agent 系统 - 快速启动
echo ========================================
echo.

REM 检查 Python 是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到 Python，请先安装 Python 3.8+
    pause
    exit /b 1
)

echo [1/3] 检查依赖...
pip show loguru >nul 2>&1
if errorlevel 1 (
    echo [2/3] 安装依赖包...
    pip install loguru -q
) else (
    echo [2/3] 依赖已安装
)

echo [3/3] 启动系统...
echo.
python main.py

pause

