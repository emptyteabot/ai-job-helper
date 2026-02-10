@echo off
echo ============================================
echo Git Push to GitHub
echo ============================================
echo.

cd /d "c:\Users\陈盈桦\Desktop\Desktop_整理_2026-02-09_172732\Folders\自动投简历"

echo [1/6] Check Git...
if not exist .git (
    echo Init Git...
    git init
)
echo.

echo [2/6] Add remote...
git remote remove origin 2>nul
git remote add origin https://github.com/emptyteabot/ai-job-helper.git
echo.

echo [3/6] Add files...
git add web_app.py requirements.txt Procfile render.yaml runtime.txt README.md
git add app/ static/ data/
echo.

echo [4/6] Commit...
git commit -m "Update project files"
echo.

echo [5/6] Set branch...
git branch -M main
echo.

echo [6/6] Push to GitHub...
echo Please login if prompted...
git push -u origin main --force
echo.

if %errorlevel%==0 (
    echo ============================================
    echo SUCCESS!
    echo ============================================
    echo.
    echo Next: Visit https://github.com/emptyteabot/ai-job-helper
    echo.
) else (
    echo ============================================
    echo FAILED - Please use GitHub Desktop
    echo ============================================
    echo.
)

pause

echo ============================================
echo Git Push to GitHub
echo ============================================
echo.

cd /d "c:\Users\陈盈桦\Desktop\Desktop_整理_2026-02-09_172732\Folders\自动投简历"

echo [1/6] Check Git...
if not exist .git (
    echo Init Git...
    git init
)
echo.

echo [2/6] Add remote...
git remote remove origin 2>nul
git remote add origin https://github.com/emptyteabot/ai-job-helper.git
echo.

echo [3/6] Add files...
git add web_app.py requirements.txt Procfile render.yaml runtime.txt README.md
git add app/ static/ data/
echo.

echo [4/6] Commit...
git commit -m "Update project files"
echo.

echo [5/6] Set branch...
git branch -M main
echo.

echo [6/6] Push to GitHub...
echo Please login if prompted...
git push -u origin main --force
echo.

if %errorlevel%==0 (
    echo ============================================
    echo SUCCESS!
    echo ============================================
    echo.
    echo Next: Visit https://github.com/emptyteabot/ai-job-helper
    echo.
) else (
    echo ============================================
    echo FAILED - Please use GitHub Desktop
    echo ============================================
    echo.
)

pause

