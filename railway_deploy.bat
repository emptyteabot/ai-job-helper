@echo off
echo ============================================
echo Railway Deploy
echo ============================================
echo.

cd /d "c:\Users\陈盈桦\Desktop\Desktop_整理_2026-02-09_172732\Folders\自动投简历"

echo [1/7] Check Node.js...
node --version >nul 2>&1
if errorlevel 1 (
    echo Node.js not installed
    echo Please install from: https://nodejs.org
    pause
    exit /b 1
)
echo OK
echo.

echo [2/7] Check Railway CLI...
railway --version >nul 2>&1
if errorlevel 1 (
    echo Installing Railway CLI...
    npm install -g @railway/cli
    if errorlevel 1 (
        echo Install failed
        pause
        exit /b 1
    )
)
echo OK
echo.

echo [3/7] Login to Railway...
echo Browser will open, please login with GitHub
railway login
if errorlevel 1 (
    echo Login failed
    pause
    exit /b 1
)
echo.

echo [4/7] Create project...
railway init
if errorlevel 1 (
    echo Init failed
    pause
    exit /b 1
)
echo.

echo [5/7] Set environment variables...
echo.
echo Please enter your DeepSeek API Key:
set /p deepseek_key="DEEPSEEK_API_KEY: "
echo.

echo Generating CRAWLER_API_KEY...
python -c "import secrets; print(secrets.token_urlsafe(32))" > temp_key.txt
set /p crawler_key=<temp_key.txt
echo CRAWLER_API_KEY: %crawler_key%
echo.
echo IMPORTANT: Save this key for later!
echo.
pause
echo.

railway variables set DEEPSEEK_API_KEY=%deepseek_key%
railway variables set CRAWLER_API_KEY=%crawler_key%
railway variables set JOB_DATA_PROVIDER=cloud
railway variables set PORT=8000
echo.

echo [6/7] Deploy...
railway up
if errorlevel 1 (
    echo Deploy failed
    pause
    exit /b 1
)
echo.

echo [7/7] Generate domain...
railway domain
echo.

del temp_key.txt 2>nul

echo ============================================
echo SUCCESS!
echo ============================================
echo.
echo Your app URL (see above)
echo.
echo IMPORTANT: Save these:
echo 1. Your Railway URL
echo 2. CRAWLER_API_KEY: %crawler_key%
echo.
echo Next steps:
echo 1. Visit your Railway URL
echo 2. Test: https://your-url/api/health
echo 3. Configure local crawler
echo.

pause

