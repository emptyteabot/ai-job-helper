@echo off
chcp 65001 >nul
echo ============================================================
echo 🚀 AI求职助手 - Streamlit 自动投递界面
echo ============================================================
echo.

echo [1/2] 启动后端服务...
start "后端服务" cmd /k "cd /d "%~dp0" && python web_app.py"

timeout /t 3 /nobreak >nul

echo [2/2] 启动 Streamlit 界面...
echo.
echo 📍 访问地址:
echo    - Streamlit 界面: http://localhost:8501
echo    - 后端 API: http://localhost:8000
echo.
echo 按 Ctrl+C 停止服务
echo.

streamlit run streamlit_app.py
