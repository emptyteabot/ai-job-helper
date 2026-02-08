"""
实时进度系统 - WebSocket实时通信
真正的实时进度，不是假的！
"""

import asyncio
from typing import Dict, List, Callable
from datetime import datetime
import json

class RealtimeProgressTracker:
    """实时进度追踪器"""
    
    def __init__(self):
        self.connections: List = []  # WebSocket连接列表
        self.current_progress = {
            "step": 0,
            "total_steps": 5,
            "percentage": 0,
            "status": "idle",
            "message": "",
            "ai_messages": [],
            "start_time": None,
            "current_agent": None
        }
    
    async def connect(self, websocket):
        """添加WebSocket连接"""
        self.connections.append(websocket)
        # 发送当前进度
        await websocket.send_json(self.current_progress)
    
    def disconnect(self, websocket):
        """移除WebSocket连接"""
        if websocket in self.connections:
            self.connections.remove(websocket)
    
    async def update_progress(self, step: int, message: str, agent: str = None):
        """更新进度并广播"""
        self.current_progress.update({
            "step": step,
            "percentage": (step / 5) * 100,
            "status": "processing",
            "message": message,
            "current_agent": agent,
            "timestamp": datetime.now().isoformat()
        })
        
        await self.broadcast(self.current_progress)
    
    async def add_ai_message(self, agent: str, message: str):
        """添加AI消息"""
        ai_msg = {
            "agent": agent,
            "message": message,
            "timestamp": datetime.now().isoformat()
        }
        self.current_progress["ai_messages"].append(ai_msg)
        
        await self.broadcast({
            "type": "ai_message",
            "data": ai_msg
        })
    
    async def complete(self):
        """完成处理"""
        self.current_progress.update({
            "step": 5,
            "percentage": 100,
            "status": "completed",
            "message": "所有AI协作完成！"
        })
        
        await self.broadcast(self.current_progress)
    
    async def error(self, error_message: str):
        """错误处理"""
        self.current_progress.update({
            "status": "error",
            "message": error_message
        })
        
        await self.broadcast(self.current_progress)
    
    async def broadcast(self, data: Dict):
        """广播消息到所有连接"""
        if not self.connections:
            return
        
        message = json.dumps(data, ensure_ascii=False)
        
        # 移除已断开的连接
        disconnected = []
        for websocket in self.connections:
            try:
                await websocket.send_text(message)
            except:
                disconnected.append(websocket)
        
        for ws in disconnected:
            self.disconnect(ws)
    
    def reset(self):
        """重置进度"""
        self.current_progress = {
            "step": 0,
            "total_steps": 5,
            "percentage": 0,
            "status": "idle",
            "message": "",
            "ai_messages": [],
            "start_time": None,
            "current_agent": None
        }


# 全局进度追踪器
progress_tracker = RealtimeProgressTracker()

