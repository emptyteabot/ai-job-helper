@echo off
chcp 65001 >nul
cls
echo.
echo ╔════════════════════════════════════════╗
echo ║     AI求职助手 - 一键启动网站          ║
echo ╚════════════════════════════════════════╝
echo.
echo [1/3] 设置API密钥...
set DEEPSEEK_API_KEY=sk-da34a79604824fc28f73fca8381ed92f
echo       ✓ API密钥已配置
echo.
echo [2/3] 安装依赖包...
pip install fastapi uvicorn python-dotenv openai -q 2>nul
echo       ✓ 依赖安装完成
echo.
echo [3/3] 启动Web服务...
echo.
echo ╔════════════════════════════════════════╗
echo ║  🚀 服务已启动！                       ║
echo ║                                        ║
echo ║  📍 请在浏览器打开:                    ║
echo ║     http://localhost:8000              ║
echo ║                                        ║
echo ║  💡 使用说明:                          ║
echo ║     1. 在网页中输入简历                ║
echo ║     2. 点击"开始AI协作"                ║
echo ║     3. 等待1-2分钟                     ║
echo ║     4. 查看6个AI的协作结果             ║
echo ║                                        ║
echo ║  ⚠️  按 Ctrl+C 可停止服务              ║
echo ╚════════════════════════════════════════╝
echo.

python web_app.py

pause
