@echo off
REM AI求职助手 - Streamlit 启动脚本

echo ========================================
echo   AI求职助手 - Streamlit 版本
echo ========================================
echo.

REM 检查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Python，请先安装 Python 3.8+
    pause
    exit /b 1
)

REM 检查 Streamlit
python -c "import streamlit" >nul 2>&1
if errorlevel 1 (
    echo [提示] 正在安装依赖...
    pip install -r requirements.txt
)

echo [启动] 正在启动应用...
echo.
echo 浏览器将自动打开 http://localhost:8501
echo.
echo 按 Ctrl+C 停止应用
echo ========================================
echo.

streamlit run streamlit_app.py

pause
