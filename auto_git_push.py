"""
自动Git推送脚本
代码更新后自动提交到GitHub
"""
import subprocess
import sys
from datetime import datetime

def run_command(command):
    """运行命令"""
    try:
        result = subprocess.run(
            command,
            shell=True,
            check=True,
            capture_output=True,
            text=True,
            encoding='utf-8'
        )
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        return False, e.stderr

def auto_git_push(commit_message=None):
    """自动Git推送"""
    
    print("🔄 开始自动Git推送...")
    
    # 1. 检查Git状态
    print("\n📊 检查Git状态...")
    success, output = run_command("git status")
    if not success:
        print("❌ Git状态检查失败")
        return False
    
    # 2. 添加所有更改
    print("\n📦 添加所有更改...")
    success, output = run_command("git add .")
    if not success:
        print("❌ 添加文件失败")
        return False
    print("✅ 文件添加成功")
    
    # 3. 提交更改
    if commit_message is None:
        commit_message = f"Auto update - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    
    print(f"\n💾 提交更改: {commit_message}")
    success, output = run_command(f'git commit -m "{commit_message}"')
    if not success:
        if "nothing to commit" in output:
            print("ℹ️ 没有需要提交的更改")
            return True
        print(f"❌ 提交失败: {output}")
        return False
    print("✅ 提交成功")
    
    # 4. 推送到远程
    print("\n🚀 推送到GitHub...")
    success, output = run_command("git push")
    if not success:
        print(f"❌ 推送失败: {output}")
        print("\n💡 提示：请确保已配置Git远程仓库")
        print("   git remote add origin https://github.com/emptyteabot/ai-job-helper.git")
        return False
    print("✅ 推送成功")
    
    print("\n🎉 自动Git推送完成！")
    print("🌐 GitHub: https://github.com/emptyteabot/ai-job-helper")
    print("🚀 Railway会自动部署更新")
    
    return True

if __name__ == "__main__":
    # 从命令行参数获取提交信息
    commit_msg = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else None
    
    success = auto_git_push(commit_msg)
    sys.exit(0 if success else 1)

代码更新后自动提交到GitHub
"""
import subprocess
import sys
from datetime import datetime

def run_command(command):
    """运行命令"""
    try:
        result = subprocess.run(
            command,
            shell=True,
            check=True,
            capture_output=True,
            text=True,
            encoding='utf-8'
        )
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        return False, e.stderr

def auto_git_push(commit_message=None):
    """自动Git推送"""
    
    print("🔄 开始自动Git推送...")
    
    # 1. 检查Git状态
    print("\n📊 检查Git状态...")
    success, output = run_command("git status")
    if not success:
        print("❌ Git状态检查失败")
        return False
    
    # 2. 添加所有更改
    print("\n📦 添加所有更改...")
    success, output = run_command("git add .")
    if not success:
        print("❌ 添加文件失败")
        return False
    print("✅ 文件添加成功")
    
    # 3. 提交更改
    if commit_message is None:
        commit_message = f"Auto update - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    
    print(f"\n💾 提交更改: {commit_message}")
    success, output = run_command(f'git commit -m "{commit_message}"')
    if not success:
        if "nothing to commit" in output:
            print("ℹ️ 没有需要提交的更改")
            return True
        print(f"❌ 提交失败: {output}")
        return False
    print("✅ 提交成功")
    
    # 4. 推送到远程
    print("\n🚀 推送到GitHub...")
    success, output = run_command("git push")
    if not success:
        print(f"❌ 推送失败: {output}")
        print("\n💡 提示：请确保已配置Git远程仓库")
        print("   git remote add origin https://github.com/emptyteabot/ai-job-helper.git")
        return False
    print("✅ 推送成功")
    
    print("\n🎉 自动Git推送完成！")
    print("🌐 GitHub: https://github.com/emptyteabot/ai-job-helper")
    print("🚀 Railway会自动部署更新")
    
    return True

if __name__ == "__main__":
    # 从命令行参数获取提交信息
    commit_msg = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else None
    
    success = auto_git_push(commit_msg)
    sys.exit(0 if success else 1)

代码更新后自动提交到GitHub
"""
import subprocess
import sys
from datetime import datetime

def run_command(command):
    """运行命令"""
    try:
        result = subprocess.run(
            command,
            shell=True,
            check=True,
            capture_output=True,
            text=True,
            encoding='utf-8'
        )
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        return False, e.stderr

def auto_git_push(commit_message=None):
    """自动Git推送"""
    
    print("🔄 开始自动Git推送...")
    
    # 1. 检查Git状态
    print("\n📊 检查Git状态...")
    success, output = run_command("git status")
    if not success:
        print("❌ Git状态检查失败")
        return False
    
    # 2. 添加所有更改
    print("\n📦 添加所有更改...")
    success, output = run_command("git add .")
    if not success:
        print("❌ 添加文件失败")
        return False
    print("✅ 文件添加成功")
    
    # 3. 提交更改
    if commit_message is None:
        commit_message = f"Auto update - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    
    print(f"\n💾 提交更改: {commit_message}")
    success, output = run_command(f'git commit -m "{commit_message}"')
    if not success:
        if "nothing to commit" in output:
            print("ℹ️ 没有需要提交的更改")
            return True
        print(f"❌ 提交失败: {output}")
        return False
    print("✅ 提交成功")
    
    # 4. 推送到远程
    print("\n🚀 推送到GitHub...")
    success, output = run_command("git push")
    if not success:
        print(f"❌ 推送失败: {output}")
        print("\n💡 提示：请确保已配置Git远程仓库")
        print("   git remote add origin https://github.com/emptyteabot/ai-job-helper.git")
        return False
    print("✅ 推送成功")
    
    print("\n🎉 自动Git推送完成！")
    print("🌐 GitHub: https://github.com/emptyteabot/ai-job-helper")
    print("🚀 Railway会自动部署更新")
    
    return True

if __name__ == "__main__":
    # 从命令行参数获取提交信息
    commit_msg = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else None
    
    success = auto_git_push(commit_msg)
    sys.exit(0 if success else 1)

代码更新后自动提交到GitHub
"""
import subprocess
import sys
from datetime import datetime

def run_command(command):
    """运行命令"""
    try:
        result = subprocess.run(
            command,
            shell=True,
            check=True,
            capture_output=True,
            text=True,
            encoding='utf-8'
        )
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        return False, e.stderr

def auto_git_push(commit_message=None):
    """自动Git推送"""
    
    print("🔄 开始自动Git推送...")
    
    # 1. 检查Git状态
    print("\n📊 检查Git状态...")
    success, output = run_command("git status")
    if not success:
        print("❌ Git状态检查失败")
        return False
    
    # 2. 添加所有更改
    print("\n📦 添加所有更改...")
    success, output = run_command("git add .")
    if not success:
        print("❌ 添加文件失败")
        return False
    print("✅ 文件添加成功")
    
    # 3. 提交更改
    if commit_message is None:
        commit_message = f"Auto update - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    
    print(f"\n💾 提交更改: {commit_message}")
    success, output = run_command(f'git commit -m "{commit_message}"')
    if not success:
        if "nothing to commit" in output:
            print("ℹ️ 没有需要提交的更改")
            return True
        print(f"❌ 提交失败: {output}")
        return False
    print("✅ 提交成功")
    
    # 4. 推送到远程
    print("\n🚀 推送到GitHub...")
    success, output = run_command("git push")
    if not success:
        print(f"❌ 推送失败: {output}")
        print("\n💡 提示：请确保已配置Git远程仓库")
        print("   git remote add origin https://github.com/emptyteabot/ai-job-helper.git")
        return False
    print("✅ 推送成功")
    
    print("\n🎉 自动Git推送完成！")
    print("🌐 GitHub: https://github.com/emptyteabot/ai-job-helper")
    print("🚀 Railway会自动部署更新")
    
    return True

if __name__ == "__main__":
    # 从命令行参数获取提交信息
    commit_msg = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else None
    
    success = auto_git_push(commit_msg)
    sys.exit(0 if success else 1)
