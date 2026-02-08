@echo off
chcp 65001 >nul
cls
echo.
echo ╔════════════════════════════════════════╗
echo ║     AI求职助手 - 一键部署到公网       ║
echo ╚════════════════════════════════════════╝
echo.
echo 请选择部署方式：
echo.
echo [1] ngrok内网穿透（最快，5分钟）
echo [2] Railway部署（推荐，免费）
echo [3] Render部署（免费）
echo [4] 查看详细教程
echo.
set /p choice=请输入选项 (1-4): 

if "%choice%"=="1" goto ngrok
if "%choice%"=="2" goto railway
if "%choice%"=="3" goto render
if "%choice%"=="4" goto tutorial
goto end

:ngrok
echo.
echo ════════════════════════════════════════
echo   方案1：ngrok内网穿透
echo ════════════════════════════════════════
echo.
echo 步骤：
echo 1. 访问 https://ngrok.com/download 下载ngrok
echo 2. 注册账号获取token
echo 3. 运行: ngrok authtoken 你的token
echo 4. 启动本地服务（双击 一键启动.bat）
echo 5. 新开终端运行: ngrok http 8000
echo 6. 复制生成的公网地址分享给朋友
echo.
echo 正在打开ngrok官网...
start https://ngrok.com/download
echo.
pause
goto end

:railway
echo.
echo ════════════════════════════════════════
echo   方案2：Railway部署
echo ════════════════════════════════════════
echo.
echo 步骤：
echo 1. 访问 https://railway.app/ 注册账号
echo 2. 点击 "New Project" → "Deploy from GitHub repo"
echo 3. 连接GitHub并选择仓库
echo 4. 添加环境变量：
echo    DEEPSEEK_API_KEY=sk-da34a79604824fc28f73fca8381ed92f
echo 5. 等待自动部署完成
echo 6. 获得公网域名：https://你的项目.up.railway.app
echo.
echo 正在打开Railway官网...
start https://railway.app/
echo.
pause
goto end

:render
echo.
echo ════════════════════════════════════════
echo   方案3：Render部署
echo ════════════════════════════════════════
echo.
echo 步骤：
echo 1. 访问 https://render.com/ 注册账号
echo 2. 点击 "New" → "Web Service"
echo 3. 连接GitHub仓库
echo 4. 配置：
echo    Build Command: pip install -r requirements.txt
echo    Start Command: uvicorn web_app:app --host 0.0.0.0 --port $PORT
echo 5. 添加环境变量：DEEPSEEK_API_KEY
echo 6. 点击 "Create Web Service"
echo 7. 等待部署完成
echo.
echo 正在打开Render官网...
start https://render.com/
echo.
pause
goto end

:tutorial
echo.
echo 正在打开详细教程...
start 部署到公网教程.md
pause
goto end

:end
echo.
echo 感谢使用！
pause

