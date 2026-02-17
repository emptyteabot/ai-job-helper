"""
快速验证脚本
检查智联招聘投递器是否正确安装和配置
"""

import sys
from pathlib import Path

print("=" * 60)
print("智联招聘投递器 - 快速验证")
print("=" * 60)
print()

# 检查 1: Python 版本
print("[1/5] 检查 Python 版本...")
if sys.version_info < (3, 8):
    print("❌ Python 版本过低，需要 3.8+")
    sys.exit(1)
print(f"✓ Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")

# 检查 2: DrissionPage
print("\n[2/5] 检查 DrissionPage...")
try:
    import DrissionPage
    print(f"✓ DrissionPage 已安装")
except ImportError:
    print("❌ DrissionPage 未安装")
    print("   请运行: pip install DrissionPage")
    sys.exit(1)

# 检查 3: 核心模块
print("\n[3/5] 检查核心模块...")
try:
    from app.services.auto_apply.zhilian_applier import ZhilianApplier
    print("✓ ZhilianApplier 模块正常")
except ImportError as e:
    print(f"❌ 导入失败: {e}")
    sys.exit(1)

# 检查 4: 创建实例
print("\n[4/5] 检查实例创建...")
try:
    config = {
        'blacklist_companies': ['外包'],
        'blacklist_keywords': ['实习'],
        'min_salary': 8000
    }
    applier = ZhilianApplier(config)
    print("✓ 实例创建成功")
except Exception as e:
    print(f"❌ 创建失败: {e}")
    sys.exit(1)

# 检查 5: 基础功能
print("\n[5/5] 检查基础功能...")
try:
    # 测试黑名单过滤
    test_job = {
        'title': 'Python开发工程师',
        'company': '某某科技公司',
        'salary': '10K-15K',
        'location': '北京'
    }
    result = applier._should_apply(test_job)
    assert result is True, "黑名单过滤测试失败"

    # 测试状态获取
    status = applier.get_status()
    assert 'is_running' in status, "状态获取测试失败"

    print("✓ 基础功能正常")
except Exception as e:
    print(f"❌ 功能测试失败: {e}")
    sys.exit(1)

# 检查文件
print("\n[额外] 检查文件...")
files_to_check = [
    'app/services/auto_apply/zhilian_applier.py',
    'test_zhilian.py',
    '启动智联投递.bat',
    'docs/智联招聘投递器README.md',
    'docs/智联招聘投递器使用指南.md',
]

for file_path in files_to_check:
    if Path(file_path).exists():
        print(f"  ✓ {file_path}")
    else:
        print(f"  ⚠ {file_path} 不存在")

print("\n" + "=" * 60)
print("✅ 验证完成！智联招聘投递器已就绪")
print("=" * 60)
print()
print("快速开始:")
print("  1. 运行测试: python test_zhilian.py")
print("  2. 或使用批处理: 启动智联投递.bat")
print()
print("查看文档:")
print("  - docs/智联招聘投递器README.md")
print("  - docs/智联招聘投递器使用指南.md")
print()
