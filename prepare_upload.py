import os
import shutil

# 源文件夹
source = r"c:\Users\陈盈桦\Desktop\Desktop_整理_2026-02-09_172732\Folders\自动投简历"
target = os.path.join(source, "准备上传到GitHub")

print("=" * 50)
print("📦 准备GitHub上传文件")
print("=" * 50)
print()

# 创建目标文件夹
print("[1/3] 创建上传文件夹...")
if os.path.exists(target):
    shutil.rmtree(target)
os.makedirs(target)
print("✅ 文件夹已创建")
print()

# 复制核心文件
print("[2/3] 复制核心文件...")
files_to_copy = [
    "web_app.py",
    "requirements.txt",
    "Procfile",
    "render.yaml",
    "runtime.txt",
    "README.md"
]

for file in files_to_copy:
    src = os.path.join(source, file)
    if os.path.exists(src):
        shutil.copy2(src, target)
        print(f"  ✅ {file}")
    else:
        print(f"  ⚠️ {file} 不存在")

print()

# 复制文件夹
print("[3/3] 复制文件夹...")
folders_to_copy = ["app", "static", "data"]

for folder in folders_to_copy:
    src = os.path.join(source, folder)
    dst = os.path.join(target, folder)
    if os.path.exists(src):
        shutil.copytree(src, dst, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
        print(f"  ✅ {folder}/")
    else:
        print(f"  ⚠️ {folder}/ 不存在")

print()
print("=" * 50)
print("✅ 准备完成！")
print("=" * 50)
print()
print(f"📁 上传文件夹位置：")
print(f"   {target}")
print()
print("📋 下一步：")
print("   1. 打开上面的文件夹")
print("   2. 全选里面的所有文件（Ctrl+A）")
print("   3. 访问 https://github.com/emptyteabot/ai-job-helper")
print("   4. 点击 Add file → Upload files")
print("   5. 拖拽所有文件到网页")
print("   6. 点击 Commit changes")
print()

# 打开文件夹
os.startfile(target)

import shutil

# 源文件夹
source = r"c:\Users\陈盈桦\Desktop\Desktop_整理_2026-02-09_172732\Folders\自动投简历"
target = os.path.join(source, "准备上传到GitHub")

print("=" * 50)
print("📦 准备GitHub上传文件")
print("=" * 50)
print()

# 创建目标文件夹
print("[1/3] 创建上传文件夹...")
if os.path.exists(target):
    shutil.rmtree(target)
os.makedirs(target)
print("✅ 文件夹已创建")
print()

# 复制核心文件
print("[2/3] 复制核心文件...")
files_to_copy = [
    "web_app.py",
    "requirements.txt",
    "Procfile",
    "render.yaml",
    "runtime.txt",
    "README.md"
]

for file in files_to_copy:
    src = os.path.join(source, file)
    if os.path.exists(src):
        shutil.copy2(src, target)
        print(f"  ✅ {file}")
    else:
        print(f"  ⚠️ {file} 不存在")

print()

# 复制文件夹
print("[3/3] 复制文件夹...")
folders_to_copy = ["app", "static", "data"]

for folder in folders_to_copy:
    src = os.path.join(source, folder)
    dst = os.path.join(target, folder)
    if os.path.exists(src):
        shutil.copytree(src, dst, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
        print(f"  ✅ {folder}/")
    else:
        print(f"  ⚠️ {folder}/ 不存在")

print()
print("=" * 50)
print("✅ 准备完成！")
print("=" * 50)
print()
print(f"📁 上传文件夹位置：")
print(f"   {target}")
print()
print("📋 下一步：")
print("   1. 打开上面的文件夹")
print("   2. 全选里面的所有文件（Ctrl+A）")
print("   3. 访问 https://github.com/emptyteabot/ai-job-helper")
print("   4. 点击 Add file → Upload files")
print("   5. 拖拽所有文件到网页")
print("   6. 点击 Commit changes")
print()

# 打开文件夹
os.startfile(target)

