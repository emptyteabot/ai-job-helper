@echo off
chcp 65001
cd /d "%~dp0electron"
echo 正在启动前端开发服务器...
npm run dev
pause





