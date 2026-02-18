@echo off
echo ========================================
echo Railway 部署监控
echo ========================================
echo.
echo 代码已推送到 GitHub: https://github.com/emptyteabot/ai-job-helper
echo Railway 正在自动部署...
echo.
echo 预计部署时间: 2-3 分钟
echo.

:loop
echo [%time%] 检查部署状态...
curl -s -o nul -w "HTTP 状态码: %%{http_code}\n" https://ai-job-hunter-production-2730.up.railway.app/api/health

timeout /t 10 /nobreak >nul
goto loop
