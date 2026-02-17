"""
保持Railway服务活跃 - 防止休眠
每5分钟自动ping一次
"""
import requests
import time
import schedule
from datetime import datetime

# 您的Railway URL
RAILWAY_URL = "https://ai-job-hunter-production-2730.up.railway.app"

def keep_alive():
    """保持服务活跃"""
    try:
        response = requests.get(f"{RAILWAY_URL}/api/health", timeout=10)
        if response.status_code == 200:
            print(f"✅ {datetime.now().strftime('%H:%M:%S')} - 服务正常")
        else:
            print(f"⚠️ {datetime.now().strftime('%H:%M:%S')} - 状态码: {response.status_code}")
    except Exception as e:
        print(f"❌ {datetime.now().strftime('%H:%M:%S')} - 错误: {str(e)}")

if __name__ == "__main__":
    print("🔄 开始保持Railway服务活跃...")
    print(f"📍 目标: {RAILWAY_URL}")
    print(f"⏰ 间隔: 每5分钟")
    print()
    
    # 立即执行一次
    keep_alive()
    
    # 每5分钟执行一次
    schedule.every(5).minutes.do(keep_alive)
    
    while True:
        schedule.run_pending()
        time.sleep(60)

保持Railway服务活跃 - 防止休眠
每5分钟自动ping一次
"""
import requests
import time
import schedule
from datetime import datetime

# 您的Railway URL
RAILWAY_URL = "https://ai-job-hunter-production-2730.up.railway.app"

def keep_alive():
    """保持服务活跃"""
    try:
        response = requests.get(f"{RAILWAY_URL}/api/health", timeout=10)
        if response.status_code == 200:
            print(f"✅ {datetime.now().strftime('%H:%M:%S')} - 服务正常")
        else:
            print(f"⚠️ {datetime.now().strftime('%H:%M:%S')} - 状态码: {response.status_code}")
    except Exception as e:
        print(f"❌ {datetime.now().strftime('%H:%M:%S')} - 错误: {str(e)}")

if __name__ == "__main__":
    print("🔄 开始保持Railway服务活跃...")
    print(f"📍 目标: {RAILWAY_URL}")
    print(f"⏰ 间隔: 每5分钟")
    print()
    
    # 立即执行一次
    keep_alive()
    
    # 每5分钟执行一次
    schedule.every(5).minutes.do(keep_alive)
    
    while True:
        schedule.run_pending()
        time.sleep(60)

保持Railway服务活跃 - 防止休眠
每5分钟自动ping一次
"""
import requests
import time
import schedule
from datetime import datetime

# 您的Railway URL
RAILWAY_URL = "https://ai-job-hunter-production-2730.up.railway.app"

def keep_alive():
    """保持服务活跃"""
    try:
        response = requests.get(f"{RAILWAY_URL}/api/health", timeout=10)
        if response.status_code == 200:
            print(f"✅ {datetime.now().strftime('%H:%M:%S')} - 服务正常")
        else:
            print(f"⚠️ {datetime.now().strftime('%H:%M:%S')} - 状态码: {response.status_code}")
    except Exception as e:
        print(f"❌ {datetime.now().strftime('%H:%M:%S')} - 错误: {str(e)}")

if __name__ == "__main__":
    print("🔄 开始保持Railway服务活跃...")
    print(f"📍 目标: {RAILWAY_URL}")
    print(f"⏰ 间隔: 每5分钟")
    print()
    
    # 立即执行一次
    keep_alive()
    
    # 每5分钟执行一次
    schedule.every(5).minutes.do(keep_alive)
    
    while True:
        schedule.run_pending()
        time.sleep(60)

保持Railway服务活跃 - 防止休眠
每5分钟自动ping一次
"""
import requests
import time
import schedule
from datetime import datetime

# 您的Railway URL
RAILWAY_URL = "https://ai-job-hunter-production-2730.up.railway.app"

def keep_alive():
    """保持服务活跃"""
    try:
        response = requests.get(f"{RAILWAY_URL}/api/health", timeout=10)
        if response.status_code == 200:
            print(f"✅ {datetime.now().strftime('%H:%M:%S')} - 服务正常")
        else:
            print(f"⚠️ {datetime.now().strftime('%H:%M:%S')} - 状态码: {response.status_code}")
    except Exception as e:
        print(f"❌ {datetime.now().strftime('%H:%M:%S')} - 错误: {str(e)}")

if __name__ == "__main__":
    print("🔄 开始保持Railway服务活跃...")
    print(f"📍 目标: {RAILWAY_URL}")
    print(f"⏰ 间隔: 每5分钟")
    print()
    
    # 立即执行一次
    keep_alive()
    
    # 每5分钟执行一次
    schedule.every(5).minutes.do(keep_alive)
    
    while True:
        schedule.run_pending()
        time.sleep(60)



