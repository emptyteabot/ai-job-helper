@echo off
chcp 65001 >nul
echo ========================================
echo 推送代码到 GitHub 触发重新部署
echo ========================================

cd /d "%~dp0"

echo.
echo [1/3] 添加所有更改...
git add .

echo.
echo [2/3] 提交更改...
git commit -m "修复：删除开发环境假验证码提示，使用真实Boss直聘登录"

echo.
echo [3/3] 推送到 GitHub...
git push origin main

echo.
echo ========================================
echo ✅ 推送完成！
echo.
echo Streamlit Cloud 将在 2-3 分钟内自动重新部署
echo 访问: https://ai-job-apper-ibpzap2nnajzrnu8mkthuv.streamlit.app/
echo ========================================
echo.
pause

