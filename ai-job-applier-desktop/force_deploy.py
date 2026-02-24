"""
强制触发 Streamlit Cloud 重新部署
"""
import subprocess
import os
import time

os.chdir(r"c:\Users\陈盈桦\Desktop\一人公司260222\ai-job-applier-desktop")

print("=" * 60)
print("强制触发 Streamlit Cloud 重新部署")
print("=" * 60)

# 创建一个空的提交来触发部署
print("\n[1] 创建空提交触发部署...")
subprocess.run(["git", "commit", "--allow-empty", "-m", "触发重新部署：删除假验证码"])

print("\n[2] 推送到 GitHub...")
result = subprocess.run(["git", "push", "origin", "main"], capture_output=True, text=True)

if result.returncode == 0:
    print("\n" + "=" * 60)
    print("✅ 推送成功！")
    print("=" * 60)
    print("\n📋 接下来的步骤：")
    print("\n1. 访问 Streamlit Cloud 控制台：")
    print("   https://share.streamlit.io/")
    print("\n2. 找到你的应用")
    print("\n3. 点击右上角的 ⋮ (三个点)")
    print("\n4. 选择 'Reboot app' 或 'Clear cache'")
    print("\n5. 等待 2-3 分钟重新部署")
    print("\n6. 访问：https://ai-job-apper-ibpzap2nnajzrnu8mkthuv.streamlit.app/")
    print("\n" + "=" * 60)
else:
    print(f"\n❌ 推送失败：{result.stderr}")

