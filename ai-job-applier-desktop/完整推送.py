"""
完整推送到 GitHub 并触发 Streamlit Cloud 部署
"""
import subprocess
import os

os.chdir(r"c:\Users\陈盈桦\Desktop\一人公司260222\ai-job-applier-desktop")

print("=" * 60)
print("推送完整更新到 GitHub")
print("=" * 60)

print("\n[1/4] 检查 Git 状态...")
result = subprocess.run(["git", "status", "--short"], capture_output=True, text=True)
print(result.stdout)

print("\n[2/4] 添加所有更改...")
subprocess.run(["git", "add", "."])

print("\n[3/4] 提交更改...")
subprocess.run(["git", "commit", "-m", "完整WebSaaS：修复登录+简历分析+自动投递+Gemini渐变UI"])

print("\n[4/4] 推送到 GitHub...")
result = subprocess.run(["git", "push", "origin", "main"], capture_output=True, text=True)

if result.returncode == 0:
    print("\n" + "=" * 60)
    print("✅ 推送成功！")
    print("=" * 60)
    print("\n📋 部署信息：")
    print("- Streamlit Cloud 将在 2-3 分钟内自动重新部署")
    print("- 访问地址：https://ai-job-apper-ibpzap2nnajzrnu8mkthuv.streamlit.app/")
    print("\n🎯 功能清单：")
    print("  ✅ 简历分析（4个AI Agent）")
    print("  ✅ Boss 直聘自动投递（三步流程）")
    print("  ✅ Gemini 渐变背景 + OpenAI 打字机字体")
    print("  ✅ 真实 Boss 直聘登录（无假验证码）")
    print("\n⏳ 等待 2-3 分钟后访问查看更新！")
    print("=" * 60)
else:
    print(f"\n❌ 推送失败: {result.stderr}")
    print("\n可能的原因：")
    print("1. 没有配置 Git 远程仓库")
    print("2. 没有权限推送")
    print("3. 网络问题")

