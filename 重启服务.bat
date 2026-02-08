@echo off
echo.
echo 正在关闭占用8000端口的程序...
echo.

for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000') do (
    echo 找到进程: %%a
    taskkill /PID %%a /F
)

echo.
echo 端口已释放！
echo.
echo 现在启动服务...
echo.

python web_app.py

pause

