@echo off
chcp 65001 >nul
echo ========================================
echo 🔍 系统检查工具
echo ========================================
echo.

echo [1/5] 检查Python环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python未安装
    echo 请访问 https://www.python.org/downloads/ 下载安装
) else (
    python --version
    echo ✅ Python环境正常
)
echo.

echo [2/5] 检查Python依赖包...
python -c "import fastapi, uvicorn, openai, requests" 2>nul
if errorlevel 1 (
    echo ❌ 依赖包未完整安装
    echo 请运行：一键安装.bat
) else (
    echo ✅ 核心依赖包已安装
)
echo.

echo [3/5] 检查环境变量配置...
if exist .env (
    echo ✅ .env 文件存在
    findstr /C:"DEEPSEEK_API_KEY" .env >nul
    if errorlevel 1 (
        echo ⚠️ 未配置 DEEPSEEK_API_KEY
        echo 请编辑 .env 文件，填入您的API密钥
    ) else (
        echo ✅ DEEPSEEK_API_KEY 已配置
    )
) else (
    echo ⚠️ .env 文件不存在
    echo 请复制 env.example 为 .env 并配置
)
echo.

echo [4/5] 检查OpenClaw（可选）...
where openclaw >nul 2>&1
if errorlevel 1 (
    echo ⚠️ OpenClaw未安装（可选功能）
    echo 系统将使用本地模拟数据
) else (
    echo ✅ OpenClaw已安装
    openclaw --version
)
echo.

echo [5/5] 检查核心文件...
if exist web_app.py (
    echo ✅ web_app.py 存在
) else (
    echo ❌ web_app.py 不存在
)
if exist app\ (
    echo ✅ app/ 目录存在
) else (
    echo ❌ app/ 目录不存在
)
if exist static\ (
    echo ✅ static/ 目录存在
) else (
    echo ❌ static/ 目录不存在
)
echo.

echo ========================================
echo 📊 检查完成
echo ========================================
echo.
echo 💡 下一步：
echo   - 如果所有检查都通过，运行：启动网站.bat
echo   - 如果有错误，运行：一键安装.bat
echo.
pause

