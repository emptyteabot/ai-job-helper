@echo off
chcp 65001 >nul
echo ========================================
echo 🗂️ 文件夹整理工具
echo ========================================
echo.
echo 当前有太多重复的启动脚本和临时文件
echo 本脚本将帮您整理，只保留必要的文件
echo.
echo 📋 整理计划：
echo   - 保留 3 个核心启动脚本
echo   - 删除 20+ 个重复的启动脚本
echo   - 删除临时文件和过时脚本
echo   - 创建备份以防万一
echo.
set /p confirm="确认开始整理？(y/n): "
if /i not "%confirm%"=="y" (
    echo 已取消
    pause
    exit /b 0
)
echo.

echo [1/4] 创建备份文件夹...
if not exist "_backup_旧文件" mkdir "_backup_旧文件"
echo ✅ 备份文件夹已创建
echo.

echo [2/4] 移动重复的启动脚本到备份...
move "安装依赖.bat" "_backup_旧文件\" 2>nul
move "测试上传功能.bat" "_backup_旧文件\" 2>nul
move "快速测试.bat" "_backup_旧文件\" 2>nul
move "快速测试上传.bat" "_backup_旧文件\" 2>nul
move "快速启动.bat" "_backup_旧文件\" 2>nul
move "融资演示版启动.bat" "_backup_旧文件\" 2>nul
move "使用8001端口.bat" "_backup_旧文件\" 2>nul
move "完整修复启动.bat" "_backup_旧文件\" 2>nul
move "完整演示.bat" "_backup_旧文件\" 2>nul
move "新版界面启动.bat" "_backup_旧文件\" 2>nul
move "修复并启动.bat" "_backup_旧文件\" 2>nul
move "一键部署到公网.bat" "_backup_旧文件\" 2>nul
move "一键部署Railway.bat" "_backup_旧文件\" 2>nul
move "一键启动.bat" "_backup_旧文件\" 2>nul
move "亿级估值版启动.bat" "_backup_旧文件\" 2>nul
move "真实数据测试.bat" "_backup_旧文件\" 2>nul
move "重启服务.bat" "_backup_旧文件\" 2>nul
move "自动部署.bat" "_backup_旧文件\" 2>nul
move "最终版启动.bat" "_backup_旧文件\" 2>nul
move "install.bat" "_backup_旧文件\" 2>nul
move "start.bat" "_backup_旧文件\" 2>nul
echo ✅ 已移动 20+ 个重复的启动脚本
echo.

echo [3/4] 移动临时文件和过时脚本...
move "快速测试.py" "_backup_旧文件\" 2>nul
move "完整演示.py" "_backup_旧文件\" 2>nul
move "main.py" "_backup_旧文件\" 2>nul
move "测试上传.html" "_backup_旧文件\" 2>nul
move "~$云端部署指南.md" "_backup_旧文件\" 2>nul
move "云端部署指南.md" "_backup_旧文件\" 2>nul
move "auto-deploy.sh" "_backup_旧文件\" 2>nul
move "deploy.sh" "_backup_旧文件\" 2>nul
echo ✅ 已移动临时文件
echo.

echo [4/4] 整理完成！
echo.
echo ========================================
echo ✅ 文件夹整理完成
echo ========================================
echo.
echo 📁 保留的核心文件：
echo   ✅ 一键安装.bat       - 首次安装使用
echo   ✅ 启动网站.bat       - 日常启动使用
echo   ✅ 测试OpenClaw.bat   - 测试OpenClaw连接
echo.
echo 📦 备份位置：
echo   _backup_旧文件\
echo.
echo 💡 提示：
echo   - 如果一切正常，可以删除 _backup_旧文件 文件夹
echo   - 如果需要恢复，从备份文件夹中复制回来
echo.
echo 📖 详细说明：
echo   docs\文件整理方案.md
echo.
pause

