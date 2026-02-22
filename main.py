"""主程序 - 一人公司系统启动入口"""
from loguru import logger
import sys
from datetime import datetime

# 配置日志
logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
    level="INFO"
)
logger.add(
    "./logs/company_{time:YYYY-MM-DD}.log",
    rotation="1 day",
    retention="30 days",
    level="DEBUG"
)

# 导入核心组件
from core.router import FounderRouter, TaskPriority
from agents.l2_growth_agents import (
    GrowthEngineer, SEOArchitect, ContentStrategist,
    PaidAcquisitionHacker, CommunityOperator
)
from agents.l3_specialist_agents import (
    AlgorithmSpecialist, ComplianceDefender,
    UXSpecialist, B2BCloser
)
from mcp_servers.mcp_loader import list_mcp_servers
from skills.skill_loader import list_skills


class OnePersonCompany:
    """一人公司系统"""
    
    def __init__(self):
        logger.info("=" * 60)
        logger.info("🚀 一人公司 AI Agent 系统启动中...")
        logger.info("=" * 60)
        
        # 初始化路由器
        self.router = FounderRouter()
        
        # 初始化所有 Agents
        self._initialize_agents()
        
        # 显示系统信息
        self._show_system_info()
    
    def _initialize_agents(self):
        """初始化所有 Agent"""
        logger.info("\n📦 正在初始化 Agent 团队...")
        
        # L2 前端分发突击队
        logger.info("\n🎯 L2 前端分发突击队:")
        self.growth_engineer = GrowthEngineer()
        self.router.register_agent("growth_engineer", self.growth_engineer, self.growth_engineer.capabilities)
        
        self.seo_architect = SEOArchitect()
        self.router.register_agent("seo_architect", self.seo_architect, self.seo_architect.capabilities)
        
        self.content_strategist = ContentStrategist()
        self.router.register_agent("content_strategist", self.content_strategist, self.content_strategist.capabilities)
        
        self.paid_hacker = PaidAcquisitionHacker()
        self.router.register_agent("paid_acquisition_hacker", self.paid_hacker, self.paid_hacker.capabilities)
        
        self.community_operator = CommunityOperator()
        self.router.register_agent("community_operator", self.community_operator, self.community_operator.capabilities)
        
        # L3 后端防御与攻坚
        logger.info("\n🛡️ L3 后端防御与攻坚:")
        self.algorithm_specialist = AlgorithmSpecialist()
        self.router.register_agent("algorithm_specialist", self.algorithm_specialist, self.algorithm_specialist.capabilities)
        
        self.compliance_defender = ComplianceDefender()
        self.router.register_agent("compliance_defender", self.compliance_defender, self.compliance_defender.capabilities)
        
        self.ux_specialist = UXSpecialist()
        self.router.register_agent("ux_specialist", self.ux_specialist, self.ux_specialist.capabilities)
        
        self.b2b_closer = B2BCloser()
        self.router.register_agent("b2b_closer", self.b2b_closer, self.b2b_closer.capabilities)
        
        logger.success(f"\n✅ 共初始化 {len(self.router.agent_registry)} 个 Agent")
    
    def _show_system_info(self):
        """显示系统信息"""
        logger.info("\n" + "=" * 60)
        logger.info("📊 系统信息")
        logger.info("=" * 60)
        
        # MCP 服务器
        mcp_servers = list_mcp_servers()
        logger.info(f"\n🔧 可用 MCP 服务器 ({len(mcp_servers)} 个):")
        for name, desc in mcp_servers.items():
            logger.info(f"  • {name}: {desc}")
        
        # 技能库
        skills = list_skills()
        logger.info(f"\n🎯 可用技能 ({len(skills)} 个):")
        for name, desc in skills.items():
            logger.info(f"  • {name}: {desc}")
        
        logger.info("\n" + "=" * 60)
        logger.success("✨ 系统就绪！开始接收任务...")
        logger.info("=" * 60 + "\n")
    
    def run_demo(self):
        """运行演示任务"""
        logger.info("🎬 开始运行演示任务...\n")
        
        # 任务 1: SEO 关键词研究
        logger.info("📋 任务 1: SEO 关键词研究")
        task1 = self.router.route_task(
            task_type="seo",
            description="为'AI创业'主题进行关键词研究",
            priority=TaskPriority.HIGH,
            data={
                "action": "keyword_research",
                "seed_keyword": "AI创业"
            }
        )
        result1 = self.router.execute_task(task1)
        logger.info(f"结果: {result1}\n")
        
        # 任务 2: 内容创作
        logger.info("📋 任务 2: 深度内容创作")
        task2 = self.router.route_task(
            task_type="content",
            description="创作关于一人公司的深度文章",
            priority=TaskPriority.HIGH,
            data={
                "action": "create_content",
                "topic": "一人公司如何用AI实现10倍增长",
                "type": "article"
            }
        )
        result2 = self.router.execute_task(task2)
        logger.info(f"结果: {result2}\n")
        
        # 任务 3: A/B 测试
        logger.info("📋 任务 3: 增长 A/B 测试")
        task3 = self.router.route_task(
            task_type="growth",
            description="测试落地页两个版本",
            priority=TaskPriority.MEDIUM,
            data={
                "action": "ab_test",
                "variants": ["版本A: 强调效率", "版本B: 强调成本节省"],
                "metric": "conversion_rate"
            }
        )
        result3 = self.router.execute_task(task3)
        logger.info(f"结果: {result3}\n")
        
        # 任务 4: 广告优化
        logger.info("📋 任务 4: 付费广告优化")
        task4 = self.router.route_task(
            task_type="ads",
            description="优化广告活动预算分配",
            priority=TaskPriority.HIGH,
            data={
                "action": "optimize_campaign",
                "budget": 5000,
                "current_cpa": 45
            }
        )
        result4 = self.router.execute_task(task4)
        logger.info(f"结果: {result4}\n")
        
        # 任务 5: 社区活动
        logger.info("📋 任务 5: 社区互动活动")
        task5 = self.router.route_task(
            task_type="community",
            description="设计用户参与活动",
            priority=TaskPriority.MEDIUM,
            data={
                "action": "engagement_campaign",
                "campaign_name": "AI工具使用挑战赛"
            }
        )
        result5 = self.router.execute_task(task5)
        logger.info(f"结果: {result5}\n")
        
        # 任务 6: 设计审查
        logger.info("📋 任务 6: UI/UX 设计审查")
        task6 = self.router.route_task(
            task_type="design",
            description="审查产品首页设计",
            priority=TaskPriority.MEDIUM,
            data={
                "action": "design_review",
                "page": "产品首页"
            }
        )
        result6 = self.router.execute_task(task6)
        logger.info(f"结果: {result6}\n")
        
        # 任务 7: 销售线索评估
        logger.info("📋 任务 7: B2B 销售线索评估")
        task7 = self.router.route_task(
            task_type="sales",
            description="评估潜在客户资格",
            priority=TaskPriority.HIGH,
            data={
                "action": "qualify_lead",
                "lead_info": {
                    "company": "某科技公司",
                    "size": "50-100人",
                    "industry": "SaaS"
                }
            }
        )
        result7 = self.router.execute_task(task7)
        logger.info(f"结果: {result7}\n")
        
        # 显示仪表盘
        self.show_dashboard()
        
        # 保存审计日志
        self.router.save_audit_log()
    
    def show_dashboard(self):
        """显示系统仪表盘"""
        dashboard = self.router.get_dashboard()
        
        logger.info("\n" + "=" * 60)
        logger.info("📊 系统仪表盘")
        logger.info("=" * 60)
        logger.info(f"待处理任务: {dashboard['pending_tasks']}")
        logger.info(f"已完成任务: {dashboard['completed_tasks']}")
        logger.info(f"注册 Agent: {dashboard['registered_agents']}")
        logger.info(f"总成本: ${dashboard['total_cost']:.2f}")
        
        logger.info("\n👥 Agent 工作统计:")
        for agent_name, stats in dashboard['agents'].items():
            logger.info(f"\n  {agent_name}:")
            logger.info(f"    完成任务: {stats['tasks_completed']}")
            logger.info(f"    总成本: ${stats['total_cost']:.2f}")
            logger.info(f"    能力: {', '.join(stats['capabilities'][:3])}...")
        
        logger.info("\n" + "=" * 60)
    
    def interactive_mode(self):
        """交互模式"""
        logger.info("\n🎮 进入交互模式 (输入 'exit' 退出, 'help' 查看帮助)\n")
        
        while True:
            try:
                command = input("\n👤 创始人 > ").strip()
                
                if command.lower() == 'exit':
                    logger.info("👋 系统关闭")
                    break
                
                elif command.lower() == 'help':
                    self._show_help()
                
                elif command.lower() == 'dashboard':
                    self.show_dashboard()
                
                elif command.lower() == 'agents':
                    self._list_agents()
                
                elif command.lower() == 'skills':
                    self._list_skills()
                
                elif command.lower() == 'mcp':
                    self._list_mcp()
                
                elif command.startswith('task:'):
                    self._create_custom_task(command)
                
                else:
                    logger.warning("未知命令，输入 'help' 查看帮助")
            
            except KeyboardInterrupt:
                logger.info("\n👋 系统关闭")
                break
            except Exception as e:
                logger.error(f"错误: {str(e)}")
    
    def _show_help(self):
        """显示帮助"""
        logger.info("""
可用命令:
  help       - 显示此帮助信息
  dashboard  - 显示系统仪表盘
  agents     - 列出所有 Agent
  skills     - 列出所有技能
  mcp        - 列出所有 MCP 服务器
  task:类型  - 创建任务 (例: task:seo, task:content)
  exit       - 退出系统
        """)
    
    def _list_agents(self):
        """列出所有 Agent"""
        logger.info("\n👥 已注册的 Agent:")
        for name, info in self.router.agent_registry.items():
            logger.info(f"\n  {name}:")
            logger.info(f"    能力: {', '.join(info['capabilities'])}")
            logger.info(f"    完成任务: {info['tasks_completed']}")
    
    def _list_skills(self):
        """列出所有技能"""
        skills = list_skills()
        logger.info(f"\n🎯 可用技能 ({len(skills)} 个):")
        for name, desc in skills.items():
            logger.info(f"  • {name}: {desc}")
    
    def _list_mcp(self):
        """列出所有 MCP 服务器"""
        mcp_servers = list_mcp_servers()
        logger.info(f"\n🔧 可用 MCP 服务器 ({len(mcp_servers)} 个):")
        for name, desc in mcp_servers.items():
            logger.info(f"  • {name}: {desc}")
    
    def _create_custom_task(self, command: str):
        """创建自定义任务"""
        task_type = command.split(':')[1].strip()
        
        logger.info(f"\n创建 {task_type} 任务")
        description = input("任务描述: ").strip()
        
        task = self.router.route_task(
            task_type=task_type,
            description=description,
            priority=TaskPriority.MEDIUM,
            data={"action": "custom"}
        )
        
        result = self.router.execute_task(task)
        logger.info(f"\n结果: {result}")


def main():
    """主函数"""
    # 创建公司实例
    company = OnePersonCompany()
    
    # 运行演示
    logger.info("选择模式:")
    logger.info("1. 运行演示任务")
    logger.info("2. 进入交互模式")
    
    try:
        choice = input("\n请选择 (1/2): ").strip()
        
        if choice == "1":
            company.run_demo()
        elif choice == "2":
            company.interactive_mode()
        else:
            logger.info("运行默认演示...")
            company.run_demo()
    
    except KeyboardInterrupt:
        logger.info("\n\n👋 系统关闭")
    except Exception as e:
        logger.error(f"系统错误: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

