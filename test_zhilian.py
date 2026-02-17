"""
智联招聘投递器测试脚本
测试登录、搜索、投递功能
"""

import sys
import os
import logging
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.services.auto_apply.zhilian_applier import ZhilianApplier

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('zhilian_test.log', encoding='utf-8')
    ]
)

logger = logging.getLogger(__name__)


def test_zhilian_applier():
    """测试智联招聘投递器"""

    print("=" * 60)
    print("智联招聘自动投递器测试")
    print("=" * 60)

    # 配置
    config = {
        'blacklist_companies': ['外包', '劳务派遣'],
        'blacklist_keywords': ['实习', '兼职'],
        'min_salary': 8000,
        'max_salary': 30000
    }

    # 创建投递器
    applier = ZhilianApplier(config)

    try:
        # 测试 1: 登录
        print("\n[测试 1] 登录测试")
        print("-" * 60)
        username = input("请输入智联招聘账号（手机号/邮箱）: ").strip()
        password = input("请输入密码: ").strip()

        if not username or not password:
            print("❌ 账号或密码为空，跳过登录测试")
        else:
            print("正在登录...")
            login_success = applier.login(username, password)

            if login_success:
                print("✓ 登录成功")
            else:
                print("✗ 登录失败")
                return

        # 测试 2: 搜索职位
        print("\n[测试 2] 搜索职位测试")
        print("-" * 60)
        keywords = input("请输入搜索关键词（默认：Python开发）: ").strip() or "Python开发"
        location = input("请输入工作地点（默认：北京）: ").strip() or "北京"

        filters = {
            'salary_range': '10001-15000',
            'work_experience': '1-3年',
            'education': '本科'
        }

        print(f"正在搜索: {keywords} - {location}")
        jobs = applier.search_jobs(keywords, location, filters)

        if jobs:
            print(f"✓ 找到 {len(jobs)} 个职位")
            print("\n前 5 个职位:")
            for i, job in enumerate(jobs[:5], 1):
                print(f"  {i}. {job['title']}")
                print(f"     公司: {job['company']}")
                print(f"     薪资: {job['salary']}")
                print(f"     地点: {job['location']}")
                print()
        else:
            print("✗ 未找到职位")
            return

        # 测试 3: 投递职位
        print("\n[测试 3] 投递职位测试")
        print("-" * 60)
        test_apply = input("是否测试投递功能？(y/n): ").strip().lower()

        if test_apply == 'y':
            apply_count = input("投递数量（默认：1）: ").strip()
            apply_count = int(apply_count) if apply_count.isdigit() else 1

            print(f"正在投递前 {apply_count} 个职位...")
            results = applier.batch_apply(jobs[:apply_count], max_count=apply_count)

            print("\n投递结果:")
            print(f"  总计: {results['total_attempted']}")
            print(f"  成功: {results['applied']}")
            print(f"  失败: {results['failed']}")
            print(f"  成功率: {results['success_rate']:.1%}")

            print("\n详细结果:")
            for i, result in enumerate(results['results'], 1):
                status = "✓" if result['success'] else "✗"
                job = result['job']
                print(f"  {i}. {status} {job['title']} - {result['message']}")
        else:
            print("跳过投递测试")

        # 测试 4: 上传简历
        print("\n[测试 4] 上传简历测试")
        print("-" * 60)
        test_upload = input("是否测试上传简历功能？(y/n): ").strip().lower()

        if test_upload == 'y':
            resume_path = input("请输入简历文件路径: ").strip()
            if resume_path and os.path.exists(resume_path):
                print("正在上传简历...")
                upload_success = applier.upload_resume(resume_path)
                if upload_success:
                    print("✓ 简历上传成功")
                else:
                    print("✗ 简历上传失败")
            else:
                print("文件不存在，跳过上传测试")
        else:
            print("跳过上传测试")

        print("\n" + "=" * 60)
        print("测试完成")
        print("=" * 60)

    except KeyboardInterrupt:
        print("\n\n用户中断测试")
    except Exception as e:
        logger.exception(f"测试过程出错: {e}")
        print(f"\n❌ 测试失败: {e}")
    finally:
        # 清理资源
        print("\n正在清理资源...")
        applier.cleanup()
        print("清理完成")


if __name__ == "__main__":
    test_zhilian_applier()
