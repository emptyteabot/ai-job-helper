"""
快速测试后端
"""
import requests

ports = [8765, 8766, 8000]

print("=" * 50)
print("检查后端运行状态")
print("=" * 50)

for port in ports:
    try:
        url = f"http://localhost:{port}/docs"
        response = requests.get(url, timeout=2)
        if response.status_code == 200:
            print(f"✅ 后端运行在端口 {port}")
            print(f"   访问: http://localhost:{port}/docs")
            print(f"   API: http://localhost:{port}/api/simple-apply/status/test")
            break
    except:
        print(f"❌ 端口 {port} 未运行")
else:
    print("\n⚠️ 后端未启动，请手动运行:")
    print("   cd backend")
    print("   python main.py --port 8766")

