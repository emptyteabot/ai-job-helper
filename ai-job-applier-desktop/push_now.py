import subprocess
import os

# 切换到自动投简历目录
target_dir = os.path.join(os.getcwd(), "自动投简历")
if os.path.exists(target_dir):
    os.chdir(target_dir)
    print(f"✅ 切换到目录: {os.getcwd()}")
else:
    print(f"❌ 目录不存在: {target_dir}")
    exit(1)

# 执行 git 命令
try:
    print("\n📝 添加文件...")
    subprocess.run(["git", "add", "streamlit_app.py"], check=True)
    
    print("💾 提交更改...")
    subprocess.run(["git", "commit", "-m", "UI升级：Gemini渐变+OpenAI打字机风格+大字体居中"], check=True)
    
    print("🚀 推送到 GitHub（强制推送）...")
    subprocess.run(["git", "push", "origin", "main", "--force"], check=True)
    
    print("\n✅ 推送完成！")
    print("\n📋 下一步：")
    print("1. 等待 Streamlit Cloud 自动部署（2-3 分钟）")
    print("2. 访问：https://ai-job-apper-ibpzap2nnajzrnu8mkthuv.streamlit.app/")
    print("3. 查看新的 UI 风格：Gemini 渐变 + OpenAI 打字机字体 + 大字体居中")
    
except subprocess.CalledProcessError as e:
    print(f"\n❌ 错误: {e}")
    exit(1)

