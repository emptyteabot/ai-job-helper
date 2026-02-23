"""
搜索开发环境提示
"""
import os

file_path = r"c:\Users\陈盈桦\Desktop\一人公司260222\ai-job-applier-desktop\自动投简历\streamlit_app.py"

print("=" * 60)
print("搜索 streamlit_app.py 中的开发环境提示")
print("=" * 60)

with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()
    
found = False
for i, line in enumerate(lines, 1):
    if '开发环境' in line or '123456' in line:
        print(f"\n行 {i}: {line.rstrip()}")
        # 显示上下文
        if i > 1:
            print(f"行 {i-1}: {lines[i-2].rstrip()}")
        if i < len(lines):
            print(f"行 {i+1}: {lines[i].rstrip()}")
        found = True

if not found:
    print("\n❌ 未找到 '开发环境' 或 '123456'")
    print("\n可能的原因：")
    print("1. Streamlit Cloud 缓存了旧版本")
    print("2. 代码还没有推送到 GitHub")
    print("3. Streamlit Cloud 还没有重新部署")
else:
    print("\n✅ 找到了！需要删除这些行")

