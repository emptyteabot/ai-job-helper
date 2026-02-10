@echo off
chcp 65001 >nul
cls
echo.
echo ════════════════════════════════════════
echo   修复依赖并启动服务
echo ════════════════════════════════════════
echo.

echo [1/3] 安装缺失的依赖包...
pip install PyPDF2 python-docx python-multipart -q

echo.
echo [2/3] 设置API密钥...
set DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

echo.
echo [3/3] 启动服务...
echo.
echo ╔════════════════════════════════════════╗
echo ║  🚀 服务已启动！                       ║
echo ║                                        ║
echo ║  📍 http://localhost:8000              ║
echo ║                                        ║
echo ║  💡 使用方法：                         ║
echo ║     1. 点击上传按钮                    ║
echo ║     2. 选择简历文件                    ║
echo ║     3. 自动开始AI处理！                ║
echo ║     （不需要再点其他按钮）             ║
echo ║                                        ║
echo ╚════════════════════════════════════════╝
echo.

python web_app.py

pause

