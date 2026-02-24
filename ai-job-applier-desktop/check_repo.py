"""
检查并创建你自己的 GitHub 仓库
"""
import subprocess
import os

os.chdir(r"c:\Users\陈盈桦\Desktop\一人公司260222\ai-job-applier-desktop")

print("=" * 60)
print("检查 GitHub 仓库配置")
print("=" * 60)

# 检查当前远程仓库
print("\n[1] 当前远程仓库：")
result = subprocess.run(["git", "remote", "-v"], capture_output=True, text=True)
print(result.stdout)

print("\n" + "=" * 60)
print("解决方案")
print("=" * 60)

print("""
问题：你没有权限访问 emptyteabot/ai-job-helper

解决方案 1：Fork 这个仓库（推荐）
1. 访问：https://github.com/emptyteabot/ai-job-helper
2. 点击右上角 "Fork" 按钮
3. Fork 到你自己的账号下
4. 然后在 Streamlit Cloud 部署你 Fork 的仓库

解决方案 2：创建你自己的新仓库
1. 访问：https://github.com/new
2. 创建新仓库，例如：ai-job-helper-mine
3. 运行以下命令更改远程仓库：
   git remote set-url origin https://github.com/你的用户名/ai-job-helper-mine.git
   git push -u origin main
4. 然后在 Streamlit Cloud 部署你的新仓库

解决方案 3：使用 Hugging Face Spaces（最简单）
1. 访问：https://huggingface.co/spaces
2. 创建新 Space，选择 Streamlit
3. 上传 streamlit_app.py
4. 自动部署，完全免费
5. 域名：your-app.hf.space
""")

print("\n推荐：使用 Hugging Face Spaces，完全免费且无需 GitHub 权限")
print("=" * 60)

