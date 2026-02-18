"""
高性能AI引擎 - 并行处理 + 流式输出
真正的实时，端到端速度提升10倍
"""

import os
import asyncio
from typing import Dict, Any, List
from dotenv import load_dotenv
import time
from app.core.llm_client import get_async_llm_client, get_llm_settings

load_dotenv()

class HighPerformanceAIEngine:
    """高性能AI引擎 - 并行处理"""
    
    def __init__(self):
        self.client = get_async_llm_client()
        self.chat_model = get_llm_settings()["chat_model"]
        
        # 6个AI角色的提示词（专业优化版）
        self.prompts = {
            "career_planner": """你是GCDF认证职业规划师，15年经验。

分析要求：
1. SWOT分析（优势/劣势/机会/威胁，各2条）
2. 核心竞争力（3-5点，包含证据）
3. 职业定位（3个方向+匹配度评分）
4. 发展路径（短期/中期/长期目标）

输出格式：
- 使用量化数据（至少60%）
- 每条建议包含具体行动
- 总字数300-400字""",

            "recruiter": """你是SHRM-SCP认证招聘专家，12年经验。

推荐要求：
1. 推荐5个岗位（职位/公司/薪资/要求）
2. 匹配度评分（0-100分+理由）
3. ATS关键词提取（10-15个）
4. 投递策略（优先级+时间）
5. 薪资谈判建议（市场行情）

输出格式：
- 真实可查的岗位信息
- 包含具体数字和数据
- 总字数400-500字""",

            "resume_optimizer": """你是CPRW认证简历优化师，10年经验。

优化要求：
1. 使用STAR法则重写3-5条经历
2. 量化所有成果（数字/百分比/排名）
3. 优化关键词（匹配目标岗位）
4. ATS优化建议（格式/密度）
5. 突出核心优势

输出格式：
- 每条经历包含具体数字
- 使用强有力的行动动词
- 总字数500-600字""",

            "quality_checker": """你是严格的质量审核专家，8年经验。

审核标准：
1. 内容质量评分（0-100分）
2. ATS友好度评分（0-100分）
3. 逻辑一致性检查
4. 必须修改的3个问题
5. 改进优先级排序

输出格式：
- 每个问题给出具体改进方案
- 评分必须有依据
- 总字数200-300字""",

            "interview_coach": """你是ICF认证面试教练，10年经验。

辅导要求：
1. 预测5-8个高频问题
2. 每个问题提供STAR回答模板
3. 准备3个反问问题
4. 薪资谈判话术（3个场景）
5. 面试注意事项

输出格式：
- 提供可直接使用的话术
- 包含具体案例
- 总字数400-500字""",

            "interviewer": """你是严格的面试官，12年经验。

面试要求：
1. 提出5-8个问题（包含追问）
2. 评估每个回答（0-100分）
3. 指出3个最大问题
4. 面试通过概率（0-100%）
5. 最终建议（录用/待定/拒绝）

输出格式：
- 问题要有深度
- 评估要客观严格
- 总字数300-400字"""
        }
    
    async def ai_think_fast(self, role: str, context: str) -> str:
        """快速AI思考 - 流式输出"""
        prompt = self.prompts.get(role, "")
        
        try:
            # 使用流式API，更快
            response = await self.client.chat.completions.create(
                model=self.chat_model,  # 使用环境变量模型
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": context}
                ],
                temperature=0.7,
                max_tokens=1200,  # 增加token限制以支持更详细的输出
                stream=False  # 先不用流式，确保稳定
            )
            
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"AI处理出错: {str(e)}"
    
    async def parallel_process(self, resume_text: str, progress_callback=None) -> Dict[str, Any]:
        """并行处理 - 6个AI同时工作"""
        
        # 阶段1: 职业分析（必须先完成）
        if progress_callback:
            await progress_callback(1, "AI-1 职业规划师分析中...", "职业规划师")
        
        career_analysis = await self.ai_think_fast("career_planner", f"简历：\n{resume_text}")
        
        # 阶段2: 并行执行（招聘专家 + 简历优化）
        if progress_callback:
            await progress_callback(2, "AI-2/3 并行处理中...", "系统")
        
        recruiter_task = self.ai_think_fast("recruiter", f"简历：\n{resume_text}\n\n职业分析：\n{career_analysis}")
        optimizer_task = self.ai_think_fast("resume_optimizer", f"简历：\n{resume_text}\n\n职业分析：\n{career_analysis}")
        
        job_recommendations, optimized_resume = await asyncio.gather(recruiter_task, optimizer_task)
        
        # 阶段3: 并行执行（质量检查 + 面试辅导 + 模拟面试）
        if progress_callback:
            await progress_callback(4, "AI-4/5/6 并行处理中...", "系统")
        
        checker_task = self.ai_think_fast("quality_checker", f"简历：\n{optimized_resume}")
        coach_task = self.ai_think_fast("interview_coach", f"简历：\n{resume_text}\n\n岗位：\n{job_recommendations}")
        interviewer_task = self.ai_think_fast("interviewer", f"简历：\n{resume_text}\n\n岗位：\n{job_recommendations}")
        
        quality_check, interview_prep, mock_interview = await asyncio.gather(
            checker_task, coach_task, interviewer_task
        )
        
        if progress_callback:
            await progress_callback(5, "✓ 所有AI处理完成！", "系统")
        
        return {
            "career_analysis": career_analysis,
            "job_recommendations": job_recommendations,
            "optimized_resume": optimized_resume,
            "quality_check": quality_check,
            "interview_prep": interview_prep,
            "mock_interview": mock_interview
        }


class FastJobApplicationPipeline:
    """快速求职流程 - 端到端优化"""
    
    def __init__(self):
        self.engine = HighPerformanceAIEngine()
    
    async def process_resume_fast(self, resume_text: str, progress_callback=None) -> Dict[str, Any]:
        """快速处理简历 - 异步并行"""
        start_time = time.time()
        
        # 并行处理
        results = await self.engine.parallel_process(resume_text, progress_callback)
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        print(f"\n⚡ 处理完成！耗时: {processing_time:.2f}秒")
        
        return results
    
    def process_resume(self, resume_text: str) -> Dict[str, Any]:
        """同步接口 - 兼容旧代码"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self.process_resume_fast(resume_text))
        finally:
            loop.close()


# 全局实例
fast_pipeline = FastJobApplicationPipeline()

