@echo off
chcp 65001 >nul
echo ========================================
echo    启动后端服务（集成 GitHub 高星项目）
echo ========================================
echo.

cd backend
python main.py --port 8765

pause

