"""L1 核心路由引擎 - 创始人 API 和任务路由系统"""
from typing import Dict, List, Any, Optional
from datetime import datetime
from loguru import logger
import json
from enum import Enum

class TaskPriority(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class TaskStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"

class Task:
    """任务工单"""
    def __init__(self, task_id: str, task_type: str, description: str, 
                 priority: TaskPriority, assigned_agent: str, data: Dict[str, Any]):
        self.task_id = task_id
        self.task_type = task_type
        self.description = description
        self.priority = priority
        self.assigned_agent = assigned_agent
        self.data = data
        self.status = TaskStatus.PENDING
        self.created_at = datetime.now()
        self.completed_at = None
        self.result = None
        self.cost = 0.0
        self.tokens_used = 0

    def to_dict(self):
        return {
            "task_id": self.task_id,
            "task_type": self.task_type,
            "description": self.description,
            "priority": self.priority.value,
            "assigned_agent": self.assigned_agent,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "cost": self.cost,
            "tokens_used": self.tokens_used
        }

class FounderRouter:
    """创始人路由器 - 你是所有信息的终点站"""
    
    def __init__(self):
        self.task_queue: List[Task] = []
        self.completed_tasks: List[Task] = []
        self.agent_registry: Dict[str, Any] = {}
        logger.info("🚀 创始人路由引擎已启动")
    
    def register_agent(self, agent_name: str, agent_instance: Any, capabilities: List[str]):
        """注册 Agent 到系统"""
        self.agent_registry[agent_name] = {
            "instance": agent_instance,
            "capabilities": capabilities,
            "tasks_completed": 0,
            "total_cost": 0.0
        }
        logger.info(f"✅ Agent 已注册: {agent_name} | 能力: {', '.join(capabilities)}")
    
    def route_task(self, task_type: str, description: str, priority: TaskPriority, data: Dict[str, Any]) -> Task:
        """智能路由任务到合适的 Agent"""
        # 根据任务类型选择 Agent
        agent_mapping = {
            "seo": "seo_architect",
            "content": "content_strategist",
            "growth": "growth_engineer",
            "ads": "paid_acquisition_hacker",
            "community": "community_operator",
            "algorithm": "algorithm_specialist",
            "compliance": "compliance_defender",
            "design": "ux_specialist",
            "sales": "b2b_closer"
        }
        
        assigned_agent = agent_mapping.get(task_type, "general_agent")
        task_id = f"TASK-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        task = Task(task_id, task_type, description, priority, assigned_agent, data)
        self.task_queue.append(task)
        
        logger.info(f"📋 新任务已路由: {task_id} -> {assigned_agent} | 优先级: {priority.value}")
        return task
    
    def execute_task(self, task: Task) -> Dict[str, Any]:
        """执行任务"""
        task.status = TaskStatus.IN_PROGRESS
        logger.info(f"⚙️ 执行任务: {task.task_id} | Agent: {task.assigned_agent}")
        
        try:
            agent_info = self.agent_registry.get(task.assigned_agent)
            if not agent_info:
                raise ValueError(f"Agent {task.assigned_agent} 未注册")
            
            agent = agent_info["instance"]
            result = agent.execute(task)
            
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now()
            task.result = result
            
            # 更新统计
            agent_info["tasks_completed"] += 1
            agent_info["total_cost"] += task.cost
            
            self.completed_tasks.append(task)
            self.task_queue.remove(task)
            
            logger.success(f"✅ 任务完成: {task.task_id} | 耗时: {(task.completed_at - task.created_at).seconds}s")
            return result
            
        except Exception as e:
            task.status = TaskStatus.FAILED
            logger.error(f"❌ 任务失败: {task.task_id} | 错误: {str(e)}")
            return {"error": str(e)}
    
    def get_dashboard(self) -> Dict[str, Any]:
        """获取系统仪表盘"""
        return {
            "pending_tasks": len(self.task_queue),
            "completed_tasks": len(self.completed_tasks),
            "registered_agents": len(self.agent_registry),
            "total_cost": sum(agent["total_cost"] for agent in self.agent_registry.values()),
            "agents": {
                name: {
                    "tasks_completed": info["tasks_completed"],
                    "total_cost": info["total_cost"],
                    "capabilities": info["capabilities"]
                }
                for name, info in self.agent_registry.items()
            }
        }
    
    def save_audit_log(self, filepath: str = "./logs/audit.json"):
        """保存审计日志"""
        import os
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        audit_data = {
            "timestamp": datetime.now().isoformat(),
            "completed_tasks": [task.to_dict() for task in self.completed_tasks],
            "dashboard": self.get_dashboard()
        }
        
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(audit_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"💾 审计日志已保存: {filepath}")

