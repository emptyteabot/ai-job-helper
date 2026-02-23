"""
检查并推送到正确的 GitHub 仓库
"""
import subprocess
import os

# 切换到项目目录
project_dir = r"c:\Users\陈盈桦\Desktop\一人公司260222\ai-job-applier-desktop"
os.chdir(project_dir)

print("=" * 60)
print("检查 Git 远程仓库配置")
print("=" * 60)

# 检查当前远程仓库
print("\n[1] 当前远程仓库：")
result = subprocess.run(["git", "remote", "-v"], capture_output=True, text=True)
print(result.stdout)

current_remote = result.stdout

# 检查是否是正确的仓库
if "emptyteabot/ai-job-helper" in current_remote:
    print("✅ 远程仓库正确：emptyteabot/ai-job-helper")
    
    print("\n[2] 添加所有更改...")
    subprocess.run(["git", "add", "."])
    
    print("\n[3] 提交更改...")
    subprocess.run(["git", "commit", "-m", "修复：删除假验证码，使用真实Boss登录+Gemini渐变UI"])
    
    print("\n[4] 推送到 GitHub...")
    result = subprocess.run(["git", "push", "origin", "main"], capture_output=True, text=True)
    
    if result.returncode == 0:
        print("\n" + "=" * 60)
        print("✅ 推送成功到 emptyteabot/ai-job-helper！")
        print("=" * 60)
        print("\nStreamlit Cloud 将在 2-3 分钟内自动部署")
        print("访问：https://ai-job-apper-ibpzap2nnajzrnu8mkthuv.streamlit.app/")
    else:
        print(f"\n❌ 推送失败：{result.stderr}")
else:
    print("❌ 远程仓库不正确！")
    print("\n需要设置为：https://github.com/emptyteabot/ai-job-helper")
    print("\n运行以下命令修复：")
    print("git remote set-url origin https://github.com/emptyteabot/ai-job-helper.git")

