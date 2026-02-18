"""
优化的 AI 求职流程 - 使用推理模型 + 科学的 Agent 顺序
4个核心 Agent，逻辑清晰，效果更好
"""

import os
import time
from typing import Dict, Any
from app.core.llm_client import get_sync_llm_client, get_llm_settings


class OptimizedJobPipeline:
    """优化的求职流程 - 4个核心Agent"""

    def __init__(self):
        self.llm_client = get_sync_llm_client()
        settings = get_llm_settings()
        self.reasoning_model = settings["reasoning_model"]

        # 4个核心AI角色 - 科学排序
        self.agents = {
            "career_analyst": {
                "name": "职业分析师",
                "prompt": """你是GCDF认证职业分析师，15年经验。

任务：深度分析简历，输出完整的职业评估报告

分析框架：
1. **SWOT分析**（优势/劣势/机会/威胁，各2-3条）
2. **核心竞争力**（3-5点，包含量化证据）
3. **职业定位**（3个方向+匹配度评分0-100）
4. **技能矩阵**（硬技能/软技能/可迁移技能）
5. **发展路径**（短期6个月/中期2年/长期5年）

输出要求：
- 60%以上内容包含量化数据
- 每条建议包含具体行动
- 总字数500-600字""",
            },

            "job_matcher": {
                "name": "岗位匹配专家",
                "prompt": """你是SHRM-SCP认证招聘专家，12年经验。

任务：基于职业分析，推荐最匹配的岗位并优化简历

输出内容：
1. **岗位推荐**（5个岗位：职位/公司/薪资/要求/匹配度）
2. **简历优化**（使用STAR法则重写3-5条经历）
3. **ATS优化**（关键词提取10-15个+密度建议）
4. **投递策略**（优先级排序+时间节点）

输出要求：
- 真实可查的岗位信息
- 每条经历包含具体数字
- 总字数600-800字""",
            },

            "interview_coach": {
                "name": "面试辅导专家",
                "prompt": """你是ICF认证面试教练，10年经验。

任务：提供完整的面试准备方案

输出内容：
1. **高频问题**（5-8个问题+STAR回答模板）
2. **模拟面试**（3个追问+评分标准）
3. **反问问题**（3个高质量问题）
4. **薪资谈判**（3个场景+话术）
5. **注意事项**（着装/时间/礼仪）

输出要求：
- 提供可直接使用的话术
- 包含具体案例
- 总字数500-700字""",
            },

            "quality_auditor": {
                "name": "质量审核官",
                "prompt": """你是严格的质量审核专家，8年经验。

任务：审核前面所有AI的输出，给出改进建议

审核维度：
1. **内容质量**（0-100分+具体问题）
2. **ATS友好度**（0-100分+优化建议）
3. **逻辑一致性**（时间/职级/薪资检查）
4. **必须修改的3个问题**（优先级排序）
5. **综合评估**（通过率预测0-100%）

输出要求：
- 每个问题给出具体改进方案
- 评分必须有依据
- 总字数400-500字""",
            }
        }

    def _ai_think(self, role: str, context: str, show_progress: bool = True) -> str:
        """AI思考 - 使用推理模型"""
        agent = self.agents[role]

        if show_progress:
            print(f"\n🤖 {agent['name']} 正在深度思考...")

        try:
            import random
            max_retries = 3
            retry_delay = 3

            for attempt in range(max_retries):
                try:
                    # 每次重试重新获取 client（轮换 Key）
                    if attempt > 0:
                        self.llm_client = get_sync_llm_client()
                        settings = get_llm_settings()
                        self.reasoning_model = settings["reasoning_model"]
                        if show_progress:
                            print(f"   ↻ 重试 {attempt + 1}/{max_retries}...")

                    response = self.llm_client.chat.completions.create(
                        model=self.reasoning_model,
                        messages=[
                            {"role": "system", "content": agent['prompt']},
                            {"role": "user", "content": context}
                        ],
                        temperature=0.7
                    )

                    message = response.choices[0].message
                    output = message.content or ""

                    if show_progress:
                        print(f"   ✓ {agent['name']} 完成")

                    return output.strip()

                except Exception as e:
                    error_msg = str(e)
                    if "governor" in error_msg.lower() or "rate" in error_msg.lower() or "429" in error_msg:
                        if attempt < max_retries - 1:
                            if show_progress:
                                print(f"   ⚠ 限流，{retry_delay}秒后重试...")
                            time.sleep(retry_delay)
                            retry_delay += 2
                            continue
                    raise

            return f"❌ {agent['name']} 处理失败：所有API Key都达到限流"

        except Exception as e:
            return f"❌ {agent['name']} 处理失败: {str(e)}"

    def process_resume(self, resume_text: str) -> Dict[str, Any]:
        """处理简历 - 4个Agent顺序执行"""

        print("\n" + "="*60)
        print("🚀 开始AI求职分析流程（使用推理模型）")
        print("="*60)

        start_time = time.time()

        # Agent 1: 职业分析
        print("\n【阶段1/4】职业分析")
        career_analysis = self._ai_think(
            "career_analyst",
            f"请分析以下简历：\n\n{resume_text}"
        )

        # Agent 2: 岗位匹配 + 简历优化
        print("\n【阶段2/4】岗位匹配与简历优化")
        job_and_resume = self._ai_think(
            "job_matcher",
            f"简历：\n{resume_text}\n\n职业分析：\n{career_analysis}"
        )

        # Agent 3: 面试辅导
        print("\n【阶段3/4】面试准备")
        interview_prep = self._ai_think(
            "interview_coach",
            f"简历：\n{resume_text}\n\n职业分析：\n{career_analysis}\n\n岗位匹配：\n{job_and_resume}"
        )

        # Agent 4: 质量审核
        print("\n【阶段4/4】质量审核")
        quality_audit = self._ai_think(
            "quality_auditor",
            f"职业分析：\n{career_analysis}\n\n岗位匹配：\n{job_and_resume}\n\n面试准备：\n{interview_prep}"
        )

        elapsed = time.time() - start_time

        print("\n" + "="*60)
        print(f"✅ 分析完成！总耗时: {elapsed:.1f}秒")
        print("="*60)

        return {
            "career_analysis": career_analysis,
            "job_recommendations": job_and_resume,
            "resume_optimization": job_and_resume,  # 包含在岗位匹配中
            "interview_preparation": interview_prep,
            "mock_interview": interview_prep,  # 包含在面试准备中
            "skill_gap_analysis": quality_audit,  # 质量审核包含技能分析
            "quality_audit": quality_audit
        }
