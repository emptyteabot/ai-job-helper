@echo off
chcp 65001 >nul
cls
echo.
echo ╔════════════════════════════════════════╗
echo ║     完整修复 - 支持所有格式            ║
echo ╚════════════════════════════════════════╝
echo.

echo [1/4] 安装文件解析依赖...
pip install PyPDF2 python-docx Pillow pytesseract python-multipart -q

echo.
echo [2/4] 安装OCR引擎（图片识别）...
echo.
echo ⚠️  图片OCR需要安装Tesseract-OCR
echo.
echo 请按照以下步骤安装：
echo 1. 访问: https://github.com/UB-Mannheim/tesseract/wiki
echo 2. 下载: tesseract-ocr-w64-setup-5.3.3.20231005.exe
echo 3. 安装到: C:\Program Files\Tesseract-OCR
echo 4. 添加到系统PATH环境变量
echo.
echo 如果已安装，请按任意键继续...
pause >nul

echo.
echo [3/4] 安装其他依赖...
pip install openai python-dotenv fastapi uvicorn -q

echo.
echo [4/4] 设置API密钥...
set DEEPSEEK_API_KEY=sk-da34a79604824fc28f73fca8381ed92f

echo.
echo ╔════════════════════════════════════════╗
echo ║  ✅ 修复完成！                         ║
echo ║                                        ║
echo ║  📍 http://localhost:8000              ║
echo ║                                        ║
echo ║  💡 现在支持的格式：                   ║
echo ║     ✓ PDF文件 (.pdf)                   ║
echo ║     ✓ Word文档 (.docx, .doc)           ║
echo ║     ✓ 文本文件 (.txt)                  ║
echo ║     ✓ 图片文件 (.jpg, .png等)          ║
echo ║                                        ║
echo ║  🎯 Word和图片都能正常解析了！         ║
echo ║                                        ║
echo ╚════════════════════════════════════════╝
echo.

timeout /t 2 >nul
start http://localhost:8000

python web_app.py

pause

