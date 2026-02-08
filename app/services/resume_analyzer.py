"""
简历分析服务 - 提取简历关键信息
"""

import re
from typing import Dict, List, Any

class ResumeAnalyzer:
    """简历分析器 - 提取关键信息"""
    
    def __init__(self):
        self.skill_keywords = {
            "编程语言": ["Python", "Java", "JavaScript", "C++", "Go", "Rust", "PHP", "Ruby"],
            "前端": ["React", "Vue", "Angular", "HTML", "CSS", "TypeScript", "Next.js"],
            "后端": ["Django", "Flask", "Spring", "Node.js", "Express", "FastAPI"],
            "数据库": ["MySQL", "PostgreSQL", "MongoDB", "Redis", "Oracle", "SQL Server"],
            "云服务": ["AWS", "Azure", "阿里云", "腾讯云", "Docker", "Kubernetes"],
            "数据分析": ["Pandas", "NumPy", "Matplotlib", "Tableau", "Power BI"],
            "机器学习": ["TensorFlow", "PyTorch", "Scikit-learn", "Keras", "OpenCV"]
        }
    
    def extract_info(self, resume_text: str) -> Dict[str, Any]:
        """
        从简历中提取关键信息
        
        Returns:
            {
                "name": "姓名",
                "education": "学历",
                "experience_years": 工作年限,
                "skills": ["技能列表"],
                "skill_categories": {"分类": ["技能"]},
                "projects": ["项目经验"],
                "job_intention": "求职意向"
            }
        """
        info = {
            "name": self._extract_name(resume_text),
            "education": self._extract_education(resume_text),
            "experience_years": self._extract_experience(resume_text),
            "skills": self._extract_skills(resume_text),
            "skill_categories": self._categorize_skills(resume_text),
            "projects": self._extract_projects(resume_text),
            "job_intention": self._extract_job_intention(resume_text),
            "preferred_locations": self._extract_locations(resume_text),
        }
        return info
    
    def _extract_name(self, text: str) -> str:
        """提取姓名"""
        patterns = [
            r"姓名[：:]\s*([^\n]+)",
            r"Name[：:]\s*([^\n]+)",
            r"^([^\n]{2,4})\n",  # 第一行2-4个字符
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.MULTILINE)
            if match:
                return match.group(1).strip()
        return "未知"
    
    def _extract_education(self, text: str) -> str:
        """提取学历"""
        education_levels = ["博士", "硕士", "研究生", "本科", "大专", "专科"]
        for level in education_levels:
            if level in text:
                return level
        return "未知"
    
    def _extract_experience(self, text: str) -> int:
        """提取工作年限"""
        patterns = [
            r"(\d+)\s*年.*?经验",
            r"工作.*?(\d+)\s*年",
            r"经验[：:]\s*(\d+)\s*年"
        ]
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return int(match.group(1))
        return 0
    
    def _extract_skills(self, text: str) -> List[str]:
        """提取所有技能"""
        skills = []
        for category, keywords in self.skill_keywords.items():
            for keyword in keywords:
                if keyword.lower() in text.lower():
                    skills.append(keyword)
        return list(set(skills))
    
    def _categorize_skills(self, text: str) -> Dict[str, List[str]]:
        """按类别分类技能"""
        categorized = {}
        for category, keywords in self.skill_keywords.items():
            found = [k for k in keywords if k.lower() in text.lower()]
            if found:
                categorized[category] = found
        return categorized
    
    def _extract_projects(self, text: str) -> List[str]:
        """提取项目经验"""
        projects = []
        # 查找项目相关的段落
        project_patterns = [
            r"项目[：:]\s*([^\n]+)",
            r"-\s*([^\n]+项目[^\n]*)",
            r"•\s*([^\n]+项目[^\n]*)"
        ]
        for pattern in project_patterns:
            matches = re.findall(pattern, text)
            projects.extend(matches)
        return projects[:5]  # 最多返回5个项目
    
    def _extract_job_intention(self, text: str) -> str:
        """提取求职意向"""
        patterns = [
            r"求职意向[：:]\s*([^\n]+)",
            r"期望职位[：:]\s*([^\n]+)",
            r"应聘岗位[：:]\s*([^\n]+)"
        ]
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1).strip()
        return "未指定"

    def _extract_locations(self, text: str) -> List[str]:
        """提取期望工作地点/城市（尽量宽松）"""
        patterns = [
            r"工作地点[：:]\s*([^\n]+)",
            r"期望地点[：:]\s*([^\n]+)",
            r"期望城市[：:]\s*([^\n]+)",
            r"意向城市[：:]\s*([^\n]+)",
            r"地点[：:]\s*([^\n]+)",
        ]
        raw = ""
        for pattern in patterns:
            m = re.search(pattern, text)
            if m:
                raw = (m.group(1) or "").strip()
                break
        if not raw:
            return []

        # split by common separators
        raw = raw.replace("，", ",").replace("、", ",").replace("；", ",").replace(";", ",")
        parts = [p.strip() for p in re.split(r"[,\s/]+", raw) if p.strip()]
        # de-dup preserving order
        out = []
        seen = set()
        for p in parts:
            if p in seen:
                continue
            seen.add(p)
            out.append(p)
        return out[:5]
    
    def generate_summary(self, info: Dict[str, Any]) -> str:
        """生成简历摘要"""
        summary = f"""
📋 简历分析摘要
{'='*50}

👤 基本信息
  姓名: {info['name']}
  学历: {info['education']}
  工作经验: {info['experience_years']}年
  求职意向: {info['job_intention']}

💻 技能清单 (共{len(info['skills'])}项)
"""
        for category, skills in info['skill_categories'].items():
            summary += f"  {category}: {', '.join(skills)}\n"
        
        if info['projects']:
            summary += f"\n🚀 项目经验 (共{len(info['projects'])}个)\n"
            for i, project in enumerate(info['projects'], 1):
                summary += f"  {i}. {project}\n"
        
        return summary

