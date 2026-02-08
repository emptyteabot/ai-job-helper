"""
Multi-Agent协调器 - 参考OpenClaw和AutoGPT思想
实现智能Agent协作、任务分解、结果聚合
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum
import asyncio
import time

class AgentRole(Enum):
    """Agent角色枚举"""
    PLANNER = "职业规划师"
    RECRUITER = "招聘专家"
    OPTIMIZER = "简历优化师"
    REVIEWER = "质量检查官"
    COACH = "面试教练"
    INTERVIEWER = "模拟面试官"

@dataclass
class AgentTask:
    """Agent任务"""
    role: AgentRole
    input_data: Dict[str, Any]
    dependencies: List[str]  # 依赖的其他任务
    priority: int  # 优先级
    status: str = "pending"  # pending, running, completed, failed
    output: Optional[Dict] = None
    start_time: Optional[float] = None
    end_time: Optional[float] = None

class AgentOrchestrator:
    """
    Agent协调器 - 核心思想：
    1. 任务分解 (Task Decomposition)
    2. 依赖管理 (Dependency Management)
    3. 并行执行 (Parallel Execution)
    4. 结果聚合 (Result Aggregation)
    5. 错误恢复 (Error Recovery)
    """
    
    def __init__(self):
        self.tasks: List[AgentTask] = []
        self.results: Dict[str, Any] = {}
        self.execution_log: List[Dict] = []
    
    def create_pipeline(self, resume_text: str) -> List[AgentTask]:
        """
        创建完整的处理管道
        参考AutoGPT的任务分解思想
        """
        tasks = [
            # 阶段1: 职业分析 (无依赖，可立即执行)
            AgentTask(
                role=AgentRole.PLANNER,
                input_data={"resume": resume_text},
                dependencies=[],
                priority=1
            ),
            
            # 阶段2: 岗位搜索 (依赖职业分析)
            AgentTask(
                role=AgentRole.RECRUITER,
                input_data={"resume": resume_text},
                dependencies=["PLANNER"],
                priority=2
            ),
            
            # 阶段3: 简历优化 (依赖岗位搜索)
            AgentTask(
                role=AgentRole.OPTIMIZER,
                input_data={"resume": resume_text},
                dependencies=["RECRUITER"],
                priority=3
            ),
            
            # 阶段4: 质量审核 (依赖简历优化)
            AgentTask(
                role=AgentRole.REVIEWER,
                input_data={},
                dependencies=["OPTIMIZER"],
                priority=4
            ),
            
            # 阶段5: 二次优化 (依赖质量审核)
            AgentTask(
                role=AgentRole.OPTIMIZER,
                input_data={},
                dependencies=["REVIEWER"],
                priority=5
            ),
            
            # 阶段6: 面试辅导 (依赖二次优化)
            AgentTask(
                role=AgentRole.COACH,
                input_data={},
                dependencies=["OPTIMIZER"],
                priority=6
            ),
            
            # 阶段7: 模拟面试 (依赖面试辅导)
            AgentTask(
                role=AgentRole.INTERVIEWER,
                input_data={},
                dependencies=["COACH"],
                priority=7
            ),
        ]
        
        self.tasks = tasks
        return tasks
    
    def get_ready_tasks(self) -> List[AgentTask]:
        """获取可以执行的任务（依赖已满足）"""
        ready = []
        for task in self.tasks:
            if task.status == "pending":
                # 检查依赖是否都完成
                deps_satisfied = all(
                    any(t.role.name == dep and t.status == "completed" 
                        for t in self.tasks)
                    for dep in task.dependencies
                )
                if deps_satisfied:
                    ready.append(task)
        return ready
    
    def execute_task(self, task: AgentTask, ai_engine) -> Dict[str, Any]:
        """执行单个任务"""
        task.status = "running"
        task.start_time = time.time()
        
        try:
            # 构建上下文（包含依赖任务的输出）
            context = task.input_data.copy()
            for dep in task.dependencies:
                dep_task = next((t for t in self.tasks if t.role.name == dep), None)
                if dep_task and dep_task.output:
                    context[dep] = dep_task.output
            
            # 调用AI引擎执行
            result = ai_engine.ai_think(
                role=task.role.name.lower(),
                context=str(context),
                previous_output=context.get(task.dependencies[-1], {}).get("output", "") if task.dependencies else ""
            )
            
            task.output = result
            task.status = "completed"
            task.end_time = time.time()
            
            # 记录日志
            self.execution_log.append({
                "role": task.role.value,
                "status": "success",
                "duration": task.end_time - task.start_time,
                "output_preview": result.get("output", "")[:100]
            })
            
            return result
            
        except Exception as e:
            task.status = "failed"
            task.end_time = time.time()
            
            self.execution_log.append({
                "role": task.role.value,
                "status": "failed",
                "error": str(e)
            })
            
            raise
    
    def run_pipeline(self, ai_engine) -> Dict[str, Any]:
        """
        运行完整管道
        支持并行执行（如果依赖允许）
        """
        print("\n" + "="*60)
        print("🚀 Agent协调器启动")
        print("="*60)
        
        while True:
            # 获取可执行任务
            ready_tasks = self.get_ready_tasks()
            
            if not ready_tasks:
                # 检查是否全部完成
                if all(t.status == "completed" for t in self.tasks):
                    break
                # 检查是否有失败
                if any(t.status == "failed" for t in self.tasks):
                    raise Exception("管道执行失败")
                continue
            
            # 执行任务（这里可以改为并行）
            for task in ready_tasks:
                print(f"\n▶ 执行: {task.role.value}")
                self.execute_task(task, ai_engine)
                print(f"✓ 完成: {task.role.value}")
        
        print("\n" + "="*60)
        print("✅ 所有Agent任务完成")
        print("="*60)
        
        # 聚合结果
        return self.aggregate_results()
    
    def aggregate_results(self) -> Dict[str, Any]:
        """聚合所有Agent的输出"""
        results = {}
        
        for task in self.tasks:
            if task.output:
                key = task.role.name.lower()
                if key not in results:
                    results[key] = []
                results[key].append(task.output)
        
        # 提取最终结果
        final_results = {
            "career_analysis": results.get("planner", [{}])[0].get("output", ""),
            "job_recommendations": results.get("recruiter", [{}])[0].get("output", ""),
            "optimized_resume": results.get("optimizer", [{}])[-1].get("output", ""),  # 取最后一次优化
            "interview_prep": results.get("coach", [{}])[0].get("output", ""),
            "mock_interview": results.get("interviewer", [{}])[0].get("output", ""),
            "execution_log": self.execution_log
        }
        
        return final_results
    
    def get_progress(self) -> Dict[str, Any]:
        """获取执行进度"""
        total = len(self.tasks)
        completed = sum(1 for t in self.tasks if t.status == "completed")
        running = sum(1 for t in self.tasks if t.status == "running")
        
        return {
            "total": total,
            "completed": completed,
            "running": running,
            "progress": (completed / total * 100) if total > 0 else 0,
            "current_task": next((t.role.value for t in self.tasks if t.status == "running"), None)
        }

