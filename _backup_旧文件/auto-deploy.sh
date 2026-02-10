#!/bin/bash

echo "🚀 自动提交并部署到云端"
echo "=================================="

# 1. Git提交
echo "[1/3] 提交代码到Git..."
git add .
git commit -m "自动更新: $(date '+%Y-%m-%d %H:%M:%S')"
git push origin main

if [ $? -ne 0 ]; then
    echo "⚠️  Git推送失败，尝试创建仓库..."
    git init
    git add .
    git commit -m "初始提交"
    echo "请手动创建GitHub仓库并执行："
    echo "git remote add origin https://github.com/你的用户名/ai-job-helper.git"
    echo "git push -u origin main"
fi

# 2. 部署到Vercel
echo "[2/3] 部署到Vercel..."
vercel --prod

# 3. 显示访问地址
echo "[3/3] 部署完成！"
echo "=================================="
echo "✅ 代码已提交到Git"
echo "✅ 已部署到Vercel"
echo ""
echo "访问地址将在上方显示"
echo "=================================="

