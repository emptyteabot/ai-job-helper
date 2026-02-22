"""自动演示脚本 - 展示一人公司系统能力"""
import sys
sys.path.insert(0, '.')

from main import OnePersonCompany
from loguru import logger

def auto_demo():
    """自动运行演示"""
    logger.info("🎬 自动演示模式启动\n")
    
    # 创建公司实例
    company = OnePersonCompany()
    
    # 运行演示任务
    company.run_demo()
    
    logger.info("\n" + "=" * 60)
    logger.success("✅ 演示完成！查看 logs/audit.json 了解详细执行记录")
    logger.info("=" * 60)

if __name__ == "__main__":
    auto_demo()

