"""
测试多平台投递 API
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"


def test_get_platforms():
    """测试获取平台列表"""
    print("\n=== 测试获取平台列表 ===")
    response = requests.get(f"{BASE_URL}/api/auto-apply/platforms")
    print(f"状态码: {response.status_code}")
    data = response.json()
    print(f"支持的平台数量: {len(data['data']['platforms'])}")
    for platform in data['data']['platforms']:
        print(f"  - {platform['name']} ({platform['id']}): {platform['status']}")
    return data


def test_platform_config():
    """测试平台配置"""
    print("\n=== 测试平台配置 ===")

    # 测试 Boss 配置
    boss_config = {
        "platform": "boss",
        "config": {
            "phone": "13800138000"
        }
    }
    response = requests.post(
        f"{BASE_URL}/api/auto-apply/test-platform",
        json=boss_config
    )
    print(f"Boss 配置测试: {response.json()}")

    # 测试智联配置
    zhilian_config = {
        "platform": "zhilian",
        "config": {
            "username": "test@example.com",
            "password": "password123"
        }
    }
    response = requests.post(
        f"{BASE_URL}/api/auto-apply/test-platform",
        json=zhilian_config
    )
    print(f"智联配置测试: {response.json()}")

    # 测试 LinkedIn 配置
    linkedin_config = {
        "platform": "linkedin",
        "config": {
            "email": "test@example.com",
            "password": "password123"
        }
    }
    response = requests.post(
        f"{BASE_URL}/api/auto-apply/test-platform",
        json=linkedin_config
    )
    print(f"LinkedIn 配置测试: {response.json()}")


def test_multi_platform_apply():
    """测试多平台投递（模拟）"""
    print("\n=== 测试多平台投递 ===")

    # 注意：这只是测试 API 接口，不会真正投递
    # 实际使用时需要提供真实的登录凭证
    config = {
        "platforms": ["boss", "zhilian", "linkedin"],
        "config": {
            "keywords": "Python开发",
            "location": "北京",
            "max_count": 10,
            "blacklist": ["测试公司"],
            "headless": True,
            "use_ai_answers": True,
            "boss_config": {
                "phone": "13800138000"
            },
            "zhilian_config": {
                "username": "test@example.com",
                "password": "password123"
            },
            "linkedin_config": {
                "email": "test@example.com",
                "password": "password123"
            }
        }
    }

    print("发送多平台投递请求...")
    print(f"平台: {config['platforms']}")
    print(f"关键词: {config['config']['keywords']}")
    print(f"地点: {config['config']['location']}")

    # 注意：实际运行会启动浏览器并尝试登录
    # 这里只是展示 API 调用方式
    print("\n⚠️  实际投递需要真实的登录凭证")
    print("⚠️  取消注释下面的代码来测试实际投递\n")

    # response = requests.post(
    #     f"{BASE_URL}/api/auto-apply/start-multi",
    #     json=config
    # )
    # data = response.json()
    # print(f"任务已创建: {data}")
    #
    # if data['success']:
    #     task_id = data['data']['task_id']
    #     print(f"\n任务 ID: {task_id}")
    #     print("可以通过以下方式查询进度:")
    #     print(f"  GET {BASE_URL}/api/auto-apply/status/{task_id}")
    #     print(f"  WebSocket: ws://localhost:8000/ws/auto-apply/{task_id}")


def test_get_stats():
    """测试获取统计"""
    print("\n=== 测试获取统计 ===")
    response = requests.get(f"{BASE_URL}/api/auto-apply/stats")
    print(f"状态码: {response.status_code}")
    data = response.json()
    if data['success']:
        stats = data['data']
        print(f"总任务数: {stats['total_tasks']}")
        print(f"已完成: {stats['completed_tasks']}")
        print(f"运行中: {stats['running_tasks']}")
        print(f"总投递: {stats['total_applied']}")
        print(f"总失败: {stats['total_failed']}")
        print(f"成功率: {stats['success_rate']}%")
        print(f"平台统计: {stats['platform_stats']}")
    return data


def main():
    """主测试函数"""
    print("=" * 60)
    print("多平台投递 API 测试")
    print("=" * 60)

    try:
        # 测试 1: 获取平台列表
        test_get_platforms()

        # 测试 2: 测试平台配置
        test_platform_config()

        # 测试 3: 获取统计
        test_get_stats()

        # 测试 4: 多平台投递（仅展示）
        test_multi_platform_apply()

        print("\n" + "=" * 60)
        print("✅ 所有测试完成")
        print("=" * 60)

    except requests.exceptions.ConnectionError:
        print("\n❌ 错误: 无法连接到服务器")
        print("请确保 web_app.py 正在运行:")
        print("  python web_app.py")
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
