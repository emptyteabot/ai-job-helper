"""
复制 streamlit_app.py 到根目录
"""
import shutil
import os

source = r"c:\Users\陈盈桦\Desktop\一人公司260222\ai-job-applier-desktop\自动投简历\streamlit_app.py"
dest = r"c:\Users\陈盈桦\Desktop\一人公司260222\ai-job-applier-desktop\streamlit_app.py"

print("=" * 60)
print("复制 streamlit_app.py 到根目录")
print("=" * 60)

print(f"\n源文件：{source}")
print(f"目标文件：{dest}")

if os.path.exists(source):
    shutil.copy2(source, dest)
    print("\n✅ 复制成功！")
    
    # 推送到 GitHub
    os.chdir(r"c:\Users\陈盈桦\Desktop\一人公司260222\ai-job-applier-desktop")
    
    import subprocess
    
    print("\n[1] 添加文件...")
    subprocess.run(["git", "add", "streamlit_app.py"])
    
    print("\n[2] 提交...")
    subprocess.run(["git", "commit", "-m", "修复：复制streamlit_app.py到根目录，删除假验证码"])
    
    print("\n[3] 推送...")
    result = subprocess.run(["git", "push", "origin", "main"], capture_output=True, text=True)
    
    if result.returncode == 0:
        print("\n" + "=" * 60)
        print("✅ 推送成功！")
        print("=" * 60)
        print("\nStreamlit Cloud 将在 2-3 分钟内自动部署")
        print("访问：https://ai-job-apper-ibpzap2nnajzrnu8mkthuv.streamlit.app/")
    else:
        print(f"\n❌ 推送失败：{result.stderr}")
else:
    print("\n❌ 源文件不存在！")

