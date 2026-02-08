@echo off
cd /d "C:\Users\陈盈桦\Desktop\自动投简历"

echo Initializing Git...
git init

echo Configuring Git user...
git config user.name "emptyteabot"
git config user.email "13398580812@163.com"

echo Adding remote...
git remote remove origin 2>nul
git remote add origin https://github.com/emptyteabot/ai-job-helper.git

echo Adding files...
git add .

echo Committing...
git commit -m "Initial commit: AI Job Helper with Market-Driven Architecture"

echo Renaming branch to main...
git branch -M main

echo Pushing to GitHub...
git push -u origin main --force

echo Done!
pause

