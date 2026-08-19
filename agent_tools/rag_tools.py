# -*- coding: utf-8 -*-
"""
RAG 知识库工具集（P1） - 让 Agent 更聪明
把项目文件分块索引到本地 SQLite，按 token 相关度检索，注入上下文。
放于 agent_tools/ 目录，由 HotReloader 自动扫描注册，改文件保存即热更新。
"""
import json
import os
import re
import sys
import sqlite3
import threading
import hashlib
from datetime import datetime

# agent_tools 的上一级 = hermes/，数据放 hermes/data/rag.db
_HERMES_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _HERMES_DIR not in sys.path:
    sys.path.insert(0, _HERMES_DIR)
_DB_PATH = os.path.join(_HERMES_DIR, "data", "rag.db")

# 默认索引的文本扩展名
_DEFAULT_EXTS = {".py", ".js", ".ts", ".jsx", ".tsx", ".html", ".css", ".json",
                 ".md", ".txt", ".yaml", ".yml", ".toml", ".ini", ".cfg",
                 ".sh", ".bat", ".ps1", ".xml", ".csv", ".sql"}
# 跳过的目录
_SKIP_DIRS = {".git", "__pycache__", "node_modules", ".venv", "venv", "dist",
              "build", ".hermes_backup", "data"}
_MAX_FILE_CHARS = 200_000  # 单文件索引上限
_CHUNK_LINES = 200          # 每块行数
_CHUNK_OVERLAP = 40         # 相邻块重叠行数


def _tokens(query: str):
    """分词：英文/数字词 + 中文双字组"""
    toks = []
    for w in re.findall(r"[A-Za-z0-9_]{2,}", query or ""):
        toks.append(w.lower())
    cjk = re.sub(r"[^\u4e00-\u9fff]", "", query or "")
    for i in range(len(cjk) - 1):
        b = cjk[i:i + 2]
        if b not in toks:
            toks.append(b)
    return toks


def _chunk_text(text: str, lines: int = _CHUNK_LINES,
                overlap: int = _CHUNK_OVERLAP):
    """按行分块，块间重叠"""
    all_lines = text.splitlines()
    chunks = []
    i = 0
    n = len(all_lines)
    while i < n:
        chunk = "\n".join(all_lines[i:i + lines])
        if chunk.strip():
            chunks.append(chunk)
        i += lines - overlap
    return chunks


class RagIndex:
    """本地文件 RAG 索引（SQLite 持久化）"""

    def __init__(self, db_path: str = _DB_PATH):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._lock = threading.Lock()
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=10)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS chunks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file TEXT NOT NULL,
                    chunk TEXT NOT NULL,
                    chunk_index INTEGER DEFAULT 0,
                    file_hash TEXT DEFAULT '',
                    mtime REAL DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );
                CREATE INDEX IF NOT EXISTS idx_chunks_file ON chunks(file);
                """
            )

    # ===== 索引 =====

    def _iter_files(self, path: str):
        if os.path.isfile(path):
            yield path
            return
        if os.path.isdir(path):
            for root, dirs, files in os.walk(path):
                dirs[:] = [d for d in dirs if d not in _SKIP_DIRS
                           and not d.startswith(".")]
                for f in files:
                    yield os.path.join(root, f)

    def index(self, path: str) -> dict:
        if not os.path.exists(path):
            return {"success": False, "error": f"路径不存在: {path}"}
        files = list(self._iter_files(path))
        indexed_files = 0
        indexed_chunks = 0
        skipped = []
        errors = []
        for f in files:
            ext = os.path.splitext(f)[1].lower()
            if ext not in _DEFAULT_EXTS:
                skipped.append(f)
                continue
            try:
                size = os.path.getsize(f)
                if size > _MAX_FILE_CHARS:
                    skipped.append(f"{f}(过大)")
                    continue
                with open(f, "r", encoding="utf-8", errors="replace") as fh:
                    content = fh.read()
                if not content.strip():
                    skipped.append(f"{f}(空)")
                    continue
                mtime = os.path.getmtime(f)
                digest = hashlib.md5(content.encode("utf-8", "replace")).hexdigest()
                rel = f.replace(_HERMES_DIR, "").lstrip("\\/")
                with self._lock:
                    conn = self._connect()
                    old = conn.execute(
                        "SELECT file_hash, mtime FROM chunks WHERE file = ? LIMIT 1",
                        (rel,)).fetchone()
                    if old and old["file_hash"] == digest:
                        conn.close()
                        indexed_files += 1
                        continue  # 未变化，跳过
                    conn.execute("DELETE FROM chunks WHERE file = ?", (rel,))
                    chunks = _chunk_text(content)
                    conn.executemany(
                        "INSERT INTO chunks (file, chunk, chunk_index, file_hash, mtime)"
                        " VALUES (?, ?, ?, ?, ?)",
                        [(rel, c, i, digest, mtime) for i, c in enumerate(chunks)],
                    )
                    conn.commit()
                    conn.close()
                indexed_files += 1
                indexed_chunks += len(chunks)
            except Exception as e:
                errors.append(f"{f}: {e}")
        return {
            "success": True,
            "path": path,
            "indexed_files": indexed_files,
            "indexed_chunks": indexed_chunks,
            "skipped": len(skipped),
            "errors": errors[:5],
        }

    # ===== 检索 =====

    def search(self, query: str, top_k: int = 5) -> list:
        toks = _tokens(query)
        if not toks:
            return []
        with self._lock:
            conn = self._connect()
            rows = conn.execute(
                "SELECT file, chunk, chunk_index, mtime FROM chunks"
            ).fetchall()
            conn.close()
        scored = []
        for r in rows:
            low = (r["chunk"] or "").lower()
            score = sum(low.count(t) for t in toks)
            if score:
                scored.append({
                    "score": score,
                    "file": r["file"],
                    "chunk_index": r["chunk_index"],
                    "text": (r["chunk"] or "")[:800],
                })
        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:top_k]

    def drop(self, path: str) -> dict:
        if not os.path.exists(path):
            return {"success": False, "error": f"路径不存在: {path}"}
        rels = []
        for f in self._iter_files(path):
            rels.append(f.replace(_HERMES_DIR, "").lstrip("\\/"))
        with self._lock:
            conn = self._connect()
            cur = conn.execute(
                f"DELETE FROM chunks WHERE file IN ({','.join('?' * len(rels))})",
                rels) if rels else None
            conn.commit()
            conn.close()
        return {"success": True, "removed_chunks": cur.rowcount if cur else 0}

    def status(self) -> dict:
        with self._lock:
            conn = self._connect()
            total = conn.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
            files = conn.execute(
                "SELECT file, COUNT(*) c, MAX(mtime) m FROM chunks GROUP BY file"
            ).fetchall()
            conn.close()
        return {
            "success": True,
            "db": self.db_path,
            "total_chunks": total,
            "indexed_files": len(files),
            "files": [{"file": f["file"], "chunks": f["c"]} for f in files[:100]],
        }

    def clear(self) -> dict:
        with self._lock:
            conn = self._connect()
            conn.execute("DELETE FROM chunks")
            conn.commit()
            conn.close()
        return {"success": True, "message": "知识库已清空"}


_index: RagIndex | None = None


def _get_index() -> RagIndex:
    global _index
    if _index is None:
        _index = RagIndex(_DB_PATH)
    return _index


# ==================== 工具实现 ====================

def _rag_index(args: dict) -> str:
    path = args.get("path", "")
    if not path:
        return "错误: 缺少 path 参数"
    return json.dumps(_get_index().index(path), ensure_ascii=False, indent=2)


def _rag_search(args: dict) -> str:
    query = args.get("query", "")
    top_k = min(20, int(args.get("top_k", 5)))
    if not query:
        return "错误: 缺少 query 参数"
    hits = _get_index().search(query, top_k)
    if not hits:
        return json.dumps({"success": True, "count": 0,
                           "提示": "未命中，可先 rag_index 索引目录后再检索"},
                          ensure_ascii=False, indent=2)
    return json.dumps({"success": True, "count": len(hits), "hits": hits},
                      ensure_ascii=False, indent=2)


def _rag_status(args: dict) -> str:
    return json.dumps(_get_index().status(), ensure_ascii=False, indent=2)


def _rag_drop(args: dict) -> str:
    path = args.get("path", "")
    if not path:
        return "错误: 缺少 path 参数"
    return json.dumps(_get_index().drop(path), ensure_ascii=False, indent=2)


def _rag_clear(args: dict) -> str:
    return json.dumps(_get_index().clear(), ensure_ascii=False, indent=2)


# ==================== 热加载注册 ====================

def register_tools():
    import tools
    tools.register(
        name="rag_index",
        description="把文件或目录分块索引进本地知识库（RAG）。参数: path(文件或目录路径)。支持常见代码/文本格式，自动跳过二进制与 .git",
        parameters={"type": "object", "properties": {"path": {"type": "string"}},
                    "required": ["path"]},
        func=_rag_index,
    )
    tools.register(
        name="rag_search",
        description="在知识库中检索与 query 最相关的内容块（RAG 召回）。参数: query(查询词), top_k(返回条数,默认5)",
        parameters={"type": "object", "properties": {
            "query": {"type": "string"},
            "top_k": {"type": "integer"},
        }, "required": ["query"]},
        func=_rag_search,
    )
    tools.register(
        name="rag_status",
        description="查看知识库状态（已索引文件数/块数）",
        parameters={"type": "object", "properties": {}},
        func=_rag_status,
    )
    tools.register(
        name="rag_drop",
        description="从知识库移除某个文件/目录的索引。参数: path",
        parameters={"type": "object", "properties": {"path": {"type": "string"}},
                    "required": ["path"]},
        func=_rag_drop,
    )
    tools.register(
        name="rag_clear",
        description="清空整个知识库索引",
        parameters={"type": "object", "properties": {}},
        func=_rag_clear,
    )
    return 5


def unregister_tools():
    import tools
    for name in ["rag_index", "rag_search", "rag_status", "rag_drop", "rag_clear"]:
        tools.TOOLS.pop(name, None)