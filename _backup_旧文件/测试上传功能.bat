@echo off
chcp 65001 >nul
cls
echo.
echo ╔════════════════════════════════════════╗
echo ║     测试文件上传功能                   ║
echo ╚════════════════════════════════════════╝
echo.
echo [1/2] 设置环境变量...
set DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
echo       ✓ 完成
echo.
echo [2/2] 启动服务...
echo.
echo ╔════════════════════════════════════════╗
echo ║  🚀 服务启动成功！                     ║
echo ║                                        ║
echo ║  📍 请在浏览器打开:                    ║
echo ║     http://localhost:8000              ║
echo ║                                        ║
echo ║  📎 上传功能位置:                      ║
echo ║     页面顶部有个大按钮                 ║
echo ║     "📎 点击上传简历文件"              ║
echo ║                                        ║
echo ║  💡 支持格式:                          ║
echo ║     - PDF文件 (.pdf)                   ║
echo ║     - Word文档 (.docx, .doc)           ║
echo ║     - 文本文件 (.txt)                  ║
echo ║                                        ║
echo ║  ⚠️  按 Ctrl+C 停止服务                ║
echo ╚════════════════════════════════════════╝
echo.

python web_app.py

pause

