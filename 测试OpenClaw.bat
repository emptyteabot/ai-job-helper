@echo off
chcp 65001 >nul
echo ========================================
echo 🔍 OpenClaw 健康检查
echo ========================================
echo.

echo [1/4] 检查OpenClaw是否安装...
where openclaw >nul 2>&1
if errorlevel 1 (
    echo ❌ OpenClaw未安装
    echo.
    echo 📦 正在安装OpenClaw...
    pip install openclaw
    if errorlevel 1 (
        echo ❌ 安装失败，请检查网络连接
        pause
        exit /b 1
    )
    echo ✅ OpenClaw安装完成
) else (
    echo ✅ OpenClaw已安装
    openclaw --version
)
echo.

echo [2/4] 检查Chrome扩展...
echo 💡 如果Chrome中没有OpenClaw扩展，请运行：
echo    openclaw browser install-extension
echo.
set /p has_ext="Chrome中是否已安装OpenClaw扩展？(y/n): "
if /i not "%has_ext%"=="y" (
    echo.
    echo 📦 正在安装Chrome扩展...
    openclaw browser install-extension
    echo.
    echo ⚠️ 请重启Chrome浏览器后继续
    pause
)
echo.

echo [3/4] 启动OpenClaw浏览器...
echo 💡 这会打开一个受OpenClaw控制的Chrome窗口
echo.
start /B openclaw browser start
timeout /t 3 >nul
echo ✅ 浏览器已启动
echo.

echo [4/4] 连接指南...
echo.
echo 📋 请按以下步骤操作：
echo.
echo 1️⃣ 在打开的Chrome中访问Boss直聘
echo    https://www.zhipin.com
echo.
echo 2️⃣ 登录您的Boss直聘账号（如果还没登录）
echo.
echo 3️⃣ 点击Chrome右上角的OpenClaw扩展图标（🔧）
echo.
echo 4️⃣ 在弹出的面板中点击 "Attach" 按钮
echo.
echo 5️⃣ 看到 "✅ Connected" 提示即表示成功
echo.
echo ========================================
echo.
echo 💡 提示：连接一次后，只要不关闭浏览器就一直有效
echo.
echo 🔍 验证连接状态：
echo    访问 http://localhost:8000/api/health
echo.
pause

chcp 65001 >nul
echo ========================================
echo 🔍 OpenClaw 健康检查
echo ========================================
echo.

echo [1/4] 检查OpenClaw是否安装...
where openclaw >nul 2>&1
if errorlevel 1 (
    echo ❌ OpenClaw未安装
    echo.
    echo 📦 正在安装OpenClaw...
    pip install openclaw
    if errorlevel 1 (
        echo ❌ 安装失败，请检查网络连接
        pause
        exit /b 1
    )
    echo ✅ OpenClaw安装完成
) else (
    echo ✅ OpenClaw已安装
    openclaw --version
)
echo.

echo [2/4] 检查Chrome扩展...
echo 💡 如果Chrome中没有OpenClaw扩展，请运行：
echo    openclaw browser install-extension
echo.
set /p has_ext="Chrome中是否已安装OpenClaw扩展？(y/n): "
if /i not "%has_ext%"=="y" (
    echo.
    echo 📦 正在安装Chrome扩展...
    openclaw browser install-extension
    echo.
    echo ⚠️ 请重启Chrome浏览器后继续
    pause
)
echo.

echo [3/4] 启动OpenClaw浏览器...
echo 💡 这会打开一个受OpenClaw控制的Chrome窗口
echo.
start /B openclaw browser start
timeout /t 3 >nul
echo ✅ 浏览器已启动
echo.

echo [4/4] 连接指南...
echo.
echo 📋 请按以下步骤操作：
echo.
echo 1️⃣ 在打开的Chrome中访问Boss直聘
echo    https://www.zhipin.com
echo.
echo 2️⃣ 登录您的Boss直聘账号（如果还没登录）
echo.
echo 3️⃣ 点击Chrome右上角的OpenClaw扩展图标（🔧）
echo.
echo 4️⃣ 在弹出的面板中点击 "Attach" 按钮
echo.
echo 5️⃣ 看到 "✅ Connected" 提示即表示成功
echo.
echo ========================================
echo.
echo 💡 提示：连接一次后，只要不关闭浏览器就一直有效
echo.
echo 🔍 验证连接状态：
echo    访问 http://localhost:8000/api/health
echo.
pause

chcp 65001 >nul
echo ========================================
echo 🔍 OpenClaw 健康检查
echo ========================================
echo.

echo [1/4] 检查OpenClaw是否安装...
where openclaw >nul 2>&1
if errorlevel 1 (
    echo ❌ OpenClaw未安装
    echo.
    echo 📦 正在安装OpenClaw...
    pip install openclaw
    if errorlevel 1 (
        echo ❌ 安装失败，请检查网络连接
        pause
        exit /b 1
    )
    echo ✅ OpenClaw安装完成
) else (
    echo ✅ OpenClaw已安装
    openclaw --version
)
echo.

echo [2/4] 检查Chrome扩展...
echo 💡 如果Chrome中没有OpenClaw扩展，请运行：
echo    openclaw browser install-extension
echo.
set /p has_ext="Chrome中是否已安装OpenClaw扩展？(y/n): "
if /i not "%has_ext%"=="y" (
    echo.
    echo 📦 正在安装Chrome扩展...
    openclaw browser install-extension
    echo.
    echo ⚠️ 请重启Chrome浏览器后继续
    pause
)
echo.

echo [3/4] 启动OpenClaw浏览器...
echo 💡 这会打开一个受OpenClaw控制的Chrome窗口
echo.
start /B openclaw browser start
timeout /t 3 >nul
echo ✅ 浏览器已启动
echo.

echo [4/4] 连接指南...
echo.
echo 📋 请按以下步骤操作：
echo.
echo 1️⃣ 在打开的Chrome中访问Boss直聘
echo    https://www.zhipin.com
echo.
echo 2️⃣ 登录您的Boss直聘账号（如果还没登录）
echo.
echo 3️⃣ 点击Chrome右上角的OpenClaw扩展图标（🔧）
echo.
echo 4️⃣ 在弹出的面板中点击 "Attach" 按钮
echo.
echo 5️⃣ 看到 "✅ Connected" 提示即表示成功
echo.
echo ========================================
echo.
echo 💡 提示：连接一次后，只要不关闭浏览器就一直有效
echo.
echo 🔍 验证连接状态：
echo    访问 http://localhost:8000/api/health
echo.
pause

chcp 65001 >nul
echo ========================================
echo 🔍 OpenClaw 健康检查
echo ========================================
echo.

echo [1/4] 检查OpenClaw是否安装...
where openclaw >nul 2>&1
if errorlevel 1 (
    echo ❌ OpenClaw未安装
    echo.
    echo 📦 正在安装OpenClaw...
    pip install openclaw
    if errorlevel 1 (
        echo ❌ 安装失败，请检查网络连接
        pause
        exit /b 1
    )
    echo ✅ OpenClaw安装完成
) else (
    echo ✅ OpenClaw已安装
    openclaw --version
)
echo.

echo [2/4] 检查Chrome扩展...
echo 💡 如果Chrome中没有OpenClaw扩展，请运行：
echo    openclaw browser install-extension
echo.
set /p has_ext="Chrome中是否已安装OpenClaw扩展？(y/n): "
if /i not "%has_ext%"=="y" (
    echo.
    echo 📦 正在安装Chrome扩展...
    openclaw browser install-extension
    echo.
    echo ⚠️ 请重启Chrome浏览器后继续
    pause
)
echo.

echo [3/4] 启动OpenClaw浏览器...
echo 💡 这会打开一个受OpenClaw控制的Chrome窗口
echo.
start /B openclaw browser start
timeout /t 3 >nul
echo ✅ 浏览器已启动
echo.

echo [4/4] 连接指南...
echo.
echo 📋 请按以下步骤操作：
echo.
echo 1️⃣ 在打开的Chrome中访问Boss直聘
echo    https://www.zhipin.com
echo.
echo 2️⃣ 登录您的Boss直聘账号（如果还没登录）
echo.
echo 3️⃣ 点击Chrome右上角的OpenClaw扩展图标（🔧）
echo.
echo 4️⃣ 在弹出的面板中点击 "Attach" 按钮
echo.
echo 5️⃣ 看到 "✅ Connected" 提示即表示成功
echo.
echo ========================================
echo.
echo 💡 提示：连接一次后，只要不关闭浏览器就一直有效
echo.
echo 🔍 验证连接状态：
echo    访问 http://localhost:8000/api/health
echo.
pause



