"""
飞书机器人配置 - 使用 App ID 和 App Secret
"""

import requests
import json
import time
from typing import Dict, Any


class FeishuBot:
    """飞书机器人客户端"""

    def __init__(self, app_id: str, app_secret: str):
        self.app_id = app_id
        self.app_secret = app_secret
        self.tenant_access_token = None
        self.token_expire_time = 0

    def get_tenant_access_token(self) -> str:
        """获取 tenant_access_token"""

        # 如果 token 还没过期，直接返回
        if self.tenant_access_token and time.time() < self.token_expire_time:
            return self.tenant_access_token

        # 获取新的 token
        url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"

        payload = {
            "app_id": self.app_id,
            "app_secret": self.app_secret
        }

        response = requests.post(url, json=payload)
        data = response.json()

        if data.get("code") == 0:
            self.tenant_access_token = data["tenant_access_token"]
            # token 有效期 2 小时，提前 5 分钟刷新
            self.token_expire_time = time.time() + data["expire"] - 300
            return self.tenant_access_token
        else:
            raise Exception(f"获取 token 失败: {data}")

    def send_message(self, receive_id: str, msg_type: str, content: Dict[str, Any], receive_id_type: str = "open_id") -> Dict[str, Any]:
        """发送消息

        Args:
            receive_id: 接收者 ID
            msg_type: 消息类型
            content: 消息内容
            receive_id_type: ID 类型，可选：open_id, user_id, union_id, email, chat_id
        """

        token = self.get_tenant_access_token()

        url = "https://open.feishu.cn/open-apis/im/v1/messages"

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        # 自动判断 receive_id 类型
        if "@" in receive_id:
            receive_id_type = "email"
        elif receive_id.startswith("ou_"):
            receive_id_type = "open_id"
        elif receive_id.isdigit() and len(receive_id) == 11:
            # 手机号，需要先转换为 open_id
            raise Exception("不支持手机号，请使用飞书邮箱或 open_id")

        params = {
            "receive_id_type": receive_id_type
        }

        payload = {
            "receive_id": receive_id,
            "msg_type": msg_type,
            "content": json.dumps(content)
        }

        response = requests.post(url, headers=headers, params=params, json=payload)
        return response.json()

    def send_text(self, receive_id: str, text: str) -> Dict[str, Any]:
        """发送文本消息"""

        content = {
            "text": text
        }

        return self.send_message(receive_id, "text", content)

    def send_card(self, receive_id: str, card: Dict[str, Any]) -> Dict[str, Any]:
        """发送卡片消息"""

        return self.send_message(receive_id, "interactive", card)

    def send_apply_card(self, receive_id: str, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """发送投递任务卡片"""

        card = {
            "config": {
                "wide_screen_mode": True
            },
            "header": {
                "title": {
                    "tag": "plain_text",
                    "content": "🚀 智能投递任务"
                },
                "template": "blue"
            },
            "elements": [
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": f"""**平台：** {task_data['platform']}
**关键词：** {', '.join(task_data['keywords'])}
**地点：** {', '.join(task_data['locations'])}
**每天数量：** {task_data['max_count']}

**AI 推荐理由：**
- 匹配度 ≥ 70%
- 优先实习岗位
- 避免销售/客服类

**投递脚本：**
```bash
python auto_apply.py \\
  --platform "{task_data['platform']}" \\
  --keywords "{','.join(task_data['keywords'])}" \\
  --locations "{','.join(task_data['locations'])}" \\
  --count {task_data['max_count']}
```"""
                    }
                },
                {
                    "tag": "action",
                    "actions": [
                        {
                            "tag": "button",
                            "text": {
                                "tag": "plain_text",
                                "content": "开始投递"
                            },
                            "type": "primary",
                            "value": {
                                "action": "start_apply",
                                "task_id": task_data.get('task_id', '')
                            }
                        },
                        {
                            "tag": "button",
                            "text": {
                                "tag": "plain_text",
                                "content": "查看详情"
                            },
                            "type": "default",
                            "url": task_data.get('detail_url', '')
                        }
                    ]
                }
            ]
        }

        return self.send_card(receive_id, card)


# 全局实例（使用环境变量或配置）
def get_feishu_bot(app_id: str = None, app_secret: str = None) -> FeishuBot:
    """获取飞书机器人实例"""

    import os

    app_id = app_id or os.getenv("FEISHU_APP_ID", "cli_a908b88dc6b8dcd4")
    app_secret = app_secret or os.getenv("FEISHU_APP_SECRET", "Q8jjY7RDcwfcsmTd0Zvylee4dfs6kVhK")

    return FeishuBot(app_id, app_secret)
