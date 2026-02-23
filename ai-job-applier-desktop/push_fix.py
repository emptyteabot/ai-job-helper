"""
推送代码到 GitHub
"""
import subprocess
import os

os.chdir(r"c:\Users\陈盈桦\Desktop\一人公司260222\ai-job-applier-desktop")

print("=" * 60)
print("推送代码到 GitHub")
print("=" * 60)

print("\n[1/3] 添加所有更改...")
subprocess.run(["git", "add", "."])

print("\n[2/3] 提交更改...")
subprocess.run(["git", "commit", "-m", "修复：删除开发环境假验证码提示，使用真实Boss直聘登录"])

print("\n[3/3] 推送到 GitHub...")
result = subprocess.run(["git", "push", "origin", "main"], capture_output=True, text=True)

if result.returncode == 0:
    print("\n✅ 推送成功！")
    print("\nStreamlit Cloud 将在 2-3 分钟内自动重新部署")
    print("访问: https://ai-job-apper-ibpzap2nnajzrnu8mkthuv.streamlit.app/")
else:
    print(f"\n❌ 推送失败: {result.stderr}")

print("\n" + "=" * 60)

