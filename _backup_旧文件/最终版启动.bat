@echo off
chcp 65001 >nul
cls
echo.
echo ╔════════════════════════════════════════╗
echo ║     AI求职助手 - 最终版启动            ║
echo ╚════════════════════════════════════════╝
echo.

echo [1/3] 安装所有依赖包...
pip install PyPDF2 python-docx python-multipart openai python-dotenv fastapi uvicorn -q

if errorlevel 1 (
    echo.
    echo ❌ 依赖安装失败，请检查网络连接
    pause
    exit /b 1
)

echo       ✓ 依赖安装完成
echo.

echo [2/3] 设置API密钥...
set DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
echo       ✓ API密钥已配置
echo.

echo [3/3] 启动服务...
echo.
echo ╔════════════════════════════════════════╗
echo ║  🎉 服务启动成功！                     ║
echo ║                                        ║
echo ║  📍 访问地址:                          ║
echo ║     http://localhost:8000              ║
echo ║                                        ║
echo ║  💡 使用方法（超简单）:                ║
echo ║                                        ║
echo ║  1️⃣  点击上传按钮                      ║
echo ║  2️⃣  选择简历文件                      ║
echo ║  3️⃣  自动开始AI处理！                  ║
echo ║                                        ║
echo ║  ✨ 不需要点其他任何按钮！             ║
echo ║     上传完自动处理！                   ║
echo ║                                        ║
echo ║  📎 支持格式:                          ║
echo ║     - PDF (.pdf)                       ║
echo ║     - Word (.docx, .doc)               ║
echo ║     - 文本 (.txt)                      ║
echo ║                                        ║
echo ║  ⚠️  按 Ctrl+C 停止服务                ║
echo ╚════════════════════════════════════════╝
echo.

timeout /t 2 >nul
start http://localhost:8000

python web_app.py

pause

