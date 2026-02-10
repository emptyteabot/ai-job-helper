@echo off
chcp 65001 >nul
echo.
echo ========================================
echo    安装所有依赖包
echo ========================================
echo.

echo [1/2] 安装核心依赖...
pip install fastapi==0.104.1 uvicorn[standard]==0.24.0 python-multipart==0.0.6 websockets==12.0 -i https://pypi.tuna.tsinghua.edu.cn/simple

if errorlevel 1 (
    echo.
    echo ❌ 核心依赖安装失败，尝试使用默认源...
    pip install fastapi uvicorn[standard] python-multipart websockets
)

echo.
echo [2/2] 安装其他依赖...
pip install python-dotenv openai PyPDF2 python-docx Pillow pytesseract -i https://pypi.tuna.tsinghua.edu.cn/simple

if errorlevel 1 (
    echo.
    echo ❌ 其他依赖安装失败，尝试使用默认源...
    pip install python-dotenv openai PyPDF2 python-docx Pillow pytesseract
)

echo.
echo ========================================
echo    ✅ 依赖安装完成！
echo ========================================
echo.
echo 现在可以运行:
echo   python web_app.py
echo.

pause

