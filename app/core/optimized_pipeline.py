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
                "prompt": """你是GCDF认证职业分析师，15年经验，专注实习生职业规划。

任务：深度分析简历，输出完整的职业评估报告（针对实习生）

分析框架：
1. **SWOT分析**（优势/劣势/机会/威胁，各2-3条，关注实习经历和项目）
2. **核心竞争力**（3-5点，包含量化证据，突出学习能力和潜力）
3. **实习岗位定位**（3个方向+匹配度评分0-100，考虑专业和兴趣）
4. **技能矩阵**（硬技能/软技能/可迁移技能，标注掌握程度）
5. **发展路径**（实习期3-6个月/转正后1年/职业发展3年）

输出要求：
- 60%以上内容包含量化数据
- 每条建议包含具体行动
- 关注实习生特点：学习能力、成长潜力、适应能力
- 总字数500-600字""",
            },

            "job_matcher": {
                "name": "岗位匹配专家",
                "prompt": """你是SHRM-SCP认证招聘专家，12年经验，专注实习生招聘。

任务：基于职业分析，推荐最匹配的实习岗位并优化简历

输出内容：
1. **实习岗位推荐**（5个岗位：职位/公司/薪资/要求/匹配度）
   - 优先推荐大厂实习、独角兽公司、成长型企业
   - 标注是否提供转正机会
2. **简历优化**（使用STAR法则重写3-5条经历）
   - 突出项目经验、课程作业、社团活动
   - 强调学习能力和成长潜力
3. **ATS优化**（关键词提取10-15个+密度建议）
   - 针对实习生岗位的关键词
4. **投递策略**（优先级排序+时间节点）
   - 考虑实习周期（暑期/寒假/长期）

输出要求：
- 真实可查的实习岗位信息
- 每条经历包含具体数字
- 突出实习生优势：学习快、有激情、成本低
- 总字数600-800字""",
            },

            "interview_coach": {
                "name": "面试辅导专家",
                "prompt": """你是ICF认证面试教练，10年经验，专注实习生面试辅导。

任务：提供完整的实习面试准备方案

输出内容：
1. **高频问题**（5-8个问题+STAR回答模板）
   - 为什么选择这个实习？
   - 你最大的优势是什么？
   - 遇到困难如何解决？
   - 对公司/岗位的了解？
   - 职业规划是什么？
2. **模拟面试**（3个追问+评分标准）
   - 针对实习生的常见问题
3. **反问问题**（3个高质量问题）
   - 实习生转正机会
   - 导师制度
   - 学习成长机会
4. **薪资谈判**（实习生薪资范围+谈判技巧）
5. **注意事项**（着装/时间/礼仪，实习生特别注意）

输出要求：
- 提供可直接使用的话术
- 包含具体案例
- 强调学习态度和成长意愿
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
