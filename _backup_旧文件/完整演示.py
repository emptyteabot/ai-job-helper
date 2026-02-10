"""
完整演示 - 展示从上传简历到获得面试的完整流程
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from app.core.multi_ai_debate import JobApplicationPipeline
from app.services.resume_analyzer import ResumeAnalyzer
from app.services.job_searcher import JobSearcher

def print_section(title: str):
    """打印章节标题"""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70 + "\n")

def main():
    print("\n" + "🎯"*35)
    print("         AI求职助手 - 完整流程演示")
    print("         从上传简历到获得面试邀约")
    print("🎯"*35 + "\n")
    
    # 步骤0：准备简历
    print_section("📄 步骤0：准备您的简历")
    
    print("您可以：")
    print("1. 直接输入简历内容")
    print("2. 使用示例简历（推荐首次测试）")
    print()
    
    choice = input("请选择 (1/2): ").strip()
    
    if choice == "1":
        print("\n请输入您的简历内容（输入END结束）：")
        lines = []
        while True:
            line = input()
            if line.strip().upper() == "END":
                break
            lines.append(line)
        resume_text = "\n".join(lines)
    else:
        # 使用示例简历
        resume_text = """
姓名：李明
学历：本科 - 软件工程
工作经验：3年Python开发经验

技能清单：
- 编程语言: Python, JavaScript, SQL
- 后端框架: Django, Flask, FastAPI
- 数据库: MySQL, Redis, MongoDB
- 前端: React, Vue.js, HTML/CSS
- 工具: Docker, Git, Linux

项目经验：
1. 电商后台管理系统
   - 使用Django + MySQL开发
   - 实现商品管理、订单处理、用户权限等功能
   - 日均处理订单5000+

2. 数据分析平台
   - 使用Python + Pandas进行数据处理
   - 开发可视化报表系统
   - 支持实时数据监控

3. RESTful API服务
   - 使用FastAPI开发高性能API
   - 集成Redis缓存，响应时间<100ms
   - 日均请求量100万+

求职意向：Python后端开发工程师 / 全栈开发工程师
期望薪资：20-35K
工作地点：北京、上海、杭州
"""
        print("\n✅ 使用示例简历")
    
    print("\n您的简历：")
    print("-"*70)
    print(resume_text)
    print("-"*70)
    
    # 步骤1：AI分析简历
    print_section("🤖 步骤1：AI分析您的简历")
    
    analyzer = ResumeAnalyzer()
    resume_info = analyzer.extract_info(resume_text)
    summary = analyzer.generate_summary(resume_info)
    print(summary)
    
    input("\n按回车继续...")
    
    # 步骤2：智能搜索岗位
    print_section("🔍 步骤2：智能搜索匹配岗位")
    
    searcher = JobSearcher()
    jobs = searcher.search_jobs(
        resume_info['skills'],
        resume_info['job_intention'],
        resume_info['experience_years']
    )
    
    print(searcher.format_job_list(jobs))
    
    if not jobs:
        print("❌ 未找到匹配岗位，请优化简历后重试")
        return
    
    input("\n按回车继续...")
    
    # 步骤3：多AI协作优化
    print_section("🤖🤖🤖 步骤3：多AI协作优化简历")
    
    print("现在将启动6个AI进行协作：")
    print("  AI-1 职业规划师 → 分析优势")
    print("  AI-2 招聘专家 → 推荐岗位")
    print("  AI-3 简历优化师 → 改写简历")
    print("  AI-4 质量检查官 → 审核质量")
    print("  AI-3 简历优化师 → 再次优化")
    print("  AI-5 面试教练 → 面试辅导")
    print("  AI-6 模拟面试官 → 模拟面试")
    print()
    print("⚠️  这将调用DeepSeek API，需要1-2分钟")
    print()
    
    # 检查API密钥
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        print("❌ 错误: 未设置 DEEPSEEK_API_KEY 环境变量")
        print("请先设置: set DEEPSEEK_API_KEY=你的API密钥")
        return
    
    user_input = input("是否继续？(y/n): ").strip().lower()
    if user_input != 'y':
        print("\n已取消。您可以随时重新运行此脚本。")
        return
    
    # 执行多AI协作
    pipeline = JobApplicationPipeline()
    results = pipeline.process_resume(resume_text)
    
    # 保存结果
    pipeline.save_results(results, "output")
    
    # 步骤4：展示最终结果
    print_section("🎉 步骤4：查看最终结果")
    
    print("\n【1】职业分析报告")
    print("-"*70)
    print(results['career_analysis'])
    print()
    
    input("按回车查看推荐岗位...")
    
    print("\n【2】推荐岗位列表")
    print("-"*70)
    print(results['job_recommendations'])
    print()
    
    input("按回车查看优化后的简历...")
    
    print("\n【3】优化后的简历")
    print("-"*70)
    print(results['optimized_resume'])
    print()
    
    input("按回车查看面试准备...")
    
    print("\n【4】面试准备指南")
    print("-"*70)
    print(results['interview_prep'])
    print()
    
    input("按回车查看模拟面试...")
    
    print("\n【5】模拟面试问答")
    print("-"*70)
    print(results['mock_interview'])
    print()
    
    # 步骤5：下一步行动
    print_section("✅ 步骤5：下一步行动")
    
    print("恭喜！您已完成完整的求职准备流程！")
    print()
    print("📁 所有结果已保存到 output/ 目录：")
    print("   ✓ 职业分析.txt")
    print("   ✓ 推荐岗位.txt")
    print("   ✓ 优化后简历.txt")
    print("   ✓ 面试准备.txt")
    print("   ✓ 模拟面试.txt")
    print("   ✓ 完整AI辩论记录.json")
    print()
    print("🎯 建议下一步：")
    print("   1. 仔细阅读优化后的简历")
    print("   2. 根据面试准备指南做好准备")
    print("   3. 练习模拟面试中的问题")
    print("   4. 开始投递简历！")
    print()
    
    print("\n" + "🎯"*35)
    print("         感谢使用 AI求职助手！")
    print("         祝您求职顺利，早日拿到offer！")
    print("🎯"*35 + "\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n已取消。")
    except Exception as e:
        print(f"\n❌ 发生错误: {str(e)}")
        import traceback
        traceback.print_exc()

