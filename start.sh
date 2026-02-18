#!/bin/bash
# AI求职助手 - Streamlit 启动脚本

echo "========================================"
echo "  AI求职助手 - Streamlit 版本"
echo "========================================"
echo ""

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "[错误] 未找到 Python，请先安装 Python 3.8+"
    exit 1
fi

# 检查 Streamlit
if ! python3 -c "import streamlit" &> /dev/null; then
    echo "[提示] 正在安装依赖..."
    pip3 install -r requirements.txt
fi

echo "[启动] 正在启动应用..."
echo ""
echo "浏览器将自动打开 http://localhost:8501"
echo ""
echo "按 Ctrl+C 停止应用"
echo "========================================"
echo ""

streamlit run streamlit_app.py
