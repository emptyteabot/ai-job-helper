@echo off
chcp 65001 >nul
echo ========================================
echo 🚀 AI求职助手 - 一键安装脚本
echo ========================================
echo.

echo [1/5] 检查Python环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 未检测到Python，请先安装Python 3.8+
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)
echo ✅ Python环境正常
echo.

echo [2/5] 安装Python依赖包...
pip install -r requirements.txt
if errorlevel 1 (
    echo ❌ 依赖安装失败，请检查网络连接
    pause
    exit /b 1
)
echo ✅ Python依赖安装完成
echo.

echo [3/5] 检查OpenClaw（浏览器自动化工具）...
where openclaw >nul 2>&1
if errorlevel 1 (
    echo ⚠️ OpenClaw未安装（这是正常的）
    echo.
    echo 💡 OpenClaw是可选功能，用于抓取Boss直聘真实岗位
    echo    不安装也可以正常使用，系统会使用本地模拟数据
    echo.
    echo 📖 如需安装OpenClaw，请访问：
    echo    https://github.com/getcursor/openclaw
    echo.
) else (
    echo ✅ OpenClaw已安装
    openclaw --version
)
echo.

echo [4/5] 配置环境变量...
if not exist .env (
    if exist env.example (
        copy env.example .env >nul
        echo ✅ 已创建 .env 文件
        echo.
        echo ⚠️ 重要：请编辑 .env 文件，填入您的 DeepSeek API Key
        echo 获取地址: https://platform.deepseek.com/api_keys
        echo.
        notepad .env
    ) else (
        echo ⚠️ 未找到 env.example 模板
    )
) else (
    echo ✅ .env 文件已存在
)
echo.

echo [5/5] 安装Chrome扩展（可选，用于OpenClaw）...
echo.
where openclaw >nul 2>&1
if errorlevel 1 (
    echo ⚠️ 跳过（OpenClaw未安装）
    echo.
) else (
    echo 📋 手动安装步骤：
    echo 1. 打开Chrome浏览器
    echo 2. 访问: chrome://extensions/
    echo 3. 开启右上角的"开发者模式"
    echo 4. 运行命令: openclaw browser install-extension
    echo 5. 按照提示完成安装
    echo.
    set /p install_ext="是否现在安装Chrome扩展？(y/n): "
    if /i "%install_ext%"=="y" (
        openclaw browser install-extension
        if errorlevel 1 (
            echo ⚠️ 扩展安装失败，请手动安装
        ) else (
            echo ✅ Chrome扩展安装完成
        )
    )
)
echo.

echo ========================================
echo ✅ 安装完成！
echo ========================================
echo.
echo 📖 下一步操作：
echo.
echo 1. 确保 .env 文件中已配置 DEEPSEEK_API_KEY
echo 2. 运行 "启动网站.bat" 启动服务
echo 3. 浏览器访问 http://localhost:8000/app
echo.
echo 💡 使用说明：
echo    - 不使用OpenClaw：系统会使用本地模拟数据（推荐新手）
echo    - 使用OpenClaw：可以抓取Boss直聘真实岗位
echo      安装方法见：docs/完整使用指南.md
echo.
echo 📚 详细文档: docs/howto/OPENCLAW_BOSS_MVP.md
echo.
pause


echo ========================================
echo 🚀 AI求职助手 - 一键安装脚本
echo ========================================
echo.

echo [1/5] 检查Python环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 未检测到Python，请先安装Python 3.8+
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)
echo ✅ Python环境正常
echo.

echo [2/5] 安装Python依赖包...
pip install -r requirements.txt
if errorlevel 1 (
    echo ❌ 依赖安装失败，请检查网络连接
    pause
    exit /b 1
)
echo ✅ Python依赖安装完成
echo.

echo [3/5] 检查OpenClaw（浏览器自动化工具）...
where openclaw >nul 2>&1
if errorlevel 1 (
    echo ⚠️ OpenClaw未安装（这是正常的）
    echo.
    echo 💡 OpenClaw是可选功能，用于抓取Boss直聘真实岗位
    echo    不安装也可以正常使用，系统会使用本地模拟数据
    echo.
    echo 📖 如需安装OpenClaw，请访问：
    echo    https://github.com/getcursor/openclaw
    echo.
) else (
    echo ✅ OpenClaw已安装
    openclaw --version
)
echo.

echo [4/5] 配置环境变量...
if not exist .env (
    if exist env.example (
        copy env.example .env >nul
        echo ✅ 已创建 .env 文件
        echo.
        echo ⚠️ 重要：请编辑 .env 文件，填入您的 DeepSeek API Key
        echo 获取地址: https://platform.deepseek.com/api_keys
        echo.
        notepad .env
    ) else (
        echo ⚠️ 未找到 env.example 模板
    )
) else (
    echo ✅ .env 文件已存在
)
echo.

echo [5/5] 安装Chrome扩展（可选，用于OpenClaw）...
echo.
where openclaw >nul 2>&1
if errorlevel 1 (
    echo ⚠️ 跳过（OpenClaw未安装）
    echo.
) else (
    echo 📋 手动安装步骤：
    echo 1. 打开Chrome浏览器
    echo 2. 访问: chrome://extensions/
    echo 3. 开启右上角的"开发者模式"
    echo 4. 运行命令: openclaw browser install-extension
    echo 5. 按照提示完成安装
    echo.
    set /p install_ext="是否现在安装Chrome扩展？(y/n): "
    if /i "%install_ext%"=="y" (
        openclaw browser install-extension
        if errorlevel 1 (
            echo ⚠️ 扩展安装失败，请手动安装
        ) else (
            echo ✅ Chrome扩展安装完成
        )
    )
)
echo.

echo ========================================
echo ✅ 安装完成！
echo ========================================
echo.
echo 📖 下一步操作：
echo.
echo 1. 确保 .env 文件中已配置 DEEPSEEK_API_KEY
echo 2. 运行 "启动网站.bat" 启动服务
echo 3. 浏览器访问 http://localhost:8000/app
echo.
echo 💡 使用说明：
echo    - 不使用OpenClaw：系统会使用本地模拟数据（推荐新手）
echo    - 使用OpenClaw：可以抓取Boss直聘真实岗位
echo      安装方法见：docs/完整使用指南.md
echo.
echo 📚 详细文档: docs/howto/OPENCLAW_BOSS_MVP.md
echo.
pause

