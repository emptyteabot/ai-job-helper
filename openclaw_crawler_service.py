"""
OpenClaw爬虫服务 - 本地运行，定时爬取Boss直聘岗位并推送到云端
"""

import os
import time
import json
import requests
from datetime import datetime
from typing import List, Dict, Any
import schedule
from app.services.job_providers.openclaw_browser_provider import OpenClawBrowserProvider
from app.services.job_providers.base import JobSearchParams

class OpenClawCrawlerService:
    """OpenClaw爬虫服务 - 本地运行"""
    
    def __init__(self, cloud_api_url: str, api_key: str):
        """
        初始化爬虫服务
        
        Args:
            cloud_api_url: 云端API地址，如 https://your-app.railway.app
            api_key: API密钥，用于认证
        """
        self.cloud_api_url = cloud_api_url.rstrip('/')
        self.api_key = api_key
        self.openclaw = OpenClawBrowserProvider()
        
        # 预定义的热门搜索关键词
        self.hot_keywords = [
            ["Python", "后端开发"],
            ["Java", "Spring Boot"],
            ["前端", "React", "Vue"],
            ["算法工程师", "机器学习"],
            ["数据分析", "SQL"],
            ["产品经理"],
            ["测试工程师", "自动化"],
            ["运维", "DevOps", "Kubernetes"],
        ]
        
        self.hot_cities = ["北京", "上海", "深圳", "杭州", "广州", "成都"]
    
    def crawl_jobs(self, keywords: List[str], location: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        爬取岗位数据
        
        Args:
            keywords: 搜索关键词列表
            location: 城市
            limit: 数量限制
            
        Returns:
            岗位列表
        """
        print(f"🔍 开始爬取：{keywords} @ {location}")
        
        try:
            params = JobSearchParams(
                keywords=keywords,
                location=location,
                limit=limit
            )
            
            jobs = self.openclaw.search_jobs(params)
            print(f"✅ 爬取成功：{len(jobs)} 个岗位")
            return jobs
            
        except Exception as e:
            print(f"❌ 爬取失败：{str(e)}")
            return []
    
    def push_to_cloud(self, jobs: List[Dict[str, Any]]) -> bool:
        """
        推送岗位数据到云端
        
        Args:
            jobs: 岗位列表
            
        Returns:
            是否成功
        """
        if not jobs:
            return False
        
        try:
            url = f"{self.cloud_api_url}/api/crawler/upload"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "jobs": jobs,
                "timestamp": datetime.now().isoformat(),
                "source": "openclaw_local"
            }
            
            response = requests.post(url, json=data, headers=headers, timeout=30)
            
            if response.status_code == 200:
                print(f"✅ 推送成功：{len(jobs)} 个岗位")
                return True
            else:
                print(f"❌ 推送失败：{response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ 推送异常：{str(e)}")
            return False
    
    def crawl_and_push_all(self):
        """爬取所有热门关键词并推送"""
        print("\n" + "="*60)
        print(f"🚀 开始定时爬取任务 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*60)
        
        total_jobs = 0
        
        for keywords in self.hot_keywords:
            for city in self.hot_cities:
                # 爬取岗位
                jobs = self.crawl_jobs(keywords, city, limit=10)
                
                if jobs:
                    # 推送到云端
                    if self.push_to_cloud(jobs):
                        total_jobs += len(jobs)
                
                # 避免请求过快
                time.sleep(5)
        
        print("\n" + "="*60)
        print(f"✅ 本次任务完成：共爬取并推送 {total_jobs} 个岗位")
        print("="*60 + "\n")
    
    def start_scheduled_crawling(self, interval_hours: int = 6):
        """
        启动定时爬取
        
        Args:
            interval_hours: 爬取间隔（小时）
        """
        print("\n" + "🤖"*30)
        print("OpenClaw爬虫服务启动")
        print("🤖"*30)
        print(f"\n📋 配置信息：")
        print(f"  - 云端API: {self.cloud_api_url}")
        print(f"  - 爬取间隔: 每 {interval_hours} 小时")
        print(f"  - 关键词数: {len(self.hot_keywords)}")
        print(f"  - 城市数: {len(self.hot_cities)}")
        print(f"\n⚠️ 请确保：")
        print(f"  1. Chrome已打开Boss直聘并登录")
        print(f"  2. OpenClaw扩展已Attach到标签页")
        print(f"  3. 保持浏览器窗口不要关闭")
        print(f"\n🔄 首次爬取将在启动后立即开始...\n")
        
        # 立即执行一次
        self.crawl_and_push_all()
        
        # 设置定时任务
        schedule.every(interval_hours).hours.do(self.crawl_and_push_all)
        
        print(f"⏰ 下次爬取时间：{interval_hours} 小时后")
        print(f"💡 按 Ctrl+C 停止服务\n")
        
        # 运行定时任务
        while True:
            schedule.run_pending()
            time.sleep(60)  # 每分钟检查一次


if __name__ == "__main__":
    # 配置
    CLOUD_API_URL = os.getenv("CLOUD_API_URL", "https://your-app.railway.app")
    API_KEY = os.getenv("CRAWLER_API_KEY", "your-secret-key")
    INTERVAL_HOURS = int(os.getenv("CRAWL_INTERVAL_HOURS", "6"))
    
    # 启动爬虫服务
    crawler = OpenClawCrawlerService(
        cloud_api_url=CLOUD_API_URL,
        api_key=API_KEY
    )
    
    try:
        crawler.start_scheduled_crawling(interval_hours=INTERVAL_HOURS)
    except KeyboardInterrupt:
        print("\n\n👋 爬虫服务已停止")

OpenClaw爬虫服务 - 本地运行，定时爬取Boss直聘岗位并推送到云端
"""

import os
import time
import json
import requests
from datetime import datetime
from typing import List, Dict, Any
import schedule
from app.services.job_providers.openclaw_browser_provider import OpenClawBrowserProvider
from app.services.job_providers.base import JobSearchParams

class OpenClawCrawlerService:
    """OpenClaw爬虫服务 - 本地运行"""
    
    def __init__(self, cloud_api_url: str, api_key: str):
        """
        初始化爬虫服务
        
        Args:
            cloud_api_url: 云端API地址，如 https://your-app.railway.app
            api_key: API密钥，用于认证
        """
        self.cloud_api_url = cloud_api_url.rstrip('/')
        self.api_key = api_key
        self.openclaw = OpenClawBrowserProvider()
        
        # 预定义的热门搜索关键词
        self.hot_keywords = [
            ["Python", "后端开发"],
            ["Java", "Spring Boot"],
            ["前端", "React", "Vue"],
            ["算法工程师", "机器学习"],
            ["数据分析", "SQL"],
            ["产品经理"],
            ["测试工程师", "自动化"],
            ["运维", "DevOps", "Kubernetes"],
        ]
        
        self.hot_cities = ["北京", "上海", "深圳", "杭州", "广州", "成都"]
    
    def crawl_jobs(self, keywords: List[str], location: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        爬取岗位数据
        
        Args:
            keywords: 搜索关键词列表
            location: 城市
            limit: 数量限制
            
        Returns:
            岗位列表
        """
        print(f"🔍 开始爬取：{keywords} @ {location}")
        
        try:
            params = JobSearchParams(
                keywords=keywords,
                location=location,
                limit=limit
            )
            
            jobs = self.openclaw.search_jobs(params)
            print(f"✅ 爬取成功：{len(jobs)} 个岗位")
            return jobs
            
        except Exception as e:
            print(f"❌ 爬取失败：{str(e)}")
            return []
    
    def push_to_cloud(self, jobs: List[Dict[str, Any]]) -> bool:
        """
        推送岗位数据到云端
        
        Args:
            jobs: 岗位列表
            
        Returns:
            是否成功
        """
        if not jobs:
            return False
        
        try:
            url = f"{self.cloud_api_url}/api/crawler/upload"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "jobs": jobs,
                "timestamp": datetime.now().isoformat(),
                "source": "openclaw_local"
            }
            
            response = requests.post(url, json=data, headers=headers, timeout=30)
            
            if response.status_code == 200:
                print(f"✅ 推送成功：{len(jobs)} 个岗位")
                return True
            else:
                print(f"❌ 推送失败：{response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ 推送异常：{str(e)}")
            return False
    
    def crawl_and_push_all(self):
        """爬取所有热门关键词并推送"""
        print("\n" + "="*60)
        print(f"🚀 开始定时爬取任务 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*60)
        
        total_jobs = 0
        
        for keywords in self.hot_keywords:
            for city in self.hot_cities:
                # 爬取岗位
                jobs = self.crawl_jobs(keywords, city, limit=10)
                
                if jobs:
                    # 推送到云端
                    if self.push_to_cloud(jobs):
                        total_jobs += len(jobs)
                
                # 避免请求过快
                time.sleep(5)
        
        print("\n" + "="*60)
        print(f"✅ 本次任务完成：共爬取并推送 {total_jobs} 个岗位")
        print("="*60 + "\n")
    
    def start_scheduled_crawling(self, interval_hours: int = 6):
        """
        启动定时爬取
        
        Args:
            interval_hours: 爬取间隔（小时）
        """
        print("\n" + "🤖"*30)
        print("OpenClaw爬虫服务启动")
        print("🤖"*30)
        print(f"\n📋 配置信息：")
        print(f"  - 云端API: {self.cloud_api_url}")
        print(f"  - 爬取间隔: 每 {interval_hours} 小时")
        print(f"  - 关键词数: {len(self.hot_keywords)}")
        print(f"  - 城市数: {len(self.hot_cities)}")
        print(f"\n⚠️ 请确保：")
        print(f"  1. Chrome已打开Boss直聘并登录")
        print(f"  2. OpenClaw扩展已Attach到标签页")
        print(f"  3. 保持浏览器窗口不要关闭")
        print(f"\n🔄 首次爬取将在启动后立即开始...\n")
        
        # 立即执行一次
        self.crawl_and_push_all()
        
        # 设置定时任务
        schedule.every(interval_hours).hours.do(self.crawl_and_push_all)
        
        print(f"⏰ 下次爬取时间：{interval_hours} 小时后")
        print(f"💡 按 Ctrl+C 停止服务\n")
        
        # 运行定时任务
        while True:
            schedule.run_pending()
            time.sleep(60)  # 每分钟检查一次


if __name__ == "__main__":
    # 配置
    CLOUD_API_URL = os.getenv("CLOUD_API_URL", "https://your-app.railway.app")
    API_KEY = os.getenv("CRAWLER_API_KEY", "your-secret-key")
    INTERVAL_HOURS = int(os.getenv("CRAWL_INTERVAL_HOURS", "6"))
    
    # 启动爬虫服务
    crawler = OpenClawCrawlerService(
        cloud_api_url=CLOUD_API_URL,
        api_key=API_KEY
    )
    
    try:
        crawler.start_scheduled_crawling(interval_hours=INTERVAL_HOURS)
    except KeyboardInterrupt:
        print("\n\n👋 爬虫服务已停止")

OpenClaw爬虫服务 - 本地运行，定时爬取Boss直聘岗位并推送到云端
"""

import os
import time
import json
import requests
from datetime import datetime
from typing import List, Dict, Any
import schedule
from app.services.job_providers.openclaw_browser_provider import OpenClawBrowserProvider
from app.services.job_providers.base import JobSearchParams

class OpenClawCrawlerService:
    """OpenClaw爬虫服务 - 本地运行"""
    
    def __init__(self, cloud_api_url: str, api_key: str):
        """
        初始化爬虫服务
        
        Args:
            cloud_api_url: 云端API地址，如 https://your-app.railway.app
            api_key: API密钥，用于认证
        """
        self.cloud_api_url = cloud_api_url.rstrip('/')
        self.api_key = api_key
        self.openclaw = OpenClawBrowserProvider()
        
        # 预定义的热门搜索关键词
        self.hot_keywords = [
            ["Python", "后端开发"],
            ["Java", "Spring Boot"],
            ["前端", "React", "Vue"],
            ["算法工程师", "机器学习"],
            ["数据分析", "SQL"],
            ["产品经理"],
            ["测试工程师", "自动化"],
            ["运维", "DevOps", "Kubernetes"],
        ]
        
        self.hot_cities = ["北京", "上海", "深圳", "杭州", "广州", "成都"]
    
    def crawl_jobs(self, keywords: List[str], location: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        爬取岗位数据
        
        Args:
            keywords: 搜索关键词列表
            location: 城市
            limit: 数量限制
            
        Returns:
            岗位列表
        """
        print(f"🔍 开始爬取：{keywords} @ {location}")
        
        try:
            params = JobSearchParams(
                keywords=keywords,
                location=location,
                limit=limit
            )
            
            jobs = self.openclaw.search_jobs(params)
            print(f"✅ 爬取成功：{len(jobs)} 个岗位")
            return jobs
            
        except Exception as e:
            print(f"❌ 爬取失败：{str(e)}")
            return []
    
    def push_to_cloud(self, jobs: List[Dict[str, Any]]) -> bool:
        """
        推送岗位数据到云端
        
        Args:
            jobs: 岗位列表
            
        Returns:
            是否成功
        """
        if not jobs:
            return False
        
        try:
            url = f"{self.cloud_api_url}/api/crawler/upload"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "jobs": jobs,
                "timestamp": datetime.now().isoformat(),
                "source": "openclaw_local"
            }
            
            response = requests.post(url, json=data, headers=headers, timeout=30)
            
            if response.status_code == 200:
                print(f"✅ 推送成功：{len(jobs)} 个岗位")
                return True
            else:
                print(f"❌ 推送失败：{response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ 推送异常：{str(e)}")
            return False
    
    def crawl_and_push_all(self):
        """爬取所有热门关键词并推送"""
        print("\n" + "="*60)
        print(f"🚀 开始定时爬取任务 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*60)
        
        total_jobs = 0
        
        for keywords in self.hot_keywords:
            for city in self.hot_cities:
                # 爬取岗位
                jobs = self.crawl_jobs(keywords, city, limit=10)
                
                if jobs:
                    # 推送到云端
                    if self.push_to_cloud(jobs):
                        total_jobs += len(jobs)
                
                # 避免请求过快
                time.sleep(5)
        
        print("\n" + "="*60)
        print(f"✅ 本次任务完成：共爬取并推送 {total_jobs} 个岗位")
        print("="*60 + "\n")
    
    def start_scheduled_crawling(self, interval_hours: int = 6):
        """
        启动定时爬取
        
        Args:
            interval_hours: 爬取间隔（小时）
        """
        print("\n" + "🤖"*30)
        print("OpenClaw爬虫服务启动")
        print("🤖"*30)
        print(f"\n📋 配置信息：")
        print(f"  - 云端API: {self.cloud_api_url}")
        print(f"  - 爬取间隔: 每 {interval_hours} 小时")
        print(f"  - 关键词数: {len(self.hot_keywords)}")
        print(f"  - 城市数: {len(self.hot_cities)}")
        print(f"\n⚠️ 请确保：")
        print(f"  1. Chrome已打开Boss直聘并登录")
        print(f"  2. OpenClaw扩展已Attach到标签页")
        print(f"  3. 保持浏览器窗口不要关闭")
        print(f"\n🔄 首次爬取将在启动后立即开始...\n")
        
        # 立即执行一次
        self.crawl_and_push_all()
        
        # 设置定时任务
        schedule.every(interval_hours).hours.do(self.crawl_and_push_all)
        
        print(f"⏰ 下次爬取时间：{interval_hours} 小时后")
        print(f"💡 按 Ctrl+C 停止服务\n")
        
        # 运行定时任务
        while True:
            schedule.run_pending()
            time.sleep(60)  # 每分钟检查一次


if __name__ == "__main__":
    # 配置
    CLOUD_API_URL = os.getenv("CLOUD_API_URL", "https://your-app.railway.app")
    API_KEY = os.getenv("CRAWLER_API_KEY", "your-secret-key")
    INTERVAL_HOURS = int(os.getenv("CRAWL_INTERVAL_HOURS", "6"))
    
    # 启动爬虫服务
    crawler = OpenClawCrawlerService(
        cloud_api_url=CLOUD_API_URL,
        api_key=API_KEY
    )
    
    try:
        crawler.start_scheduled_crawling(interval_hours=INTERVAL_HOURS)
    except KeyboardInterrupt:
        print("\n\n👋 爬虫服务已停止")

OpenClaw爬虫服务 - 本地运行，定时爬取Boss直聘岗位并推送到云端
"""

import os
import time
import json
import requests
from datetime import datetime
from typing import List, Dict, Any
import schedule
from app.services.job_providers.openclaw_browser_provider import OpenClawBrowserProvider
from app.services.job_providers.base import JobSearchParams

class OpenClawCrawlerService:
    """OpenClaw爬虫服务 - 本地运行"""
    
    def __init__(self, cloud_api_url: str, api_key: str):
        """
        初始化爬虫服务
        
        Args:
            cloud_api_url: 云端API地址，如 https://your-app.railway.app
            api_key: API密钥，用于认证
        """
        self.cloud_api_url = cloud_api_url.rstrip('/')
        self.api_key = api_key
        self.openclaw = OpenClawBrowserProvider()
        
        # 预定义的热门搜索关键词
        self.hot_keywords = [
            ["Python", "后端开发"],
            ["Java", "Spring Boot"],
            ["前端", "React", "Vue"],
            ["算法工程师", "机器学习"],
            ["数据分析", "SQL"],
            ["产品经理"],
            ["测试工程师", "自动化"],
            ["运维", "DevOps", "Kubernetes"],
        ]
        
        self.hot_cities = ["北京", "上海", "深圳", "杭州", "广州", "成都"]
    
    def crawl_jobs(self, keywords: List[str], location: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        爬取岗位数据
        
        Args:
            keywords: 搜索关键词列表
            location: 城市
            limit: 数量限制
            
        Returns:
            岗位列表
        """
        print(f"🔍 开始爬取：{keywords} @ {location}")
        
        try:
            params = JobSearchParams(
                keywords=keywords,
                location=location,
                limit=limit
            )
            
            jobs = self.openclaw.search_jobs(params)
            print(f"✅ 爬取成功：{len(jobs)} 个岗位")
            return jobs
            
        except Exception as e:
            print(f"❌ 爬取失败：{str(e)}")
            return []
    
    def push_to_cloud(self, jobs: List[Dict[str, Any]]) -> bool:
        """
        推送岗位数据到云端
        
        Args:
            jobs: 岗位列表
            
        Returns:
            是否成功
        """
        if not jobs:
            return False
        
        try:
            url = f"{self.cloud_api_url}/api/crawler/upload"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "jobs": jobs,
                "timestamp": datetime.now().isoformat(),
                "source": "openclaw_local"
            }
            
            response = requests.post(url, json=data, headers=headers, timeout=30)
            
            if response.status_code == 200:
                print(f"✅ 推送成功：{len(jobs)} 个岗位")
                return True
            else:
                print(f"❌ 推送失败：{response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ 推送异常：{str(e)}")
            return False
    
    def crawl_and_push_all(self):
        """爬取所有热门关键词并推送"""
        print("\n" + "="*60)
        print(f"🚀 开始定时爬取任务 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*60)
        
        total_jobs = 0
        
        for keywords in self.hot_keywords:
            for city in self.hot_cities:
                # 爬取岗位
                jobs = self.crawl_jobs(keywords, city, limit=10)
                
                if jobs:
                    # 推送到云端
                    if self.push_to_cloud(jobs):
                        total_jobs += len(jobs)
                
                # 避免请求过快
                time.sleep(5)
        
        print("\n" + "="*60)
        print(f"✅ 本次任务完成：共爬取并推送 {total_jobs} 个岗位")
        print("="*60 + "\n")
    
    def start_scheduled_crawling(self, interval_hours: int = 6):
        """
        启动定时爬取
        
        Args:
            interval_hours: 爬取间隔（小时）
        """
        print("\n" + "🤖"*30)
        print("OpenClaw爬虫服务启动")
        print("🤖"*30)
        print(f"\n📋 配置信息：")
        print(f"  - 云端API: {self.cloud_api_url}")
        print(f"  - 爬取间隔: 每 {interval_hours} 小时")
        print(f"  - 关键词数: {len(self.hot_keywords)}")
        print(f"  - 城市数: {len(self.hot_cities)}")
        print(f"\n⚠️ 请确保：")
        print(f"  1. Chrome已打开Boss直聘并登录")
        print(f"  2. OpenClaw扩展已Attach到标签页")
        print(f"  3. 保持浏览器窗口不要关闭")
        print(f"\n🔄 首次爬取将在启动后立即开始...\n")
        
        # 立即执行一次
        self.crawl_and_push_all()
        
        # 设置定时任务
        schedule.every(interval_hours).hours.do(self.crawl_and_push_all)
        
        print(f"⏰ 下次爬取时间：{interval_hours} 小时后")
        print(f"💡 按 Ctrl+C 停止服务\n")
        
        # 运行定时任务
        while True:
            schedule.run_pending()
            time.sleep(60)  # 每分钟检查一次


if __name__ == "__main__":
    # 配置
    CLOUD_API_URL = os.getenv("CLOUD_API_URL", "https://your-app.railway.app")
    API_KEY = os.getenv("CRAWLER_API_KEY", "your-secret-key")
    INTERVAL_HOURS = int(os.getenv("CRAWL_INTERVAL_HOURS", "6"))
    
    # 启动爬虫服务
    crawler = OpenClawCrawlerService(
        cloud_api_url=CLOUD_API_URL,
        api_key=API_KEY
    )
    
    try:
        crawler.start_scheduled_crawling(interval_hours=INTERVAL_HOURS)
    except KeyboardInterrupt:
        print("\n\n👋 爬虫服务已停止")



