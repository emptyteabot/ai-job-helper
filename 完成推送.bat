@echo off
chcp 65001 >nul
cd /d "C:\Users\陈盈桦\Desktop\Desktop_整理_2026-02-09_172732\Folders\自动投简历"
echo 正在拉取远程更改...
git pull --rebase
echo.
echo 正在推送到GitHub...
git push
echo.
echo 完成！
echo.
echo 等待2-3分钟后，访问网站测试：
echo https://ai-job-hunter-production-2730.up.railway.app/app
echo.
pause



