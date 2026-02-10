@echo off
echo.
echo 使用8001端口启动服务...
echo.
echo 访问地址: http://localhost:8001
echo 应用页面: http://localhost:8001/app
echo.

set PORT=8001
python web_app.py

pause

