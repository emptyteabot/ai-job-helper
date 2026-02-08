#!/bin/bash

echo "🚀 AI求职助手 - 一键部署到Railway"
echo "=================================="
echo ""

# 检查Railway CLI
if ! command -v railway &> /dev/null; then
    echo "📦 安装Railway CLI..."
    npm i -g @railway/cli
    if [ $? -ne 0 ]; then
        echo "❌ 安装失败，请手动安装: npm i -g @railway/cli"
        exit 1
    fi
fi

echo "✅ Railway CLI已安装"
echo ""

# 登录Railway
echo "🔐 登录Railway..."
railway login

if [ $? -ne 0 ]; then
    echo "❌ 登录失败"
    exit 1
fi

echo "✅ 登录成功"
echo ""

# 初始化项目
echo "📁 初始化项目..."
railway init

if [ $? -ne 0 ]; then
    echo "❌ 初始化失败"
    exit 1
fi

echo "✅ 项目初始化成功"
echo ""

# 添加环境变量
echo "🔑 配置环境变量..."
echo "请输入您的DeepSeek API Key:"
read -r api_key

railway variables set DEEPSEEK_API_KEY="$api_key"

if [ $? -ne 0 ]; then
    echo "❌ 环境变量配置失败"
    exit 1
fi

echo "✅ 环境变量配置成功"
echo ""

# 部署
echo "🚀 开始部署..."
railway up

if [ $? -ne 0 ]; then
    echo "❌ 部署失败"
    exit 1
fi

echo "✅ 部署成功"
echo ""

# 获取域名
echo "🌐 获取访问域名..."
railway domain

echo ""
echo "=================================="
echo "🎉 部署完成！"
echo "=================================="
echo ""
echo "📍 您的应用已上线，可以通过上面的域名访问"
echo "📊 查看日志: railway logs"
echo "⚙️  管理项目: railway open"
echo ""
echo "🎯 下一步:"
echo "1. 访问您的域名测试功能"
echo "2. 配置自定义域名（可选）"
echo "3. 开始推广您的产品！"
echo ""

