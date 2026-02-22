"""MCP 工具接入层 - 统一外部系统接入"""
from typing import Dict, Any, List
from loguru import logger
import json

class MCPServer:
    """MCP 服务器基类"""
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.tools: Dict[str, Any] = {}
    
    def register_tool(self, tool_name: str, tool_func: callable):
        """注册工具"""
        self.tools[tool_name] = tool_func
        logger.info(f"🔧 MCP工具已注册: {self.name}.{tool_name}")
    
    def call_tool(self, tool_name: str, params: Dict[str, Any]) -> Any:
        """调用工具"""
        if tool_name not in self.tools:
            raise ValueError(f"工具 {tool_name} 不存在于 {self.name}")
        
        logger.info(f"📡 调用MCP工具: {self.name}.{tool_name}")
        return self.tools[tool_name](params)


class GoogleSheetsMCP(MCPServer):
    """Google Sheets MCP 服务器"""
    def __init__(self):
        super().__init__(
            name="google_sheets",
            description="Google Sheets 数据读写"
        )
        self._setup_tools()
    
    def _setup_tools(self):
        self.register_tool("read_sheet", self._read_sheet)
        self.register_tool("write_sheet", self._write_sheet)
        self.register_tool("append_row", self._append_row)
    
    def _read_sheet(self, params: Dict[str, Any]) -> Dict[str, Any]:
        sheet_id = params.get("sheet_id")
        range_name = params.get("range", "A1:Z100")
        
        # 模拟读取
        return {
            "sheet_id": sheet_id,
            "range": range_name,
            "data": [
                ["任务ID", "状态", "负责人", "完成时间"],
                ["TASK-001", "已完成", "SEO架构师", "2026-02-20"],
                ["TASK-002", "进行中", "增长工程师", ""]
            ]
        }
    
    def _write_sheet(self, params: Dict[str, Any]) -> Dict[str, Any]:
        sheet_id = params.get("sheet_id")
        data = params.get("data", [])
        
        return {
            "status": "success",
            "rows_written": len(data),
            "sheet_id": sheet_id
        }
    
    def _append_row(self, params: Dict[str, Any]) -> Dict[str, Any]:
        sheet_id = params.get("sheet_id")
        row_data = params.get("row_data", [])
        
        return {
            "status": "success",
            "row_appended": row_data,
            "sheet_id": sheet_id
        }


class NotionMCP(MCPServer):
    """Notion MCP 服务器"""
    def __init__(self):
        super().__init__(
            name="notion",
            description="Notion 数据库和页面操作"
        )
        self._setup_tools()
    
    def _setup_tools(self):
        self.register_tool("query_database", self._query_database)
        self.register_tool("create_page", self._create_page)
        self.register_tool("update_page", self._update_page)
    
    def _query_database(self, params: Dict[str, Any]) -> Dict[str, Any]:
        database_id = params.get("database_id")
        filter_params = params.get("filter", {})
        
        return {
            "database_id": database_id,
            "results": [
                {
                    "id": "page-001",
                    "title": "产品路线图",
                    "status": "进行中",
                    "owner": "创始人"
                },
                {
                    "id": "page-002",
                    "title": "Q1营销计划",
                    "status": "已完成",
                    "owner": "增长工程师"
                }
            ],
            "count": 2
        }
    
    def _create_page(self, params: Dict[str, Any]) -> Dict[str, Any]:
        parent_id = params.get("parent_id")
        title = params.get("title")
        content = params.get("content", "")
        
        return {
            "status": "success",
            "page_id": "page-new-001",
            "title": title,
            "url": f"https://notion.so/page-new-001"
        }
    
    def _update_page(self, params: Dict[str, Any]) -> Dict[str, Any]:
        page_id = params.get("page_id")
        updates = params.get("updates", {})
        
        return {
            "status": "success",
            "page_id": page_id,
            "updated_fields": list(updates.keys())
        }


class SlackMCP(MCPServer):
    """Slack MCP 服务器"""
    def __init__(self):
        super().__init__(
            name="slack",
            description="Slack 消息和通知"
        )
        self._setup_tools()
    
    def _setup_tools(self):
        self.register_tool("send_message", self._send_message)
        self.register_tool("create_channel", self._create_channel)
        self.register_tool("get_messages", self._get_messages)
    
    def _send_message(self, params: Dict[str, Any]) -> Dict[str, Any]:
        channel = params.get("channel")
        message = params.get("message")
        
        logger.info(f"💬 发送Slack消息到 {channel}")
        
        return {
            "status": "success",
            "channel": channel,
            "message": message,
            "timestamp": "1708617600"
        }
    
    def _create_channel(self, params: Dict[str, Any]) -> Dict[str, Any]:
        channel_name = params.get("channel_name")
        
        return {
            "status": "success",
            "channel_id": f"C{channel_name.upper()}",
            "channel_name": channel_name
        }
    
    def _get_messages(self, params: Dict[str, Any]) -> Dict[str, Any]:
        channel = params.get("channel")
        limit = params.get("limit", 10)
        
        return {
            "channel": channel,
            "messages": [
                {"user": "创始人", "text": "今天的任务进展如何？", "timestamp": "1708617600"},
                {"user": "SEO架构师", "text": "关键词研究已完成，发现15个机会", "timestamp": "1708617700"}
            ],
            "count": 2
        }


class WebScraperMCP(MCPServer):
    """网页抓取 MCP 服务器"""
    def __init__(self):
        super().__init__(
            name="web_scraper",
            description="网页内容抓取和分析"
        )
        self._setup_tools()
    
    def _setup_tools(self):
        self.register_tool("scrape_url", self._scrape_url)
        self.register_tool("extract_data", self._extract_data)
        self.register_tool("monitor_changes", self._monitor_changes)
    
    def _scrape_url(self, params: Dict[str, Any]) -> Dict[str, Any]:
        url = params.get("url")
        
        return {
            "url": url,
            "title": "示例页面标题",
            "content": "页面主要内容...",
            "meta": {
                "description": "页面描述",
                "keywords": ["关键词1", "关键词2"]
            },
            "links": ["https://example.com/page1", "https://example.com/page2"]
        }
    
    def _extract_data(self, params: Dict[str, Any]) -> Dict[str, Any]:
        url = params.get("url")
        selector = params.get("selector", "")
        
        return {
            "url": url,
            "selector": selector,
            "extracted_data": [
                {"title": "文章1", "date": "2026-02-20"},
                {"title": "文章2", "date": "2026-02-21"}
            ]
        }
    
    def _monitor_changes(self, params: Dict[str, Any]) -> Dict[str, Any]:
        url = params.get("url")
        
        return {
            "url": url,
            "monitoring": True,
            "check_interval": "1小时",
            "last_change": "2026-02-22 10:30"
        }


class EmailMCP(MCPServer):
    """邮件 MCP 服务器"""
    def __init__(self):
        super().__init__(
            name="email",
            description="邮件发送和管理"
        )
        self._setup_tools()
    
    def _setup_tools(self):
        self.register_tool("send_email", self._send_email)
        self.register_tool("send_bulk", self._send_bulk)
        self.register_tool("track_opens", self._track_opens)
    
    def _send_email(self, params: Dict[str, Any]) -> Dict[str, Any]:
        to = params.get("to")
        subject = params.get("subject")
        body = params.get("body")
        
        logger.info(f"📧 发送邮件到 {to}")
        
        return {
            "status": "success",
            "to": to,
            "subject": subject,
            "message_id": "msg-001"
        }
    
    def _send_bulk(self, params: Dict[str, Any]) -> Dict[str, Any]:
        recipients = params.get("recipients", [])
        template = params.get("template")
        
        return {
            "status": "success",
            "sent_count": len(recipients),
            "template": template,
            "campaign_id": "campaign-001"
        }
    
    def _track_opens(self, params: Dict[str, Any]) -> Dict[str, Any]:
        campaign_id = params.get("campaign_id")
        
        return {
            "campaign_id": campaign_id,
            "sent": 100,
            "opened": 45,
            "clicked": 12,
            "open_rate": 0.45,
            "click_rate": 0.12
        }


# MCP 服务器注册表
MCP_REGISTRY = {
    "google_sheets": GoogleSheetsMCP(),
    "notion": NotionMCP(),
    "slack": SlackMCP(),
    "web_scraper": WebScraperMCP(),
    "email": EmailMCP()
}


def get_mcp_server(server_name: str) -> MCPServer:
    """获取 MCP 服务器"""
    server = MCP_REGISTRY.get(server_name)
    if not server:
        raise ValueError(f"MCP服务器 {server_name} 不存在")
    return server


def list_mcp_servers() -> Dict[str, str]:
    """列出所有 MCP 服务器"""
    return {
        name: server.description 
        for name, server in MCP_REGISTRY.items()
    }


def call_mcp_tool(server_name: str, tool_name: str, params: Dict[str, Any]) -> Any:
    """调用 MCP 工具"""
    server = get_mcp_server(server_name)
    return server.call_tool(tool_name, params)

