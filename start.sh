#!/bin/bash

echo "========================================"
echo "一人公司 AI Agent 系统 - 快速启动"
echo "========================================"
echo ""

# 检查 Python 是否安装
if ! command -v python3 &> /dev/null; then
    echo "[错误] 未检测到 Python，请先安装 Python 3.8+"
    exit 1
fi

echo "[1/3] 检查依赖..."
if ! python3 -c "import loguru" 2>/dev/null; then
    echo "[2/3] 安装依赖包..."
    pip3 install loguru -q
else
    echo "[2/3] 依赖已安装"
fi

echo "[3/3] 启动系统..."
echo ""
python3 main.py

