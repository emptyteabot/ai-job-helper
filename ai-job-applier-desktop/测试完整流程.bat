@echo off
chcp 65001 >nul
echo ========================================
echo 🚀 Boss 直聘自动投递 - 完整测试
echo ========================================
echo.

echo [1/3] 测试 BossApplier 导入...
python test_boss_applier.py
if errorlevel 1 (
    echo ❌ BossApplier 导入失败
    pause
    exit /b 1
)
echo.

echo [2/3] 启动后端服务...
cd backend
start "后端服务" cmd /k "python main.py --port 8765"
echo ✅ 后端服务已启动（端口 8765）
echo.

timeout /t 3 >nul

echo [3/3] 启动前端应用...
cd ..\electron
start "前端应用" cmd /k "npm run dev"
echo ✅ 前端应用已启动
echo.

echo ========================================
echo ✅ 所有服务已启动！
echo ========================================
echo.
echo 📋 测试步骤：
echo 1. 等待前端应用打开
echo 2. 点击左侧菜单 "自动投递"
echo 3. 输入手机号，点击 "获取验证码"
echo 4. 输入收到的验证码，点击 "确认登录"
echo 5. 填写岗位信息，点击 "开始自动投递"
echo.
echo 💡 提示：
echo - 后端地址: http://localhost:8765
echo - API 文档: http://localhost:8765/docs
echo - 浏览器会自动打开并保持运行
echo.
pause

