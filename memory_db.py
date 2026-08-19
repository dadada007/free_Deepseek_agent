# -*- coding: utf-8 -*-
"""记忆系统 - SQLite 数据库层（本地存储，零配置）"""
import json
import re
import sqlite3
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)


@dataclass
class Memory:
    id: int
    content: str
    embedding: Optional[str] = None
    category: str = "general"
    timestamp: float = field(default_factory=lambda: datetime.now().timestamp())
    source: str = ""
    importance: int = 1
    related_ids: List[int] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "content": self.content,
            "category": self.category,
            "timestamp": self.timestamp,
            "time": datetime.fromtimestamp(self.timestamp).strftime("%Y-%m-%d %H:%M"),
            "source": self.source,
            "importance": self.importance,
        }


class MemoryDB:
    """SQLite 记忆存储。每次操作独立连接，线程安全；供后台写入线程使用。"""

    def __init__(self, db_path: str = None):
        if db_path is None:
            db_path = Path(__file__).parent / "data" / "memory.db"
        self.db_path = str(db_path)
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=10)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS memories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    content TEXT NOT NULL,
                    embedding TEXT,
                    category TEXT DEFAULT 'general',
                    timestamp REAL NOT NULL,
                    source TEXT DEFAULT '',
                    importance INTEGER DEFAULT 1,
                    related_ids TEXT DEFAULT '[]',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );
                CREATE INDEX IF NOT EXISTS idx_mem_category ON memories(category);
                CREATE INDEX IF NOT EXISTS idx_mem_timestamp ON memories(timestamp);
                CREATE INDEX IF NOT EXISTS idx_mem_importance ON memories(importance);
                """
            )

    # ============ 写入 ============

    def save(self, content: str, category: str = "general",
             source: str = "", importance: int = 1,
             embedding: Optional[str] = None) -> int:
        if not content or not str(content).strip():
            return 0
        with self._connect() as conn:
            cur = conn.execute(
                "INSERT INTO memories (content, embedding, category, timestamp, source, importance)"
                " VALUES (?, ?, ?, ?, ?, ?)",
                (str(content), embedding, category, datetime.now().timestamp(),
                 source, int(importance)),
            )
            return cur.lastrowid

    def save_batch(self, items: List[dict]) -> int:
        """批量写入 [ {content, category, source, importance, embedding}, ... ]"""
        if not items:
            return 0
        rows = []
        for it in items:
            if not it or not str(it.get("content", "")).strip():
                continue
            rows.append({
                "content": str(it["content"]),
                "embedding": it.get("embedding"),
                "category": it.get("category", "general"),
                "timestamp": datetime.now().timestamp(),
                "source": it.get("source", ""),
                "importance": int(it.get("importance", 1)),
            })
        if not rows:
            return 0
        with self._connect() as conn:
            cur = conn.executemany(
                "INSERT INTO memories (content, embedding, category, timestamp, source, importance)"
                " VALUES (:content, :embedding, :category, :timestamp, :source, :importance)",
                rows,
            )
            return cur.rowcount or len(rows)

    # ============ 检索 ============

    @staticmethod
    def _tokens(query: str) -> List[str]:
        """分词：英文/数字词（>=2 字符）+ 中文双字组"""
        toks = []
        for w in re.findall(r"[A-Za-z0-9_]{2,}", query or ""):
            toks.append(w.lower())
        cjk = re.sub(r"[^\u4e00-\u9fff]", "", query or "")
        for i in range(len(cjk) - 1):
            bigram = cjk[i:i + 2]
            if bigram not in toks:
                toks.append(bigram)
        return toks

    def search(self, query: str, limit: int = 10,
               category: Optional[str] = None,
               min_importance: int = 1) -> List[Memory]:
        """关键词检索（多 token 匹配，按相关度 + 新鲜度排序）"""
        toks = self._tokens(query)
        sql = ("SELECT id, content, embedding, category, timestamp, source, importance, related_ids"
               " FROM memories WHERE")
        params = []
        if toks:
            sql += " (" + " OR ".join(["content LIKE ?"] * len(toks)) + ")"
            params = [f"%{t}%" for t in toks]
        else:
            sql += " 1=1"
        sql += " AND importance >= ?"
        params.append(min_importance)
        if category:
            sql += " AND category = ?"
            params.append(category)
        sql += " ORDER BY timestamp DESC LIMIT ?"
        params.append(max(1, limit * 4))  # 多取一些再做相关度排序

        with self._connect() as conn:
            rows = conn.execute(sql, params).fetchall()

        scored = []
        for row in rows:
            mem = self._row_to_memory(row)
            score = sum(mem.content.lower().count(t) for t in toks) if toks else 0
            scored.append((score, mem.timestamp, mem))
        scored.sort(key=lambda x: (x[0], x[1]), reverse=True)
        return [mem for _, _, mem in scored[:limit]]

    def search_by_time(self, days: int = 7, limit: int = 20) -> List[Memory]:
        cutoff = datetime.now().timestamp() - days * 86400
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT id, content, embedding, category, timestamp, source, importance, related_ids"
                " FROM memories WHERE timestamp > ? ORDER BY timestamp DESC LIMIT ?",
                (cutoff, limit),
            ).fetchall()
        return [self._row_to_memory(r) for r in rows]

    def search_by_importance(self, min_importance: int = 5, limit: int = 20) -> List[Memory]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT id, content, embedding, category, timestamp, source, importance, related_ids"
                " FROM memories WHERE importance >= ? ORDER BY importance DESC, timestamp DESC LIMIT ?",
                (min_importance, limit),
            ).fetchall()
        return [self._row_to_memory(r) for r in rows]

    def recent(self, limit: int = 20) -> List[Memory]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT id, content, embedding, category, timestamp, source, importance, related_ids"
                " FROM memories ORDER BY timestamp DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [self._row_to_memory(r) for r in rows]

    def get(self, memory_id: int) -> Optional[Memory]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT id, content, embedding, category, timestamp, source, importance, related_ids"
                " FROM memories WHERE id = ?",
                (memory_id,),
            ).fetchone()
        return self._row_to_memory(row) if row else None

    # ============ 更新 / 删除 ============

    def update_importance(self, memory_id: int, importance: int):
        with self._connect() as conn:
            conn.execute("UPDATE memories SET importance = ? WHERE id = ?",
                         (int(importance), memory_id))

    def link_memories(self, memory_id: int, related_ids: List[int]):
        with self._connect() as conn:
            conn.execute("UPDATE memories SET related_ids = ? WHERE id = ?",
                         (json.dumps(related_ids), memory_id))

    def delete(self, memory_id: int):
        with self._connect() as conn:
            conn.execute("DELETE FROM memories WHERE id = ?", (memory_id,))

    def delete_old(self, days: int = 30) -> int:
        cutoff = datetime.now().timestamp() - days * 86400
        with self._connect() as conn:
            cur = conn.execute("DELETE FROM memories WHERE timestamp < ?", (cutoff,))
            return cur.rowcount or 0

    def count(self) -> int:
        with self._connect() as conn:
            return conn.execute("SELECT COUNT(*) FROM memories").fetchone()[0]

    # ============ 工具 ============

    def _row_to_memory(self, row) -> Memory:
        return Memory(
            id=row["id"],
            content=row["content"],
            embedding=row["embedding"],
            category=row["category"],
            timestamp=row["timestamp"],
            source=row["source"],
            importance=row["importance"],
            related_ids=json.loads(row["related_ids"] or "[]"),
        )