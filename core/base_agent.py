"""基础 Agent 类 - 所有员工的基类"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List
from loguru import logger
import time

class BaseAgent(ABC):
    """Agent 基类"""
    
    def __init__(self, name: str, role: str, capabilities: List[str], skills: List[str]):
        self.name = name
        self.role = role
        self.capabilities = capabilities
        self.skills = skills
        self.memory = []
        logger.info(f"🤖 {name} ({role}) 已初始化")
    
    @abstractmethod
    def execute(self, task: Any) -> Dict[str, Any]:
        """执行任务 - 子类必须实现"""
        pass
    
    def use_skill(self, skill_name: str, params: Dict[str, Any]) -> Any:
        """调用技能库"""
        logger.info(f"🔧 {self.name} 使用技能: {skill_name}")
        # 这里会调用 skills 目录下的具体技能
        from skills.skill_loader import load_skill
        skill = load_skill(skill_name)
        return skill.run(params)
    
    def log_action(self, action: str, result: Any):
        """记录行动"""
        self.memory.append({
            "timestamp": time.time(),
            "action": action,
            "result": result
        })
    
    def get_context(self) -> str:
        """获取 Agent 上下文"""
        return f"""
你是 {self.name}，职位是 {self.role}。
你的核心能力：{', '.join(self.capabilities)}
你掌握的技能：{', '.join(self.skills)}
"""

