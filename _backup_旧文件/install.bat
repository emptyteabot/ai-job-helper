@echo off
echo 正在安装依赖...
pip install fastapi uvicorn websockets python-multipart python-dotenv openai PyPDF2 python-docx Pillow pytesseract
echo.
echo 依赖安装完成！
echo.
pause

