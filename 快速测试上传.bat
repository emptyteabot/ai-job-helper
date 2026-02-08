@echo off
chcp 65001 >nul
cls
echo.
echo ════════════════════════════════════════
echo   快速测试上传功能
echo ════════════════════════════════════════
echo.
echo 步骤1: 启动服务
echo.

set DEEPSEEK_API_KEY=sk-da34a79604824fc28f73fca8381ed92f

start "AI求职助手" cmd /k "python web_app.py"

timeout /t 3 >nul

echo.
echo 步骤2: 打开测试页面
echo.

start http://localhost:8000

echo.
echo ════════════════════════════════════════
echo   上传按钮位置说明
echo ════════════════════════════════════════
echo.
echo 在打开的网页中，您会看到：
echo.
echo 1. 顶部：紫色背景，白色标题
echo 2. 中间：白色卡片
echo 3. 6个紫色的AI角色卡片
echo 4. 下面有个标签："📄 上传简历或输入内容："
echo 5. 标签下面就是上传按钮！
echo    ┌─────────────────────────────────┐
echo    │ 📎 点击上传简历文件             │
echo    │   （支持PDF、Word、TXT）        │
echo    └─────────────────────────────────┘
echo.
echo 6. 按钮是灰色的，占满整行
echo 7. 下面有个"或者"分隔线
echo 8. 再下面是文本框
echo.
echo ════════════════════════════════════════
echo.
echo 💡 提示：
echo   - 如果看不到按钮，按 Ctrl+F5 强制刷新
echo   - 或者关闭浏览器重新打开
echo.
echo 按任意键打开简化测试页面...
pause >nul

start 测试上传.html

echo.
echo ✅ 已打开两个页面：
echo    1. http://localhost:8000 (完整版)
echo    2. 测试上传.html (简化版)
echo.
echo 两个页面都可以测试上传功能！
echo.
pause

