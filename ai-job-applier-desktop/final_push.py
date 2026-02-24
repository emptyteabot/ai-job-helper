"""
最终推送到 emptyteabot/ai-job-helper
"""
import subprocess
import os

os.chdir(r"c:\Users\陈盈桦\Desktop\一人公司260222\ai-job-applier-desktop")

print("=" * 60)
print("最终推送到 GitHub: emptyteabot/ai-job-helper")
print("=" * 60)

# 1. 检查远程仓库
print("\n[1/5] 检查远程仓库...")
result = subprocess.run(["git", "remote", "-v"], capture_output=True, text=True)
print(result.stdout)

if "emptyteabot/ai-job-helper" not in result.stdout:
    print("❌ 远程仓库不正确！")
    exit(1)

# 2. 检查 streamlit_app.py 是否在根目录
print("\n[2/5] 检查 streamlit_app.py...")
if os.path.exists("streamlit_app.py"):
    print("✅ streamlit_app.py 存在于根目录")
else:
    print("❌ streamlit_app.py 不存在，正在复制...")
    import shutil
    shutil.copy2(r"自动投简历\streamlit_app.py", "streamlit_app.py")
    print("✅ 已复制")

# 3. 添加所有更改
print("\n[3/5] 添加所有更改...")
subprocess.run(["git", "add", "."])

# 4. 提交
print("\n[4/5] 提交更改...")
subprocess.run(["git", "commit", "-m", "最终版本：删除假验证码+Gemini渐变UI+真实Boss登录"])

# 5. 推送
print("\n[5/5] 推送到 GitHub...")
result = subprocess.run(["git", "push", "origin", "main", "-f"], capture_output=True, text=True)

if result.returncode == 0:
    print("\n" + "=" * 60)
    print("✅ 推送成功到 emptyteabot/ai-job-helper！")
    print("=" * 60)
    print("\n📋 下一步：")
    print("\n1. 访问：https://share.streamlit.io/")
    print("2. 点击 'New app'")
    print("3. 填写：")
    print("   - Repository: emptyteabot/ai-job-helper")
    print("   - Branch: main")
    print("   - Main file path: streamlit_app.py")
    print("4. 点击 'Deploy'")
    print("5. 等待 2-3 分钟")
    print("\n✅ 确认文件已推送：")
    print("   https://github.com/emptyteabot/ai-job-helper/blob/main/streamlit_app.py")
    print("=" * 60)
else:
    print(f"\n❌ 推送失败：{result.stderr}")

