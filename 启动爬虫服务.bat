@echo off
chcp 65001 >nul
echo ========================================
echo 🤖 OpenClaw爬虫服务启动
echo ========================================
echo.

echo [1/3] 检查配置文件...
if not exist crawler.env (
    if exist crawler.env.example (
        copy crawler.env.example crawler.env >nul
        echo ⚠️ 已创建 crawler.env 文件
        echo 请编辑 crawler.env 文件，配置云端API地址和密钥
        echo.
        notepad crawler.env
        echo.
        echo 配置完成后，请重新运行此脚本
        pause
        exit /b 1
    ) else (
        echo ❌ 缺少配置文件
        pause
        exit /b 1
    )
)
echo ✅ 配置文件存在
echo.

echo [2/3] 检查OpenClaw...
where openclaw >nul 2>&1
if errorlevel 1 (
    echo ❌ OpenClaw未安装
    echo 请先安装OpenClaw：
    echo   访问 https://github.com/getcursor/openclaw
    pause
    exit /b 1
)
echo ✅ OpenClaw已安装
echo.

echo [3/3] 启动爬虫服务...
echo.
echo ⚠️ 重要提示：
echo   1. 请确保Chrome已打开Boss直聘并登录
echo   2. 请确保OpenClaw扩展已Attach到标签页
echo   3. 保持浏览器窗口不要关闭
echo.
set /p confirm="确认已完成上述步骤？(y/n): "
if /i not "%confirm%"=="y" (
    echo 已取消
    pause
    exit /b 0
)
echo.

echo 🚀 启动爬虫服务...
python openclaw_crawler_service.py

pause

