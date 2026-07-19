"""
memory.py
---------
الذاكرة الدائمة للوكيل. الهدف: أي معلومة تتقال في محادثة النهاردة
تفضل موجودة لما تفتح المشروع تاني بعد أسبوع.

بنستخدم SQLite لأنه:
  - ملف واحد، مفيش سيرفر منفصل تشغّله
  - يدعم استعلامات SQL كاملة لو احتجت تفلتر أو تبحث
  - سهل جدًا تنقله لـ Postgres لاحقًا لو المشروع كبر

الجدول الأول (facts): حقائق ثابتة عن المستخدم (اسم، تفضيلات، مشاريع...)
الجدول التاني (conversation_log): سجل كامل للمحادثات لغرض المراجعة والـ context
"""

import sqlite3
import time
from contextlib import contextmanager
from typing import Iterator, Optional

from .config import settings


SCHEMA = """
CREATE TABLE IF NOT EXISTS facts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key TEXT NOT NULL UNIQUE,
    value TEXT NOT NULL,
    updated_at REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS conversation_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at REAL NOT NULL
);
"""


class Memory:
    def __init__(self, db_path: str = settings.db_path):
        self.db_path = db_path
        self._init_db()

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.executescript(SCHEMA)

    # ---------- حقائق ثابتة (long-term facts) ----------

    def remember_fact(self, key: str, value: str) -> None:
        """يخزّن أو يحدّث حقيقة ثابتة، زي: name -> 'محمد'، prefers_detail -> 'true'"""
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO facts (key, value, updated_at)
                VALUES (?, ?, ?)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = excluded.updated_at
                """,
                (key, value, time.time()),
            )

    def recall_fact(self, key: str) -> Optional[str]:
        with self._connect() as conn:
            row = conn.execute("SELECT value FROM facts WHERE key = ?", (key,)).fetchone()
            return row["value"] if row else None

    def all_facts(self) -> dict:
        with self._connect() as conn:
            rows = conn.execute("SELECT key, value FROM facts").fetchall()
            return {r["key"]: r["value"] for r in rows}

    def forget_fact(self, key: str) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM facts WHERE key = ?", (key,))

    # ---------- سجل المحادثة ----------

    def log_message(self, role: str, content: str) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO conversation_log (role, content, created_at) VALUES (?, ?, ?)",
                (role, content, time.time()),
            )

    def recent_history(self, limit: int = 20) -> list[dict]:
        """بيرجع آخر N رسالة بترتيب زمني تصاعدي، جاهزة للحقن في الـ context"""
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT role, content FROM conversation_log ORDER BY id DESC LIMIT ?",
                (limit,),
            ).fetchall()
            return [{"role": r["role"], "content": r["content"]} for r in reversed(rows)]

    def facts_as_context_block(self) -> str:
        """بيحول الحقائق المخزنة لنص جاهز نحقنه في الـ system prompt"""
        facts = self.all_facts()
        if not facts:
            return ""
        lines = [f"- {k}: {v}" for k, v in facts.items()]
        return "معلومات محفوظة عن المستخدم من محادثات سابقة:\n" + "\n".join(lines)
