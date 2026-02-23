"""
启动后端服务
"""
import subprocess
import sys
import os
from pathlib import Path

# 切换到 backend 目录
backend_dir = Path(__file__).parent / "backend"
os.chdir(backend_dir)

print("=" * 50)
print("启动 AI求职助手后端")
print("=" * 50)
print(f"工作目录: {backend_dir}")
print(f"端口: 8765")
print(f"文档: http://localhost:8765/docs")
print("=" * 50)
print()

# 启动后端
subprocess.run([sys.executable, "main.py", "--port", "8765"])

