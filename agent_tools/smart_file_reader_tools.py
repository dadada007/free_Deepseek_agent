# -*- coding: utf-8 -*-
"""
智能大文件读取工具
功能：分块读取大文件，自动管理阅读进度，生成文件结构摘要

解决问题：AI 读大文件只能看到一小部分

核心策略：
1. 自动分块读取 — 大文件按行分块，每块独立返回，AI 可逐块累积理解
2. 内容缓存 — 已读文件内容存内存，后续轮次可直接引用而无需重读
3. 智能摘要 — 同时提供文件结构摘要（函数/类/变量列表），让 AI 快速定位
4. 阅读进度追踪 — 记录已读范围，避免重复读取
5. 全局视图 — 所有块读完后，汇总生成完整文件概览
"""

import os
import sys
import re
import json
import hashlib
import time
import logging
from typing import Optional, Dict, List, Tuple
from collections import OrderedDict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tools import register

logger = logging.getLogger(__name__)

# ==================== 配置 ====================

MAX_CHUNK_CHARS = 200000   # 20万字符
MAX_CHUNK_LINES = 5000     # 5000行
MAX_CACHED_FILES = 50
MAX_CACHE_SIZE_CHARS = 1_000_000  # 缓存单个文件最大字符数，增大到100万


# ==================== 缓存管理器 ====================

class FileContextCache:
    """文件内容缓存 — 单例"""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, "_initialized"):
            return
        self._initialized = True
        self._cache: OrderedDict[str, Dict] = OrderedDict()
        self._read_log: Dict[str, List[Tuple[int, int]]] = {}

    def _make_key(self, path: str) -> str:
        """生成缓存 key（规范化路径 + mtime）"""
        try:
            real_path = os.path.abspath(path)
            mtime = os.path.getmtime(real_path)
            return f"{real_path}:{int(mtime)}"
        except Exception:
            return path

    def put(self, path: str, content: str, lines: List[str], summary: str = ""):
        """缓存文件内容"""
        key = self._make_key(path)
        total_chars = len(content)
        
        # 如果文件太大，截断缓存
        if total_chars > MAX_CACHE_SIZE_CHARS:
            content = content[:MAX_CACHE_SIZE_CHARS]
            lines = lines[:5000]
            logger.info(f"📦 文件过大，仅缓存前 {len(lines)} 行 / {MAX_CACHE_SIZE_CHARS} 字符")

        self._cache[key] = {
            "path": os.path.abspath(path),
            "content": content,
            "lines": lines,
            "summary": summary,
            "total_lines": len(lines),
            "total_chars": total_chars,
            "cached_at": time.time(),
            "key": key,
        }
        while len(self._cache) > MAX_CACHED_FILES:
            oldest_key = next(iter(self._cache))
            del self._cache[oldest_key]

    def get(self, path: str) -> Optional[Dict]:
        """获取缓存"""
        key = self._make_key(path)
        if key in self._cache:
            entry = self._cache.pop(key)
            self._cache[key] = entry
            return entry
        return None

    def get_lines(self, path: str, start: int, end: int) -> Optional[List[str]]:
        """从缓存获取指定行范围"""
        entry = self.get(path)
        if not entry:
            return None
        lines = entry["lines"]
        s = max(0, start - 1)
        e = min(len(lines), end)
        return lines[s:e]

    def log_read(self, path: str, start_line: int, end_line: int):
        """记录已读范围"""
        real_path = os.path.abspath(path)
        if real_path not in self._read_log:
            self._read_log[real_path] = []
        self._read_log[real_path].append((start_line, end_line))

    def get_read_ranges(self, path: str) -> List[Tuple[int, int]]:
        """获取已读范围"""
        real_path = os.path.abspath(path)
        return self._read_log.get(real_path, [])

    def get_unread_ranges(self, path: str, total_lines: int) -> List[Tuple[int, int]]:
        """获取未读范围"""
        read_ranges = self.get_read_ranges(path)
        if not read_ranges:
            return [(1, total_lines)]

        merged = []
        for s, e in sorted(read_ranges):
            if merged and s <= merged[-1][1] + 1:
                merged[-1] = (merged[-1][0], max(merged[-1][1], e))
            else:
                merged.append((s, e))

        unread = []
        prev_end = 0
        for s, e in merged:
            if s > prev_end + 1:
                unread.append((prev_end + 1, s - 1))
            prev_end = max(prev_end, e)
        if prev_end < total_lines:
            unread.append((prev_end + 1, total_lines))

        return unread

    def generate_summary(self, path: str, lines: List[str]) -> str:
        """生成文件结构摘要 - 扫描全部行"""
        try:
            ext = os.path.splitext(path)[1].lower()
            summary_parts = []
            lang = self._detect_language(ext)

            if lang in ("python", "javascript", "typescript", "java", "go", "rust", "cpp"):
                patterns = {
                    "python": [
                        (r"^class\s+(\w+)", "类"),
                        (r"^def\s+(\w+)", "函数"),
                        (r"^\s+def\s+(\w+)", "方法"),
                        (r"^import\s+(.+)", "导入"),
                        (r"^from\s+(\S+)", "从导入"),
                        (r"^const\s+(\w+)", "常量"),
                    ],
                    "javascript": [
                        (r"class\s+(\w+)", "类"),
                        (r"function\s+(\w+)", "函数"),
                        (r"const\s+(\w+)\s*=", "常量"),
                        (r"async\s+function\s+(\w+)", "异步函数"),
                        (r"export\s+(?:default\s+)?(?:function|const|class)\s+(\w+)", "导出"),
                    ],
                    "typescript": [
                        (r"class\s+(\w+)", "类"),
                        (r"interface\s+(\w+)", "接口"),
                        (r"function\s+(\w+)", "函数"),
                        (r"const\s+(\w+)\s*:", "常量"),
                        (r"type\s+(\w+)", "类型"),
                        (r"export\s+(?:default\s+)?(?:function|const|class|interface|type)\s+(\w+)", "导出"),
                    ],
                    "java": [
                        (r"class\s+(\w+)", "类"),
                        (r"interface\s+(\w+)", "接口"),
                        (r"(?:public|private|protected)\s+(?:static\s+)?\w+\s+(\w+)\s*\(", "方法"),
                        (r"import\s+(.+)", "导入"),
                    ],
                    "go": [
                        (r"^func\s+(\w+)", "函数"),
                        (r"^func\s*\([^)]*\)\s*(\w+)", "方法"),
                        (r"^type\s+(\w+)", "类型"),
                        (r"^const\s+(\w+)", "常量"),
                        (r"^var\s+(\w+)", "变量"),
                    ],
                    "rust": [
                        (r"^fn\s+(\w+)", "函数"),
                        (r"^struct\s+(\w+)", "结构体"),
                        (r"^enum\s+(\w+)", "枚举"),
                        (r"^impl\s+(\w+)", "实现"),
                        (r"^trait\s+(\w+)", "特质"),
                        (r"^pub\s+const\s+(\w+)", "常量"),
                    ],
                    "cpp": [
                        (r"class\s+(\w+)", "类"),
                        (r"struct\s+(\w+)", "结构体"),
                        (r"namespace\s+(\w+)", "命名空间"),
                        (r"template\s*<.*>\s*(?:class|struct)\s+(\w+)", "模板类"),
                    ],
                }

                lang_patterns = patterns.get(lang, [])
                found = {}

                # ✅ 扫描全部行，不再限制
                for i, line in enumerate(lines, 1):
                    for pattern, category in lang_patterns:
                        match = re.match(pattern, line.strip())
                        if match:
                            name = match.group(1)
                            found.setdefault(category, []).append(f"{name}(L{i})")

                for category in ["类", "接口", "结构体", "枚举", "实现", "特质", "类型", 
                                "函数", "方法", "异步函数", "常量", "变量", "导出", 
                                "导入", "从导入", "命名空间", "模板类"]:
                    items = found.get(category, [])
                    if items:
                        # 显示前30个，超过则省略
                        display_items = ', '.join(items[:30])
                        if len(items) > 30:
                            display_items += f'... (共{len(items)}个)'
                        summary_parts.append(f"  {category}({len(items)}): {display_items}")

            elif ext in (".md", ".rst", ".txt"):
                headings = []
                for i, line in enumerate(lines, 1):
                    m = re.match(r'^(#+)\s+(.+)', line.strip())
                    if m:
                        level = len(m.group(1))
                        title = m.group(2).strip()
                        headings.append(f"{'#' * level} {title}(L{i})")
                if headings:
                    summary_parts.append(f"  标题({len(headings)}):")
                    for h in headings[:30]:
                        summary_parts.append(f"    {h}")

            elif ext == ".json":
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    if isinstance(data, dict):
                        keys = list(data.keys())[:20]
                        summary_parts.append(f"  顶层键: {', '.join(keys)}")
                    elif isinstance(data, list):
                        summary_parts.append(f"  数组长度: {len(data)}")
                        if data and isinstance(data[0], dict):
                            keys = list(data[0].keys())[:20]
                            summary_parts.append(f"  元素键: {', '.join(keys)}")
                except Exception:
                    pass

            total_lines = len(lines)
            total_chars = sum(len(l) for l in lines)
            non_empty = sum(1 for l in lines if l.strip())
            summary_parts.insert(0, f"📊 文件统计: {total_lines} 行, {total_chars} 字符, {non_empty} 非空行, 语言={lang}")

            return "\n".join(summary_parts)
        except Exception as e:
            return f"📊 文件摘要生成失败: {e}"

    def _detect_language(self, ext: str) -> str:
        mapping = {
            ".py": "python", ".js": "javascript", ".jsx": "javascript",
            ".ts": "typescript", ".tsx": "typescript",
            ".java": "java", ".go": "go", ".rs": "rust",
            ".cpp": "cpp", ".h": "cpp", ".hpp": "cpp", ".c": "cpp",
            ".cs": "csharp", ".rb": "ruby", ".php": "php",
            ".html": "html", ".css": "css", ".scss": "css",
            ".json": "json", ".yaml": "yaml", ".yml": "yaml",
            ".toml": "toml", ".xml": "xml", ".sql": "sql",
            ".sh": "shell", ".bash": "shell", ".bat": "shell", ".ps1": "shell",
            ".md": "markdown", ".rst": "markdown",
        }
        return mapping.get(ext, "unknown")

    def clear(self):
        """清空缓存"""
        self._cache.clear()
        self._read_log.clear()


# ==================== 全局缓存实例 ====================

_file_cache = FileContextCache()


# ==================== 工具实现函数 ====================

def read_file_by_chunks(args: dict) -> str:
    """
    智能分块读取大文件

    自动将大文件按行分块，每块最多指定行数或字符数。
    AI 可通过 chunk_index 逐块读取，读取完所有块后获得完整理解。

    参数:
        path: 文件路径
        chunk_index: 块索引（从1开始），可选值：
            - 不传或 1: 返回文件信息 + 结构摘要 + 第1块
            - N: 返回第N块
            - all: 返回所有块
            - summary_only: 只返回结构摘要
        chunk_size: 每块最大字符数，默认 200000
        chunk_lines: 每块最大行数，默认 5000
    """
    try:
        path = args.get('path', '').strip()
        if not path:
            return "❌ 错误: 请提供 path 参数"

        chunk_index = args.get('chunk_index', 1)
        
        # ✅ 支持动态调整分块大小
        chunk_size = args.get('chunk_size', MAX_CHUNK_CHARS)
        chunk_lines = args.get('chunk_lines', MAX_CHUNK_LINES)

        if not os.path.exists(path):
            return f"❌ 文件不存在: {path}"
        if not os.path.isfile(path):
            return f"❌ 不是文件: {path}"

        file_size = os.path.getsize(path)
        if file_size > 100 * 1024 * 1024:  # ✅ 增大到100MB
            return f"❌ 文件过大 ({file_size / 1024 / 1024:.1f}MB)，拒绝完整读取"

        # ✅ 优先从缓存读取
        cache_entry = _file_cache.get(path)
        if cache_entry:
            all_lines = cache_entry["lines"]
            total_lines = len(all_lines)
            total_chars = cache_entry["total_chars"]
            summary = cache_entry.get("summary", "")
            logger.info(f"📦 使用缓存: {os.path.basename(path)}")
        else:
            # 缓存未命中，读取文件
            with open(path, 'r', encoding='utf-8', errors='replace') as f:
                all_lines = f.readlines()
            total_lines = len(all_lines)
            total_chars = sum(len(l) for l in all_lines)
            summary = _file_cache.generate_summary(path, all_lines)
            _file_cache.put(path, "".join(all_lines), all_lines, summary)
            logger.info(f"📖 首次读取并缓存: {os.path.basename(path)}")

        # 只返回摘要
        if str(chunk_index).lower() == "summary_only":
            return (
                f"📄 {os.path.basename(path)}（{total_lines} 行, {total_chars} 字符）\n\n"
                f"【结构摘要】\n{summary}\n\n"
                f"💡 用 read_file_by_chunks path={path} chunk_index=N 读取第 N 块内容"
            )

        # 计算分块 - 使用参数值
        chunks = []
        current_chunk_lines = []
        current_chunk_chars = 0
        chunk_start = 1

        for i, line in enumerate(all_lines, 1):
            line_len = len(line)
            if current_chunk_lines and (
                len(current_chunk_lines) >= chunk_lines or 
                current_chunk_chars + line_len > chunk_size
            ):
                chunks.append((list(current_chunk_lines), chunk_start, i - 1))
                current_chunk_lines = []
                current_chunk_chars = 0
                chunk_start = i
            if not current_chunk_lines:
                chunk_start = i
            current_chunk_lines.append(line)
            current_chunk_chars += line_len

        if current_chunk_lines:
            chunks.append((list(current_chunk_lines), chunk_start, total_lines))

        total_chunks = len(chunks)

        # 返回所有块
        if str(chunk_index).lower() == "all":
            result_parts = [
                f"📄 {os.path.basename(path)}（{total_lines} 行, {total_chars} 字符, {total_chunks} 块）",
                f"\n【结构摘要】\n{summary}\n",
            ]
            for ci, (chunk_lines_part, s, e) in enumerate(chunks, 1):
                _file_cache.log_read(path, s, e)
                chunk_text = "".join(chunk_lines_part)
                result_parts.append(
                    f"\n{'='*50}\n📦 第 {ci}/{total_chunks} 块（行 {s}-{e}）\n{'='*50}\n"
                    f"{chunk_text}"
                )
            result_parts.append(f"\n✅ 已完整读取 {os.path.basename(path)} 全部 {total_chunks} 块内容")
            return "\n".join(result_parts)

        # 返回指定块
        try:
            idx = int(chunk_index)
            idx = max(1, min(idx, total_chunks))
        except (ValueError, TypeError):
            idx = 1

        chunk_lines_part, s, e = chunks[idx - 1]
        _file_cache.log_read(path, s, e)

        unread = _file_cache.get_unread_ranges(path, total_lines)
        unread_desc = ", ".join(f"{s}-{e}" for s, e in unread[:5])
        if len(unread) > 5:
            unread_desc += f" ...等 {len(unread)} 段"

        chunk_text = "".join(chunk_lines_part)
        result = (
            f"📄 {os.path.basename(path)}（{total_lines} 行, {total_chars} 字符, {total_chunks} 块）\n"
            f"\n【结构摘要】\n{summary}\n"
            f"\n📦 第 {idx}/{total_chunks} 块（行 {s}-{e}）\n"
            f"{'='*50}\n"
            f"{chunk_text}\n"
            f"{'='*50}\n"
        )
        if idx < total_chunks:
            result += f"💡 还有 {total_chunks - idx} 块未读，用 read_file_by_chunks path={path} chunk_index={idx + 1} 继续"
        else:
            result += f"✅ 已读完最后一块！整个文件已完整读取"

        return result

    except Exception as e:
        logger.error(f"❌ read_file_by_chunks 异常: {e}")
        return f"❌ read_file_by_chunks 执行异常: {e}"


def get_file_summary(args: dict) -> str:
    """获取文件结构摘要（不返回内容）"""
    try:
        path = args.get('path', '').strip()
        if not path:
            return "❌ 错误: 请提供 path 参数"

        if not os.path.exists(path):
            return f"❌ 文件不存在: {path}"

        cache_entry = _file_cache.get(path)
        if cache_entry:
            return f"📄 {os.path.basename(path)}\n【结构摘要】\n{cache_entry.get('summary', '')}"

        with open(path, 'r', encoding='utf-8', errors='replace') as f:
            lines = f.readlines()

        summary = _file_cache.generate_summary(path, lines)
        _file_cache.put(path, "".join(lines), lines, summary)
        return f"📄 {os.path.basename(path)}（{len(lines)} 行）\n【结构摘要】\n{summary}"
    except Exception as e:
        return f"❌ get_file_summary 异常: {e}"


def cache_file_content(args: dict) -> str:
    """预加载文件内容到缓存"""
    try:
        path = args.get('path', '').strip()
        if not path:
            return "❌ 错误: 请提供 path 参数"

        if not os.path.exists(path):
            return f"❌ 文件不存在: {path}"

        if _file_cache.get(path):
            return f"📦 {os.path.basename(path)} 已在缓存中"

        with open(path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
            lines = content.split('\n')

        summary = _file_cache.generate_summary(path, lines)
        _file_cache.put(path, content, lines, summary)
        return f"📦 {os.path.basename(path)} 已缓存（{len(lines)} 行, {len(content)} 字符）"
    except Exception as e:
        return f"❌ cache_file_content 异常: {e}"


def clear_file_cache(args: dict) -> str:
    """清空文件缓存"""
    _file_cache.clear()
    return "📦 文件缓存已清空"


# ==================== 工具注册 ====================

def register_tools() -> int:
    """注册所有工具，供热加载器调用"""
    registered = 0

    register(
        name="read_file_by_chunks",
        description=(
            "智能分块读取大文件。自动将大文件按行分块（每块最多5000行或200000字符），"
            "支持逐块读取、进度追踪。参数: path(文件路径), chunk_index(块索引，从1开始，"
            "支持数字、'all'全部读取、'summary_only'仅摘要), "
            "chunk_size(每块最大字符数，默认200000), chunk_lines(每块最大行数，默认5000)"
        ),
        parameters={
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "要读取的文件路径"
                },
                "chunk_index": {
                    "type": "string",
                    "description": "块索引（从1开始），或 'all' 读取全部，或 'summary_only' 仅返回摘要",
                    "default": "1"
                },
                "chunk_size": {
                    "type": "integer",
                    "description": "每块最大字符数，默认 200000",
                    "default": 200000
                },
                "chunk_lines": {
                    "type": "integer",
                    "description": "每块最大行数，默认 5000",
                    "default": 5000
                }
            },
            "required": ["path"]
        },
        func=read_file_by_chunks
    )
    registered += 1

    register(
        name="get_file_summary",
        description="获取文件的结构摘要（函数、类、方法列表），不返回文件内容本身。用于快速了解文件结构。",
        parameters={
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "要分析的文件路径"
                }
            },
            "required": ["path"]
        },
        func=get_file_summary
    )
    registered += 1

    register(
        name="cache_file_content",
        description="预加载文件内容到缓存，后续读取可加速。适用于即将多次读取的大文件。",
        parameters={
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "要缓存的文件路径"
                }
            },
            "required": ["path"]
        },
        func=cache_file_content
    )
    registered += 1

    register(
        name="clear_file_cache",
        description="清空所有已缓存的文件内容，释放内存。",
        parameters={
            "type": "object",
            "properties": {},
            "required": []
        },
        func=clear_file_cache
    )
    registered += 1

    return registered


# ==================== 直接运行测试 ====================

if __name__ == "__main__":
    register_tools()
    print("✅ smart_file_reader_tools 已加载")
    print("\n测试: read_file_by_chunks")
    print(read_file_by_chunks({"path": __file__, "chunk_index": "summary_only"}))