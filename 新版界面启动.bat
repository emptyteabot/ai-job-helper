@echo off
chcp 65001 >nul
cls
color 0A
echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║                                                            ║
echo ║          🎨 AI求职助手 - 新版界面启动 🎨                  ║
echo ║                                                            ║
echo ║          OpenAI风格 + 实时进度条                          ║
echo ║                                                            ║
echo ╚════════════════════════════════════════════════════════════╝
echo.
echo.
echo ════════════════════════════════════════════════════════════
echo   系统初始化中...
echo ════════════════════════════════════════════════════════════
echo.

echo [1/4] 检查环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python未安装
    pause
    exit /b 1
)
echo ✓ Python环境正常

echo.
echo [2/4] 安装依赖...
pip install openai python-dotenv fastapi uvicorn PyPDF2 python-docx Pillow python-multipart -q
echo ✓ 依赖安装完成

echo.
echo [3/4] 配置API密钥...
set DEEPSEEK_API_KEY=sk-da34a79604824fc28f73fca8381ed92f
echo ✓ API密钥已配置

echo.
echo [4/4] 启动服务...
echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║                                                            ║
echo ║  🎉 新版界面启动成功！                                     ║
echo ║                                                            ║
echo ║  ✨ 新特性:                                                ║
echo ║     • OpenAI风格的深色主题                                 ║
echo ║     • 实时进度条显示                                       ║
echo ║     • 流畅的动画效果                                       ║
echo ║     • 现代化的卡片设计                                     ║
echo ║     • AI处理状态实时显示                                   ║
echo ║                                                            ║
echo ║  📍 访问地址: http://localhost:8000                        ║
echo ║                                                            ║
echo ║  💡 使用方法:                                              ║
echo ║     1. 上传简历或粘贴内容                                  ║
echo ║     2. 点击"开始AI分析"                                    ║
echo ║     3. 观看实时进度条                                      ║
echo ║     4. 查看AI协作结果                                      ║
echo ║                                                            ║
echo ╚════════════════════════════════════════════════════════════╝
echo.
echo.
echo 正在打开浏览器...
timeout /t 2 >nul
start http://localhost:8000

echo.
echo ════════════════════════════════════════════════════════════
echo   服务运行中... 按 Ctrl+C 停止
echo ════════════════════════════════════════════════════════════
echo.

python web_app.py

pause

