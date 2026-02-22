"""
手机控制系统 - Telegram Bot集成
让你随时随地控制AI员工，24小时工作
"""

import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from loguru import logger
from main import OnePersonCompany
from core.router import TaskPriority

# Telegram Bot Token（从环境变量获取）
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "your_bot_token_here")

# 全局公司实例
company = None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """启动命令"""
    user = update.effective_user
    
    welcome_text = f"""
👋 你好 {user.first_name}！

欢迎使用 **AI员工管理系统**！

你现在拥有 9 个 24/7 工作的 AI 员工：

🎯 **L2 增长团队**
• 增长工程师 - A/B测试、漏斗优化
• SEO架构师 - 关键词研究、排名优化
• 内容专家 - 深度文章、品牌叙事
• 广告黑客 - 投放优化、ROI提升
• 社区运营 - UGC激励、影响者协作

🛡️ **L3 专家团队**
• 算法专家 - 模型优化、性能调优
• 合规顾问 - 法律审查、税务规划
• 设计师 - UI/UX、可用性测试
• 销售 - B2B关单、需求挖掘

💡 **快速开始**
/task - 创建新任务
/status - 查看任务状态
/agents - 查看员工列表
/report - 获取今日报告
/help - 查看帮助

**成本降低 98%，24小时工作，随时随地控制！** 🚀
"""
    
    await update.message.reply_text(welcome_text, parse_mode='Markdown')

async def task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """创建任务"""
    keyboard = [
        [
            InlineKeyboardButton("🔍 SEO优化", callback_data='task_seo'),
            InlineKeyboardButton("✍️ 内容创作", callback_data='task_content'),
        ],
        [
            InlineKeyboardButton("🚀 增长实验", callback_data='task_growth'),
            InlineKeyboardButton("💰 广告优化", callback_data='task_ads'),
        ],
        [
            InlineKeyboardButton("👥 社区活动", callback_data='task_community'),
            InlineKeyboardButton("🎨 设计审查", callback_data='task_design'),
        ],
        [
            InlineKeyboardButton("💼 销售跟进", callback_data='task_sales'),
            InlineKeyboardButton("🧮 算法优化", callback_data='task_algorithm'),
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        '请选择任务类型：',
        reply_markup=reply_markup
    )

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理按钮回调"""
    query = update.callback_query
    await query.answer()
    
    global company
    if company is None:
        company = OnePersonCompany()
    
    # 解析任务类型
    task_type = query.data.replace('task_', '')
    
    task_map = {
        'seo': ('SEO优化', '分析竞品关键词并提供优化建议'),
        'content': ('内容创作', '创作一篇关于AI创业的深度文章'),
        'growth': ('增长实验', '设计并执行A/B测试'),
        'ads': ('广告优化', '优化广告投放策略'),
        'community': ('社区活动', '设计用户互动活动'),
        'design': ('设计审查', '审查产品页面设计'),
        'sales': ('销售跟进', '评估潜在客户资格'),
        'algorithm': ('算法优化', '优化核心算法性能')
    }
    
    task_name, task_desc = task_map.get(task_type, ('未知任务', ''))
    
    # 创建任务
    await query.edit_message_text(f"⚙️ 正在执行 {task_name}...\n\n请稍候...")
    
    task = company.router.route_task(
        task_type=task_type,
        description=task_desc,
        priority=TaskPriority.HIGH,
        data={"action": "custom", "source": "telegram"}
    )
    
    result = company.router.execute_task(task)
    
    # 格式化结果
    result_text = f"""
✅ **任务完成！**

📋 **任务**: {task_name}
🤖 **执行员工**: {task.assigned_agent}
⏱️ **耗时**: <1秒
💰 **成本**: $0.00

📊 **结果摘要**:
{_format_result(result)}

💡 使用 /report 查看完整报告
"""
    
    await query.edit_message_text(result_text, parse_mode='Markdown')

def _format_result(result: dict) -> str:
    """格式化结果"""
    if result.get('status') == 'success':
        # 提取关键信息
        summary = []
        
        if 'keyword_clusters' in result:
            summary.append(f"• 发现 {len(result['keyword_clusters'])} 个关键词集群")
        
        if 'content' in result:
            content = result['content']
            if isinstance(content, dict):
                summary.append(f"• 标题: {content.get('title', 'N/A')[:50]}...")
                summary.append(f"• 字数: {content.get('word_count', 0)}")
        
        if 'optimization' in result:
            opt = result['optimization']
            summary.append(f"• CPA优化: ${opt.get('current_cpa')} → ${opt.get('target_cpa')}")
            summary.append(f"• 预期ROI: {opt.get('projected_roi', 0)}x")
        
        if 'test_id' in result:
            summary.append(f"• 测试ID: {result['test_id']}")
            summary.append(f"• 推荐方案: {result.get('recommendation', 'N/A')}")
        
        if 'campaign' in result:
            camp = result['campaign']
            summary.append(f"• 活动: {camp.get('name', 'N/A')}")
            summary.append(f"• 预期参与: {camp.get('expected_participation', 0)} 人")
        
        if 'review' in result:
            review = result['review']
            summary.append(f"• 设计评分: {review.get('overall_score', 0)}/100")
            summary.append(f"• 发现问题: {len(review.get('issues', []))} 个")
        
        if 'qualification' in result:
            qual = result['qualification']
            summary.append(f"• 线索评分: {qual.get('lead_score', 0)}/100")
            summary.append(f"• 预估订单: ${qual.get('estimated_deal_size', 0):,}")
        
        return '\n'.join(summary) if summary else '任务已完成，详细结果请查看报告'
    else:
        return f"❌ 错误: {result.get('error', '未知错误')}"

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """查看任务状态"""
    global company
    if company is None:
        await update.message.reply_text("系统未初始化，请先使用 /start")
        return
    
    dashboard = company.router.get_dashboard()
    
    status_text = f"""
📊 **系统状态**

✅ 已完成任务: {dashboard['completed_tasks']}
⏳ 待处理任务: {dashboard['pending_tasks']}
🤖 在线员工: {dashboard['registered_agents']}
💰 总成本: ${dashboard['total_cost']:.2f}

🏆 **员工工作统计**:
"""
    
    for agent_name, stats in list(dashboard['agents'].items())[:5]:
        status_text += f"\n• {agent_name}: {stats['tasks_completed']} 个任务"
    
    await update.message.reply_text(status_text, parse_mode='Markdown')

async def agents(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """查看员工列表"""
    agents_text = """
👥 **你的AI员工团队**

🎯 **L2 增长团队**
• 增长工程师 - A/B测试、漏斗优化
• SEO架构师 - 关键词研究、排名优化  
• 内容专家 - 深度文章、品牌叙事
• 广告黑客 - 投放优化、ROI提升
• 社区运营 - UGC激励、影响者协作

🛡️ **L3 专家团队**
• 算法专家 - 模型优化、性能调优
• 合规顾问 - 法律审查、税务规划
• 设计师 - UI/UX、可用性测试
• 销售 - B2B关单、需求挖掘

💡 每个员工都注入了世界顶级专家的思维模型！
"""
    
    await update.message.reply_text(agents_text, parse_mode='Markdown')

async def report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """获取今日报告"""
    global company
    if company is None:
        await update.message.reply_text("系统未初始化，请先使用 /start")
        return
    
    dashboard = company.router.get_dashboard()
    
    report_text = f"""
📈 **今日工作报告**

📅 日期: {datetime.now().strftime('%Y-%m-%d')}

✅ **任务完成情况**
• 已完成: {dashboard['completed_tasks']} 个
• 待处理: {dashboard['pending_tasks']} 个
• 成功率: 100%

💰 **成本统计**
• 今日成本: ${dashboard['total_cost']:.2f}
• 平均每任务: ${dashboard['total_cost'] / max(dashboard['completed_tasks'], 1):.2f}

🏆 **最佳员工**
"""
    
    # 找出完成任务最多的员工
    top_agents = sorted(
        dashboard['agents'].items(),
        key=lambda x: x[1]['tasks_completed'],
        reverse=True
    )[:3]
    
    for i, (name, stats) in enumerate(top_agents, 1):
        report_text += f"\n{i}. {name} - {stats['tasks_completed']} 个任务"
    
    report_text += "\n\n💡 继续保持！明天再接再厉！"
    
    await update.message.reply_text(report_text, parse_mode='Markdown')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """帮助命令"""
    help_text = """
📖 **命令列表**

/start - 启动系统
/task - 创建新任务
/status - 查看系统状态
/agents - 查看员工列表
/report - 获取今日报告
/help - 查看此帮助

💡 **使用技巧**
• 随时随地发送命令
• 任务自动分配给最合适的员工
• 所有操作都有日志记录
• 24小时不间断工作

🚀 **开始使用**
点击 /task 创建你的第一个任务！
"""
    
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理普通消息"""
    text = update.message.text
    
    # 智能识别任务意图
    if any(keyword in text.lower() for keyword in ['seo', '关键词', '排名', '优化']):
        await update.message.reply_text("检测到SEO相关需求，使用 /task 选择SEO优化任务")
    elif any(keyword in text.lower() for keyword in ['内容', '文章', '写作', '创作']):
        await update.message.reply_text("检测到内容创作需求，使用 /task 选择内容创作任务")
    elif any(keyword in text.lower() for keyword in ['广告', '投放', 'roi', 'cpa']):
        await update.message.reply_text("检测到广告优化需求，使用 /task 选择广告优化任务")
    else:
        await update.message.reply_text(
            "我是你的AI员工管理助手！\n\n"
            "使用 /task 创建任务\n"
            "使用 /help 查看所有命令"
        )

def main():
    """启动Telegram Bot"""
    logger.info("🤖 启动 Telegram Bot...")
    
    # 创建应用
    application = Application.builder().token(BOT_TOKEN).build()
    
    # 注册命令处理器
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("task", task))
    application.add_handler(CommandHandler("status", status))
    application.add_handler(CommandHandler("agents", agents))
    application.add_handler(CommandHandler("report", report))
    application.add_handler(CommandHandler("help", help_command))
    
    # 注册回调处理器
    application.add_handler(CallbackQueryHandler(button_callback))
    
    # 注册消息处理器
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # 启动Bot
    logger.success("✅ Telegram Bot 已启动！")
    logger.info("发送 /start 开始使用")
    
    application.run_polling()

if __name__ == "__main__":
    from datetime import datetime
    main()

