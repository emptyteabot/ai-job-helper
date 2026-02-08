"""
快速测试脚本 - 测试完整的多AI协作流程
"""

import os
import sys

# 添加项目路径
sys.path.insert(0, os.path.dirname(__file__))

from app.core.multi_ai_debate import JobApplicationPipeline
from app.services.resume_analyzer import ResumeAnalyzer
from app.services.job_searcher import JobSearcher

def main():
    print("\n" + "🎯"*30)
    print("欢迎使用 AI求职助手 - 多AI协作系统")
    print("🎯"*30 + "\n")
    
    # 检查API密钥
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        print("⚠️  警告: 未设置 DEEPSEEK_API_KEY 环境变量")
        print("请先设置: set DEEPSEEK_API_KEY=你的API密钥\n")
        return
    
    # 示例简历
    sample_resume = """
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
    
    print("📄 您的简历：")
    print("-"*60)
    print(sample_resume)
    print("-"*60 + "\n")
    
    # 步骤1：分析简历
    print("\n【步骤1】分析简历...")
    analyzer = ResumeAnalyzer()
    resume_info = analyzer.extract_info(sample_resume)
    print(analyzer.generate_summary(resume_info))
    
    # 步骤2：搜索岗位
    print("\n【步骤2】搜索匹配岗位...")
    searcher = JobSearcher()
    jobs = searcher.search_jobs(
        resume_info['skills'],
        resume_info['job_intention'],
        resume_info['experience_years']
    )
    print(searcher.format_job_list(jobs))
    
    # 步骤3：多AI协作处理
    print("\n【步骤3】启动多AI协作系统...")
    print("这将调用DeepSeek API，可能需要1-2分钟...\n")
    
    user_input = input("是否继续？(y/n): ").strip().lower()
    if user_input != 'y':
        print("\n已取消。您可以随时运行此脚本继续测试。")
        return
    
    pipeline = JobApplicationPipeline()
    results = pipeline.process_resume(sample_resume)
    
    # 保存结果
    pipeline.save_results(results, "output")
    
    # 显示最终结果
    print("\n" + "="*60)
    print("🎉 完整流程执行完毕！")
    print("="*60)
    
    print("\n📊 最终输出：\n")
    
    print("1️⃣ 职业分析：")
    print("-"*60)
    print(results['career_analysis'][:300] + "...\n")
    
    print("2️⃣ 推荐岗位：")
    print("-"*60)
    print(results['job_recommendations'][:300] + "...\n")
    
    print("3️⃣ 优化后的简历：")
    print("-"*60)
    print(results['optimized_resume'][:300] + "...\n")
    
    print("4️⃣ 面试准备：")
    print("-"*60)
    print(results['interview_prep'][:300] + "...\n")
    
    print("\n✅ 完整结果已保存到 output/ 目录")
    print("   - 职业分析.txt")
    print("   - 推荐岗位.txt")
    print("   - 优化后简历.txt")
    print("   - 面试准备.txt")
    print("   - 模拟面试.txt")
    print("   - 完整AI辩论记录.json")
    
    print("\n" + "🎯"*30)
    print("感谢使用！")
    print("🎯"*30 + "\n")

if __name__ == "__main__":
    main()

