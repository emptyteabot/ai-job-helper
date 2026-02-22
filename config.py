"""一人公司系统配置"""
import os
from dotenv import load_dotenv

load_dotenv()

# API 配置
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

# 系统配置
COMPANY_NAME = os.getenv("COMPANY_NAME", "一人公司")
FOUNDER_NAME = os.getenv("FOUNDER_NAME", "创始人")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# 数据库
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./company.db")

# Agent 配置
AGENT_CONFIG = {
    "temperature": 0.7,
    "max_tokens": 4000,
    "model": "gpt-4-turbo-preview"
}

# 技能库路径
SKILLS_PATH = "./skills"
MCP_SERVERS_PATH = "./mcp_servers"

