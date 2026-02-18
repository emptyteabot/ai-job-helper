"""
飞书 + OpenClaw 混合投递方案
- 飞书机器人发送指令
- 本地 OpenClaw 执行投递
- 结果回传到飞书
"""

import json
from typing import Dict, Any, List
from app.core.feishu_bot import get_feishu_bot


class FeishuOpenClawBridge:
    """飞书 + OpenClaw 桥接器"""

    def __init__(self, app_id: str = None, app_secret: str = None):
        self.feishu_bot = get_feishu_bot(app_id, app_secret)

    def send_apply_task(
        self,
        receive_id: str,
        targets: Dict[str, Any],
        platform: str = "Boss直聘"
    ) -> Dict[str, Any]:
        """发送投递任务到飞书"""

        # 生成任务 ID
        import uuid
        task_id = str(uuid.uuid4())[:8]

        # 构建任务数据
        task_data = {
            'task_id': task_id,
            'platform': platform,
            'keywords': targets.get('keywords', []),
            'locations': targets.get('locations', []),
            'max_count': targets.get('match_criteria', {}).get('max_per_day', 30),
            'positions': targets.get('positions', [])
        }

        # 方案1：使用 OpenClaw（如果已安装）
        openclaw_script = self._generate_openclaw_script(task_data)

        # 方案2：使用 Selenium 脚本（备用）
        from app.core.smart_apply import smart_apply_engine
        config = smart_apply_engine.generate_apply_config(targets)
        selenium_script = smart_apply_engine.generate_selenium_script(config, platform)

        # 发送卡片消息
        card = {
            "config": {
                "wide_screen_mode": True
            },
            "header": {
                "title": {
                    "tag": "plain_text",
                    "content": f"🚀 智能投递任务 #{task_id}"
                },
                "template": "blue"
            },
            "elements": [
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": f"""**平台：** {platform}
**关键词：** {', '.join(task_data['keywords'][:3])}
**地点：** {', '.join(task_data['locations'])}
**每天数量：** {task_data['max_count']}

**AI 推荐理由：**
- 匹配度 ≥ 70%
- 优先实习岗位
- 避免销售/客服类

---

### 🤖 方案1：OpenClaw（推荐）

如果你已安装 OpenClaw，运行：

```bash
{openclaw_script}
```

### 💻 方案2：Selenium 脚本（备用）

如果没有 OpenClaw，下载并运行：

```bash
# 下载脚本
curl -O https://your-service.com/scripts/apply_{task_id}.py

# 运行
python apply_{task_id}.py
```

---

**投递完成后，结果会自动发送到这里 📊**"""
                    }
                },
                {
                    "tag": "action",
                    "actions": [
                        {
                            "tag": "button",
                            "text": {
                                "tag": "plain_text",
                                "content": "📥 下载 OpenClaw 脚本"
                            },
                            "type": "primary",
                            "url": f"https://your-service.com/download/openclaw_{task_id}.sh"
                        },
                        {
                            "tag": "button",
                            "text": {
                                "tag": "plain_text",
                                "content": "📥 下载 Selenium 脚本"
                            },
                            "type": "default",
                            "url": f"https://your-service.com/download/selenium_{task_id}.py"
                        },
                        {
                            "tag": "button",
                            "text": {
                                "tag": "plain_text",
                                "content": "❓ 查看教程"
                            },
                            "type": "default",
                            "url": "https://your-service.com/docs/how-to-apply"
                        }
                    ]
                }
            ]
        }

        # 发送消息
        result = self.feishu_bot.send_card(receive_id, card)

        return {
            'task_id': task_id,
            'status': 'sent',
            'result': result,
            'openclaw_script': openclaw_script,
            'selenium_script': selenium_script
        }

    def _generate_openclaw_script(self, task_data: Dict[str, Any]) -> str:
        """生成 OpenClaw 脚本"""

        keywords = ' OR '.join(task_data['keywords'][:3])
        locations = ','.join(task_data['locations'])

        if task_data['platform'] == "Boss直聘":
            return f"""openclaw run \\
  --site zhipin \\
  --keywords "{keywords}" \\
  --locations "{locations}" \\
  --max-count {task_data['max_count']} \\
  --interval 5 \\
  --callback https://your-service.com/api/callback/{task_data['task_id']}"""

        elif task_data['platform'] == "实习僧":
            return f"""openclaw run \\
  --site shixiseng \\
  --keywords "{keywords}" \\
  --locations "{locations}" \\
  --max-count {task_data['max_count']}"""

        else:
            return f"""# OpenClaw 暂不支持 {task_data['platform']}
# 请使用 Selenium 脚本"""

    def send_progress_update(
        self,
        receive_id: str,
        task_id: str,
        progress: Dict[str, Any]
    ):
        """发送进度更新"""

        text = f"""📊 投递进度更新 #{task_id}

已投递：{progress['completed']}/{progress['total']}
成功：{progress['success']}
失败：{progress['failed']}

最新投递：
{progress.get('latest', '暂无')}"""

        self.feishu_bot.send_text(receive_id, text)

    def send_completion_report(
        self,
        receive_id: str,
        task_id: str,
        report: Dict[str, Any]
    ):
        """发送完成报告"""

        card = {
            "config": {
                "wide_screen_mode": True
            },
            "header": {
                "title": {
                    "tag": "plain_text",
                    "content": f"✅ 投递完成 #{task_id}"
                },
                "template": "green"
            },
            "elements": [
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": f"""**总投递：** {report['total']}
**成功：** {report['success']} ✅
**失败：** {report['failed']} ❌
**耗时：** {report['duration']} 分钟

**投递详情：**

{self._format_apply_results(report['results'])}

---

**下一步：**
- 等待 HR 回复（通常 1-3 天）
- 准备面试（查看面试准备）
- 继续投递其他岗位"""
                    }
                },
                {
                    "tag": "action",
                    "actions": [
                        {
                            "tag": "button",
                            "text": {
                                "tag": "plain_text",
                                "content": "📊 查看详细报告"
                            },
                            "type": "primary",
                            "url": f"https://your-service.com/reports/{task_id}"
                        },
                        {
                            "tag": "button",
                            "text": {
                                "tag": "plain_text",
                                "content": "🚀 继续投递"
                            },
                            "type": "default",
                            "url": "https://your-service.com/apply"
                        }
                    ]
                }
            ]
        }

        self.feishu_bot.send_card(receive_id, card)

    def _format_apply_results(self, results: List[Dict]) -> str:
        """格式化投递结果"""

        lines = []

        for i, result in enumerate(results[:10], 1):  # 最多显示 10 条
            status_emoji = "✅" if result['status'] == 'success' else "❌"
            lines.append(f"{i}. {status_emoji} **{result['position']}** - {result['company']}")

        if len(results) > 10:
            lines.append(f"\n... 还有 {len(results) - 10} 条")

        return '\n'.join(lines)


# 全局实例
feishu_openclaw_bridge = FeishuOpenClawBridge()
