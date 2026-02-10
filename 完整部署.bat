@echo off
chcp 65001 >nul
color 0B
title AI求职助手 - 完整部署

echo.
echo ========================================
echo   🚀 AI求职助手 - 完整部署流程
echo ========================================
echo.
echo 本脚本将帮您完成：
echo   1. 推送代码到GitHub
echo   2. 自动部署到Railway
echo   3. 启动本地保活服务
echo   4. 启动本地爬虫服务（可选）
echo.
pause

REM 步骤1：推送到GitHub
echo.
echo ========================================
echo   📤 步骤1：推送代码到GitHub
echo ========================================
echo.
python auto_git_push.py "完整部署更新"
if %ERRORLEVEL% NEQ 0 (
    echo ❌ GitHub推送失败
    pause
    exit /b 1
)
echo ✅ GitHub推送成功
echo.

REM 步骤2：等待Railway部署
echo.
echo ========================================
echo   ⏰ 步骤2：等待Railway自动部署
echo ========================================
echo.
echo Railway正在自动部署，预计需要2-3分钟...
echo 您可以访问以下地址查看部署状态：
echo https://railway.com/project/0d756c19-9686-43c6-91cd-5af8357f473b
echo.
echo 等待中...
timeout /t 180 /nobreak
echo.
echo ✅ 部署应该已完成
echo.

REM 步骤3：测试云端服务
echo.
echo ========================================
echo   🧪 步骤3：测试云端服务
echo ========================================
echo.
echo 正在打开云端网站...
start https://ai-job-hunter-production-2730.up.railway.app/app
echo.
echo 请在浏览器中测试以下功能：
echo   - 上传简历
echo   - AI分析
echo   - 查看结果
echo.
pause

REM 步骤4：启动保活服务
echo.
echo ========================================
echo   🔋 步骤4：启动保活服务
echo ========================================
echo.
echo 保活服务会每5分钟ping一次云端，防止休眠
echo.
set /p start_keepalive="是否启动保活服务？(Y/N): "
if /i "%start_keepalive%"=="Y" (
    echo 正在启动保活服务...
    start "保活服务" cmd /k python keep_alive.py
    echo ✅ 保活服务已在新窗口启动
) else (
    echo ⏭️ 跳过保活服务
)
echo.

REM 步骤5：启动爬虫服务
echo.
echo ========================================
echo   🕷️ 步骤5：启动爬虫服务（可选）
echo ========================================
echo.
echo 爬虫服务会定时抓取Boss直聘真实岗位
echo 需要先安装并配置OpenClaw
echo.
set /p start_crawler="是否启动爬虫服务？(Y/N): "
if /i "%start_crawler%"=="Y" (
    echo 正在启动爬虫服务...
    start "爬虫服务" cmd /k python openclaw_crawler_service.py
    echo ✅ 爬虫服务已在新窗口启动
) else (
    echo ⏭️ 跳过爬虫服务
)
echo.

REM 完成
echo.
echo ========================================
echo   🎉 部署完成！
echo ========================================
echo.
echo 📍 云端地址：
echo    https://ai-job-hunter-production-2730.up.railway.app
echo.
echo 📍 GitHub仓库：
echo    https://github.com/emptyteabot/ai-job-helper
echo.
echo 📍 Railway控制台：
echo    https://railway.com/project/0d756c19-9686-43c6-91cd-5af8357f473b
echo.
echo 💡 提示：
echo    - 保活服务会持续运行，防止休眠
echo    - 爬虫服务会定时抓取岗位数据
echo    - 代码更新后会自动部署到云端
echo.
echo 🎊 现在可以分享给朋友使用了！
echo.
pause

