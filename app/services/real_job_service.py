"""
真实招聘数据服务 - 对接各大招聘平台
支持: Boss直聘、猎聘、智联招聘、前程无忧
"""

import os
import json
from typing import List, Dict, Any
import random
from datetime import datetime, timedelta
from urllib.parse import quote

from app.services.application_record_service import ApplicationRecordService
from app.services.job_providers.base import JobSearchParams
from app.services.job_providers.jooble_provider import JoobleProvider
from app.services.job_providers.bing_provider import BingWebSearchProvider
from app.services.job_providers.baidu_provider import BaiduSearchProvider
from app.services.job_providers.brave_provider import BraveSearchProvider
from app.services.job_providers.openclaw_browser_provider import OpenClawBrowserProvider

class RealJobService:
    """真实招聘数据服务"""
    
    def __init__(self):
        # Provider selection:
        # - If JOOBLE_API_KEY is set, use real-time Jooble API results.
        # - Otherwise fall back to the bundled local dataset generator.
        self.provider_name = os.getenv("JOB_DATA_PROVIDER", "auto").strip().lower()
        # Keep local synthetic dataset strictly opt-in in production paths.
        self.allow_local_fallback = os.getenv("ALLOW_LOCAL_JOB_FALLBACK", "").strip().lower() in {
            "1", "true", "yes", "on"
        }
        self.jooble = JoobleProvider()
        self.bing = BingWebSearchProvider()
        self.baidu = BaiduSearchProvider()
        self.brave = BraveSearchProvider()
        self.openclaw = OpenClawBrowserProvider()

        # 本地岗位数据库（fallback；用于无API Key时的演示/离线运行）
        self.real_jobs_database = self._load_real_jobs()

        # 投递记录
        self.records = ApplicationRecordService()
        
        # 第三方API配置（可选）
        self.api_configs = {
            "juhe": {
                "key": "",  # 聚合数据API Key
                "url": "http://apis.juhe.cn/recruit/query"
            },
            "aliyun": {
                "key": "",  # 阿里云市场API Key
                "url": ""
            }
        }
    
    def _load_real_jobs(self) -> List[Dict[str, Any]]:
        """加载本地岗位数据库（fallback；用于无API Key时的演示/离线运行）"""

        # Keep output stable across runs so job IDs don't reshuffle every restart.
        rng = random.Random(42)

        def build_link(platform: str, title: str, company: str) -> str:
            q = quote(f"{title} {company}")
            if platform == "Boss直聘":
                return f"https://www.zhipin.com/web/geek/job?query={q}"
            if platform == "猎聘":
                return f"https://www.liepin.com/zhaopin/?key={q}"
            if platform == "智联招聘":
                return f"https://sou.zhaopin.com/?kw={q}"
            if platform == "前程无忧":
                return f"https://search.51job.com/list/000000,000000,0000,00,9,99,{q},2,1.html"
            return f"https://www.baidu.com/s?wd={quote(platform + ' ' + title + ' ' + company + ' 投递')}"
        
        # 真实公司列表
        companies = {
            "互联网大厂": [
                "字节跳动", "阿里巴巴", "腾讯", "百度", "美团",
                "京东", "拼多多", "小米", "华为", "网易",
                "滴滴出行", "快手", "B站", "知乎", "携程"
            ],
            "独角兽": [
                "商汤科技", "旷视科技", "依图科技", "第四范式",
                "地平线", "寒武纪", "云从科技", "澜起科技"
            ],
            "新兴公司": [
                "理想汽车", "蔚来汽车", "小鹏汽车", "零跑汽车",
                "元气森林", "完美日记", "泡泡玛特", "喜茶"
            ],
            "传统企业": [
                "中国移动", "中国电信", "中国联通", "工商银行",
                "建设银行", "招商银行", "平安集团", "中国人寿"
            ]
        }
        
        # 真实岗位模板
        job_templates = [
            # Python后端
            {
                "title": "Python后端开发工程师",
                "salary_range": ["15-30K", "20-40K", "25-50K"],
                "requirements": ["Python", "Django/Flask", "MySQL", "Redis", "Docker"],
                "description": "负责后端服务开发，参与系统架构设计",
                "experience": ["3-5年", "5-10年"],
                "education": ["本科", "硕士"],
                "platform": "Boss直聘"
            },
            # Java后端
            {
                "title": "Java开发工程师",
                "salary_range": ["18-35K", "25-45K", "30-60K"],
                "requirements": ["Java", "Spring Boot", "MySQL", "Redis", "Kafka"],
                "description": "负责核心业务系统开发和优化",
                "experience": ["3-5年", "5-10年"],
                "education": ["本科", "硕士"],
                "platform": "猎聘"
            },
            # 前端
            {
                "title": "前端开发工程师",
                "salary_range": ["15-28K", "20-38K", "25-48K"],
                "requirements": ["React/Vue", "TypeScript", "Webpack", "Node.js"],
                "description": "负责前端页面开发和性能优化",
                "experience": ["3-5年", "5-10年"],
                "education": ["本科", "硕士"],
                "platform": "智联招聘"
            },
            # 全栈
            {
                "title": "全栈开发工程师",
                "salary_range": ["20-35K", "25-45K", "30-55K"],
                "requirements": ["Python/Java", "React/Vue", "MySQL", "Docker"],
                "description": "负责前后端开发，独立完成项目",
                "experience": ["3-5年", "5-10年"],
                "education": ["本科", "硕士"],
                "platform": "前程无忧"
            },
            # 算法工程师
            {
                "title": "算法工程师",
                "salary_range": ["25-45K", "35-60K", "40-80K"],
                "requirements": ["Python", "TensorFlow/PyTorch", "机器学习", "深度学习"],
                "description": "负责算法研发和模型优化",
                "experience": ["3-5年", "5-10年"],
                "education": ["硕士", "博士"],
                "platform": "Boss直聘"
            },
            # 数据分析
            {
                "title": "数据分析师",
                "salary_range": ["15-25K", "20-35K", "25-45K"],
                "requirements": ["Python", "SQL", "Pandas", "数据可视化"],
                "description": "负责数据分析和报表制作",
                "experience": ["2-5年", "3-5年"],
                "education": ["本科", "硕士"],
                "platform": "猎聘"
            },
            # 产品经理
            {
                "title": "产品经理",
                "salary_range": ["20-35K", "25-45K", "30-60K"],
                "requirements": ["产品设计", "需求分析", "Axure", "用户研究"],
                "description": "负责产品规划和需求管理",
                "experience": ["3-5年", "5-10年"],
                "education": ["本科", "硕士"],
                "platform": "智联招聘"
            },
            # 测试工程师
            {
                "title": "测试工程师",
                "salary_range": ["12-22K", "18-30K", "22-40K"],
                "requirements": ["Python", "自动化测试", "性能测试", "Selenium"],
                "description": "负责软件测试和质量保证",
                "experience": ["2-5年", "3-5年"],
                "education": ["本科"],
                "platform": "前程无忧"
            },
            # 运维工程师
            {
                "title": "运维工程师",
                "salary_range": ["15-28K", "20-38K", "25-48K"],
                "requirements": ["Linux", "Docker", "Kubernetes", "监控"],
                "description": "负责系统运维和故障处理",
                "experience": ["3-5年", "5-10年"],
                "education": ["本科"],
                "platform": "Boss直聘"
            },
            # 架构师
            {
                "title": "架构师",
                "salary_range": ["35-60K", "45-80K", "50-100K"],
                "requirements": ["分布式系统", "微服务", "高并发", "系统设计"],
                "description": "负责系统架构设计和技术选型",
                "experience": ["5-10年", "8-15年"],
                "education": ["本科", "硕士"],
                "platform": "猎聘"
            }
        ]
        
        # 生成1000+真实岗位
        jobs = []
        job_id = 1
        
        for category, company_list in companies.items():
            for company in company_list:
                for template in job_templates:
                    # 每个公司每个岗位生成1-2个职位
                    for _ in range(rng.randint(1, 2)):
                        job = {
                            "id": f"JOB{job_id:06d}",
                            "title": template["title"],
                            "company": company,
                            "company_category": category,
                            "salary": rng.choice(template["salary_range"]),
                            "location": rng.choice(["北京", "上海", "深圳", "杭州", "广州", "成都"]),
                            "experience": rng.choice(template["experience"]),
                            "education": rng.choice(template["education"]),
                            "requirements": template["requirements"],
                            "description": template["description"],
                            "platform": template["platform"],
                            "link": build_link(template["platform"], template["title"], company),
                            "publish_date": (datetime.now() - timedelta(days=rng.randint(0, 30))).strftime("%Y-%m-%d"),
                            "company_size": rng.choice(["50-150人", "150-500人", "500-2000人", "2000人以上"]),
                            "company_type": rng.choice(["互联网", "金融", "教育", "医疗", "电商"]),
                            "welfare": rng.sample([
                                "五险一金", "年终奖", "股票期权", "弹性工作",
                                "带薪年假", "免费三餐", "健身房", "团建活动",
                                "节日福利", "通讯补贴", "交通补贴", "住房补贴"
                            ], k=rng.randint(4, 8)),
                            "hr_name": f"HR{rng.randint(1000, 9999)}",
                            "hr_response_rate": f"{rng.randint(70, 99)}%",
                            "view_count": rng.randint(100, 5000),
                            "apply_count": rng.randint(10, 500),
                            "provider": "local",
                        }
                        jobs.append(job)
                        job_id += 1
        
        return jobs

    def _use_jooble(self) -> bool:
        if self.provider_name in ("jooble",):
            return True
        if self.provider_name in ("local", "offline"):
            return False
        # auto
        return bool(self.jooble.api_key)

    def _use_bing(self) -> bool:
        if self.provider_name in ("bing", "bing_search"):
            return True
        if self.provider_name in ("local", "offline"):
            return False
        # auto (only if jooble is not enabled)
        return (not self._use_jooble()) and bool(self.bing.api_key)

    def _use_brave(self) -> bool:
        if self.provider_name in ("brave", "brave_search"):
            return True
        if self.provider_name in ("local", "offline"):
            return False
        # auto (only if jooble is not enabled)
        return (not self._use_jooble()) and bool(self.brave.api_key)

    def _use_openclaw(self) -> bool:
        if self.provider_name in ("openclaw", "openclaw_browser"):
            return True
        if self.provider_name in ("local", "offline"):
            return False
        # auto: prefer API providers; OpenClaw is a local interactive option.
        return False

    def _use_baidu(self) -> bool:
        if self.provider_name in ("baidu", "baidu_search", "deepseek_search"):
            return True
        if self.provider_name in ("local", "offline"):
            return False
        # auto fallback: if no API-based provider is enabled, use Baidu.
        return (not self._use_jooble()) and (not self._use_brave()) and (not self._use_bing())

    def _use_local_dataset(self) -> bool:
        # Local synthetic jobs are allowed only when explicitly requested.
        return self.provider_name in ("local", "offline") or self.allow_local_fallback
    
    def search_jobs(self, 
                   keywords: List[str] = None,
                   location: str = None,
                   salary_min: int = None,
                   experience: str = None,
                   limit: int = 50,
                   progress_callback=None) -> List[Dict[str, Any]]:
        """
        搜索岗位（实时优先；无API Key时自动回退到本地数据）
        
        Args:
            keywords: 关键词列表（技能、职位等）
            location: 工作地点
            salary_min: 最低薪资
            experience: 工作经验
            limit: 返回数量
        
        Returns:
            匹配的岗位列表
        """
        
        keywords = keywords or []

        # Real-time provider path.
        if self._use_jooble():
            params = JobSearchParams(
                keywords=keywords,
                location=location,
                salary_min=salary_min,
                experience=experience,
                limit=limit,
            )
            return self.jooble.search_jobs(params)

        if self._use_openclaw():
            params = JobSearchParams(
                keywords=keywords,
                location=location,
                salary_min=salary_min,
                experience=experience,
                limit=limit,
            )
            return self.openclaw.search_jobs(params, progress_callback=progress_callback)

        if self._use_brave():
            params = JobSearchParams(
                keywords=keywords,
                location=location,
                salary_min=salary_min,
                experience=experience,
                limit=limit,
            )
            return self.brave.search_jobs(params)

        # Real-time link discovery via search engine.
        if self._use_bing():
            params = JobSearchParams(
                keywords=keywords,
                location=location,
                salary_min=salary_min,
                experience=experience,
                limit=limit,
            )
            return self.bing.search_jobs(params)

        # No-key China-friendly option: Baidu SERP -> real job URLs.
        if self._use_baidu():
            params = JobSearchParams(
                keywords=keywords,
                location=location,
                salary_min=salary_min,
                experience=experience,
                limit=limit,
            )
            return self.baidu.search_jobs(params)

        if not self._use_local_dataset():
            return []

        matched_jobs: List[Dict[str, Any]] = []
        
        for job in self.real_jobs_database:
            score = 0
            
            # 关键词匹配
            if keywords:
                for keyword in keywords:
                    keyword_lower = keyword.lower()
                    # 检查标题
                    if keyword_lower in job['title'].lower():
                        score += 10
                    # 检查技能要求
                    for req in job['requirements']:
                        if keyword_lower in req.lower():
                            score += 5
            
            # 地点匹配
            if location and location in job['location']:
                score += 8
            
            # 薪资匹配
            if salary_min:
                salary_range = job['salary'].replace('K', '').split('-')
                if len(salary_range) == 2:
                    min_salary = int(salary_range[0])
                    if min_salary >= salary_min:
                        score += 5
            
            # 经验匹配
            if experience and experience in job['experience']:
                score += 5
            
            if score > 0:
                job_copy = job.copy()
                job_copy['match_score'] = score
                job_copy['match_percentage'] = min(int(score * 2), 100)
                matched_jobs.append(job_copy)
        
        # 按匹配度排序
        matched_jobs.sort(key=lambda x: x['match_score'], reverse=True)
        
        return matched_jobs[:limit]
    
    def get_job_detail(self, job_id: str) -> Dict[str, Any]:
        """获取岗位详情"""
        if job_id and job_id.startswith("jooble_"):
            job = self.jooble.get_job_detail(job_id)
            if job:
                return job
        if job_id and job_id.startswith("bing_"):
            job = self.bing.get_job_detail(job_id)
            if job:
                return job
        if job_id and job_id.startswith("baidu_"):
            job = self.baidu.get_job_detail(job_id)
            if job:
                return job
        if job_id and job_id.startswith("brave_"):
            job = self.brave.get_job_detail(job_id)
            if job:
                return job
        if job_id and job_id.startswith("openclaw_"):
            job = self.openclaw.get_job_detail(job_id)
            if job:
                return job
        for job in self.real_jobs_database:
            if job['id'] == job_id:
                return job
        return None
    
    def apply_job(self, job_id: str, resume_text: str, user_info: Dict) -> Dict[str, Any]:
        """
        投递简历到指定岗位
        
        Args:
            job_id: 岗位ID
            resume_text: 简历内容
            user_info: 用户信息
        
        Returns:
            投递结果
        """
        job = self.get_job_detail(job_id)
        
        if not job:
            return {
                "success": False,
                "message": "岗位不存在"
            }
        
        # IMPORTANT:
        # Most job boards (Boss/猎聘/智联/51job) do not provide a public "apply"
        # API. Real automated applying generally requires logged-in browser
        # automation and may violate platform ToS, and also runs into captchas.
        # Here we implement "真实岗位 + 跳转投递" and record an application entry.
        application_id = f"APP{random.randint(100000, 999999)}"
        apply_link = job.get("link") or job.get("apply_url") or ""
        status = "待投递" if apply_link else "待处理"

        application = {
            "application_id": application_id,
            "job_id": job_id,
            "job_title": job.get('title', ''),
            "company": job.get('company', ''),
            "platform": job.get('platform', job.get('provider', '')),
            "apply_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "status": status,
            "apply_link": apply_link,
            "user_info": user_info or {},
        }
        self.records.add_record(application)

        if apply_link:
            return {
                "success": True,
                "message": "已生成投递链接（请在打开的招聘网站完成真实投递）",
                "data": application,
            }

        return {
            "success": False,
            "message": "该岗位未提供可跳转的投递链接，无法进行真实投递。",
            "data": application,
        }
    
    def batch_apply(self, job_ids: List[str], resume_text: str, user_info: Dict) -> List[Dict]:
        """批量投递"""
        results = []
        for job_id in job_ids:
            result = self.apply_job(job_id, resume_text, user_info)
            results.append(result)
        return results
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取数据统计"""
        return {
            "total_jobs": len(self.real_jobs_database),
            "total_companies": len(set(job['company'] for job in self.real_jobs_database)),
            "provider_mode": (
                "jooble"
                if self._use_jooble()
                else (
                    "openclaw"
                    if self._use_openclaw()
                    else (
                    "brave"
                    if self._use_brave()
                    else (
                        "bing"
                        if self._use_bing()
                        else ("baidu" if self._use_baidu() else ("local" if self._use_local_dataset() else "none"))
                    )
                    )
                )
            ),
            "platforms": {
                "Boss直聘": len([j for j in self.real_jobs_database if j['platform'] == 'Boss直聘']),
                "猎聘": len([j for j in self.real_jobs_database if j['platform'] == '猎聘']),
                "智联招聘": len([j for j in self.real_jobs_database if j['platform'] == '智联招聘']),
                "前程无忧": len([j for j in self.real_jobs_database if j['platform'] == '前程无忧'])
            },
            "locations": {
                "北京": len([j for j in self.real_jobs_database if j['location'] == '北京']),
                "上海": len([j for j in self.real_jobs_database if j['location'] == '上海']),
                "深圳": len([j for j in self.real_jobs_database if j['location'] == '深圳']),
                "杭州": len([j for j in self.real_jobs_database if j['location'] == '杭州']),
                "广州": len([j for j in self.real_jobs_database if j['location'] == '广州']),
                "成都": len([j for j in self.real_jobs_database if j['location'] == '成都'])
            }
        }


# 快速测试
if __name__ == "__main__":
    service = RealJobService()
    
    # 测试搜索
    print("搜索Python岗位...")
    jobs = service.search_jobs(keywords=["Python", "Django"], location="北京", limit=10)
    
    print(f"\n找到 {len(jobs)} 个匹配岗位:\n")
    for i, job in enumerate(jobs, 1):
        print(f"{i}. {job['title']} - {job['company']}")
        print(f"   薪资: {job['salary']} | 地点: {job['location']}")
        print(f"   平台: {job['platform']} | 匹配度: {job['match_percentage']}%")
        print()
    
    # 统计信息
    stats = service.get_statistics()
    print(f"\n数据库统计:")
    print(f"总岗位数: {stats['total_jobs']}")
    print(f"总公司数: {stats['total_companies']}")
    print(f"平台分布: {stats['platforms']}")

