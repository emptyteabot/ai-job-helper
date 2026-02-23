@echo off
chcp 65001 >nul
echo ========================================
echo 安装 Playwright 和浏览器
echo ========================================

echo.
echo [1/3] 安装 Playwright...
pip install playwright playwright-stealth

echo.
echo [2/3] 下载 Chromium 浏览器...
playwright install chromium

echo.
echo [3/3] 验证安装...
python -c "from playwright.sync_api import sync_playwright; print('✅ Playwright 安装成功')"

echo.
echo ========================================
echo ✅ 安装完成！
echo ========================================
echo.
pause

