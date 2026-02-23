"""
测试 simple_apply API
"""
import requests
import json

BASE_URL = "http://localhost:8765"

def test_init_login():
    """测试初始化登录"""
    print("=" * 50)
    print("测试 1: 初始化登录")
    print("=" * 50)
    
    url = f"{BASE_URL}/api/simple-apply/init-login"
    data = {"phone": "13800138000"}
    
    try:
        response = requests.post(url, json=data, timeout=60)
        print(f"状态码: {response.status_code}")
        print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        return response.json()
    except Exception as e:
        print(f"❌ 错误: {e}")
        return None

def test_status():
    """测试状态检查"""
    print("\n" + "=" * 50)
    print("测试 2: 检查登录状态")
    print("=" * 50)
    
    url = f"{BASE_URL}/api/simple-apply/status/13800138000"
    
    try:
        response = requests.get(url, timeout=10)
        print(f"状态码: {response.status_code}")
        print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        return response.json()
    except Exception as e:
        print(f"❌ 错误: {e}")
        return None

def test_health():
    """测试健康检查"""
    print("\n" + "=" * 50)
    print("测试 0: 健康检查")
    print("=" * 50)
    
    url = f"{BASE_URL}/docs"
    
    try:
        response = requests.get(url, timeout=10)
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            print("✅ 后端运行正常")
            return True
        else:
            print("❌ 后端异常")
            return False
    except Exception as e:
        print(f"❌ 后端未启动: {e}")
        return False

if __name__ == "__main__":
    print("开始测试 simple_apply API...\n")
    
    # 测试健康检查
    if not test_health():
        print("\n请先启动后端: python backend/main.py --port 8765")
        exit(1)
    
    # 测试状态检查
    test_status()
    
    # 测试初始化登录
    result = test_init_login()
    
    if result and result.get("success"):
        print("\n✅ 测试通过！")
        print("\n下一步:")
        print("1. 查看浏览器是否打开")
        print("2. 检查是否自动填写了手机号")
        print("3. 检查是否自动点击了获取验证码")
    else:
        print("\n❌ 测试失败！")

