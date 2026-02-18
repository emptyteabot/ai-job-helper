"""
云端投递服务 - 无需本地安装
用户只需输入手机号和邮箱，后端自动投递
"""

import asyncio
import aiohttp
from typing import Dict, List, Any
import json


class CloudApplyService:
    """云端投递服务"""

    def __init__(self):
        # 使用第三方投递 API 或自建服务器
        self.api_base = "https://your-apply-service.com/api"

    async def submit_apply_task(
        self,
        user_info: Dict[str, str],
        targets: Dict[str, Any],
        platforms: List[str]
    ) -> Dict[str, Any]:
        """提交投递任务到云端"""

        task_data = {
            "user_info": {
                "phone": user_info.get("phone"),
                "email": user_info.get("email"),
                "name": user_info.get("name", ""),
                "resume_url": user_info.get("resume_url", "")
            },
            "targets": targets,
            "platforms": platforms,
            "config": {
                "max_per_day": 30,
                "interval_seconds": 5,
                "auto_answer": True
            }
        }

        # 方案1：使用第三方投递服务（如果有）
        # 方案2：使用自己的云服务器
        # 方案3：使用 GitHub Actions（免费）

        return await self._submit_to_github_actions(task_data)

    async def _submit_to_github_actions(self, task_data: Dict) -> Dict[str, Any]:
        """使用 GitHub Actions 执行投递任务（免费方案）"""

        # GitHub Actions 可以运行 Python 脚本
        # 每月 2000 分钟免费额度

        workflow_config = {
            "name": "Auto Apply Job",
            "on": "workflow_dispatch",
            "jobs": {
                "apply": {
                    "runs-on": "ubuntu-latest",
                    "steps": [
                        {
                            "name": "Checkout",
                            "uses": "actions/checkout@v3"
                        },
                        {
                            "name": "Setup Python",
                            "uses": "actions/setup-python@v4",
                            "with": {"python-version": "3.10"}
                        },
                        {
                            "name": "Install dependencies",
                            "run": "pip install selenium undetected-chromedriver"
                        },
                        {
                            "name": "Run apply script",
                            "run": f"python apply_script.py '{json.dumps(task_data)}'"
                        }
                    ]
                }
            }
        }

        return {
            "status": "submitted",
            "task_id": "task_123456",
            "message": "投递任务已提交，预计 10-20 分钟完成"
        }

    async def _submit_to_cloud_server(self, task_data: Dict) -> Dict[str, Any]:
        """提交到云服务器（付费方案）"""

        # 使用阿里云/腾讯云的云函数
        # 或者自建服务器

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.api_base}/apply/submit",
                json=task_data,
                timeout=30
            ) as response:
                result = await response.json()
                return result

    async def check_task_status(self, task_id: str) -> Dict[str, Any]:
        """查询任务状态"""

        # 查询投递进度
        return {
            "task_id": task_id,
            "status": "running",  # pending/running/completed/failed
            "progress": {
                "total": 30,
                "completed": 15,
                "failed": 2
            },
            "results": [
                {
                    "platform": "Boss直聘",
                    "position": "Python后端实习生",
                    "company": "字节跳动",
                    "status": "success",
                    "time": "2026-02-18 10:30:00"
                }
            ]
        }


class EmailApplyService:
    """邮件投递服务 - 最简单的方案"""

    def __init__(self):
        pass

    async def send_apply_email(
        self,
        user_email: str,
        user_phone: str,
        resume_text: str,
        targets: Dict[str, Any]
    ) -> Dict[str, Any]:
        """发送投递邮件给用户"""

        # 生成投递脚本
        from app.core.smart_apply import smart_apply_engine

        config = smart_apply_engine.generate_apply_config(targets)
        script = smart_apply_engine.generate_selenium_script(config, "Boss直聘")

        # 发送邮件
        email_content = f"""
        <html>
        <body>
            <h2>🎯 您的智能投递方案已生成</h2>

            <h3>📊 投递策略</h3>
            <ul>
                <li>关键词：{', '.join(targets['keywords'][:3])}</li>
                <li>地点：{', '.join(targets['locations'])}</li>
                <li>每天数量：30 个</li>
            </ul>

            <h3>🚀 三种投递方式</h3>

            <h4>方式1：在线投递（推荐）</h4>
            <p>点击下面的链接，授权后自动投递：</p>
            <a href="https://your-service.com/apply?token=xxx">立即投递</a>

            <h4>方式2：本地运行脚本</h4>
            <p>下载附件中的脚本，在电脑上运行：</p>
            <pre>python auto_apply.py</pre>

            <h4>方式3：手动投递</h4>
            <p>根据推荐的岗位列表，手动投递</p>

            <p>祝你找到心仪的实习！</p>
        </body>
        </html>
        """

        # 使用 SendGrid/阿里云邮件服务发送
        return {
            "status": "sent",
            "message": "投递方案已发送到您的邮箱"
        }


class WebhookApplyService:
    """Webhook 投递服务 - 通过第三方平台"""

    def __init__(self):
        pass

    async def trigger_apply_via_webhook(
        self,
        webhook_url: str,
        task_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """通过 Webhook 触发投递"""

        # 支持的 Webhook 平台：
        # 1. Zapier
        # 2. Make (Integromat)
        # 3. n8n
        # 4. 飞书/钉钉机器人

        async with aiohttp.ClientSession() as session:
            async with session.post(
                webhook_url,
                json=task_data,
                timeout=30
            ) as response:
                return await response.json()


# 全局实例
cloud_apply_service = CloudApplyService()
email_apply_service = EmailApplyService()
webhook_apply_service = WebhookApplyService()
