#!/bin/bash

echo "========================================"
echo "Railway 部署监控"
echo "========================================"
echo ""
echo "代码已推送到 GitHub: https://github.com/emptyteabot/ai-job-helper"
echo "Railway 正在自动部署..."
echo ""
echo "预计部署时间: 2-3 分钟"
echo ""

while true; do
    echo "[$(date +%H:%M:%S)] 检查部署状态..."

    # 检查健康状态
    http_code=$(curl -s -o /dev/null -w "%{http_code}" https://ai-job-hunter-production-2730.up.railway.app/api/health)
    echo "HTTP 状态码: $http_code"

    # 检查 API 端点
    if [ "$http_code" = "200" ]; then
        echo "检查 /api/auto-apply/platforms 端点..."
        platforms=$(curl -s https://ai-job-hunter-production-2730.up.railway.app/api/auto-apply/platforms)

        if [[ $platforms == *"boss"* ]]; then
            echo ""
            echo "✅ 部署成功！所有 API 端点正常工作"
            echo ""
            echo "测试结果："
            echo "$platforms" | head -20
            echo ""
            echo "你现在可以访问："
            echo "- Streamlit: https://ai-job-apper-ibpzap2nnajzrnu8mkthuv.streamlit.app"
            echo "- Railway 后端: https://ai-job-hunter-production-2730.up.railway.app"
            break
        else
            echo "⏳ API 端点还未更新，继续等待..."
        fi
    else
        echo "⏳ 服务正在重启，继续等待..."
    fi

    echo ""
    sleep 10
done
