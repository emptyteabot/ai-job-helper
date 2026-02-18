"""
多AI协作辩论系统 - 核心引擎
让多个AI像辩论一样协作，互相改进输出
"""

import os
import json
from typing import List, Dict, Any
from openai import OpenAI
from dotenv import load_dotenv
from app.core.llm_client import get_sync_llm_client, get_llm_settings

# 加载.env文件
load_dotenv()

class MultiAIDebateEngine:
    """多AI辩论引擎 - 让AI互相辩论、改进、检查"""
    
    def __init__(self):
        self.llm_client = get_sync_llm_client()
        settings = get_llm_settings()
        self.reasoning_model = settings["reasoning_model"]
        
        # 定义6个AI角色 - 使用专业框架和方法论
        self.ai_roles = {
            "career_planner": {
                "name": "职业规划师",
                "prompt": """你是拥有15年经验的资深职业规划师（GCDF全球职业发展师认证），精通SWOT分析、霍兰德职业兴趣理论、舒伯职业发展理论。

核心能力：
- 深度挖掘求职者的核心竞争力和隐藏优势
- 基于行业趋势和市场需求进行职业定位
- 提供可量化的职业发展路径规划

分析方法：
1. SWOT分析（优势/劣势/机会/威胁）
2. 技能矩阵评估（硬技能/软技能/可迁移技能）
3. 职业匹配度评分（0-100分）
4. 3-5年职业发展路径规划""",
                "task": """分析简历，输出以下内容：

1. 核心优势分析（至少3条，每条包含具体证据）
2. SWOT分析（每项至少2条）
3. 最适合的3个职业方向（包含匹配度评分）
4. 职业发展路径建议（短期/中期/长期目标）
5. 需要提升的关键技能（优先级排序）

要求：60%以上内容包含量化数据或具体案例"""
            },
            "recruiter": {
                "name": "招聘专家",
                "prompt": """你是拥有12年招聘经验的资深HR（SHRM-SCP认证），精通ATS系统优化、岗位匹配算法、人才画像构建。

核心能力：
- 精准解读JD（职位描述）中的显性和隐性要求
- 掌握各大招聘平台（Boss直聘/智联/LinkedIn）的推荐算法
- 了解不同行业的薪资水平和晋升路径

匹配方法：
1. 3P匹配模型（Person-Position-Place）
2. 关键词密度分析（ATS优化）
3. 能力-岗位匹配矩阵
4. 薪资竞争力评估""",
                "task": """根据求职者优势，推荐岗位：

1. 推荐3-5个高匹配岗位（包含公司/薪资/要求）
2. 每个岗位的匹配度分析（0-100分）
3. 岗位关键词提取（用于ATS优化）
4. 薪资谈判建议（市场行情+个人定位）
5. 投递策略（优先级+时间节点）

要求：提供真实可查的岗位信息，包含具体数据"""
            },
            "resume_optimizer": {
                "name": "简历优化师",
                "prompt": """你是拥有10年经验的简历优化专家（CPRW认证），精通STAR法则、ATS系统优化、视觉设计原则。

核心能力：
- 使用STAR法则（情境-任务-行动-结果）重构经历
- 优化关键词密度，提升ATS通过率
- 量化成果，增强说服力

优化原则：
1. STAR法则：每条经历包含具体场景和量化结果
2. 关键词优化：匹配JD中的核心技能词
3. 成果量化：至少60%的描述包含数字
4. 动词优先：使用强有力的行动动词""",
                "task": """优化简历内容：

1. 重写3-5条核心工作经历（使用STAR法则）
2. 提取并优化关键词（匹配目标岗位）
3. 量化所有可量化的成果（数字/百分比/排名）
4. 优化简历结构（突出核心优势）
5. ATS优化建议（格式/关键词/密度）

要求：每条经历必须包含具体数字和成果"""
            },
            "quality_checker": {
                "name": "质量检查官",
                "prompt": """你是严格的质量审核专家，拥有8年简历审核经验，精通ATS系统规则、HR筛选标准、行业规范。

审核标准：
1. 内容真实性（是否有夸大或虚假信息）
2. 逻辑一致性（时间线/职级/薪资是否合理）
3. ATS友好度（格式/关键词/结构）
4. 说服力评估（是否有足够的量化证据）

评分维度：
- 内容质量（0-100分）
- ATS通过率（0-100分）
- HR吸引力（0-100分）
- 改进空间（高/中/低）""",
                "task": """审核简历质量：

1. 逐条检查工作经历（指出问题+改进建议）
2. ATS友好度评分（0-100分+具体问题）
3. 关键词密度分析（是否匹配目标岗位）
4. 逻辑一致性检查（时间/职级/薪资）
5. 必须修改的3个问题（优先级排序）

要求：每个问题必须给出具体的改进方案"""
            },
            "interview_coach": {
                "name": "面试教练",
                "prompt": """你是拥有10年经验的面试辅导专家（ICF认证教练），精通STAR面试法、行为面试技巧、压力面试应对。

核心能力：
- 预测面试官的提问逻辑和考察重点
- 使用PREP框架（观点-理由-例子-观点）构建回答
- 提供具体的话术和案例

辅导方法：
1. 高频问题预测（基于岗位和行业）
2. STAR回答模板（针对每个问题）
3. 肢体语言和表达技巧
4. 薪资谈判策略""",
                "task": """提供面试辅导：

1. 预测5-8个高频面试问题
2. 每个问题提供STAR回答模板
3. 准备3个反问面试官的问题
4. 薪资谈判话术（3个场景）
5. 面试注意事项（着装/时间/礼仪）

要求：提供可直接使用的话术和案例"""
            },
            "interviewer": {
                "name": "模拟面试官",
                "prompt": """你是严格的面试官，拥有12年面试经验，精通行为面试、技术面试、压力面试。

面试风格：
- 提问尖锐，直击要害
- 关注细节，追问深度
- 评估真实能力，而非背诵答案

考察重点：
1. 技术能力（深度和广度）
2. 问题解决能力（思维逻辑）
3. 团队协作能力（沟通和配合）
4. 抗压能力（应对挑战）""",
                "task": """模拟面试：

1. 提出5-8个面试问题（包含追问）
2. 评估每个回答（0-100分+改进建议）
3. 指出3个最大的问题
4. 给出面试通过概率（0-100%）
5. 最终建议（是否推荐录用）

要求：问题要有深度，评估要客观严格"""
            }
        }
    
    def _clean_markdown(self, text: str) -> str:
        """清理Markdown格式符号，让输出更干净"""
        # 移除多余的*、**、###等符号
        import re
        text = re.sub(r'\*\*\*(.+?)\*\*\*', r'\1', text)  # ***粗体*** -> 粗体
        text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)      # **粗体** -> 粗体
        text = re.sub(r'\*(.+?)\*', r'\1', text)          # *斜体* -> 斜体
        text = re.sub(r'###\s+', '', text)                # ### 标题 -> 标题
        text = re.sub(r'##\s+', '', text)                 # ## 标题 -> 标题
        text = re.sub(r'#\s+', '', text)                  # # 标题 -> 标题
        return text.strip()
    
    def ai_think(self, role: str, context: str, previous_output: str = "") -> Dict[str, Any]:
        """
        让指定AI角色思考并输出
        
        Args:
            role: AI角色 (career_planner, recruiter, etc.)
            context: 上下文信息（简历、岗位等）
            previous_output: 上一个AI的输出（用于辩论改进）
        
        Returns:
            {
                "role": "角色名",
                "output": "AI输出内容",
                "reasoning": "推理过程"
            }
        """
        role_info = self.ai_roles[role]
        
        # 构建提示词
        if previous_output:
            prompt = f"""
{role_info['prompt']}

你的任务：{role_info['task']}

上下文信息：
{context}

上一个AI的输出：
{previous_output}

请基于上一个AI的输出，进行改进、补充或审核。如果发现问题，请明确指出并给出改进建议。
"""
        else:
            prompt = f"""
{role_info['prompt']}

你的任务：{role_info['task']}

上下文信息：
{context}

请完成你的任务，给出详细的分析和建议。
"""
        
        # 调用DeepSeek推理模式
        try:
            import time
            max_retries = 3
            retry_delay = 3

            for attempt in range(max_retries):
                try:
                    # 每次重试重新获取 client（可能会轮换到不同的 Key）
                    if attempt > 0:
                        self.llm_client = get_sync_llm_client()
                        settings = get_llm_settings()
                        self.reasoning_model = settings["reasoning_model"]
                        print(f"重试 {attempt + 1}/{max_retries}，使用新的 API Key...")

                    response = self.llm_client.chat.completions.create(
                        model=self.reasoning_model,
                        messages=[{"role": "user", "content": prompt}],
                        temperature=0.7
                    )

                    message = response.choices[0].message
                    reasoning = getattr(message, "reasoning_content", "") or ""
                    output = message.content or ""

                    # 清理Markdown格式
                    output = self._clean_markdown(output)
                    reasoning = self._clean_markdown(reasoning)

                    return {
                        "role": role_info['name'],
                        "output": output,
                        "reasoning": reasoning
                    }
                except Exception as e:
                    error_msg = str(e)
                    if "governor" in error_msg.lower() or "rate" in error_msg.lower() or "429" in error_msg:
                        if attempt < max_retries - 1:
                            print(f"限流错误，{retry_delay}秒后重试... (尝试 {attempt + 1}/{max_retries})")
                            time.sleep(retry_delay)
                            retry_delay += 2  # 递增延迟
                            continue
                    raise

            # 所有重试都失败
            return {
                "role": role_info['name'],
                "output": f"AI思考出错: 所有 API Key 都达到限流，请稍后再试",
                "reasoning": ""
            }
        except Exception as e:
            return {
                "role": role_info['name'],
                "output": f"AI思考出错: {str(e)}",
                "reasoning": ""
            }
    
    def debate_chain(self, initial_context: str, roles: List[str]) -> List[Dict[str, Any]]:
        """
        AI辩论链：让多个AI依次处理，后面的AI基于前面的输出改进
        
        Args:
            initial_context: 初始上下文（如简历内容）
            roles: AI角色列表，按顺序执行
        
        Returns:
            所有AI的输出列表
        """
        results = []
        previous_output = ""
        
        print("\n" + "="*60)
        print("🤖 多AI协作辩论开始...")
        print("="*60 + "\n")
        
        for i, role in enumerate(roles, 1):
            role_name = self.ai_roles[role]['name']
            print(f"[{i}/{len(roles)}] {role_name} 正在思考...")
            
            result = self.ai_think(role, initial_context, previous_output)
            results.append(result)
            
            print(f"✓ {role_name} 完成\n")
            print(f"输出预览: {result['output'][:100]}...\n")
            
            # 下一个AI基于这个输出继续
            previous_output = result['output']
        
        print("="*60)
        print("✅ 所有AI协作完成！")
        print("="*60 + "\n")
        
        return results


class JobApplicationPipeline:
    """完整求职流程管道"""
    
    def __init__(self):
        self.debate_engine = MultiAIDebateEngine()
    
    def process_resume(self, resume_text: str) -> Dict[str, Any]:
        """
        处理简历的完整流程
        
        流程：
        1. 职业规划师分析优势
        2. 招聘专家搜索岗位
        3. 简历优化师改写简历 → 质量检查官审核 → 再次优化
        4. 面试教练提供辅导 → 模拟面试官测试
        
        Returns:
            {
                "career_analysis": "职业分析结果",
                "job_recommendations": "推荐岗位",
                "optimized_resume": "优化后的简历",
                "interview_prep": "面试准备",
                "all_debates": [所有AI的完整输出]
            }
        """
        
        print("\n" + "🚀"*30)
        print("开始完整求职流程...")
        print("🚀"*30 + "\n")
        
        # 阶段1：职业分析
        print("\n【阶段1】职业分析")
        career_result = self.debate_engine.ai_think(
            "career_planner", 
            f"简历内容：\n{resume_text}"
        )
        
        # 阶段2：岗位搜索
        print("\n【阶段2】岗位搜索")
        job_result = self.debate_engine.ai_think(
            "recruiter",
            f"简历内容：\n{resume_text}",
            career_result['output']
        )
        
        # 阶段3：简历优化（辩论模式：优化师 → 检查官 → 再优化）
        print("\n【阶段3】简历优化（多轮辩论）")
        resume_debates = self.debate_engine.debate_chain(
            f"简历内容：\n{resume_text}\n\n目标岗位：\n{job_result['output']}",
            ["resume_optimizer", "quality_checker", "resume_optimizer"]
        )
        
        # 阶段4：面试准备（辩论模式：教练 → 面试官）
        print("\n【阶段4】面试准备")
        interview_debates = self.debate_engine.debate_chain(
            f"简历内容：\n{resume_text}\n\n目标岗位：\n{job_result['output']}\n\n优化后简历：\n{resume_debates[-1]['output']}",
            ["interview_coach", "interviewer"]
        )
        
        return {
            "career_analysis": career_result['output'],
            "job_recommendations": job_result['output'],
            "optimized_resume": resume_debates[-1]['output'],
            "interview_prep": interview_debates[0]['output'],
            "mock_interview": interview_debates[1]['output'],
            "all_debates": [career_result, job_result] + resume_debates + interview_debates
        }
    
    def save_results(self, results: Dict[str, Any], output_dir: str = "output"):
        """保存所有结果到文件"""
        os.makedirs(output_dir, exist_ok=True)
        
        # 保存各个阶段的结果
        with open(f"{output_dir}/职业分析.txt", "w", encoding="utf-8") as f:
            f.write(results['career_analysis'])
        
        with open(f"{output_dir}/推荐岗位.txt", "w", encoding="utf-8") as f:
            f.write(results['job_recommendations'])
        
        with open(f"{output_dir}/优化后简历.txt", "w", encoding="utf-8") as f:
            f.write(results['optimized_resume'])
        
        with open(f"{output_dir}/面试准备.txt", "w", encoding="utf-8") as f:
            f.write(results['interview_prep'])
        
        with open(f"{output_dir}/模拟面试.txt", "w", encoding="utf-8") as f:
            f.write(results['mock_interview'])
        
        # 保存完整的AI辩论记录
        with open(f"{output_dir}/完整AI辩论记录.json", "w", encoding="utf-8") as f:
            json.dump(results['all_debates'], f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ 所有结果已保存到 {output_dir}/ 目录")


# 快速测试函数
def quick_test():
    """快速测试多AI协作"""
    
    # 示例简历
    sample_resume = """
姓名：张三
学历：本科 - 计算机科学与技术
工作经验：2年Python开发经验
技能：Python, Django, MySQL, Redis, Docker
项目经验：
- 电商后台管理系统（Django + MySQL）
- 数据分析平台（Python + Pandas）
求职意向：后端开发工程师
"""
    
    pipeline = JobApplicationPipeline()
    results = pipeline.process_resume(sample_resume)
    pipeline.save_results(results)
    
    print("\n" + "="*60)
    print("📊 最终结果预览")
    print("="*60)
    print(f"\n职业分析：\n{results['career_analysis'][:200]}...\n")
    print(f"\n推荐岗位：\n{results['job_recommendations'][:200]}...\n")
    print(f"\n优化后简历：\n{results['optimized_resume'][:200]}...\n")


if __name__ == "__main__":
    quick_test()
