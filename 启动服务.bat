@echo off
chcp 65001 >nul
color 0A
title AI求职助手 - 一键启动

echo.
echo ========================================
echo   🤖 AI求职助手 - 一键启动
echo ========================================
echo.
echo 正在启动所有服务...
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ❌ 错误：未检测到Python
    echo 请先安装Python 3.11+
    echo 下载地址：https://www.python.org/downloads/
    pause
    exit /b 1
)

echo ✅ Python已安装
echo.

REM 检查依赖是否安装
echo 📦 检查依赖...
pip show fastapi >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ⚠️ 依赖未安装，正在安装...
    pip install -r requirements.txt
    if %ERRORLEVEL% NEQ 0 (
        echo ❌ 依赖安装失败
        pause
        exit /b 1
    )
    echo ✅ 依赖安装成功
) else (
    echo ✅ 依赖已安装
)
echo.

REM 检查环境变量
if not exist .env (
    echo ⚠️ 未找到.env文件，正在创建...
    (
        echo # AI求职助手 - 环境变量配置
        echo.
        echo # DeepSeek API密钥（必填）
        echo DEEPSEEK_API_KEY=sk-d86589fb80f248cea3f4a843eaebce5a
        echo.
        echo # 爬虫API密钥（可选）
        echo CRAWLER_API_KEY=SGSAc_Oxm4A7vyoF6VdjW70_Q27hLvrC9opFGynGB_8
        echo.
        echo # 岗位数据提供方式（local=本地模拟, cloud=云端, openclaw=本地OpenClaw）
        echo JOB_DATA_PROVIDER=local
        echo.
        echo # 服务端口
        echo PORT=8000
    ) > .env
    echo ✅ .env文件已创建
)
echo.

echo ========================================
echo   🚀 启动服务
echo ========================================
echo.
echo 📍 本地地址：http://localhost:8000
echo 📍 应用页面：http://localhost:8000/app
echo 📍 API文档：http://localhost:8000/docs
echo.
echo 💡 提示：
echo   - 按 Ctrl+C 停止服务
echo   - 浏览器会自动打开
echo   - 手机访问请使用电脑IP地址
echo.
echo ========================================
echo.

REM 等待2秒后自动打开浏览器
timeout /t 2 /nobreak >nul
start http://localhost:8000/app

REM 启动Web服务
echo 🚀 正在启动Web服务...
echo.
python web_app.py

pause

chcp 65001 >nul
color 0A
title AI求职助手 - 一键启动

echo.
echo ========================================
echo   🤖 AI求职助手 - 一键启动
echo ========================================
echo.
echo 正在启动所有服务...
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ❌ 错误：未检测到Python
    echo 请先安装Python 3.11+
    echo 下载地址：https://www.python.org/downloads/
    pause
    exit /b 1
)

echo ✅ Python已安装
echo.

REM 检查依赖是否安装
echo 📦 检查依赖...
pip show fastapi >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ⚠️ 依赖未安装，正在安装...
    pip install -r requirements.txt
    if %ERRORLEVEL% NEQ 0 (
        echo ❌ 依赖安装失败
        pause
        exit /b 1
    )
    echo ✅ 依赖安装成功
) else (
    echo ✅ 依赖已安装
)
echo.

REM 检查环境变量
if not exist .env (
    echo ⚠️ 未找到.env文件，正在创建...
    (
        echo # AI求职助手 - 环境变量配置
        echo.
        echo # DeepSeek API密钥（必填）
        echo DEEPSEEK_API_KEY=sk-d86589fb80f248cea3f4a843eaebce5a
        echo.
        echo # 爬虫API密钥（可选）
        echo CRAWLER_API_KEY=SGSAc_Oxm4A7vyoF6VdjW70_Q27hLvrC9opFGynGB_8
        echo.
        echo # 岗位数据提供方式（local=本地模拟, cloud=云端, openclaw=本地OpenClaw）
        echo JOB_DATA_PROVIDER=local
        echo.
        echo # 服务端口
        echo PORT=8000
    ) > .env
    echo ✅ .env文件已创建
)
echo.

echo ========================================
echo   🚀 启动服务
echo ========================================
echo.
echo 📍 本地地址：http://localhost:8000
echo 📍 应用页面：http://localhost:8000/app
echo 📍 API文档：http://localhost:8000/docs
echo.
echo 💡 提示：
echo   - 按 Ctrl+C 停止服务
echo   - 浏览器会自动打开
echo   - 手机访问请使用电脑IP地址
echo.
echo ========================================
echo.

REM 等待2秒后自动打开浏览器
timeout /t 2 /nobreak >nul
start http://localhost:8000/app

REM 启动Web服务
echo 🚀 正在启动Web服务...
echo.
python web_app.py

pause

chcp 65001 >nul
color 0A
title AI求职助手 - 一键启动

echo.
echo ========================================
echo   🤖 AI求职助手 - 一键启动
echo ========================================
echo.
echo 正在启动所有服务...
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ❌ 错误：未检测到Python
    echo 请先安装Python 3.11+
    echo 下载地址：https://www.python.org/downloads/
    pause
    exit /b 1
)

echo ✅ Python已安装
echo.

REM 检查依赖是否安装
echo 📦 检查依赖...
pip show fastapi >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ⚠️ 依赖未安装，正在安装...
    pip install -r requirements.txt
    if %ERRORLEVEL% NEQ 0 (
        echo ❌ 依赖安装失败
        pause
        exit /b 1
    )
    echo ✅ 依赖安装成功
) else (
    echo ✅ 依赖已安装
)
echo.

REM 检查环境变量
if not exist .env (
    echo ⚠️ 未找到.env文件，正在创建...
    (
        echo # AI求职助手 - 环境变量配置
        echo.
        echo # DeepSeek API密钥（必填）
        echo DEEPSEEK_API_KEY=sk-d86589fb80f248cea3f4a843eaebce5a
        echo.
        echo # 爬虫API密钥（可选）
        echo CRAWLER_API_KEY=SGSAc_Oxm4A7vyoF6VdjW70_Q27hLvrC9opFGynGB_8
        echo.
        echo # 岗位数据提供方式（local=本地模拟, cloud=云端, openclaw=本地OpenClaw）
        echo JOB_DATA_PROVIDER=local
        echo.
        echo # 服务端口
        echo PORT=8000
    ) > .env
    echo ✅ .env文件已创建
)
echo.

echo ========================================
echo   🚀 启动服务
echo ========================================
echo.
echo 📍 本地地址：http://localhost:8000
echo 📍 应用页面：http://localhost:8000/app
echo 📍 API文档：http://localhost:8000/docs
echo.
echo 💡 提示：
echo   - 按 Ctrl+C 停止服务
echo   - 浏览器会自动打开
echo   - 手机访问请使用电脑IP地址
echo.
echo ========================================
echo.

REM 等待2秒后自动打开浏览器
timeout /t 2 /nobreak >nul
start http://localhost:8000/app

REM 启动Web服务
echo 🚀 正在启动Web服务...
echo.
python web_app.py

pause

chcp 65001 >nul
color 0A
title AI求职助手 - 一键启动

echo.
echo ========================================
echo   🤖 AI求职助手 - 一键启动
echo ========================================
echo.
echo 正在启动所有服务...
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ❌ 错误：未检测到Python
    echo 请先安装Python 3.11+
    echo 下载地址：https://www.python.org/downloads/
    pause
    exit /b 1
)

echo ✅ Python已安装
echo.

REM 检查依赖是否安装
echo 📦 检查依赖...
pip show fastapi >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ⚠️ 依赖未安装，正在安装...
    pip install -r requirements.txt
    if %ERRORLEVEL% NEQ 0 (
        echo ❌ 依赖安装失败
        pause
        exit /b 1
    )
    echo ✅ 依赖安装成功
) else (
    echo ✅ 依赖已安装
)
echo.

REM 检查环境变量
if not exist .env (
    echo ⚠️ 未找到.env文件，正在创建...
    (
        echo # AI求职助手 - 环境变量配置
        echo.
        echo # DeepSeek API密钥（必填）
        echo DEEPSEEK_API_KEY=sk-d86589fb80f248cea3f4a843eaebce5a
        echo.
        echo # 爬虫API密钥（可选）
        echo CRAWLER_API_KEY=SGSAc_Oxm4A7vyoF6VdjW70_Q27hLvrC9opFGynGB_8
        echo.
        echo # 岗位数据提供方式（local=本地模拟, cloud=云端, openclaw=本地OpenClaw）
        echo JOB_DATA_PROVIDER=local
        echo.
        echo # 服务端口
        echo PORT=8000
    ) > .env
    echo ✅ .env文件已创建
)
echo.

echo ========================================
echo   🚀 启动服务
echo ========================================
echo.
echo 📍 本地地址：http://localhost:8000
echo 📍 应用页面：http://localhost:8000/app
echo 📍 API文档：http://localhost:8000/docs
echo.
echo 💡 提示：
echo   - 按 Ctrl+C 停止服务
echo   - 浏览器会自动打开
echo   - 手机访问请使用电脑IP地址
echo.
echo ========================================
echo.

REM 等待2秒后自动打开浏览器
timeout /t 2 /nobreak >nul
start http://localhost:8000/app

REM 启动Web服务
echo 🚀 正在启动Web服务...
echo.
python web_app.py

pause



