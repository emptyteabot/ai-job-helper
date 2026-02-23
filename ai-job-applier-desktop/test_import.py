"""
测试 BossApplier 导入
"""
import sys
from pathlib import Path

# 添加 backend 到路径
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

print("=" * 50)
print("测试 BossApplier 导入")
print("=" * 50)

try:
    from automation.boss_applier import BossApplier
    print("✅ 成功导入 BossApplier")
    print(f"类: {BossApplier}")
    print(f"方法: {[m for m in dir(BossApplier) if not m.startswith('_')]}")
    
    # 测试创建实例
    config = {
        'headless': False,
        'random_delay_min': 2,
        'random_delay_max': 5,
    }
    applier = BossApplier(config)
    print(f"✅ 成功创建实例: {applier}")
    
except Exception as e:
    print(f"❌ 导入失败: {e}")
    import traceback
    traceback.print_exc()

