@echo off
chcp 65001 >nul
color 0E
title 本地启动 - 真实岗位模式

echo.
echo ========================================
echo   本地启动 - 真实岗位模式
echo ========================================
echo.

REM 检查Python
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo 错误：未安装Python
    echo 请访问：https://www.python.org/downloads/
    pause
    exit /b 1
)

echo Python已安装
echo.

REM 安装依赖
echo 正在安装依赖...
pip install -r requirements.txt -q
echo 依赖安装完成
echo.

REM 创建.env文件
if not exist .env (
    echo 创建配置文件...
    (
        echo DEEPSEEK_API_KEY=sk-d86589fb80f248cea3f4a843eaebce5a
        echo JOB_DATA_PROVIDER=local
        echo PORT=8000
    ) > .env
    echo 配置文件已创建
)
echo.

echo ========================================
echo   启动服务
echo ========================================
echo.
echo 本地地址：http://localhost:8000/app
echo.
echo 提示：
echo   - 按 Ctrl+C 停止服务
echo   - 浏览器会自动打开
echo.

timeout /t 2 /nobreak >nul
start http://localhost:8000/app

python web_app.py

pause

