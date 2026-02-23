"""
测试后端登录 API
"""
import requests
import json

BACKEND_URL = "http://localhost:8765"

print("=" * 60)
print("测试 Boss 直聘登录流程")
print("=" * 60)

# 测试 1: 健康检查
print("\n[测试 1] 健康检查")
try:
    response = requests.get(f"{BACKEND_URL}/docs", timeout=5)
    if response.status_code == 200:
        print("✅ 后端运行正常")
    else:
        print(f"❌ 后端异常: HTTP {response.status_code}")
        exit(1)
except Exception as e:
    print(f"❌ 后端未启动: {e}")
    exit(1)

# 测试 2: 初始化登录
print("\n[测试 2] 初始化登录 (输入手机号)")
phone = "13800138000"
try:
    response = requests.post(
        f"{BACKEND_URL}/api/simple-apply/init-login",
        json={"phone": phone},
        timeout=60
    )
    print(f"状态码: {response.status_code}")
    print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    
    if response.status_code == 200:
        data = response.json()
        if data.get('success'):
            print("✅ 初始化登录成功")
            print(f"   消息: {data.get('message')}")
            print(f"   步骤: {data.get('step')}")
        else:
            print(f"❌ 初始化登录失败: {data.get('message')}")
    else:
        print(f"❌ HTTP 错误: {response.status_code}")
        if response.headers.get('content-type') == 'application/json':
            print(f"   详情: {response.json()}")
        
except Exception as e:
    print(f"❌ 请求失败: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("测试完成")
print("=" * 60)

