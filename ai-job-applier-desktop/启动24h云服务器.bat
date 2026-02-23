@echo off
chcp 65001 >nul
echo ========================================
echo    启动 24 小时云服务器
echo ========================================
echo.

cd backend

echo [1/3] 检查依赖...
pip show fastapi >nul 2>&1
if errorlevel 1 (
    echo 正在安装依赖...
    pip install -r requirements.txt
)

echo.
echo [2/3] 启动后端服务（端口 8765）...
echo.
echo 后端服务地址: http://localhost:8765
echo API 文档: http://localhost:8765/docs
echo.
echo ⚠️ 请保持此窗口打开，关闭后服务会停止
echo.

start "后端服务" python main.py --port 8765

echo.
echo [3/3] 启动 ngrok 公网隧道...
echo.
echo 请在新窗口运行: ngrok http 8765
echo.
echo ========================================
echo    服务启动完成！
echo ========================================
echo.
echo 下一步：
echo 1. 打开新命令行窗口
echo 2. 运行: ngrok http 8765
echo 3. 复制 ngrok 提供的公网地址
echo 4. 更新 Streamlit 前端的 BACKEND_URL
echo.
pause

