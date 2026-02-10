@echo off
chcp 65001 >nul
echo.
echo ========================================
echo    🚀 自动提交并部署到云端
echo ========================================
echo.

echo [1/4] 检查Git...
git --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 未安装Git，请先安装: https://git-scm.com
    pause
    exit /b 1
)
echo ✅ Git已安装
echo.

echo [2/4] 提交代码...
git add .
git commit -m "自动更新: %date% %time%"

git push origin main
if errorlevel 1 (
    echo.
    echo ⚠️  首次使用需要初始化Git仓库
    echo.
    echo 请按以下步骤操作：
    echo 1. 访问 https://github.com/new 创建新仓库
    echo 2. 仓库名称: ai-job-helper
    echo 3. 设置为Public
    echo 4. 不要勾选任何初始化选项
    echo 5. 创建后，复制仓库地址
    echo.
    set /p repo_url="请粘贴仓库地址（如 https://github.com/用户名/ai-job-helper.git）: "
    
    git init
    git add .
    git commit -m "初始提交"
    git branch -M main
    git remote add origin %repo_url%
    git push -u origin main
)
echo ✅ 代码已提交
echo.

echo [3/4] 部署到Vercel...
echo.
echo 请访问: https://vercel.com/new
echo 1. 使用GitHub登录
echo 2. 导入刚才创建的仓库
echo 3. 点击Deploy
echo 4. 等待部署完成
echo.
echo 或者使用Vercel CLI:
echo npm i -g vercel
echo vercel --prod
echo.

echo [4/4] 完成！
echo ========================================
echo.
echo ✅ 代码已提交到GitHub
echo 📍 GitHub仓库: %repo_url%
echo 🌐 Vercel部署: 请在Vercel控制台查看
echo.
echo 每次修改后运行此脚本即可自动部署！
echo ========================================
echo.

pause

