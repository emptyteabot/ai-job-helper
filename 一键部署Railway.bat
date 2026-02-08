@echo off
chcp 65001 >nul
echo.
echo ========================================
echo    AI求职助手 - 一键部署到Railway
echo ========================================
echo.

echo [1/5] 检查Node.js环境...
node --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 未找到Node.js，请先安装: https://nodejs.org
    pause
    exit /b 1
)
echo ✅ Node.js环境正常
echo.

echo [2/5] 检查Railway CLI...
railway --version >nul 2>&1
if errorlevel 1 (
    echo 📦 安装Railway CLI...
    npm i -g @railway/cli
    if errorlevel 1 (
        echo ❌ 安装失败
        pause
        exit /b 1
    )
)
echo ✅ Railway CLI已安装
echo.

echo [3/5] 登录Railway...
echo 浏览器将打开，请完成登录...
railway login
if errorlevel 1 (
    echo ❌ 登录失败
    pause
    exit /b 1
)
echo ✅ 登录成功
echo.

echo [4/5] 初始化项目...
railway init
if errorlevel 1 (
    echo ❌ 初始化失败
    pause
    exit /b 1
)
echo ✅ 项目初始化成功
echo.

echo [5/5] 配置环境变量...
set /p api_key="请输入您的DeepSeek API Key: "
railway variables set DEEPSEEK_API_KEY=%api_key%
if errorlevel 1 (
    echo ❌ 环境变量配置失败
    pause
    exit /b 1
)
echo ✅ 环境变量配置成功
echo.

echo ========================================
echo    🚀 开始部署...
echo ========================================
echo.

railway up

if errorlevel 1 (
    echo ❌ 部署失败
    pause
    exit /b 1
)

echo.
echo ========================================
echo    🎉 部署成功！
echo ========================================
echo.

echo 🌐 获取访问域名...
railway domain

echo.
echo ========================================
echo    📝 后续操作
echo ========================================
echo.
echo 📊 查看日志: railway logs
echo ⚙️  管理项目: railway open
echo 🌐 自定义域名: railway domain
echo.
echo 🎯 下一步:
echo 1. 访问上面的域名测试功能
echo 2. 配置自定义域名（可选）
echo 3. 开始推广您的产品！
echo.
echo ========================================
echo.

pause

