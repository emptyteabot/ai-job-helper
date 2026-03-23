from __future__ import annotations

import json
import re
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


KNOWN_CITIES = (
    "全国",
    "北京",
    "上海",
    "深圳",
    "杭州",
    "广州",
    "成都",
    "南京",
    "苏州",
    "武汉",
    "西安",
)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class ChatSessionStore:
    def __init__(self, store_file: Path) -> None:
        self.store_file = Path(store_file)
        self._lock = threading.RLock()
        self._sessions = self._load()

    def _load(self) -> Dict[str, Dict[str, Any]]:
        if not self.store_file.exists():
            return {}
        try:
            raw = json.loads(self.store_file.read_text(encoding="utf-8") or "{}")
        except Exception:
            return {}
        if not isinstance(raw, dict):
            return {}
        return {str(key): dict(value) for key, value in raw.items() if isinstance(value, dict)}

    def _save(self) -> None:
        self.store_file.parent.mkdir(parents=True, exist_ok=True)
        self.store_file.write_text(
            json.dumps(self._sessions, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def list_sessions(self, user_id: str) -> List[Dict[str, Any]]:
        rows = [dict(row) for row in self._sessions.values() if str(row.get("user_id") or "") == str(user_id or "")]
        rows.sort(key=lambda row: str(row.get("updated_at") or ""), reverse=True)
        return rows

    def create_session(self, user_id: str, title: str = "") -> Dict[str, Any]:
        session_id = uuid.uuid4().hex
        row = {
            "id": session_id,
            "user_id": str(user_id or ""),
            "title": title or "New chat",
            "created_at": utc_now_iso(),
            "updated_at": utc_now_iso(),
            "messages": [],
            "context": {},
        }
        self._sessions[session_id] = row
        self._save()
        return dict(row)

    def get_session(self, session_id: str, user_id: str) -> Dict[str, Any]:
        row = dict(self._sessions.get(str(session_id or ""), {}))
        if not row or str(row.get("user_id") or "") != str(user_id or ""):
            return {}
        return row

    def append_messages(
        self,
        session_id: str,
        user_id: str,
        messages: List[Dict[str, Any]],
        context_patch: Optional[Dict[str, Any]] = None,
        title: Optional[str] = None,
    ) -> Dict[str, Any]:
        row = self.get_session(session_id, user_id)
        if not row:
            return {}
        existing = list(row.get("messages") or [])
        existing.extend(messages)
        row["messages"] = existing[-80:]
        if context_patch:
            current_context = dict(row.get("context") or {})
            current_context.update(context_patch)
            row["context"] = current_context
        if title:
            row["title"] = title
        row["updated_at"] = utc_now_iso()
        self._sessions[session_id] = row
        self._save()
        return dict(row)


def _extract_city(message: str, previous_city: str = "") -> str:
    text = str(message or "")
    for city in KNOWN_CITIES:
        if city in text:
            return city
    return previous_city or "全国"


def _extract_max_count(message: str, previous_value: int = 10) -> int:
    text = str(message or "")
    match = re.search(r"(\d{1,2})\s*(?:个|条|份|次)", text)
    if match:
        return max(1, min(int(match.group(1)), 50))
    return max(1, min(int(previous_value or 10), 50))


def _extract_keyword(message: str, previous_keyword: str = "") -> str:
    text = str(message or "").strip()
    patterns = [
        r"(?:找|搜|投|执行|申请|应聘)(.+?)(?:岗位|实习|工作|offer|$)",
        r"(?:想找|目标是|我要)(.+?)(?:岗位|实习|工作|offer|$)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            value = re.sub(r"[，,。.!！?？]+$", "", match.group(1)).strip()
            if value:
                return value
    for token in ("产品", "运营", "增长", "前端", "后端", "算法", "AI", "数据", "测试", "设计"):
        if token in text:
            return token
    return previous_keyword or "产品实习生"


def heuristic_orchestrator_reply(message: str, context: Dict[str, Any]) -> Dict[str, Any]:
    text = str(message or "").strip()
    lower = text.lower()
    previous_keyword = str(context.get("keyword") or "").strip()
    previous_city = str(context.get("city") or "").strip()
    previous_max_count = int(context.get("max_count") or 10)
    resume_available = bool(context.get("resume_available"))

    keyword = _extract_keyword(text, previous_keyword)
    city = _extract_city(text, previous_city)
    max_count = _extract_max_count(text, previous_max_count)

    actions: List[Dict[str, Any]] = []
    response = "我已经接住你的目标，会先判断你是要搜索、分析简历、执行投递，还是进入人工接管。"

    if any(token in lower for token in ("面经", "复盘", "记录", "漏斗", "统计")):
        actions.append({"type": "show_records", "limit": 8})
        response = "我先把最近的执行记录和回流状态拉出来，不再让你在多个页面之间跳。"
    elif any(token in lower for token in ("简历", "分析", "优化", "改简历")):
        actions.append({"type": "analyze_resume"})
        response = "我先分析你当前简历，再给出针对性的改写方向。"
    elif any(token in lower for token in ("boss", "验证码", "滑块", "challenge", "接管")):
        actions.append({"type": "open_challenge_center", "keyword": keyword, "city": city, "max_count": max_count})
        response = "这类请求应该直接进入 Challenge Center，而不是假装后台能全自动绕过验证。"
    elif any(token in lower for token in ("投递", "海投", "开始执行", "帮我投", "apply")):
        actions.append({"type": "search_jobs", "keyword": keyword, "city": city, "max_count": max_count})
        if resume_available:
            actions.append({"type": "run_apply", "keyword": keyword, "city": city, "max_count": max_count})
            response = f"我会先找 {city} 的 {keyword}，然后直接推进执行；中途遇到 challenge 再把接管点抛给你。"
        else:
            response = "我知道你想直接执行，但你当前还没有可用简历。先上传简历，我再推进这一轮。"
            actions.append({"type": "request_resume_upload"})
    else:
        actions.append({"type": "search_jobs", "keyword": keyword, "city": city, "max_count": max_count})
        response = f"我先按 {city} / {keyword} 给你筛一轮真实岗位入口，再根据结果决定是否继续执行。"

    return {
        "assistant_message": response,
        "actions": actions,
        "context_patch": {
            "keyword": keyword,
            "city": city,
            "max_count": max_count,
        },
    }
