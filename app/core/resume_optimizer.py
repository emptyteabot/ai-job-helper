"""
简历优化器 - 基于AI分析结果生成优化简历
去除markdown语法，生成纯文本/PDF格式
"""

import re
from typing import Dict, Any
from datetime import datetime


class ResumeOptimizer:
    """简历优化器"""

    def __init__(self):
        pass

    def optimize_resume(self, original_resume: str, analysis_results: Dict[str, Any]) -> str:
        """
        基于AI分析结果优化简历

        Args:
            original_resume: 原始简历文本
            analysis_results: AI分析结果（包含career_analysis, job_recommendations等）

        Returns:
            优化后的纯文本简历
        """
        if not original_resume:
            return "请先上传简历"

        # 去除markdown语法
        clean_resume = self._remove_markdown(original_resume)

        # 提取AI建议
        resume_optimization = analysis_results.get('resume_optimization', '')
        career_analysis = analysis_results.get('career_analysis', '')

        # 构建优化简历
        parts = []

        # 1. 原始简历（去除markdown）
        parts.append("=" * 60)
        parts.append("AI 优化简历")
        parts.append("=" * 60)
        parts.append("")
        parts.append(clean_resume)
        parts.append("")

        # 2. AI 优化建议
        if resume_optimization:
            parts.append("-" * 60)
            parts.append("【AI 优化建议】")
            parts.append("-" * 60)
            parts.append(self._remove_markdown(resume_optimization))
            parts.append("")

        # 3. 职业分析
        if career_analysis:
            parts.append("-" * 60)
            parts.append("【职业分析】")
            parts.append("-" * 60)
            parts.append(self._remove_markdown(career_analysis))
            parts.append("")

        # 4. 生成时间
        parts.append("-" * 60)
        parts.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        parts.append("由 AI 求职助手自动生成")
        parts.append("-" * 60)

        return "\n".join(parts)

    def _extract_star_experiences(self, resume_optimization: str) -> list:
        """从AI建议中提取STAR法则重写的经历"""
        experiences = []

        # 查找"简历优化"或"STAR"相关段落
        patterns = [
            r'(?:简历优化|STAR法则|经历重写)[\s\S]*?(?=\n\n|\n[#*]|$)',
            r'\d+\.\s*\*\*.*?\*\*[\s\S]*?(?=\n\d+\.|\n\n|$)',
        ]

        for pattern in patterns:
            matches = re.findall(pattern, resume_optimization)
            for match in matches:
                # 去除markdown语法
                clean_text = self._remove_markdown(match)
                if len(clean_text) > 50:  # 过滤太短的内容
                    experiences.append(clean_text.strip())

        return experiences[:5]  # 最多5条

    def _extract_core_competencies(self, career_analysis: str) -> list:
        """从职业分析中提取核心竞争力"""
        competencies = []

        # 查找"核心竞争力"段落
        pattern = r'(?:核心竞争力|优势)[\s\S]*?(?=\n\n[#*]|$)'
        matches = re.findall(pattern, career_analysis)

        for match in matches:
            # 提取列表项
            items = re.findall(r'[-•]\s*(.+)', match)
            for item in items:
                clean_text = self._remove_markdown(item)
                if clean_text:
                    competencies.append(clean_text.strip())

        return competencies[:5]

    def _extract_keywords(self, resume_optimization: str) -> list:
        """从岗位匹配中提取ATS关键词"""
        keywords = []

        # 查找"关键词"或"ATS"段落
        pattern = r'(?:关键词|ATS优化)[\s\S]*?(?=\n\n[#*]|$)'
        matches = re.findall(pattern, resume_optimization)

        for match in matches:
            # 提取关键词
            words = re.findall(r'[A-Za-z]+|[\u4e00-\u9fa5]{2,}', match)
            keywords.extend(words)

        # 去重并返回前15个
        return list(dict.fromkeys(keywords))[:15]

    def _remove_markdown(self, text: str) -> str:
        """去除markdown语法"""
        # 去除标题符号
        text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)

        # 去除粗体/斜体
        text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
        text = re.sub(r'\*(.+?)\*', r'\1', text)
        text = re.sub(r'__(.+?)__', r'\1', text)
        text = re.sub(r'_(.+?)_', r'\1', text)

        # 去除链接
        text = re.sub(r'\[(.+?)\]\(.+?\)', r'\1', text)

        # 去除代码块
        text = re.sub(r'```[\s\S]*?```', '', text)
        text = re.sub(r'`(.+?)`', r'\1', text)

        # 去除引用
        text = re.sub(r'^>\s+', '', text, flags=re.MULTILINE)

        # 去除列表符号（保留内容）
        text = re.sub(r'^[-*+]\s+', '', text, flags=re.MULTILINE)
        text = re.sub(r'^\d+\.\s+', '', text, flags=re.MULTILINE)

        return text.strip()

    def _build_optimized_resume(
        self,
        original_resume: str,
        optimized_experiences: list,
        core_competencies: list,
        keywords: list
    ) -> str:
        """构建优化后的简历"""

        # 从原始简历中提取基本信息
        name = self._extract_name(original_resume)
        contact = self._extract_contact(original_resume)
        education = self._extract_education(original_resume)

        # 构建简历
        resume_parts = []

        # 1. 基本信息
        resume_parts.append("=" * 60)
        resume_parts.append(f"姓名: {name}")
        resume_parts.append(contact)
        resume_parts.append("=" * 60)
        resume_parts.append("")

        # 2. 核心竞争力
        if core_competencies:
            resume_parts.append("【核心竞争力】")
            for i, comp in enumerate(core_competencies, 1):
                resume_parts.append(f"{i}. {comp}")
            resume_parts.append("")

        # 3. 教育背景
        if education:
            resume_parts.append("【教育背景】")
            resume_parts.append(education)
            resume_parts.append("")

        # 4. 项目经历/实习经历（使用AI优化后的）
        if optimized_experiences:
            resume_parts.append("【项目经历 / 实习经历】")
            for i, exp in enumerate(optimized_experiences, 1):
                resume_parts.append(f"\n{i}. {exp}")
            resume_parts.append("")

        # 5. 技能关键词（ATS优化）
        if keywords:
            resume_parts.append("【技能关键词】")
            resume_parts.append(" | ".join(keywords))
            resume_parts.append("")

        # 6. 生成时间
        resume_parts.append("-" * 60)
        resume_parts.append(f"简历生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        resume_parts.append("由 AI 求职助手自动优化生成")
        resume_parts.append("-" * 60)

        return "\n".join(resume_parts)

    def _extract_name(self, resume: str) -> str:
        """提取姓名"""
        # 简单提取第一行或"姓名"字段
        lines = resume.split('\n')
        for line in lines[:5]:
            if '姓名' in line:
                return line.split('姓名')[-1].strip(':：').strip()

        # 如果没找到，返回第一行
        return lines[0].strip() if lines else "未知"

    def _extract_contact(self, resume: str) -> str:
        """提取联系方式"""
        contact_info = []

        # 提取手机号
        phone_match = re.search(r'1[3-9]\d{9}', resume)
        if phone_match:
            contact_info.append(f"手机: {phone_match.group()}")

        # 提取邮箱
        email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', resume)
        if email_match:
            contact_info.append(f"邮箱: {email_match.group()}")

        return " | ".join(contact_info) if contact_info else "联系方式: 待补充"

    def _extract_education(self, resume: str) -> str:
        """提取教育背景"""
        # 查找"教育"相关段落
        pattern = r'(?:教育背景|教育经历|学历)[\s\S]*?(?=\n\n[#\[]|项目经历|工作经历|$)'
        match = re.search(pattern, resume)

        if match:
            edu_text = match.group()
            # 去除markdown
            return self._remove_markdown(edu_text).strip()

        return "教育背景: 待补充"

    def save_to_file(self, resume_text: str, file_path: str):
        """保存简历到文件"""
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(resume_text)


# 全局实例
resume_optimizer = ResumeOptimizer()
