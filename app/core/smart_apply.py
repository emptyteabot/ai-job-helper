"""
智能投递系统 - 基于简历分析结果的精准投递
闭环：分析 → 推荐 → 投递
"""

import json
import re
from typing import Dict, List, Any


class SmartApplyEngine:
    """智能投递引擎 - 基于 AI 分析结果"""

    def __init__(self):
        pass

    def extract_job_targets(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """从 AI 分析结果中提取投递目标"""

        # 从职业分析中提取岗位定位
        career_analysis = analysis_results.get('career_analysis', '')
        job_recommendations = analysis_results.get('job_recommendations', '')

        # 提取关键信息
        targets = {
            'keywords': [],
            'positions': [],
            'companies': [],
            'locations': [],
            'salary_range': None,
            'skills': [],
            'match_criteria': {}
        }

        # 1. 提取岗位关键词
        keywords = self._extract_keywords(career_analysis, job_recommendations)
        targets['keywords'] = keywords[:5]  # 取前5个最重要的

        # 2. 提取推荐岗位
        positions = self._extract_positions(job_recommendations)
        targets['positions'] = positions

        # 3. 提取公司类型
        companies = self._extract_companies(job_recommendations)
        targets['companies'] = companies

        # 4. 提取地点偏好
        locations = self._extract_locations(job_recommendations)
        targets['locations'] = locations if locations else ['北京', '上海', '深圳']

        # 5. 提取薪资范围
        salary = self._extract_salary(job_recommendations)
        targets['salary_range'] = salary

        # 6. 提取核心技能
        skills = self._extract_skills(career_analysis)
        targets['skills'] = skills

        # 7. 匹配标准
        targets['match_criteria'] = {
            'min_match_score': 70,  # 最低匹配度 70%
            'prefer_internship': True,  # 优先实习
            'prefer_conversion': True,  # 优先有转正机会
            'avoid_keywords': ['销售', '客服', '外包']  # 避免的关键词
        }

        return targets

    def _extract_keywords(self, career_text: str, job_text: str) -> List[str]:
        """提取关键词"""
        keywords = []

        # 常见技术关键词
        tech_keywords = [
            'Python', 'Java', 'JavaScript', 'React', 'Vue', 'Node.js',
            'Django', 'Flask', 'Spring', 'MySQL', 'Redis', 'Docker',
            '前端', '后端', '全栈', '算法', '数据分析', '机器学习',
            'AI', '深度学习', '自然语言处理', '计算机视觉'
        ]

        combined_text = career_text + job_text

        for keyword in tech_keywords:
            if keyword in combined_text:
                keywords.append(keyword)

        return keywords

    def _extract_positions(self, job_text: str) -> List[Dict[str, str]]:
        """提取推荐岗位"""
        positions = []

        # 使用正则提取岗位信息
        # 格式：职位名称 | 公司名称 | 薪资 | 匹配度
        pattern = r'(\d+)\.\s*\*\*(.+?)\*\*.*?公司[：:]\s*(.+?)(?:\n|薪资|匹配)'
        matches = re.findall(pattern, job_text)

        for match in matches:
            position = {
                'title': match[1].strip(),
                'company': match[2].strip() if len(match) > 2 else '',
                'source': 'AI推荐'
            }
            positions.append(position)

        return positions[:5]  # 最多5个

    def _extract_companies(self, job_text: str) -> List[str]:
        """提取公司类型"""
        companies = []

        company_types = ['大厂', '独角兽', '创业公司', '外企', '国企', '互联网']

        for company_type in company_types:
            if company_type in job_text:
                companies.append(company_type)

        return companies

    def _extract_locations(self, job_text: str) -> List[str]:
        """提取地点"""
        locations = []

        cities = ['北京', '上海', '深圳', '杭州', '广州', '成都', '南京', '武汉']

        for city in cities:
            if city in job_text:
                locations.append(city)

        return locations[:3]  # 最多3个

    def _extract_salary(self, job_text: str) -> Dict[str, int]:
        """提取薪资范围"""
        # 提取薪资范围，如 "3000-5000"
        pattern = r'(\d+)-(\d+)'
        match = re.search(pattern, job_text)

        if match:
            return {
                'min': int(match.group(1)),
                'max': int(match.group(2))
            }

        return {'min': 3000, 'max': 6000}  # 默认实习生薪资

    def _extract_skills(self, career_text: str) -> List[str]:
        """提取核心技能"""
        skills = []

        # 从 SWOT 分析中提取优势技能
        if '优势' in career_text or 'SWOT' in career_text:
            # 简单提取，实际可以用 NLP
            skill_keywords = [
                'Python', 'Java', 'JavaScript', '算法', '数据结构',
                '项目经验', '团队协作', '学习能力', '沟通能力'
            ]

            for skill in skill_keywords:
                if skill in career_text:
                    skills.append(skill)

        return skills

    def generate_apply_config(self, targets: Dict[str, Any]) -> Dict[str, Any]:
        """生成投递配置"""

        config = {
            'platforms': ['Boss直聘', '实习僧', '牛客网'],
            'search_config': {
                'keywords': ' OR '.join(targets['keywords'][:3]),  # 前3个关键词
                'locations': targets['locations'],
                'salary_min': targets['salary_range']['min'],
                'salary_max': targets['salary_range']['max'],
                'job_type': '实习',
                'experience': '在校生/应届生'
            },
            'filter_config': {
                'must_include': targets['keywords'],
                'must_exclude': targets['match_criteria']['avoid_keywords'],
                'min_match_score': targets['match_criteria']['min_match_score'],
                'prefer_tags': ['转正机会', '导师制', '大厂', '实习证明']
            },
            'apply_config': {
                'max_per_day': 30,  # 每天最多30个
                'interval_seconds': 5,  # 间隔5秒
                'auto_answer': True,  # 自动回答问题
                'custom_cover_letter': True  # 使用定制求职信
            },
            'target_positions': targets['positions']
        }

        return config

    def generate_selenium_script(self, config: Dict[str, Any], platform: str) -> str:
        """生成 Selenium 自动化脚本"""

        if platform == 'Boss直聘':
            return self._generate_boss_script(config)
        elif platform == '实习僧':
            return self._generate_shixiseng_script(config)
        elif platform == '牛客网':
            return self._generate_nowcoder_script(config)
        else:
            return ""

    def _generate_boss_script(self, config: Dict[str, Any]) -> str:
        """生成 Boss 直聘脚本"""

        script = f"""
# Boss直聘自动投递脚本
# 基于 AI 简历分析结果生成

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import random

# 配置
KEYWORDS = {config['search_config']['keywords']}
LOCATIONS = {config['search_config']['locations']}
MAX_APPLY = {config['apply_config']['max_per_day']}
INTERVAL = {config['apply_config']['interval_seconds']}

# 必须包含的关键词
MUST_INCLUDE = {config['filter_config']['must_include']}
MUST_EXCLUDE = {config['filter_config']['must_exclude']}

def init_driver():
    options = webdriver.ChromeOptions()
    options.add_argument('--disable-blink-features=AutomationControlled')
    driver = webdriver.Chrome(options=options)
    return driver

def login(driver):
    driver.get('https://www.zhipin.com/')
    input("请手动登录后按回车继续...")

def search_jobs(driver, keyword, location):
    search_url = f'https://www.zhipin.com/web/geek/job?query={{keyword}}&city={{location}}'
    driver.get(search_url)
    time.sleep(2)

def filter_job(job_element):
    job_title = job_element.find_element(By.CLASS_NAME, 'job-title').text
    job_desc = job_element.find_element(By.CLASS_NAME, 'job-detail').text

    # 检查必须包含的关键词
    for keyword in MUST_INCLUDE:
        if keyword.lower() not in (job_title + job_desc).lower():
            return False

    # 检查排除的关键词
    for keyword in MUST_EXCLUDE:
        if keyword.lower() in (job_title + job_desc).lower():
            return False

    return True

def apply_job(driver, job_element):
    try:
        # 点击立即沟通
        chat_btn = job_element.find_element(By.CLASS_NAME, 'start-chat-btn')
        chat_btn.click()
        time.sleep(random.uniform(2, 4))

        # 发送打招呼消息（可选）
        # message_input = driver.find_element(By.CLASS_NAME, 'message-input')
        # message_input.send_keys("您好，我对这个实习岗位很感兴趣...")

        return True
    except Exception as e:
        print(f"投递失败: {{e}}")
        return False

def main():
    driver = init_driver()
    login(driver)

    applied_count = 0

    for location in LOCATIONS:
        if applied_count >= MAX_APPLY:
            break

        search_jobs(driver, KEYWORDS, location)

        job_list = driver.find_elements(By.CLASS_NAME, 'job-card-wrapper')

        for job in job_list:
            if applied_count >= MAX_APPLY:
                break

            if filter_job(job):
                if apply_job(driver, job):
                    applied_count += 1
                    print(f"已投递 {{applied_count}}/{{MAX_APPLY}}")
                    time.sleep(INTERVAL)

    print(f"投递完成！共投递 {{applied_count}} 个岗位")
    driver.quit()

if __name__ == '__main__':
    main()
"""
        return script

    def _generate_shixiseng_script(self, config: Dict[str, Any]) -> str:
        """生成实习僧脚本"""
        return "# 实习僧脚本（待实现）"

    def _generate_nowcoder_script(self, config: Dict[str, Any]) -> str:
        """生成牛客网脚本"""
        return "# 牛客网脚本（待实现）"


# 全局实例
smart_apply_engine = SmartApplyEngine()
