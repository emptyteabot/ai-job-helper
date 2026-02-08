"""
岗位搜索服务 - 模拟从各大招聘网站搜索岗位
"""

from typing import List, Dict, Any
import random

class JobSearcher:
    """岗位搜索器 - 搜索匹配的岗位"""
    
    def __init__(self):
        # 模拟岗位数据库（实际应该对接真实API）
        self.mock_jobs = [
            {
                "title": "Python后端开发工程师",
                "company": "字节跳动",
                "salary": "20-40K",
                "location": "北京",
                "requirements": ["Python", "Django", "MySQL", "Redis", "3年经验"],
                "platform": "Boss直聘"
            },
            {
                "title": "全栈开发工程师",
                "company": "阿里巴巴",
                "salary": "25-45K",
                "location": "杭州",
                "requirements": ["Python", "React", "Node.js", "MongoDB", "5年经验"],
                "platform": "猎聘"
            },
            {
                "title": "数据分析师",
                "company": "腾讯",
                "salary": "18-35K",
                "location": "深圳",
                "requirements": ["Python", "Pandas", "SQL", "数据可视化", "2年经验"],
                "platform": "智联招聘"
            },
            {
                "title": "机器学习工程师",
                "company": "百度",
                "salary": "30-50K",
                "location": "北京",
                "requirements": ["Python", "TensorFlow", "PyTorch", "算法", "3年经验"],
                "platform": "前程无忧"
            },
            {
                "title": "Django开发工程师",
                "company": "美团",
                "salary": "22-38K",
                "location": "北京",
                "requirements": ["Python", "Django", "MySQL", "Redis", "Docker"],
                "platform": "Boss直聘"
            }
        ]
    
    def search_jobs(self, skills: List[str], job_intention: str, experience_years: int) -> List[Dict[str, Any]]:
        """
        根据技能和意向搜索岗位
        
        Args:
            skills: 技能列表
            job_intention: 求职意向
            experience_years: 工作年限
        
        Returns:
            匹配的岗位列表
        """
        matched_jobs = []
        
        for job in self.mock_jobs:
            # 计算匹配度
            match_score = self._calculate_match_score(job, skills, job_intention)
            
            if match_score > 0.3:  # 匹配度超过30%
                job_copy = job.copy()
                job_copy['match_score'] = match_score
                job_copy['match_percentage'] = f"{int(match_score * 100)}%"
                matched_jobs.append(job_copy)
        
        # 按匹配度排序
        matched_jobs.sort(key=lambda x: x['match_score'], reverse=True)
        
        return matched_jobs[:10]  # 返回前10个最匹配的岗位
    
    def _calculate_match_score(self, job: Dict, skills: List[str], job_intention: str) -> float:
        """计算岗位匹配度"""
        score = 0.0
        
        # 技能匹配
        job_requirements = [r.lower() for r in job['requirements']]
        user_skills = [s.lower() for s in skills]
        
        matched_skills = sum(1 for skill in user_skills if any(skill in req for req in job_requirements))
        if len(job_requirements) > 0:
            score += (matched_skills / len(job_requirements)) * 0.7
        
        # 职位意向匹配
        if job_intention and job_intention.lower() in job['title'].lower():
            score += 0.3
        
        return min(score, 1.0)
    
    def format_job_list(self, jobs: List[Dict[str, Any]]) -> str:
        """格式化岗位列表为文本"""
        if not jobs:
            return "未找到匹配的岗位"
        
        output = f"\n🎯 找到 {len(jobs)} 个匹配岗位\n"
        output += "="*60 + "\n\n"
        
        for i, job in enumerate(jobs, 1):
            output += f"【岗位 {i}】{job['title']}\n"
            output += f"  公司: {job['company']}\n"
            output += f"  薪资: {job['salary']}\n"
            output += f"  地点: {job['location']}\n"
            output += f"  匹配度: {job['match_percentage']}\n"
            output += f"  要求: {', '.join(job['requirements'])}\n"
            output += f"  来源: {job['platform']}\n"
            output += "-"*60 + "\n\n"
        
        return output

