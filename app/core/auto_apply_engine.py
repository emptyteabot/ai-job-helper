"""
自动投递引擎 - 使用 AI 生成求职信并自动投递
"""

import time
from typing import Dict, List
from datetime import datetime


class AutoApplyEngine:
    """自动投递引擎"""

    def __init__(self, llm_client, reasoning_model):
        self.llm_client = llm_client
        self.reasoning_model = reasoning_model

    def auto_apply_jobs(
        self,
        jobs: List[Dict],
        resume_text: str,
        user_info: Dict,
        progress_callback=None
    ) -> Dict:
        """
        自动投递岗位

        Args:
            jobs: 岗位列表
            resume_text: 简历文本
            user_info: 用户信息（姓名、邮箱、电话等）
            progress_callback: 进度回调函数

        Returns:
            投递结果统计
        """
        results = {
            'total': len(jobs),
            'success': 0,
            'failed': 0,
            'details': []
        }

        for i, job in enumerate(jobs):
            if progress_callback:
                progress_callback(i + 1, len(jobs), f"正在投递: {job['title']}")

            try:
                # 1. 生成个性化求职信
                cover_letter = self._generate_cover_letter(
                    job=job,
                    resume=resume_text,
                    user_info=user_info
                )

                # 2. 生成申请表单答案
                answers = self._generate_application_answers(
                    job=job,
                    resume=resume_text
                )

                # 3. 模拟投递（实际需要调用平台API或使用浏览器自动化）
                success = self._submit_application(
                    job=job,
                    cover_letter=cover_letter,
                    answers=answers,
                    user_info=user_info
                )

                if success:
                    results['success'] += 1
                    results['details'].append({
                        'job': job['title'],
                        'company': job['company'],
                        'status': 'success',
                        'cover_letter': cover_letter[:200] + '...',
                        'time': datetime.now().isoformat()
                    })
                else:
                    results['failed'] += 1
                    results['details'].append({
                        'job': job['title'],
                        'company': job['company'],
                        'status': 'failed',
                        'error': '投递失败',
                        'time': datetime.now().isoformat()
                    })

                # 间隔3秒，避免被限流
                time.sleep(3)

            except Exception as e:
                results['failed'] += 1
                results['details'].append({
                    'job': job['title'],
                    'company': job['company'],
                    'status': 'error',
                    'error': str(e),
                    'time': datetime.now().isoformat()
                })

        return results

    def _generate_cover_letter(self, job: Dict, resume: str, user_info: Dict) -> str:
        """使用 AI 生成个性化求职信"""
        try:
            prompt = f"""请为以下岗位生成一封专业的求职信：

【岗位信息】
职位: {job['title']}
公司: {job['company']}
描述: {job.get('description', '暂无')}

【我的简历】
{resume[:1000]}

【要求】
1. 字数控制在200-300字
2. 突出我的相关经验和技能
3. 表达对公司和岗位的兴趣
4. 语气专业但不失热情
5. 不要使用markdown格式

请直接输出求职信内容，不要有任何前缀或后缀。"""

            response = self.llm_client.chat.completions.create(
                model=self.reasoning_model,
                messages=[
                    {"role": "system", "content": "你是一个专业的求职信撰写专家。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            return f"尊敬的招聘负责人，\n\n我对{job['company']}的{job['title']}职位非常感兴趣。我相信我的技能和经验能够为贵公司创造价值。期待与您进一步交流。\n\n此致\n敬礼"

    def _generate_application_answers(self, job: Dict, resume: str) -> Dict:
        """使用 AI 生成申请表单答案"""
        try:
            # 常见问题
            questions = [
                "为什么想加入我们公司？",
                "你的优势是什么？",
                "你对这个岗位的理解？",
                "你的职业规划是什么？"
            ]

            answers = {}

            for question in questions:
                prompt = f"""请简短回答以下问题（50-100字）：

问题: {question}

岗位: {job['title']} @ {job['company']}
我的简历: {resume[:500]}

要求: 真诚、专业、简洁"""

                response = self.llm_client.chat.completions.create(
                    model=self.reasoning_model,
                    messages=[
                        {"role": "system", "content": "你是一个求职顾问。"},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7
                )

                answers[question] = response.choices[0].message.content.strip()

            return answers

        except Exception as e:
            return {}

    def _submit_application(
        self,
        job: Dict,
        cover_letter: str,
        answers: Dict,
        user_info: Dict
    ) -> bool:
        """
        提交申请

        注意：这里是模拟投递
        实际部署时需要：
        1. 使用 Selenium/Playwright 浏览器自动化
        2. 或调用招聘平台的 API
        3. 或使用 AIHawk 项目
        """
        try:
            # 模拟投递成功
            # 实际需要调用平台API或使用浏览器自动化

            print(f"[模拟投递] {job['title']} @ {job['company']}")
            print(f"求职信: {cover_letter[:100]}...")
            print(f"答案: {len(answers)} 个问题")

            # 模拟80%成功率
            import random
            return random.random() < 0.8

        except Exception as e:
            print(f"投递失败: {e}")
            return False


# 全局实例
auto_apply_engine = None

def get_auto_apply_engine(llm_client, reasoning_model):
    """获取自动投递引擎实例"""
    global auto_apply_engine
    if auto_apply_engine is None:
        auto_apply_engine = AutoApplyEngine(llm_client, reasoning_model)
    return auto_apply_engine
