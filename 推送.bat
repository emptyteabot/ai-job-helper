@echo off
cd /d "%~dp0"
git add .
git commit -m "UI upgrade"
git push
echo.
echo ===================================
echo 推送完成！
echo ===================================
echo.
echo 等待2-3分钟后，用手机访问：
echo https://ai-job-hunter-production-2730.up.railway.app/app
echo.
pause

