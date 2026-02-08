"""
技能图谱系统 - Skills Graph
参考GitHub高星项目的技能匹配算法
"""

from typing import Dict, List, Set, Tuple
import json
from dataclasses import dataclass

@dataclass
class Skill:
    """技能节点"""
    name: str
    category: str  # 编程语言、框架、工具、软技能
    level: int  # 1-5级
    related_skills: List[str]  # 相关技能
    weight: float  # 权重

class SkillsGraph:
    """技能图谱 - 用于智能匹配"""
    
    def __init__(self):
        # 技能分类体系
        self.skill_taxonomy = {
            "编程语言": {
                "Python": {"related": ["Django", "Flask", "FastAPI", "Pandas"], "weight": 1.0},
                "JavaScript": {"related": ["React", "Vue", "Node.js", "TypeScript"], "weight": 1.0},
                "Java": {"related": ["Spring", "SpringBoot", "Maven", "Gradle"], "weight": 1.0},
                "Go": {"related": ["Gin", "Echo", "gRPC"], "weight": 0.9},
                "C++": {"related": ["Qt", "Boost", "CMake"], "weight": 0.9},
            },
            "后端框架": {
                "Django": {"related": ["Python", "DRF", "Celery"], "weight": 0.8},
                "Flask": {"related": ["Python", "SQLAlchemy"], "weight": 0.7},
                "FastAPI": {"related": ["Python", "Pydantic", "Uvicorn"], "weight": 0.8},
                "Spring": {"related": ["Java", "SpringBoot", "MyBatis"], "weight": 0.9},
                "Express": {"related": ["Node.js", "JavaScript"], "weight": 0.7},
            },
            "前端框架": {
                "React": {"related": ["JavaScript", "Redux", "Next.js"], "weight": 0.9},
                "Vue": {"related": ["JavaScript", "Vuex", "Nuxt.js"], "weight": 0.9},
                "Angular": {"related": ["TypeScript", "RxJS"], "weight": 0.8},
            },
            "数据库": {
                "MySQL": {"related": ["SQL", "InnoDB"], "weight": 0.9},
                "PostgreSQL": {"related": ["SQL", "PostGIS"], "weight": 0.9},
                "MongoDB": {"related": ["NoSQL", "Mongoose"], "weight": 0.8},
                "Redis": {"related": ["缓存", "消息队列"], "weight": 0.8},
            },
            "DevOps": {
                "Docker": {"related": ["容器化", "Kubernetes"], "weight": 0.9},
                "Kubernetes": {"related": ["Docker", "Helm"], "weight": 0.9},
                "Jenkins": {"related": ["CI/CD", "Pipeline"], "weight": 0.7},
                "Git": {"related": ["GitHub", "GitLab"], "weight": 1.0},
            },
            "云服务": {
                "AWS": {"related": ["EC2", "S3", "Lambda"], "weight": 0.9},
                "阿里云": {"related": ["ECS", "OSS"], "weight": 0.8},
                "腾讯云": {"related": ["CVM", "COS"], "weight": 0.8},
            },
            "AI/ML": {
                "TensorFlow": {"related": ["Python", "Keras"], "weight": 0.9},
                "PyTorch": {"related": ["Python", "深度学习"], "weight": 0.9},
                "Scikit-learn": {"related": ["Python", "机器学习"], "weight": 0.8},
            }
        }
    
    def extract_skills(self, text: str) -> List[Dict]:
        """从文本中提取技能"""
        skills_found = []
        text_lower = text.lower()
        
        for category, skills in self.skill_taxonomy.items():
            for skill_name, skill_info in skills.items():
                if skill_name.lower() in text_lower:
                    skills_found.append({
                        "name": skill_name,
                        "category": category,
                        "weight": skill_info["weight"],
                        "related": skill_info["related"]
                    })
        
        return skills_found
    
    def calculate_match_score(self, resume_skills: List[Dict], job_skills: List[Dict]) -> float:
        """计算技能匹配度 (0-100)"""
        if not job_skills:
            return 50.0
        
        resume_skill_names = {s["name"].lower() for s in resume_skills}
        job_skill_names = {s["name"].lower() for s in job_skills}
        
        # 直接匹配
        direct_match = len(resume_skill_names & job_skill_names)
        
        # 相关技能匹配
        related_match = 0
        for resume_skill in resume_skills:
            for related in resume_skill.get("related", []):
                if related.lower() in job_skill_names:
                    related_match += 0.5
        
        total_score = (direct_match + related_match) / len(job_skill_names) * 100
        return min(100.0, total_score)
    
    def recommend_skills(self, current_skills: List[Dict], target_role: str) -> List[str]:
        """推荐需要学习的技能"""
        # 根据目标岗位推荐技能
        role_skill_map = {
            "后端开发": ["Python", "Java", "MySQL", "Redis", "Docker"],
            "前端开发": ["JavaScript", "React", "Vue", "TypeScript"],
            "全栈开发": ["Python", "JavaScript", "React", "MySQL", "Docker"],
            "数据分析": ["Python", "Pandas", "SQL", "Tableau"],
            "AI工程师": ["Python", "TensorFlow", "PyTorch", "深度学习"],
        }
        
        current_skill_names = {s["name"] for s in current_skills}
        recommended = []
        
        for role, skills in role_skill_map.items():
            if role.lower() in target_role.lower():
                for skill in skills:
                    if skill not in current_skill_names:
                        recommended.append(skill)
        
        return recommended[:5]  # 返回前5个推荐

