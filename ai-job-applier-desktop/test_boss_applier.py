"""
测试 BossApplier 导入和基本功能
"""
import sys
from pathlib import Path

# 添加自动投简历项目到路径
current_dir = Path(__file__).parent
auto_apply_path = current_dir / "自动投简历"

if auto_apply_path.exists():
    sys.path.insert(0, str(auto_apply_path))
    try:
        from app.services.auto_apply.boss_applier import BossApplier
        print("✅ BossApplier 导入成功")
        
        # 测试创建实例
        config = {
            'headless': False,
            'random_delay_min': 2,
            'random_delay_max': 5,
            'company_blacklist': ['外包', '劳务派遣'],
            'title_blacklist': [],
            'greeting': '您好，我对这个职位很感兴趣，期待与您沟通。'
        }
        
        applier = BossApplier(config)
        print("✅ BossApplier 实例创建成功")
        print(f"✅ 配置: {config}")
        
    except Exception as e:
        print(f"❌ 导入失败: {e}")
        import traceback
        traceback.print_exc()
else:
    print(f"❌ 未找到自动投简历项目: {auto_apply_path}")

