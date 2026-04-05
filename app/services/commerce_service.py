from __future__ import annotations

import json
import os
import secrets
import sqlite3
import threading
import uuid
import shutil
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _iso_now() -> str:
    return _utc_now().isoformat()


def _to_iso_days(days: int) -> str:
    return (_utc_now() + timedelta(days=max(1, int(days or 30)))).isoformat()


def _json_dump(value: Any) -> str:
    return json.dumps(value or {}, ensure_ascii=False)


def _json_load(value: Any) -> Any:
    raw = str(value or "").strip()
    if not raw:
        return {}
    try:
        return json.loads(raw)
    except Exception:
        return {}


CREDIT_PACKAGES: List[Dict[str, Any]] = [
    {
        "package_id": "trial",
        "name": "体验版",
        "credits": 12,
        "price": 0,
        "currency": "CNY",
        "headline": "先跑通一轮",
        "description": "适合先看清工作台和本地投递闭环。",
        "features": ["1 次完整求职流程", "1 次本地投递任务", "余额与流水可见"],
        "auto_activate": True,
        "trial_only": True,
        "sort_order": 1,
    },
    {
        "package_id": "starter",
        "name": "起步版",
        "credits": 48,
        "price": 39,
        "currency": "CNY",
        "headline": "个人起步",
        "description": "够你连续改简历、跑岗位池和做几轮本地投递。",
        "features": ["多轮简历分析", "多次结构化/渲染", "本地投递批次"],
        "auto_activate": False,
        "trial_only": False,
        "sort_order": 2,
    },
    {
        "package_id": "growth",
        "name": "进阶版",
        "credits": 120,
        "price": 69,
        "currency": "CNY",
        "headline": "高频求职",
        "description": "适合 2 到 4 周密集求职，把简历、岗位、训练和投递一起跑。",
        "features": ["更高额度", "适合多岗位试错", "支持多轮训练与跟进"],
        "auto_activate": False,
        "trial_only": False,
        "sort_order": 3,
    },
    {
        "package_id": "offer",
        "name": "冲刺版",
        "credits": 280,
        "price": 99,
        "currency": "CNY",
        "headline": "冲刺拿结果",
        "description": "给重度使用者，适合长期跟进、持续迭代和多批次本地执行。",
        "features": ["大额点数", "适合高强度迭代", "覆盖长期推进"],
        "auto_activate": False,
        "trial_only": False,
        "sort_order": 4,
    },
]


class CommerceService:
    """Minimal commercial backend for codes, buyers, orders, support, and local agents."""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or os.getenv("APP_DATA_DB_PATH", "data/app_data.db")
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.payment_proof_dir = os.path.join(os.path.dirname(self.db_path) or "data", "payment_proofs")
        os.makedirs(self.payment_proof_dir, exist_ok=True)
        self._lock = threading.RLock()
        self._init_db()

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=10, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def _table_columns(self, conn: sqlite3.Connection, table_name: str) -> set[str]:
        rows = conn.execute(f"PRAGMA table_info({table_name})").fetchall()
        return {str(row["name"] or "").strip() for row in rows}

    def _ensure_column(self, conn: sqlite3.Connection, table_name: str, column_name: str, ddl: str) -> None:
        if column_name in self._table_columns(conn, table_name):
            return
        conn.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {ddl}")

    def _init_db(self) -> None:
        with self._lock:
            conn = self._conn()
            try:
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS buyers (
                        buyer_id TEXT PRIMARY KEY,
                        name TEXT,
                        phone TEXT,
                        email TEXT,
                        source TEXT,
                        channel TEXT,
                        status TEXT,
                        note TEXT,
                        access_code TEXT,
                        created_at TEXT NOT NULL,
                        expires_at TEXT,
                        last_active_at TEXT
                    )
                    """
                )
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS orders (
                        order_id TEXT PRIMARY KEY,
                        buyer_id TEXT,
                        product_name TEXT,
                        amount REAL,
                        currency TEXT,
                        payment_channel TEXT,
                        payment_status TEXT,
                        delivery_status TEXT,
                        access_code TEXT,
                        note TEXT,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL
                    )
                    """
                )
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS access_codes (
                        code TEXT PRIMARY KEY,
                        buyer_id TEXT,
                        order_id TEXT,
                        label TEXT,
                        status TEXT,
                        max_uses INTEGER,
                        used_count INTEGER,
                        expires_at TEXT,
                        activated_at TEXT,
                        last_used_at TEXT,
                        note TEXT,
                        created_at TEXT NOT NULL
                    )
                    """
                )
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS support_tickets (
                        ticket_id TEXT PRIMARY KEY,
                        buyer_id TEXT,
                        order_id TEXT,
                        subject TEXT,
                        content TEXT,
                        channel TEXT,
                        status TEXT,
                        priority TEXT,
                        assignee TEXT,
                        note TEXT,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL
                    )
                    """
                )
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS local_agents (
                        agent_id TEXT PRIMARY KEY,
                        buyer_id TEXT,
                        access_code TEXT,
                        machine_name TEXT,
                        hostname TEXT,
                        platform TEXT,
                        capabilities_json TEXT,
                        status TEXT,
                        note TEXT,
                        created_at TEXT NOT NULL,
                        last_seen_at TEXT
                    )
                    """
                )
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS local_tasks (
                        task_id TEXT PRIMARY KEY,
                        agent_id TEXT,
                        buyer_id TEXT,
                        access_code TEXT,
                        task_type TEXT,
                        status TEXT,
                        payload_json TEXT,
                        progress_json TEXT,
                        result_json TEXT,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL,
                        started_at TEXT,
                        completed_at TEXT
                    )
                    """
                )
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS wallets (
                        buyer_id TEXT PRIMARY KEY,
                        balance INTEGER NOT NULL DEFAULT 0,
                        granted_total INTEGER NOT NULL DEFAULT 0,
                        consumed_total INTEGER NOT NULL DEFAULT 0,
                        last_grant_at TEXT,
                        last_consume_at TEXT,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL
                    )
                    """
                )
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS credit_ledger (
                        ledger_id TEXT PRIMARY KEY,
                        buyer_id TEXT,
                        order_id TEXT,
                        access_code TEXT,
                        direction TEXT,
                        amount INTEGER NOT NULL DEFAULT 0,
                        balance_after INTEGER NOT NULL DEFAULT 0,
                        action TEXT,
                        package_id TEXT,
                        note TEXT,
                        meta_json TEXT,
                        created_at TEXT NOT NULL
                    )
                    """
                )
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS payment_proofs (
                        proof_id TEXT PRIMARY KEY,
                        buyer_id TEXT,
                        order_id TEXT,
                        access_code TEXT,
                        status TEXT,
                        amount REAL,
                        note TEXT,
                        file_name TEXT,
                        mime_type TEXT,
                        file_path TEXT,
                        reviewed_note TEXT,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL
                    )
                    """
                )
                self._ensure_column(conn, "orders", "package_id", "TEXT DEFAULT ''")
                self._ensure_column(conn, "orders", "credits", "INTEGER NOT NULL DEFAULT 0")
                self._ensure_column(conn, "orders", "wallet_granted_at", "TEXT DEFAULT ''")
                self._ensure_column(conn, "orders", "activation_mode", "TEXT DEFAULT ''")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_orders_buyer ON orders(buyer_id, created_at)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_access_buyer ON access_codes(buyer_id, created_at)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_tickets_buyer ON support_tickets(buyer_id, created_at)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_agents_code ON local_agents(access_code, last_seen_at)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_local_tasks_status ON local_tasks(status, created_at)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_credit_ledger_buyer ON credit_ledger(buyer_id, created_at)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_credit_ledger_order ON credit_ledger(order_id, created_at)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_payment_proofs_order ON payment_proofs(order_id, created_at)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_payment_proofs_buyer ON payment_proofs(buyer_id, created_at)")
                conn.commit()
            finally:
                conn.close()

    def _new_id(self, prefix: str) -> str:
        return f"{prefix}_{uuid.uuid4().hex[:12]}"

    def _generate_code(self, length: int = 8) -> str:
        alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
        return "".join(secrets.choice(alphabet) for _ in range(max(6, int(length or 8))))

    def _unique_code(self, conn: sqlite3.Connection, length: int = 8) -> str:
        for _ in range(50):
            code = self._generate_code(length=length)
            row = conn.execute("SELECT code FROM access_codes WHERE code = ?", (code,)).fetchone()
            if not row:
                return code
        raise RuntimeError("unable_to_generate_unique_access_code")

    def _buyer_search_where(self, search: str, alias: str = "") -> tuple[str, List[str]]:
        q = str(search or "").strip()
        if not q:
            return "", []
        like = f"%{q}%"
        prefix = f"{alias}." if alias else ""
        return (
            f" WHERE {prefix}buyer_id LIKE ? OR {prefix}name LIKE ? OR {prefix}phone LIKE ? OR {prefix}email LIKE ? OR {prefix}access_code LIKE ? ",
            [like] * 5,
        )

    def _join_bundle_row(self, row: sqlite3.Row) -> Dict[str, Any]:
        return {
            "buyer_id": str(row["buyer_id"] or ""),
            "name": str(row["name"] or ""),
            "phone": str(row["phone"] or ""),
            "email": str(row["email"] or ""),
            "source": str(row["source"] or ""),
            "channel": str(row["channel"] or ""),
            "buyer_status": str(row["buyer_status"] or ""),
            "buyer_note": str(row["buyer_note"] or ""),
            "buyer_created_at": str(row["buyer_created_at"] or ""),
            "buyer_expires_at": str(row["buyer_expires_at"] or ""),
            "last_active_at": str(row["last_active_at"] or ""),
            "order_id": str(row["order_id"] or ""),
            "product_name": str(row["product_name"] or ""),
            "amount": float(row["amount"] or 0),
            "currency": str(row["currency"] or "CNY"),
            "payment_channel": str(row["payment_channel"] or ""),
            "payment_status": str(row["payment_status"] or ""),
            "delivery_status": str(row["delivery_status"] or ""),
            "order_note": str(row["order_note"] or ""),
            "order_created_at": str(row["order_created_at"] or ""),
            "order_updated_at": str(row["order_updated_at"] or ""),
            "access_code": str(row["access_code"] or ""),
            "access_label": str(row["access_label"] or ""),
            "access_status": str(row["access_status"] or ""),
            "max_uses": int(row["max_uses"] or 0),
            "used_count": int(row["used_count"] or 0),
            "code_expires_at": str(row["code_expires_at"] or ""),
            "activated_at": str(row["activated_at"] or ""),
            "last_used_at": str(row["last_used_at"] or ""),
            "access_note": str(row["access_note"] or ""),
        }

    def list_credit_packages(self) -> List[Dict[str, Any]]:
        auto_activate_paid = os.getenv("PUBLIC_AUTO_ACTIVATE_PAID_CREDITS", "0").strip().lower() in {"1", "true", "yes", "on"}
        packages: List[Dict[str, Any]] = []
        for item in sorted(CREDIT_PACKAGES, key=lambda x: int(x.get("sort_order") or 0)):
            row = dict(item)
            row["checkout_mode"] = "instant" if row.get("auto_activate") or auto_activate_paid else "manual_review"
            packages.append(row)
        return packages

    def _credit_package_map(self) -> Dict[str, Dict[str, Any]]:
        return {str(item.get("package_id") or "").strip(): dict(item) for item in self.list_credit_packages()}

    def _get_credit_package(self, package_id: str) -> Dict[str, Any]:
        key = str(package_id or "").strip()
        package = self._credit_package_map().get(key)
        if not package:
            raise ValueError("package_not_found")
        return package

    def _wallet_row_to_dict(self, row: Optional[sqlite3.Row]) -> Dict[str, Any]:
        if not row:
            return {
                "buyer_id": "",
                "balance": 0,
                "granted_total": 0,
                "consumed_total": 0,
                "last_grant_at": "",
                "last_consume_at": "",
                "created_at": "",
                "updated_at": "",
            }
        return {
            "buyer_id": str(row["buyer_id"] or ""),
            "balance": int(row["balance"] or 0),
            "granted_total": int(row["granted_total"] or 0),
            "consumed_total": int(row["consumed_total"] or 0),
            "last_grant_at": str(row["last_grant_at"] or ""),
            "last_consume_at": str(row["last_consume_at"] or ""),
            "created_at": str(row["created_at"] or ""),
            "updated_at": str(row["updated_at"] or ""),
        }

    def _ensure_wallet_row(self, conn: sqlite3.Connection, buyer_id: str) -> Dict[str, Any]:
        bid = str(buyer_id or "").strip()
        if not bid:
            raise ValueError("buyer_id_required")
        row = conn.execute(
            """
            SELECT buyer_id, balance, granted_total, consumed_total, last_grant_at, last_consume_at, created_at, updated_at
            FROM wallets WHERE buyer_id = ?
            """,
            (bid,),
        ).fetchone()
        if row:
            return self._wallet_row_to_dict(row)

        now = _iso_now()
        conn.execute(
            """
            INSERT INTO wallets(
                buyer_id, balance, granted_total, consumed_total, last_grant_at, last_consume_at, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (bid, 0, 0, 0, "", "", now, now),
        )
        row = conn.execute(
            """
            SELECT buyer_id, balance, granted_total, consumed_total, last_grant_at, last_consume_at, created_at, updated_at
            FROM wallets WHERE buyer_id = ?
            """,
            (bid,),
        ).fetchone()
        return self._wallet_row_to_dict(row)

    def _append_credit_ledger(
        self,
        conn: sqlite3.Connection,
        buyer_id: str,
        direction: str,
        amount: int,
        balance_after: int,
        action: str,
        order_id: str = "",
        access_code: str = "",
        package_id: str = "",
        note: str = "",
        meta: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        ledger_id = self._new_id("ledger")
        created_at = _iso_now()
        conn.execute(
            """
            INSERT INTO credit_ledger(
                ledger_id, buyer_id, order_id, access_code, direction, amount, balance_after,
                action, package_id, note, meta_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                ledger_id,
                str(buyer_id or "").strip(),
                str(order_id or "").strip(),
                str(access_code or "").strip().upper(),
                str(direction or "").strip(),
                int(amount or 0),
                int(balance_after or 0),
                str(action or "").strip(),
                str(package_id or "").strip(),
                str(note or "").strip(),
                _json_dump(meta or {}),
                created_at,
            ),
        )
        row = conn.execute(
            """
            SELECT ledger_id, buyer_id, order_id, access_code, direction, amount, balance_after, action, package_id, note, meta_json, created_at
            FROM credit_ledger WHERE ledger_id = ?
            """,
            (ledger_id,),
        ).fetchone()
        payload = dict(row or {})
        payload["meta"] = _json_load(payload.pop("meta_json", ""))
        return payload

    def _find_buyer_account(
        self,
        conn: sqlite3.Connection,
        email: str = "",
        phone: str = "",
    ) -> Optional[sqlite3.Row]:
        normalized_email = str(email or "").strip().lower()
        normalized_phone = str(phone or "").strip()
        if normalized_email:
            row = conn.execute(
                """
                SELECT buyer_id, name, phone, email, access_code, expires_at, status
                FROM buyers WHERE lower(email) = lower(?) ORDER BY created_at DESC LIMIT 1
                """,
                (normalized_email,),
            ).fetchone()
            if row:
                return row
        if normalized_phone:
            row = conn.execute(
                """
                SELECT buyer_id, name, phone, email, access_code, expires_at, status
                FROM buyers WHERE phone = ? ORDER BY created_at DESC LIMIT 1
                """,
                (normalized_phone,),
            ).fetchone()
            if row:
                return row
        return None

    def _buyer_current_access_code(self, conn: sqlite3.Connection, buyer_id: str) -> str:
        bid = str(buyer_id or "").strip()
        if not bid:
            return ""
        row = conn.execute("SELECT access_code FROM buyers WHERE buyer_id = ? LIMIT 1", (bid,)).fetchone()
        code = str((row["access_code"] if row else "") or "").strip().upper()
        if code:
            return code
        row = conn.execute(
            """
            SELECT code FROM access_codes
            WHERE buyer_id = ?
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (bid,),
        ).fetchone()
        return str((row["code"] if row else "") or "").strip().upper()

    def _ensure_web_account(
        self,
        conn: sqlite3.Connection,
        name: str = "",
        email: str = "",
        phone: str = "",
        source: str = "web",
        channel: str = "web",
        duration_days: int = 365,
    ) -> Dict[str, str]:
        normalized_email = str(email or "").strip().lower()
        normalized_phone = str(phone or "").strip()
        row = self._find_buyer_account(conn, email=normalized_email, phone=normalized_phone)
        expires_at = _to_iso_days(duration_days)
        now = _iso_now()
        if row:
            buyer_id = str(row["buyer_id"] or "").strip()
            access_code = self._buyer_current_access_code(conn, buyer_id)
            if not access_code:
                access_code = self._unique_code(conn)
                conn.execute(
                    """
                    INSERT INTO access_codes(
                        code, buyer_id, order_id, label, status, max_uses, used_count, expires_at, activated_at, last_used_at, note, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        access_code,
                        buyer_id,
                        "",
                        "网站账户访问码",
                        "active",
                        999999,
                        0,
                        expires_at,
                        "",
                        "",
                        "",
                        now,
                    ),
                )
            conn.execute(
                """
                UPDATE buyers
                SET name = ?, phone = ?, email = ?, source = ?, channel = ?, status = ?, access_code = ?, expires_at = ?
                WHERE buyer_id = ?
                """,
                (
                    str(name or row["name"] or "").strip(),
                    normalized_phone or str(row["phone"] or "").strip(),
                    normalized_email or str(row["email"] or "").strip().lower(),
                    str(source or "").strip() or "web",
                    str(channel or "").strip() or "web",
                    "active",
                    access_code,
                    expires_at,
                    buyer_id,
                ),
            )
            conn.execute(
                """
                UPDATE access_codes
                SET status = ?, expires_at = ?, max_uses = ?
                WHERE code = ?
                """,
                ("active", expires_at, 999999, access_code),
            )
            return {"buyer_id": buyer_id, "access_code": access_code}

        buyer_id = self._new_id("buyer")
        access_code = self._unique_code(conn)
        conn.execute(
            """
            INSERT INTO buyers(
                buyer_id, name, phone, email, source, channel, status, note, access_code, created_at, expires_at, last_active_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                buyer_id,
                str(name or "").strip(),
                normalized_phone,
                normalized_email,
                str(source or "").strip() or "web",
                str(channel or "").strip() or "web",
                "active",
                "",
                access_code,
                now,
                expires_at,
                "",
            ),
        )
        conn.execute(
            """
            INSERT INTO access_codes(
                code, buyer_id, order_id, label, status, max_uses, used_count, expires_at, activated_at, last_used_at, note, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                access_code,
                buyer_id,
                "",
                "网站账户访问码",
                "active",
                999999,
                0,
                expires_at,
                "",
                "",
                "",
                now,
            ),
        )
        return {"buyer_id": buyer_id, "access_code": access_code}

    def _grant_order_credits_if_needed(self, conn: sqlite3.Connection, order_id: str) -> Dict[str, Any]:
        oid = str(order_id or "").strip()
        if not oid:
            raise ValueError("order_id_required")
        row = conn.execute(
            """
            SELECT order_id, buyer_id, access_code, payment_status, delivery_status, credits, package_id, wallet_granted_at
            FROM orders WHERE order_id = ?
            """,
            (oid,),
        ).fetchone()
        if not row:
            raise ValueError("order_not_found")

        order = dict(row or {})
        if str(order.get("payment_status") or "").strip() != "paid":
            return order
        if str(order.get("wallet_granted_at") or "").strip():
            return order
        credits = int(order.get("credits") or 0)
        if credits <= 0:
            return order

        wallet = self._ensure_wallet_row(conn, str(order.get("buyer_id") or "").strip())
        balance_after = int(wallet.get("balance") or 0) + credits
        now = _iso_now()
        conn.execute(
            """
            UPDATE wallets
            SET balance = ?, granted_total = ?, last_grant_at = ?, updated_at = ?
            WHERE buyer_id = ?
            """,
            (
                balance_after,
                int(wallet.get("granted_total") or 0) + credits,
                now,
                now,
                str(order.get("buyer_id") or "").strip(),
            ),
        )
        self._append_credit_ledger(
            conn,
            buyer_id=str(order.get("buyer_id") or "").strip(),
            order_id=oid,
            access_code=str(order.get("access_code") or "").strip().upper(),
            direction="credit",
            amount=credits,
            balance_after=balance_after,
            action="credit_checkout",
            package_id=str(order.get("package_id") or "").strip(),
            note=f"订单 {oid} 到账",
            meta={"source": "order_payment"},
        )
        conn.execute(
            """
            UPDATE orders
            SET wallet_granted_at = ?, updated_at = ?, delivery_status = ?
            WHERE order_id = ?
            """,
            (
                now,
                now,
                str(order.get("delivery_status") or "").strip() or "delivered",
                oid,
            ),
        )
        out = conn.execute(
            """
            SELECT order_id, buyer_id, product_name, amount, currency, payment_channel, payment_status,
                   delivery_status, access_code, note, created_at, updated_at, package_id, credits, wallet_granted_at, activation_mode
            FROM orders WHERE order_id = ?
            """,
            (oid,),
        ).fetchone()
        return dict(out or {})

    def create_credit_checkout(
        self,
        package_id: str,
        email: str = "",
        name: str = "",
        phone: str = "",
        source: str = "web",
        channel: str = "web",
        payment_channel: str = "manual_web",
        note: str = "",
    ) -> Dict[str, Any]:
        package = self._get_credit_package(package_id)
        normalized_email = str(email or "").strip().lower()
        normalized_phone = str(phone or "").strip()
        if not normalized_email and not normalized_phone:
            raise ValueError("email_or_phone_required")

        auto_activate = str(package.get("checkout_mode") or "").strip() == "instant"
        if package.get("trial_only"):
            auto_activate = True

        with self._lock:
            conn = self._conn()
            try:
                account = self._ensure_web_account(
                    conn,
                    name=name,
                    email=normalized_email,
                    phone=normalized_phone,
                    source=source,
                    channel=channel,
                    duration_days=365,
                )
                buyer_id = str(account.get("buyer_id") or "").strip()
                access_code = str(account.get("access_code") or "").strip().upper()

                if package.get("trial_only"):
                    existing_trial = conn.execute(
                        """
                        SELECT order_id FROM orders
                        WHERE buyer_id = ? AND package_id = ?
                        LIMIT 1
                        """,
                        (buyer_id, str(package.get("package_id") or "").strip()),
                    ).fetchone()
                    if existing_trial:
                        raise ValueError("trial_already_claimed")

                order_id = self._new_id("order")
                now = _iso_now()
                payment_status = "paid" if auto_activate else "pending"
                delivery_status = "delivered" if auto_activate else "pending"
                activation_mode = "instant" if auto_activate else "manual_review"
                credits = int(package.get("credits") or 0)
                conn.execute(
                    """
                    INSERT INTO orders(
                        order_id, buyer_id, product_name, amount, currency, payment_channel, payment_status,
                        delivery_status, access_code, note, created_at, updated_at, package_id, credits, wallet_granted_at, activation_mode
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        order_id,
                        buyer_id,
                        f"{str(package.get('name') or '').strip()} Credits",
                        float(package.get("price") or 0),
                        str(package.get("currency") or "CNY").strip() or "CNY",
                        str(payment_channel or "").strip() or "manual_web",
                        payment_status,
                        delivery_status,
                        access_code,
                        str(note or "").strip(),
                        now,
                        now,
                        str(package.get("package_id") or "").strip(),
                        credits,
                        "",
                        activation_mode,
                    ),
                )
                conn.execute(
                    """
                    UPDATE access_codes
                    SET order_id = ?, status = ?, expires_at = ?, max_uses = ?
                    WHERE code = ?
                    """,
                    (order_id, "active", _to_iso_days(365), 999999, access_code),
                )
                conn.execute(
                    """
                    UPDATE buyers
                    SET access_code = ?, source = ?, channel = ?, status = ?, expires_at = ?
                    WHERE buyer_id = ?
                    """,
                    (access_code, str(source or "").strip() or "web", str(channel or "").strip() or "web", "active", _to_iso_days(365), buyer_id),
                )
                self._ensure_wallet_row(conn, buyer_id)
                if auto_activate:
                    order = self._grant_order_credits_if_needed(conn, order_id)
                else:
                    order = conn.execute(
                        """
                        SELECT order_id, buyer_id, product_name, amount, currency, payment_channel, payment_status,
                               delivery_status, access_code, note, created_at, updated_at, package_id, credits, wallet_granted_at, activation_mode
                        FROM orders WHERE order_id = ?
                        """,
                        (order_id,),
                    ).fetchone()
                    order = dict(order or {})
                conn.commit()
                wallet = self.get_wallet_by_buyer_id(buyer_id)
                public_access_code = access_code if auto_activate else ""
                activation_instructions = (
                    "试用包已自动开通，可以直接使用访问码登录。"
                    if auto_activate
                    else "当前订单只用于对账。确认收款并到账后，系统才会发放可兑换的访问码。"
                )
                return {
                    "account": {
                        "buyer_id": buyer_id,
                        "access_code": public_access_code,
                        "name": str(name or "").strip(),
                        "email": normalized_email,
                        "phone": normalized_phone,
                    },
                    "package": package,
                    "order": order,
                    "wallet": wallet,
                    "checkout_mode": activation_mode,
                    "redeem_ready": auto_activate,
                    "redeem_code": public_access_code,
                    "activation_instructions": activation_instructions,
                    "auto_logged_access_code": public_access_code,
                }
            finally:
                conn.close()

    def get_wallet_by_buyer_id(self, buyer_id: str) -> Dict[str, Any]:
        bid = str(buyer_id or "").strip()
        if not bid:
            raise ValueError("buyer_id_required")
        with self._lock:
            conn = self._conn()
            try:
                wallet = self._ensure_wallet_row(conn, bid)
                row = conn.execute(
                    """
                    SELECT buyer_id, name, phone, email, access_code, expires_at, status
                    FROM buyers WHERE buyer_id = ?
                    """,
                    (bid,),
                ).fetchone()
                buyer = dict(row or {})
                latest_order = conn.execute(
                    """
                    SELECT order_id, product_name, amount, currency, payment_channel, payment_status,
                           delivery_status, access_code, note, created_at, updated_at, package_id, credits, wallet_granted_at, activation_mode
                    FROM orders WHERE buyer_id = ?
                    ORDER BY created_at DESC
                    LIMIT 1
                    """,
                    (bid,),
                ).fetchone()
                return {
                    "wallet": wallet,
                    "buyer": buyer,
                    "latest_order": dict(latest_order or {}),
                }
            finally:
                conn.close()

    def _direct_wallet_payload(self, access_code: str) -> Dict[str, Any]:
        code = str(access_code or "").strip().upper() or self._direct_access_code()
        return {
            "wallet": {
                "buyer_id": f"buyer_{code.lower()}",
                "balance": 999999,
                "granted_total": 999999,
                "consumed_total": 0,
                "last_grant_at": "",
                "last_consume_at": "",
                "created_at": "",
                "updated_at": "",
            },
            "buyer": {
                "buyer_id": f"buyer_{code.lower()}",
                "name": f"Buyer {code}",
                "access_code": code,
                "email": "",
                "phone": "",
                "status": "active",
            },
            "latest_order": {
                "order_id": "",
                "product_name": "AI Job Helper Direct",
                "payment_status": "paid",
                "delivery_status": "delivered",
                "package_id": "internal_direct",
                "credits": 999999,
                "activation_mode": "instant",
            },
        }

    def get_wallet_by_access_code(self, access_code: str) -> Dict[str, Any]:
        normalized_code = str(access_code or "").strip().upper()
        if not normalized_code:
            raise ValueError("access_code_required")
        if normalized_code == self._direct_access_code():
            return self._direct_wallet_payload(normalized_code)
        redeem = self.redeem_access_code(normalized_code, consume_use=False)
        buyer_id = str(redeem.get("buyer_id") or "").strip()
        payload = self.get_wallet_by_buyer_id(buyer_id)
        payload["access_code"] = normalized_code
        return payload

    def get_checkout_status(
        self,
        order_id: str = "",
        access_code: str = "",
    ) -> Dict[str, Any]:
        oid = str(order_id or "").strip()
        normalized_code = str(access_code or "").strip().upper()
        if not oid and not normalized_code:
            raise ValueError("order_id_or_access_code_required")
        if normalized_code == self._direct_access_code():
            payload = self._direct_wallet_payload(normalized_code)
            payload["access_code"] = normalized_code
            payload["order"] = payload.get("latest_order") or {}
            payload["status_text"] = "direct_access_active"
            return payload

        with self._lock:
            conn = self._conn()
            try:
                if oid:
                    order = conn.execute(
                        """
                        SELECT order_id, buyer_id, product_name, amount, currency, payment_channel, payment_status,
                               delivery_status, access_code, note, created_at, updated_at, package_id, credits, wallet_granted_at, activation_mode
                        FROM orders WHERE order_id = ?
                        LIMIT 1
                        """,
                        (oid,),
                    ).fetchone()
                    if not order:
                        raise ValueError("order_not_found")
                    order_dict = dict(order or {})
                    buyer_id = str(order_dict.get("buyer_id") or "").strip()
                    normalized_code = str(order_dict.get("access_code") or normalized_code).strip().upper()
                else:
                    redeem = self.redeem_access_code(normalized_code, consume_use=False)
                    buyer_id = str(redeem.get("buyer_id") or "").strip()
                    order = conn.execute(
                        """
                        SELECT order_id, buyer_id, product_name, amount, currency, payment_channel, payment_status,
                               delivery_status, access_code, note, created_at, updated_at, package_id, credits, wallet_granted_at, activation_mode
                        FROM orders WHERE buyer_id = ?
                        ORDER BY created_at DESC
                        LIMIT 1
                        """,
                        (buyer_id,),
                    ).fetchone()
                    if not order:
                        raise ValueError("order_not_found")
                    order_dict = dict(order or {})
                    oid = str(order_dict.get("order_id") or "").strip()

                if str(order_dict.get("payment_status") or "").strip() == "paid" and not str(order_dict.get("wallet_granted_at") or "").strip():
                    order_dict = self._grant_order_credits_if_needed(conn, oid)
                    conn.commit()

                wallet_payload = self.get_wallet_by_buyer_id(buyer_id)
                payment_status = str(order_dict.get("payment_status") or "").strip()
                wallet_balance = int(((wallet_payload.get("wallet") or {}).get("balance")) or 0)
                if payment_status == "paid" and wallet_balance > 0:
                    status_text = "paid_and_credited"
                elif payment_status == "paid":
                    status_text = "paid_pending_credit"
                else:
                    status_text = "pending_payment"
                reveal_access_code = status_text == "paid_and_credited" or str(order_dict.get("activation_mode") or "").strip() == "instant"
                public_access_code = normalized_code if reveal_access_code else ""
                activation_instructions = (
                    "访问码已经生效，可以直接去兑换登录。"
                    if reveal_access_code
                    else "订单还没到账。先完成付款并等待确认，访问码确认后才会显示。"
                )
                proofs = self.list_payment_proofs(limit=10, order_id=oid or str(order_dict.get("order_id") or "").strip())
                return {
                    "order": order_dict,
                    "wallet": wallet_payload.get("wallet") or {},
                    "buyer": wallet_payload.get("buyer") or {},
                    "latest_order": wallet_payload.get("latest_order") or {},
                    "access_code": public_access_code,
                    "status_text": status_text,
                    "redeem_ready": reveal_access_code,
                    "activation_instructions": activation_instructions,
                    "payment_proofs": proofs,
                    "payment_proof_count": len(proofs),
                    "latest_payment_proof": proofs[0] if proofs else {},
                }
            finally:
                conn.close()

    def list_wallets(self, limit: int = 50, search: str = "") -> List[Dict[str, Any]]:
        n = max(1, min(int(limit or 50), 500))
        where_sql, params = self._buyer_search_where(search, alias="b")
        with self._lock:
            conn = self._conn()
            try:
                rows = conn.execute(
                    f"""
                    SELECT
                        b.buyer_id, b.name, b.phone, b.email, b.access_code, b.status, b.expires_at,
                        w.balance, w.granted_total, w.consumed_total, w.last_grant_at, w.last_consume_at, w.created_at, w.updated_at
                    FROM buyers b
                    LEFT JOIN wallets w ON w.buyer_id = b.buyer_id
                    {where_sql}
                    ORDER BY COALESCE(w.updated_at, b.created_at) DESC
                    LIMIT ?
                    """,
                    tuple(params + [n]),
                ).fetchall()
                out: List[Dict[str, Any]] = []
                for row in rows:
                    item = dict(row or {})
                    item["balance"] = int(item.get("balance") or 0)
                    item["granted_total"] = int(item.get("granted_total") or 0)
                    item["consumed_total"] = int(item.get("consumed_total") or 0)
                    out.append(item)
                return out
            finally:
                conn.close()

    def list_credit_ledger(self, limit: int = 50, search: str = "", buyer_id: str = "") -> List[Dict[str, Any]]:
        n = max(1, min(int(limit or 50), 500))
        q = str(search or "").strip()
        bid = str(buyer_id or "").strip()
        params: List[Any] = []
        clauses: List[str] = []
        if q:
            like = f"%{q}%"
            clauses.append("(l.ledger_id LIKE ? OR l.order_id LIKE ? OR l.access_code LIKE ? OR l.action LIKE ? OR b.email LIKE ? OR b.name LIKE ?)")
            params.extend([like, like, like, like, like, like])
        if bid:
            clauses.append("l.buyer_id = ?")
            params.append(bid)
        where_sql = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        with self._lock:
            conn = self._conn()
            try:
                rows = conn.execute(
                    f"""
                    SELECT
                        l.ledger_id, l.buyer_id, l.order_id, l.access_code, l.direction, l.amount, l.balance_after,
                        l.action, l.package_id, l.note, l.meta_json, l.created_at,
                        b.name, b.email, b.phone
                    FROM credit_ledger l
                    LEFT JOIN buyers b ON b.buyer_id = l.buyer_id
                    {where_sql}
                    ORDER BY l.created_at DESC
                    LIMIT ?
                    """,
                    tuple(params + [n]),
                ).fetchall()
                out: List[Dict[str, Any]] = []
                for row in rows:
                    item = dict(row or {})
                    item["meta"] = _json_load(item.pop("meta_json", ""))
                    out.append(item)
                return out
            finally:
                conn.close()

    def _find_credit_debit_for_resource_with_conn(
        self,
        conn: sqlite3.Connection,
        action: str,
        resource_id: str,
        access_code: str = "",
        buyer_id: str = "",
        resource_keys: Optional[List[str]] = None,
        scan_limit: int = 500,
    ) -> Dict[str, Any]:
        action_key = str(action or "").strip()
        wanted_resource = str(resource_id or "").strip()
        if not action_key or not wanted_resource:
            return {}
        normalized_code = str(access_code or "").strip().upper()
        resolved_buyer_id = str(buyer_id or "").strip()
        if not resolved_buyer_id and not normalized_code:
            return {}

        keys = [str(k).strip() for k in (resource_keys or ["resource_id", "job_id"]) if str(k).strip()]
        if "resource_id" not in keys:
            keys.insert(0, "resource_id")
        wanted_resource_low = wanted_resource.lower()

        clauses = ["direction = 'debit'", "action = ?"]
        params: List[Any] = [action_key]
        if resolved_buyer_id:
            clauses.append("buyer_id = ?")
            params.append(resolved_buyer_id)
        else:
            clauses.append("access_code = ?")
            params.append(normalized_code)
        where_sql = " AND ".join(clauses)
        rows = conn.execute(
            f"""
            SELECT
                ledger_id, buyer_id, order_id, access_code, direction, amount, balance_after,
                action, package_id, note, meta_json, created_at
            FROM credit_ledger
            WHERE {where_sql}
            ORDER BY created_at DESC
            LIMIT ?
            """,
            tuple(params + [max(20, min(int(scan_limit or 500), 3000))]),
        ).fetchall()
        for row in rows:
            item = dict(row or {})
            meta = _json_load(item.pop("meta_json", ""))
            meta_map = meta if isinstance(meta, dict) else {}
            item["meta"] = meta_map
            for key in keys:
                candidate = str(meta_map.get(key) or "").strip()
                if not candidate:
                    continue
                if candidate == wanted_resource or candidate.lower() == wanted_resource_low:
                    return item
        return {}

    def find_credit_debit_for_resource(
        self,
        action: str,
        resource_id: str,
        access_code: str = "",
        buyer_id: str = "",
        resource_keys: Optional[List[str]] = None,
        scan_limit: int = 500,
    ) -> Dict[str, Any]:
        """
        Return the latest debit ledger row for one logical resource (for idempotent charging).
        """
        action_key = str(action or "").strip()
        wanted_resource = str(resource_id or "").strip()
        if not action_key or not wanted_resource:
            return {}
        normalized_code = str(access_code or "").strip().upper()
        resolved_buyer_id = str(buyer_id or "").strip()
        if not resolved_buyer_id and normalized_code:
            try:
                redeem = self.redeem_access_code(normalized_code, consume_use=False)
                resolved_buyer_id = str(redeem.get("buyer_id") or "").strip()
            except Exception:
                resolved_buyer_id = ""
        if not resolved_buyer_id and not normalized_code:
            return {}

        with self._lock:
            conn = self._conn()
            try:
                return self._find_credit_debit_for_resource_with_conn(
                    conn=conn,
                    action=action_key,
                    resource_id=wanted_resource,
                    access_code=normalized_code,
                    buyer_id=resolved_buyer_id,
                    resource_keys=resource_keys,
                    scan_limit=scan_limit,
                )
            finally:
                conn.close()

    def payment_proof_storage_path(self, proof_id: str, original_name: str = "") -> str:
        safe_ext = os.path.splitext(str(original_name or "").strip())[1].lower()
        if safe_ext not in {".png", ".jpg", ".jpeg", ".webp", ".pdf"}:
            safe_ext = ".bin"
        return os.path.join(self.payment_proof_dir, f"{str(proof_id or '').strip()}{safe_ext}")

    def _payment_proof_row_to_dict(self, row: Optional[sqlite3.Row]) -> Dict[str, Any]:
        item = dict(row or {})
        if not item:
            return {}
        return {
            "proof_id": str(item.get("proof_id") or ""),
            "buyer_id": str(item.get("buyer_id") or ""),
            "order_id": str(item.get("order_id") or ""),
            "access_code": str(item.get("access_code") or "").strip().upper(),
            "status": str(item.get("status") or ""),
            "amount": float(item.get("amount") or 0),
            "note": str(item.get("note") or ""),
            "file_name": str(item.get("file_name") or ""),
            "mime_type": str(item.get("mime_type") or ""),
            "file_path": str(item.get("file_path") or ""),
            "reviewed_note": str(item.get("reviewed_note") or ""),
            "created_at": str(item.get("created_at") or ""),
            "updated_at": str(item.get("updated_at") or ""),
        }

    def create_payment_proof(
        self,
        access_code: str = "",
        order_id: str = "",
        amount: float = 0.0,
        note: str = "",
        file_name: str = "",
        mime_type: str = "",
        source_path: str = "",
    ) -> Dict[str, Any]:
        normalized_code = str(access_code or "").strip().upper()
        oid = str(order_id or "").strip()
        if not normalized_code and not oid:
            raise ValueError("order_id_or_access_code_required")
        source = str(source_path or "").strip()
        if not source or not os.path.exists(source):
            raise ValueError("proof_file_missing")

        with self._lock:
            conn = self._conn()
            try:
                status_payload = self.get_checkout_status(order_id=oid, access_code=normalized_code)
                buyer = status_payload.get("buyer") if isinstance(status_payload, dict) else {}
                order = status_payload.get("order") if isinstance(status_payload, dict) else {}
                buyer_id = str((buyer or {}).get("buyer_id") or "").strip()
                resolved_order_id = str((order or {}).get("order_id") or oid).strip()
                resolved_code = str(status_payload.get("access_code") or normalized_code).strip().upper()
                proof_id = self._new_id("proof")
                final_path = self.payment_proof_storage_path(proof_id, file_name)
                os.makedirs(os.path.dirname(final_path) or self.payment_proof_dir, exist_ok=True)
                shutil.copyfile(source, final_path)
                now = _iso_now()
                conn.execute(
                    """
                    INSERT INTO payment_proofs(
                        proof_id, buyer_id, order_id, access_code, status, amount, note,
                        file_name, mime_type, file_path, reviewed_note, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        proof_id,
                        buyer_id,
                        resolved_order_id,
                        resolved_code,
                        "submitted",
                        float(amount or 0),
                        str(note or "").strip(),
                        str(file_name or "").strip(),
                        str(mime_type or "").strip(),
                        final_path,
                        "",
                        now,
                        now,
                    ),
                )
                conn.commit()
                row = conn.execute(
                    """
                    SELECT proof_id, buyer_id, order_id, access_code, status, amount, note, file_name, mime_type, file_path, reviewed_note, created_at, updated_at
                    FROM payment_proofs WHERE proof_id = ?
                    """,
                    (proof_id,),
                ).fetchone()
                return self._payment_proof_row_to_dict(row)
            finally:
                conn.close()

    def get_payment_proof(self, proof_id: str) -> Dict[str, Any]:
        pid = str(proof_id or "").strip()
        if not pid:
            raise ValueError("proof_id_required")
        with self._lock:
            conn = self._conn()
            try:
                row = conn.execute(
                    """
                    SELECT proof_id, buyer_id, order_id, access_code, status, amount, note, file_name, mime_type, file_path, reviewed_note, created_at, updated_at
                    FROM payment_proofs WHERE proof_id = ?
                    """,
                    (pid,),
                ).fetchone()
                if not row:
                    raise ValueError("payment_proof_not_found")
                return self._payment_proof_row_to_dict(row)
            finally:
                conn.close()

    def list_payment_proofs(self, limit: int = 50, search: str = "", status: str = "", buyer_id: str = "", order_id: str = "") -> List[Dict[str, Any]]:
        n = max(1, min(int(limit or 50), 500))
        q = str(search or "").strip()
        wanted_status = str(status or "").strip()
        bid = str(buyer_id or "").strip()
        oid = str(order_id or "").strip()
        clauses: List[str] = []
        params: List[Any] = []
        if q:
            like = f"%{q}%"
            clauses.append("(p.proof_id LIKE ? OR p.order_id LIKE ? OR p.access_code LIKE ? OR p.note LIKE ? OR b.email LIKE ? OR b.name LIKE ?)")
            params.extend([like, like, like, like, like, like])
        if wanted_status:
            clauses.append("p.status = ?")
            params.append(wanted_status)
        if bid:
            clauses.append("p.buyer_id = ?")
            params.append(bid)
        if oid:
            clauses.append("p.order_id = ?")
            params.append(oid)
        where_sql = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        with self._lock:
            conn = self._conn()
            try:
                rows = conn.execute(
                    f"""
                    SELECT
                        p.proof_id, p.buyer_id, p.order_id, p.access_code, p.status, p.amount, p.note,
                        p.file_name, p.mime_type, p.file_path, p.reviewed_note, p.created_at, p.updated_at,
                        b.name, b.email
                    FROM payment_proofs p
                    LEFT JOIN buyers b ON b.buyer_id = p.buyer_id
                    {where_sql}
                    ORDER BY p.created_at DESC
                    LIMIT ?
                    """,
                    tuple(params + [n]),
                ).fetchall()
                out: List[Dict[str, Any]] = []
                for row in rows:
                    item = self._payment_proof_row_to_dict(row)
                    item["buyer_name"] = str(row["name"] or "")
                    item["buyer_email"] = str(row["email"] or "")
                    out.append(item)
                return out
            finally:
                conn.close()

    def update_payment_proof(self, proof_id: str, patch: Dict[str, Any]) -> Dict[str, Any]:
        pid = str(proof_id or "").strip()
        if not pid:
            raise ValueError("proof_id_required")
        update_map: Dict[str, Any] = {}
        for key in ("status", "note", "reviewed_note"):
            value = str((patch or {}).get(key) or "").strip()
            if value:
                update_map[key] = value
        if (patch or {}).get("amount") is not None:
            try:
                update_map["amount"] = float((patch or {}).get("amount") or 0)
            except Exception:
                pass
        update_map["updated_at"] = _iso_now()
        with self._lock:
            conn = self._conn()
            try:
                existing = conn.execute("SELECT proof_id FROM payment_proofs WHERE proof_id = ?", (pid,)).fetchone()
                if not existing:
                    raise ValueError("payment_proof_not_found")
                sets = ", ".join([f"{key} = ?" for key in update_map.keys()])
                conn.execute(
                    f"UPDATE payment_proofs SET {sets} WHERE proof_id = ?",
                    tuple(update_map.values()) + (pid,),
                )
                conn.commit()
                row = conn.execute(
                    """
                    SELECT proof_id, buyer_id, order_id, access_code, status, amount, note, file_name, mime_type, file_path, reviewed_note, created_at, updated_at
                    FROM payment_proofs WHERE proof_id = ?
                    """,
                    (pid,),
                ).fetchone()
                return self._payment_proof_row_to_dict(row)
            finally:
                conn.close()

    def consume_credits(
        self,
        amount: int,
        action: str,
        access_code: str = "",
        buyer_id: str = "",
        note: str = "",
        order_id: str = "",
        meta: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        needed = max(0, int(amount or 0))
        normalized_code = str(access_code or "").strip().upper()
        if normalized_code == self._direct_access_code():
            return {
                "ok": True,
                "skipped": True,
                "reason": "direct_access_code",
                "wallet": self._direct_wallet_payload(normalized_code)["wallet"],
            }
        if needed <= 0:
            if normalized_code:
                return {"ok": True, "wallet": self.get_wallet_by_access_code(normalized_code).get("wallet") or {}}
            if buyer_id:
                return {"ok": True, "wallet": self.get_wallet_by_buyer_id(buyer_id).get("wallet") or {}}
            raise ValueError("buyer_id_or_access_code_required")

        resolved_buyer_id = str(buyer_id or "").strip()
        resolved_access_code = normalized_code
        if not resolved_buyer_id:
            if not resolved_access_code:
                raise ValueError("buyer_id_or_access_code_required")
            redeem = self.redeem_access_code(resolved_access_code, consume_use=False)
            resolved_buyer_id = str(redeem.get("buyer_id") or "").strip()
        with self._lock:
            conn = self._conn()
            try:
                wallet = self._ensure_wallet_row(conn, resolved_buyer_id)
                balance = int(wallet.get("balance") or 0)
                if balance < needed:
                    return {
                        "ok": False,
                        "error": "insufficient_credits",
                        "required": needed,
                        "balance": balance,
                        "wallet": wallet,
                    }
                balance_after = balance - needed
                now = _iso_now()
                conn.execute(
                    """
                    UPDATE wallets
                    SET balance = ?, consumed_total = ?, last_consume_at = ?, updated_at = ?
                    WHERE buyer_id = ?
                    """,
                    (
                        balance_after,
                        int(wallet.get("consumed_total") or 0) + needed,
                        now,
                        now,
                        resolved_buyer_id,
                    ),
                )
                ledger = self._append_credit_ledger(
                    conn,
                    buyer_id=resolved_buyer_id,
                    order_id=order_id,
                    access_code=resolved_access_code,
                    direction="debit",
                    amount=needed,
                    balance_after=balance_after,
                    action=action,
                    package_id="",
                    note=note,
                    meta=meta or {},
                )
                conn.commit()
                refreshed = self._ensure_wallet_row(conn, resolved_buyer_id)
                return {"ok": True, "wallet": refreshed, "ledger": ledger, "required": needed, "balance": balance_after}
            finally:
                conn.close()

    def consume_credits_once_for_resource(
        self,
        amount: int,
        action: str,
        resource_id: str,
        access_code: str = "",
        buyer_id: str = "",
        note: str = "",
        order_id: str = "",
        meta: Optional[Dict[str, Any]] = None,
        resource_keys: Optional[List[str]] = None,
        scan_limit: int = 500,
    ) -> Dict[str, Any]:
        """
        Idempotent debit for one logical resource.
        The existing debit lookup and consume happen under the same lock/connection.
        """
        needed = max(0, int(amount or 0))
        action_key = str(action or "").strip()
        wanted_resource = str(resource_id or "").strip()
        if not action_key:
            raise ValueError("action_required")
        if not wanted_resource:
            raise ValueError("resource_id_required")

        normalized_code = str(access_code or "").strip().upper()
        if normalized_code == self._direct_access_code():
            return {
                "ok": True,
                "skipped": True,
                "reason": "direct_access_code",
                "resource_id": wanted_resource,
                "wallet": self._direct_wallet_payload(normalized_code)["wallet"],
            }

        if needed <= 0:
            if normalized_code:
                wallet = self.get_wallet_by_access_code(normalized_code).get("wallet") or {}
                return {"ok": True, "skipped": True, "reason": "zero_amount", "resource_id": wanted_resource, "wallet": wallet}
            if buyer_id:
                wallet = self.get_wallet_by_buyer_id(buyer_id).get("wallet") or {}
                return {"ok": True, "skipped": True, "reason": "zero_amount", "resource_id": wanted_resource, "wallet": wallet}
            raise ValueError("buyer_id_or_access_code_required")

        resolved_buyer_id = str(buyer_id or "").strip()
        resolved_access_code = normalized_code
        if not resolved_buyer_id:
            if not resolved_access_code:
                raise ValueError("buyer_id_or_access_code_required")
            redeem = self.redeem_access_code(resolved_access_code, consume_use=False)
            resolved_buyer_id = str(redeem.get("buyer_id") or "").strip()

        with self._lock:
            conn = self._conn()
            try:
                wallet = self._ensure_wallet_row(conn, resolved_buyer_id)
                balance = int(wallet.get("balance") or 0)
                existing = self._find_credit_debit_for_resource_with_conn(
                    conn=conn,
                    action=action_key,
                    resource_id=wanted_resource,
                    access_code=resolved_access_code,
                    buyer_id=resolved_buyer_id,
                    resource_keys=resource_keys,
                    scan_limit=scan_limit,
                )
                if existing:
                    return {
                        "ok": True,
                        "skipped": True,
                        "reason": "already_charged_for_resource",
                        "resource_id": wanted_resource,
                        "wallet": wallet,
                        "ledger": existing,
                        "ledger_id": str(existing.get("ledger_id") or ""),
                        "required": needed,
                        "balance": balance,
                    }

                if balance < needed:
                    return {
                        "ok": False,
                        "error": "insufficient_credits",
                        "required": needed,
                        "balance": balance,
                        "wallet": wallet,
                    }

                balance_after = balance - needed
                now = _iso_now()
                conn.execute(
                    """
                    UPDATE wallets
                    SET balance = ?, consumed_total = ?, last_consume_at = ?, updated_at = ?
                    WHERE buyer_id = ?
                    """,
                    (
                        balance_after,
                        int(wallet.get("consumed_total") or 0) + needed,
                        now,
                        now,
                        resolved_buyer_id,
                    ),
                )
                meta_map = dict(meta or {}) if isinstance(meta, dict) else {}
                if wanted_resource:
                    meta_map.setdefault("resource_id", wanted_resource)
                    meta_map.setdefault("job_id", wanted_resource)
                ledger = self._append_credit_ledger(
                    conn,
                    buyer_id=resolved_buyer_id,
                    order_id=order_id,
                    access_code=resolved_access_code,
                    direction="debit",
                    amount=needed,
                    balance_after=balance_after,
                    action=action_key,
                    package_id="",
                    note=note,
                    meta=meta_map,
                )
                conn.commit()
                refreshed = self._ensure_wallet_row(conn, resolved_buyer_id)
                return {
                    "ok": True,
                    "wallet": refreshed,
                    "ledger": ledger,
                    "ledger_id": str((ledger or {}).get("ledger_id") or ""),
                    "required": needed,
                    "balance": balance_after,
                    "resource_id": wanted_resource,
                }
            except Exception:
                # Explicit rollback guards against partial state on any mid-transaction failure.
                try:
                    conn.rollback()
                except Exception:
                    pass
                raise
            finally:
                conn.close()

    def create_bundle(
        self,
        name: str = "",
        phone: str = "",
        email: str = "",
        source: str = "xianyu",
        channel: str = "xianyu",
        product_name: str = "AI Job Helper",
        amount: float = 0.0,
        currency: str = "CNY",
        payment_channel: str = "xianyu",
        payment_status: str = "paid",
        delivery_status: str = "delivered",
        duration_days: int = 30,
        max_uses: int = 3,
        label: str = "默认访问码",
        note: str = "",
    ) -> Dict[str, Any]:
        created_at = _iso_now()
        expires_at = _to_iso_days(duration_days)
        buyer_id = self._new_id("buyer")
        order_id = self._new_id("order")

        with self._lock:
            conn = self._conn()
            try:
                access_code = self._unique_code(conn)
                conn.execute(
                    """
                    INSERT INTO buyers(
                        buyer_id, name, phone, email, source, channel, status, note, access_code, created_at, expires_at, last_active_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        buyer_id,
                        str(name or "").strip(),
                        str(phone or "").strip(),
                        str(email or "").strip().lower(),
                        str(source or "").strip() or "xianyu",
                        str(channel or "").strip() or "xianyu",
                        "active",
                        str(note or "").strip(),
                        access_code,
                        created_at,
                        expires_at,
                        "",
                    ),
                )
                conn.execute(
                    """
                    INSERT INTO orders(
                        order_id, buyer_id, product_name, amount, currency, payment_channel, payment_status, delivery_status, access_code, note, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        order_id,
                        buyer_id,
                        str(product_name or "").strip() or "AI Job Helper",
                        float(amount or 0),
                        str(currency or "CNY").strip() or "CNY",
                        str(payment_channel or "").strip() or "xianyu",
                        str(payment_status or "").strip() or "paid",
                        str(delivery_status or "").strip() or "delivered",
                        access_code,
                        str(note or "").strip(),
                        created_at,
                        created_at,
                    ),
                )
                conn.execute(
                    """
                    INSERT INTO access_codes(
                        code, buyer_id, order_id, label, status, max_uses, used_count, expires_at, activated_at, last_used_at, note, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        access_code,
                        buyer_id,
                        order_id,
                        str(label or "").strip() or "默认访问码",
                        "active",
                        max(1, int(max_uses or 3)),
                        0,
                        expires_at,
                        "",
                        "",
                        str(note or "").strip(),
                        created_at,
                    ),
                )
                conn.commit()
                row = conn.execute(
                    """
                    SELECT
                        b.buyer_id, b.name, b.phone, b.email, b.source, b.channel,
                        b.status AS buyer_status, b.note AS buyer_note, b.created_at AS buyer_created_at,
                        b.expires_at AS buyer_expires_at, b.last_active_at,
                        o.order_id, o.product_name, o.amount, o.currency, o.payment_channel,
                        o.payment_status, o.delivery_status, o.note AS order_note,
                        o.created_at AS order_created_at, o.updated_at AS order_updated_at,
                        a.code AS access_code, a.label AS access_label, a.status AS access_status,
                        a.max_uses, a.used_count, a.expires_at AS code_expires_at,
                        a.activated_at, a.last_used_at, a.note AS access_note
                    FROM buyers b
                    LEFT JOIN orders o ON o.buyer_id = b.buyer_id
                    LEFT JOIN access_codes a ON a.buyer_id = b.buyer_id
                    WHERE b.buyer_id = ?
                    ORDER BY o.created_at DESC, a.created_at DESC
                    LIMIT 1
                    """,
                    (buyer_id,),
                ).fetchone()
                return self._join_bundle_row(row)
            finally:
                conn.close()

    def list_bundles(self, limit: int = 50, search: str = "") -> List[Dict[str, Any]]:
        n = max(1, min(int(limit or 50), 500))
        where_sql, params = self._buyer_search_where(search, alias="b")
        with self._lock:
            conn = self._conn()
            try:
                rows = conn.execute(
                    f"""
                    SELECT
                        b.buyer_id, b.name, b.phone, b.email, b.source, b.channel,
                        b.status AS buyer_status, b.note AS buyer_note, b.created_at AS buyer_created_at,
                        b.expires_at AS buyer_expires_at, b.last_active_at,
                        o.order_id, o.product_name, o.amount, o.currency, o.payment_channel,
                        o.payment_status, o.delivery_status, o.note AS order_note,
                        o.created_at AS order_created_at, o.updated_at AS order_updated_at,
                        a.code AS access_code, a.label AS access_label, a.status AS access_status,
                        a.max_uses, a.used_count, a.expires_at AS code_expires_at,
                        a.activated_at, a.last_used_at, a.note AS access_note
                    FROM buyers b
                    LEFT JOIN orders o ON o.buyer_id = b.buyer_id
                    LEFT JOIN access_codes a ON a.buyer_id = b.buyer_id AND a.code = b.access_code
                    {where_sql}
                    ORDER BY b.created_at DESC
                    LIMIT ?
                    """,
                    tuple(params + [n]),
                ).fetchall()
                return [self._join_bundle_row(row) for row in rows]
            finally:
                conn.close()

    def list_buyers(self, limit: int = 50, search: str = "") -> List[Dict[str, Any]]:
        n = max(1, min(int(limit or 50), 500))
        where_sql, params = self._buyer_search_where(search)
        with self._lock:
            conn = self._conn()
            try:
                rows = conn.execute(
                    f"""
                    SELECT buyer_id, name, phone, email, source, channel, status, note, access_code, created_at, expires_at, last_active_at
                    FROM buyers
                    {where_sql}
                    ORDER BY created_at DESC
                    LIMIT ?
                    """,
                    tuple(params + [n]),
                ).fetchall()
                return [dict(row) for row in rows]
            finally:
                conn.close()

    def list_orders(self, limit: int = 50, search: str = "") -> List[Dict[str, Any]]:
        n = max(1, min(int(limit or 50), 500))
        q = str(search or "").strip()
        params: List[Any] = []
        where_sql = ""
        if q:
            like = f"%{q}%"
            where_sql = " WHERE order_id LIKE ? OR buyer_id LIKE ? OR product_name LIKE ? OR access_code LIKE ? "
            params.extend([like, like, like, like])
        with self._lock:
            conn = self._conn()
            try:
                rows = conn.execute(
                    f"""
                    SELECT order_id, buyer_id, product_name, amount, currency, payment_channel, payment_status,
                           delivery_status, access_code, note, created_at, updated_at, package_id, credits, wallet_granted_at, activation_mode
                    FROM orders
                    {where_sql}
                    ORDER BY created_at DESC
                    LIMIT ?
                    """,
                    tuple(params + [n]),
                ).fetchall()
                return [dict(row) for row in rows]
            finally:
                conn.close()

    def list_access_codes(self, limit: int = 50, search: str = "") -> List[Dict[str, Any]]:
        n = max(1, min(int(limit or 50), 500))
        q = str(search or "").strip()
        params: List[Any] = []
        where_sql = ""
        if q:
            like = f"%{q}%"
            where_sql = " WHERE code LIKE ? OR buyer_id LIKE ? OR order_id LIKE ? OR label LIKE ? "
            params.extend([like, like, like, like])
        with self._lock:
            conn = self._conn()
            try:
                rows = conn.execute(
                    f"""
                    SELECT code, buyer_id, order_id, label, status, max_uses, used_count, expires_at,
                           activated_at, last_used_at, note, created_at
                    FROM access_codes
                    {where_sql}
                    ORDER BY created_at DESC
                    LIMIT ?
                    """,
                    tuple(params + [n]),
                ).fetchall()
                return [dict(row) for row in rows]
            finally:
                conn.close()

    def update_order(self, order_id: str, patch: Dict[str, Any]) -> Dict[str, Any]:
        oid = str(order_id or "").strip()
        if not oid:
            raise ValueError("order_id_required")
        update_map: Dict[str, Any] = {}
        for key in ("product_name", "payment_channel", "payment_status", "delivery_status", "access_code", "note"):
            value = str((patch or {}).get(key) or "").strip()
            if value:
                update_map[key] = value
        if (patch or {}).get("amount") is not None:
            try:
                update_map["amount"] = float((patch or {}).get("amount") or 0)
            except Exception:
                pass
        update_map["updated_at"] = _iso_now()
        if len(update_map) == 1 and update_map.get("updated_at"):
            raise ValueError("empty_patch")

        with self._lock:
            conn = self._conn()
            try:
                existing = conn.execute(
                    """
                    SELECT order_id, payment_status, credits, wallet_granted_at
                    FROM orders WHERE order_id = ?
                    """,
                    (oid,),
                ).fetchone()
                if not existing:
                    raise ValueError("order_not_found")
                sets = ", ".join([f"{key} = ?" for key in update_map.keys()])
                conn.execute(
                    f"UPDATE orders SET {sets} WHERE order_id = ?",
                    tuple(update_map.values()) + (oid,),
                )
                if str(update_map.get("payment_status") or existing["payment_status"] or "").strip() == "paid":
                    row_dict = self._grant_order_credits_if_needed(conn, oid)
                else:
                    row = conn.execute(
                        """
                        SELECT order_id, buyer_id, product_name, amount, currency, payment_channel, payment_status,
                               delivery_status, access_code, note, created_at, updated_at, package_id, credits, wallet_granted_at, activation_mode
                        FROM orders WHERE order_id = ?
                        """,
                        (oid,),
                    ).fetchone()
                    row_dict = dict(row or {})
                conn.commit()
                return row_dict
            finally:
                conn.close()

    def update_access_code(self, code: str, patch: Dict[str, Any]) -> Dict[str, Any]:
        normalized_code = str(code or "").strip().upper()
        if not normalized_code:
            raise ValueError("code_required")
        expires_at = str((patch or {}).get("expires_at") or "").strip()
        if not expires_at and (patch or {}).get("duration_days") is not None:
            expires_at = _to_iso_days(int((patch or {}).get("duration_days") or 30))
        update_map: Dict[str, Any] = {}
        for key in ("label", "status", "note"):
            value = str((patch or {}).get(key) or "").strip()
            if value:
                update_map[key] = value
        if expires_at:
            update_map["expires_at"] = expires_at
        if (patch or {}).get("max_uses") is not None:
            update_map["max_uses"] = max(1, int((patch or {}).get("max_uses") or 1))
        if not update_map:
            raise ValueError("empty_patch")

        with self._lock:
            conn = self._conn()
            try:
                row = conn.execute("SELECT code FROM access_codes WHERE code = ?", (normalized_code,)).fetchone()
                if not row:
                    raise ValueError("code_not_found")
                sets = ", ".join([f"{key} = ?" for key in update_map.keys()])
                conn.execute(
                    f"UPDATE access_codes SET {sets} WHERE code = ?",
                    tuple(update_map.values()) + (normalized_code,),
                )
                conn.commit()
                out = conn.execute(
                    """
                    SELECT code, buyer_id, order_id, label, status, max_uses, used_count, expires_at,
                           activated_at, last_used_at, note, created_at
                    FROM access_codes WHERE code = ?
                    """,
                    (normalized_code,),
                ).fetchone()
                return dict(out or {})
            finally:
                conn.close()

    def _direct_access_code(self) -> str:
        return str(os.getenv("ACCESS_CODE") or "6").strip().upper()

    def _direct_access_payload(
        self,
        code: str,
        client_ip: str = "",
        user_agent: str = "",
        machine_name: str = "",
    ) -> Dict[str, Any]:
        normalized_code = str(code or "").strip().upper()
        return {
            "access_code": normalized_code,
            "buyer_id": f"buyer_{normalized_code.lower()}",
            "order_id": "",
            "buyer_name": f"Buyer {normalized_code}",
            "phone": "",
            "email": "",
            "buyer_status": "active",
            "product_name": "AI Job Helper Direct",
            "payment_status": "",
            "delivery_status": "delivered",
            "package_id": "internal_direct",
            "credits": 999999,
            "wallet_granted_at": "",
            "activation_mode": "instant",
            "label": f"Direct access {normalized_code}",
            "status": "active",
            "used_count": 0,
            "max_uses": 999999,
            "expires_at": "",
            "client_ip": str(client_ip or ""),
            "user_agent": str(user_agent or ""),
            "machine_name": str(machine_name or ""),
        }

    def redeem_access_code(
        self,
        code: str,
        client_ip: str = "",
        user_agent: str = "",
        machine_name: str = "",
        consume_use: bool = True,
    ) -> Dict[str, Any]:
        normalized_code = str(code or "").strip().upper()
        if not normalized_code:
            raise ValueError("code_required")
        now_iso = _iso_now()
        with self._lock:
            conn = self._conn()
            try:
                row = conn.execute(
                    """
                    SELECT
                        a.code, a.buyer_id, a.order_id, a.label, a.status, a.max_uses, a.used_count,
                        a.expires_at, a.activated_at, a.last_used_at, a.note,
                        b.name, b.phone, b.email, b.status AS buyer_status,
                        o.product_name, o.payment_status, o.delivery_status, o.package_id, o.credits, o.wallet_granted_at, o.activation_mode
                    FROM access_codes a
                    LEFT JOIN buyers b ON b.buyer_id = a.buyer_id
                    LEFT JOIN orders o ON o.order_id = a.order_id
                    WHERE a.code = ?
                    LIMIT 1
                    """,
                    (normalized_code,),
                ).fetchone()
                if not row:
                    if normalized_code == self._direct_access_code():
                        return self._direct_access_payload(
                            normalized_code,
                            client_ip=client_ip,
                            user_agent=user_agent,
                            machine_name=machine_name,
                        )
                    raise ValueError("code_not_found")
                status = str(row["status"] or "inactive").strip().lower()
                if status not in {"active", "issued"}:
                    raise ValueError("code_inactive")
                expires_at = str(row["expires_at"] or "").strip()
                if expires_at and expires_at < now_iso:
                    raise ValueError("code_expired")
                used_count = int(row["used_count"] or 0)
                max_uses = max(1, int(row["max_uses"] or 1))
                if used_count >= max_uses:
                    raise ValueError("code_uses_exceeded")
                order_id = str(row["order_id"] or "").strip()
                payment_status = str(row["payment_status"] or "").strip().lower()
                activation_mode = str(row["activation_mode"] or "").strip().lower()
                if order_id and activation_mode != "instant" and payment_status != "paid":
                    raise ValueError("code_payment_pending")

                next_used_count = used_count + (1 if consume_use else 0)
                if consume_use:
                    conn.execute(
                        """
                        UPDATE access_codes
                        SET used_count = ?, activated_at = COALESCE(NULLIF(activated_at, ''), ?), last_used_at = ?
                        WHERE code = ?
                        """,
                        (next_used_count, now_iso, now_iso, normalized_code),
                    )
                    conn.execute(
                        "UPDATE buyers SET last_active_at = ? WHERE buyer_id = ?",
                        (now_iso, str(row["buyer_id"] or "").strip()),
                    )
                    conn.commit()
                return {
                    "access_code": normalized_code,
                    "buyer_id": str(row["buyer_id"] or ""),
                    "order_id": str(row["order_id"] or ""),
                    "buyer_name": str(row["name"] or ""),
                    "phone": str(row["phone"] or ""),
                    "email": str(row["email"] or ""),
                    "buyer_status": str(row["buyer_status"] or ""),
                    "product_name": str(row["product_name"] or ""),
                    "payment_status": str(row["payment_status"] or ""),
                    "delivery_status": str(row["delivery_status"] or ""),
                    "package_id": str(row["package_id"] or ""),
                    "credits": int(row["credits"] or 0),
                    "wallet_granted_at": str(row["wallet_granted_at"] or ""),
                    "activation_mode": str(row["activation_mode"] or ""),
                    "label": str(row["label"] or ""),
                    "status": str(row["status"] or ""),
                    "used_count": next_used_count,
                    "max_uses": max_uses,
                    "expires_at": expires_at,
                    "client_ip": str(client_ip or ""),
                    "user_agent": str(user_agent or ""),
                    "machine_name": str(machine_name or ""),
                }
            finally:
                conn.close()

    def create_ticket(
        self,
        buyer_id: str = "",
        order_id: str = "",
        subject: str = "",
        content: str = "",
        channel: str = "dashboard",
        status: str = "open",
        priority: str = "normal",
        assignee: str = "",
        note: str = "",
    ) -> Dict[str, Any]:
        subject_text = str(subject or "").strip() or "售后支持"
        content_text = str(content or "").strip()
        if not content_text:
            raise ValueError("ticket_content_required")
        ticket_id = self._new_id("ticket")
        now = _iso_now()
        with self._lock:
            conn = self._conn()
            try:
                conn.execute(
                    """
                    INSERT INTO support_tickets(
                        ticket_id, buyer_id, order_id, subject, content, channel, status, priority, assignee, note, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        ticket_id,
                        str(buyer_id or "").strip(),
                        str(order_id or "").strip(),
                        subject_text,
                        content_text,
                        str(channel or "").strip() or "dashboard",
                        str(status or "").strip() or "open",
                        str(priority or "").strip() or "normal",
                        str(assignee or "").strip(),
                        str(note or "").strip(),
                        now,
                        now,
                    ),
                )
                conn.commit()
                row = conn.execute(
                    """
                    SELECT ticket_id, buyer_id, order_id, subject, content, channel, status, priority, assignee, note, created_at, updated_at
                    FROM support_tickets WHERE ticket_id = ?
                    """,
                    (ticket_id,),
                ).fetchone()
                return dict(row or {})
            finally:
                conn.close()

    def list_tickets(self, limit: int = 50, search: str = "") -> List[Dict[str, Any]]:
        n = max(1, min(int(limit or 50), 500))
        q = str(search or "").strip()
        params: List[Any] = []
        where_sql = ""
        if q:
            like = f"%{q}%"
            where_sql = " WHERE ticket_id LIKE ? OR buyer_id LIKE ? OR subject LIKE ? OR content LIKE ? "
            params.extend([like, like, like, like])
        with self._lock:
            conn = self._conn()
            try:
                rows = conn.execute(
                    f"""
                    SELECT ticket_id, buyer_id, order_id, subject, content, channel, status, priority, assignee, note, created_at, updated_at
                    FROM support_tickets
                    {where_sql}
                    ORDER BY created_at DESC
                    LIMIT ?
                    """,
                    tuple(params + [n]),
                ).fetchall()
                return [dict(row) for row in rows]
            finally:
                conn.close()

    def update_ticket(self, ticket_id: str, patch: Dict[str, Any]) -> Dict[str, Any]:
        tid = str(ticket_id or "").strip()
        if not tid:
            raise ValueError("ticket_id_required")
        update_map = {}
        for key in ("subject", "content", "channel", "status", "priority", "assignee", "note", "buyer_id", "order_id"):
            value = str((patch or {}).get(key) or "").strip()
            if value:
                update_map[key] = value
        update_map["updated_at"] = _iso_now()
        with self._lock:
            conn = self._conn()
            try:
                row = conn.execute("SELECT ticket_id FROM support_tickets WHERE ticket_id = ?", (tid,)).fetchone()
                if not row:
                    raise ValueError("ticket_not_found")
                sets = ", ".join([f"{key} = ?" for key in update_map.keys()])
                conn.execute(
                    f"UPDATE support_tickets SET {sets} WHERE ticket_id = ?",
                    tuple(update_map.values()) + (tid,),
                )
                conn.commit()
                out = conn.execute(
                    """
                    SELECT ticket_id, buyer_id, order_id, subject, content, channel, status, priority, assignee, note, created_at, updated_at
                    FROM support_tickets WHERE ticket_id = ?
                    """,
                    (tid,),
                ).fetchone()
                return dict(out or {})
            finally:
                conn.close()

    def register_local_agent(
        self,
        access_code: str,
        machine_name: str = "",
        hostname: str = "",
        platform: str = "",
        capabilities: Optional[Dict[str, Any]] = None,
        note: str = "",
    ) -> Dict[str, Any]:
        redeem = self.redeem_access_code(access_code, consume_use=False)
        normalized_code = str(redeem.get("access_code") or "").strip().upper()
        buyer_id = str(redeem.get("buyer_id") or "").strip()
        host_key = str(hostname or machine_name or "").strip()
        now = _iso_now()
        with self._lock:
            conn = self._conn()
            try:
                existing = None
                if host_key:
                    existing = conn.execute(
                        """
                        SELECT agent_id FROM local_agents
                        WHERE access_code = ? AND hostname = ?
                        LIMIT 1
                        """,
                        (normalized_code, host_key),
                    ).fetchone()
                if existing:
                    agent_id = str(existing["agent_id"] or "")
                    conn.execute(
                        """
                        UPDATE local_agents
                        SET machine_name = ?, hostname = ?, platform = ?, capabilities_json = ?, status = ?, note = ?, last_seen_at = ?
                        WHERE agent_id = ?
                        """,
                        (
                            str(machine_name or "").strip(),
                            str(hostname or "").strip(),
                            str(platform or "").strip(),
                            _json_dump(capabilities or {}),
                            "online",
                            str(note or "").strip(),
                            now,
                            agent_id,
                        ),
                    )
                else:
                    agent_id = self._new_id("agent")
                    conn.execute(
                        """
                        INSERT INTO local_agents(
                            agent_id, buyer_id, access_code, machine_name, hostname, platform, capabilities_json, status, note, created_at, last_seen_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            agent_id,
                            buyer_id,
                            normalized_code,
                            str(machine_name or "").strip(),
                            str(hostname or "").strip(),
                            str(platform or "").strip(),
                            _json_dump(capabilities or {}),
                            "online",
                            str(note or "").strip(),
                            now,
                            now,
                        ),
                    )
                conn.commit()
                row = conn.execute(
                    """
                    SELECT agent_id, buyer_id, access_code, machine_name, hostname, platform, capabilities_json,
                           status, note, created_at, last_seen_at
                    FROM local_agents WHERE agent_id = ?
                    """,
                    (agent_id,),
                ).fetchone()
                out = dict(row or {})
                out["capabilities"] = _json_load(out.pop("capabilities_json", ""))
                return out
            finally:
                conn.close()

    def heartbeat_local_agent(
        self,
        agent_id: str,
        status: str = "online",
        capabilities: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        aid = str(agent_id or "").strip()
        if not aid:
            raise ValueError("agent_id_required")
        now = _iso_now()
        with self._lock:
            conn = self._conn()
            try:
                row = conn.execute("SELECT agent_id FROM local_agents WHERE agent_id = ?", (aid,)).fetchone()
                if not row:
                    raise ValueError("agent_not_found")
                if capabilities is not None:
                    conn.execute(
                        """
                        UPDATE local_agents
                        SET status = ?, capabilities_json = ?, last_seen_at = ?
                        WHERE agent_id = ?
                        """,
                        (str(status or "online").strip(), _json_dump(capabilities), now, aid),
                    )
                else:
                    conn.execute(
                        "UPDATE local_agents SET status = ?, last_seen_at = ? WHERE agent_id = ?",
                        (str(status or "online").strip(), now, aid),
                    )
                conn.commit()
                out = conn.execute(
                    """
                    SELECT agent_id, buyer_id, access_code, machine_name, hostname, platform, capabilities_json,
                           status, note, created_at, last_seen_at
                    FROM local_agents WHERE agent_id = ?
                    """,
                    (aid,),
                ).fetchone()
                payload = dict(out or {})
                payload["capabilities"] = _json_load(payload.pop("capabilities_json", ""))
                return payload
            finally:
                conn.close()

    def list_local_agents(self, limit: int = 50, search: str = "") -> List[Dict[str, Any]]:
        n = max(1, min(int(limit or 50), 500))
        q = str(search or "").strip()
        params: List[Any] = []
        where_sql = ""
        if q:
            like = f"%{q}%"
            where_sql = " WHERE agent_id LIKE ? OR buyer_id LIKE ? OR access_code LIKE ? OR hostname LIKE ? OR machine_name LIKE ? "
            params.extend([like, like, like, like, like])
        with self._lock:
            conn = self._conn()
            try:
                rows = conn.execute(
                    f"""
                    SELECT agent_id, buyer_id, access_code, machine_name, hostname, platform, capabilities_json,
                           status, note, created_at, last_seen_at
                    FROM local_agents
                    {where_sql}
                    ORDER BY last_seen_at DESC, created_at DESC
                    LIMIT ?
                    """,
                    tuple(params + [n]),
                ).fetchall()
                out: List[Dict[str, Any]] = []
                for row in rows:
                    item = dict(row)
                    item["capabilities"] = _json_load(item.pop("capabilities_json", ""))
                    out.append(item)
                return out
            finally:
                conn.close()

    def enqueue_local_task(
        self,
        access_code: str,
        task_type: str,
        payload: Optional[Dict[str, Any]] = None,
        buyer_id: str = "",
        agent_id: str = "",
    ) -> Dict[str, Any]:
        redeem = self.redeem_access_code(access_code, consume_use=False)
        normalized_code = str(redeem.get("access_code") or "").strip().upper()
        if not normalized_code:
            raise ValueError("access_code_required")
        task_id = self._new_id("task")
        now = _iso_now()
        with self._lock:
            conn = self._conn()
            try:
                resolved_buyer_id = str(buyer_id or redeem.get("buyer_id") or "").strip()
                conn.execute(
                    """
                    INSERT INTO local_tasks(
                        task_id, agent_id, buyer_id, access_code, task_type, status, payload_json, progress_json, result_json,
                        created_at, updated_at, started_at, completed_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        task_id,
                        str(agent_id or "").strip(),
                        resolved_buyer_id,
                        normalized_code,
                        str(task_type or "").strip() or "local_auto_apply",
                        "queued",
                        _json_dump(payload or {}),
                        _json_dump({}),
                        _json_dump({}),
                        now,
                        now,
                        "",
                        "",
                    ),
                )
                conn.commit()
                return self.get_local_task(task_id)
            finally:
                conn.close()

    def claim_local_task(self, agent_id: str, access_code: str) -> Dict[str, Any]:
        aid = str(agent_id or "").strip()
        normalized_code = str(access_code or "").strip().upper()
        if not aid or not normalized_code:
            raise ValueError("agent_id_and_access_code_required")
        now = _iso_now()
        with self._lock:
            conn = self._conn()
            try:
                row = conn.execute(
                    """
                    SELECT task_id FROM local_tasks
                    WHERE access_code = ?
                      AND status = 'queued'
                      AND (agent_id = '' OR agent_id IS NULL OR agent_id = ?)
                    ORDER BY created_at ASC
                    LIMIT 1
                    """,
                    (normalized_code, aid),
                ).fetchone()
                if not row:
                    return {}
                task_id = str(row["task_id"] or "")
                conn.execute(
                    """
                    UPDATE local_tasks
                    SET agent_id = ?, status = ?, started_at = ?, updated_at = ?
                    WHERE task_id = ?
                    """,
                    (aid, "running", now, now, task_id),
                )
                conn.commit()
                return self.get_local_task(task_id)
            finally:
                conn.close()

    def get_local_task(self, task_id: str) -> Dict[str, Any]:
        tid = str(task_id or "").strip()
        if not tid:
            return {}
        with self._lock:
            conn = self._conn()
            try:
                row = conn.execute(
                    """
                    SELECT task_id, agent_id, buyer_id, access_code, task_type, status, payload_json, progress_json, result_json,
                           created_at, updated_at, started_at, completed_at
                    FROM local_tasks WHERE task_id = ?
                    """,
                    (tid,),
                ).fetchone()
                if not row:
                    return {}
                out = dict(row)
                out["payload"] = _json_load(out.pop("payload_json", ""))
                out["progress"] = _json_load(out.pop("progress_json", ""))
                out["result"] = _json_load(out.pop("result_json", ""))
                return out
            finally:
                conn.close()

    def list_local_tasks(self, limit: int = 50, search: str = "") -> List[Dict[str, Any]]:
        n = max(1, min(int(limit or 50), 500))
        q = str(search or "").strip()
        params: List[Any] = []
        where_sql = ""
        if q:
            like = f"%{q}%"
            where_sql = " WHERE task_id LIKE ? OR buyer_id LIKE ? OR access_code LIKE ? OR task_type LIKE ? OR status LIKE ? "
            params.extend([like, like, like, like, like])
        with self._lock:
            conn = self._conn()
            try:
                rows = conn.execute(
                    f"""
                    SELECT task_id, agent_id, buyer_id, access_code, task_type, status, payload_json, progress_json, result_json,
                           created_at, updated_at, started_at, completed_at
                    FROM local_tasks
                    {where_sql}
                    ORDER BY created_at DESC
                    LIMIT ?
                    """,
                    tuple(params + [n]),
                ).fetchall()
                out: List[Dict[str, Any]] = []
                for row in rows:
                    item = dict(row)
                    item["payload"] = _json_load(item.pop("payload_json", ""))
                    item["progress"] = _json_load(item.pop("progress_json", ""))
                    item["result"] = _json_load(item.pop("result_json", ""))
                    out.append(item)
                return out
            finally:
                conn.close()

    def update_local_task_progress(
        self,
        task_id: str,
        status: str = "running",
        progress: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        tid = str(task_id or "").strip()
        if not tid:
            raise ValueError("task_id_required")
        now = _iso_now()
        with self._lock:
            conn = self._conn()
            try:
                row = conn.execute("SELECT task_id FROM local_tasks WHERE task_id = ?", (tid,)).fetchone()
                if not row:
                    raise ValueError("task_not_found")
                conn.execute(
                    """
                    UPDATE local_tasks
                    SET status = ?, progress_json = ?, updated_at = ?
                    WHERE task_id = ?
                    """,
                    (str(status or "running").strip(), _json_dump(progress or {}), now, tid),
                )
                conn.commit()
                return self.get_local_task(tid)
            finally:
                conn.close()

    def complete_local_task(
        self,
        task_id: str,
        success: bool,
        result: Optional[Dict[str, Any]] = None,
        status: str = "",
    ) -> Dict[str, Any]:
        tid = str(task_id or "").strip()
        if not tid:
            raise ValueError("task_id_required")
        now = _iso_now()
        final_status = str(status or ("completed" if success else "failed")).strip()
        with self._lock:
            conn = self._conn()
            try:
                row = conn.execute("SELECT task_id FROM local_tasks WHERE task_id = ?", (tid,)).fetchone()
                if not row:
                    raise ValueError("task_not_found")
                conn.execute(
                    """
                    UPDATE local_tasks
                    SET status = ?, result_json = ?, updated_at = ?, completed_at = ?
                    WHERE task_id = ?
                    """,
                    (final_status, _json_dump(result or {}), now, now, tid),
                )
                conn.commit()
                return self.get_local_task(tid)
            finally:
                conn.close()

    def summary(self) -> Dict[str, Any]:
        now = _iso_now()
        with self._lock:
            conn = self._conn()
            try:
                buyers_total = int(conn.execute("SELECT COUNT(*) FROM buyers").fetchone()[0] or 0)
                active_codes = int(
                    conn.execute(
                        "SELECT COUNT(*) FROM access_codes WHERE status IN ('active', 'issued') AND (expires_at = '' OR expires_at >= ?)",
                        (now,),
                    ).fetchone()[0]
                    or 0
                )
                paid_orders = int(conn.execute("SELECT COUNT(*) FROM orders WHERE payment_status = 'paid'").fetchone()[0] or 0)
                pending_orders = int(conn.execute("SELECT COUNT(*) FROM orders WHERE payment_status = 'pending'").fetchone()[0] or 0)
                open_tickets = int(
                    conn.execute("SELECT COUNT(*) FROM support_tickets WHERE status IN ('open', 'todo', 'pending')").fetchone()[0]
                    or 0
                )
                online_agents = int(conn.execute("SELECT COUNT(*) FROM local_agents WHERE status = 'online'").fetchone()[0] or 0)
                queued_tasks = int(conn.execute("SELECT COUNT(*) FROM local_tasks WHERE status = 'queued'").fetchone()[0] or 0)
                running_tasks = int(conn.execute("SELECT COUNT(*) FROM local_tasks WHERE status = 'running'").fetchone()[0] or 0)
                wallets_total = int(conn.execute("SELECT COUNT(*) FROM wallets").fetchone()[0] or 0)
                total_credit_balance = int(conn.execute("SELECT COALESCE(SUM(balance), 0) FROM wallets").fetchone()[0] or 0)
                total_credits_granted = int(conn.execute("SELECT COALESCE(SUM(granted_total), 0) FROM wallets").fetchone()[0] or 0)
                total_credits_consumed = int(conn.execute("SELECT COALESCE(SUM(consumed_total), 0) FROM wallets").fetchone()[0] or 0)
            finally:
                conn.close()
        return {
            "buyers_total": buyers_total,
            "active_codes": active_codes,
            "paid_orders": paid_orders,
            "pending_orders": pending_orders,
            "open_tickets": open_tickets,
            "online_agents": online_agents,
            "queued_tasks": queued_tasks,
            "running_tasks": running_tasks,
            "wallets_total": wallets_total,
            "total_credit_balance": total_credit_balance,
            "total_credits_granted": total_credits_granted,
            "total_credits_consumed": total_credits_consumed,
            "generated_at": now,
        }
