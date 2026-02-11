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
        
        # 定义6个AI角色
        self.ai_roles = {
            "career_planner": {
                "name": "职业规划师",
                "prompt": "你是资深职业规划师，擅长分析求职者优势、定位职业方向。",
                "task": "分析简历，找出核心优势和最适合的职业方向"
            },
            "recruiter": {
                "name": "招聘专家",
                "prompt": "你是招聘行业专家，了解各大招聘平台和岗位需求。",
                "task": "根据求职者优势，搜索最匹配的岗位"
            },
            "resume_optimizer": {
                "name": "简历优化师",
                "prompt": "你是简历优化专家，擅长针对岗位需求改写简历。",
                "task": "针对目标岗位，优化简历内容"
            },
            "quality_checker": {
                "name": "质量检查官",
                "prompt": "你是质量审核专家，负责检查简历是否符合岗位要求。",
                "task": "审核优化后的简历，指出问题并要求改进"
            },
            "interview_coach": {
                "name": "面试教练",
                "prompt": "你是面试辅导专家，帮助求职者准备面试。",
                "task": "根据岗位和简历，提供面试辅导建议"
            },
            "interviewer": {
                "name": "模拟面试官",
                "prompt": "你是严格的面试官，负责模拟面试并提出尖锐问题。",
                "task": "模拟真实面试场景，提出问题并评估回答"
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
