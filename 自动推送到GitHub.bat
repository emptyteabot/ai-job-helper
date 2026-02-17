@echo off
chcp 65001 >nul
echo.
echo ========================================
echo   🚀 自动Git推送
echo ========================================
echo.

REM 检查是否提供了提交信息
if "%*"=="" (
    set "commit_msg=Auto update - %date% %time%"
) else (
    set "commit_msg=%*"
)

echo 📝 提交信息: %commit_msg%
echo.

REM 运行Python脚本
python auto_git_push.py %commit_msg%

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ✅ 推送成功！
    echo 🌐 访问: https://github.com/emptyteabot/ai-job-helper
    echo 🚀 Railway会在几分钟内自动部署
) else (
    echo.
    echo ❌ 推送失败，请检查错误信息
)

echo.
pause

chcp 65001 >nul
echo.
echo ========================================
echo   🚀 自动Git推送
echo ========================================
echo.

REM 检查是否提供了提交信息
if "%*"=="" (
    set "commit_msg=Auto update - %date% %time%"
) else (
    set "commit_msg=%*"
)

echo 📝 提交信息: %commit_msg%
echo.

REM 运行Python脚本
python auto_git_push.py %commit_msg%

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ✅ 推送成功！
    echo 🌐 访问: https://github.com/emptyteabot/ai-job-helper
    echo 🚀 Railway会在几分钟内自动部署
) else (
    echo.
    echo ❌ 推送失败，请检查错误信息
)

echo.
pause

chcp 65001 >nul
echo.
echo ========================================
echo   🚀 自动Git推送
echo ========================================
echo.

REM 检查是否提供了提交信息
if "%*"=="" (
    set "commit_msg=Auto update - %date% %time%"
) else (
    set "commit_msg=%*"
)

echo 📝 提交信息: %commit_msg%
echo.

REM 运行Python脚本
python auto_git_push.py %commit_msg%

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ✅ 推送成功！
    echo 🌐 访问: https://github.com/emptyteabot/ai-job-helper
    echo 🚀 Railway会在几分钟内自动部署
) else (
    echo.
    echo ❌ 推送失败，请检查错误信息
)

echo.
pause

chcp 65001 >nul
echo.
echo ========================================
echo   🚀 自动Git推送
echo ========================================
echo.

REM 检查是否提供了提交信息
if "%*"=="" (
    set "commit_msg=Auto update - %date% %time%"
) else (
    set "commit_msg=%*"
)

echo 📝 提交信息: %commit_msg%
echo.

REM 运行Python脚本
python auto_git_push.py %commit_msg%

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ✅ 推送成功！
    echo 🌐 访问: https://github.com/emptyteabot/ai-job-helper
    echo 🚀 Railway会在几分钟内自动部署
) else (
    echo.
    echo ❌ 推送失败，请检查错误信息
)

echo.
pause



