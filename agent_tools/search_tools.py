# -*- coding: utf-8 -*-
"""搜索工具模块"""
import os
import re
import logging
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)

_IGNORE_DIRS = {
    ".git", "node_modules", "__pycache__", ".venv", "venv",
    "dist", "build", ".next", ".nuxt", "target", ".idea", ".vscode",
}

def _should_ignore(path: Path) -> bool:
    for part in path.parts:
        if part in _IGNORE_DIRS:
            return True
    return False

def glob(args: dict) -> str:
    """通配符搜索文件"""
    pattern = args.get("pattern", "")
    search_path = args.get("path", ".")
    if not pattern:
        return "请提供 pattern"
    base = Path(search_path)
    if not base.exists():
        return f"路径不存在: {base}"
    try:
        matches = [p for p in base.glob(pattern) if p.is_file() and not _should_ignore(p)]
        if not matches:
            return f"没有匹配 '{pattern}'"
        matches.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        results = []
        for p in matches[:100]:
            rel = p.relative_to(base)
            mtime = datetime.fromtimestamp(p.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
            results.append(f"{mtime}  {rel}")
        return "\n".join(results)
    except Exception as e:
        return f"搜索失败: {e}"

def grep(args: dict) -> str:
    """跨文件内容搜索（正则）"""
    pattern = args.get("pattern", "")
    file_pattern = args.get("file_pattern", "")
    search_path = args.get("path", ".")
    if not pattern:
        return "请提供搜索模式"
    try:
        regex = re.compile(pattern, re.IGNORECASE)
    except re.error as e:
        return f"正则错误: {e}"
    base = Path(search_path)
    if not base.exists() or not base.is_dir():
        return f"目录不存在: {base}"
    files = list(base.glob(f"**/{file_pattern}" if file_pattern else "**/*"))
    files = [f for f in files if f.is_file() and not _should_ignore(f)]
    results = []
    total = 0
    for fp in files:
        if total >= 50:
            break
        try:
            content = fp.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        file_matches = []
        for i, line in enumerate(content.splitlines(), 1):
            if regex.search(line):
                file_matches.append((i, line.rstrip()))
        if file_matches:
            rel = fp.relative_to(base)
            results.append(f"\n{rel}:")
            for ln, lt in file_matches[:10]:
                results.append(f"  {ln}: {lt}")
            total += 1
    if not results:
        return f"没有匹配 '{pattern}'"
    return "\n".join(results)

def search_by_name(args: dict) -> str:
    """按文件名搜索"""
    directory = args.get("directory", ".")
    pattern = args.get("pattern", "")
    recursive = args.get("recursive", True)
    if not pattern:
        return "请提供搜索模式"
    base = Path(directory)
    if not base.exists():
        return f"目录不存在: {base}"
    try:
        glob_pattern = f"**/{pattern}" if recursive else pattern
        matches = [p for p in base.glob(glob_pattern) if p.is_file() and not _should_ignore(p)]
        if not matches:
            return f"没有匹配 '{pattern}'"
        results = []
        for p in matches[:100]:
            rel = p.relative_to(base)
            results.append(str(rel))
        return "\n".join(results)
    except Exception as e:
        return f"搜索失败: {e}"

def search_by_content(args: dict) -> str:
    """搜索文件内容"""
    directory = args.get("directory", ".")
    pattern = args.get("pattern", "")
    extensions = args.get("extensions", "")
    if not pattern:
        return "请提供搜索模式"
    try:
        regex = re.compile(pattern, re.IGNORECASE)
    except re.error as e:
        return f"正则错误: {e}"
    base = Path(directory)
    if not base.exists():
        return f"目录不存在: {base}"
    ext_list = [e.strip() for e in extensions.split(',')] if extensions else []
    files = list(base.glob("**/*"))
    files = [f for f in files if f.is_file() and not _should_ignore(f)]
    if ext_list:
        files = [f for f in files if f.suffix in ext_list or f.suffix[1:] in ext_list]
    results = []
    total = 0
    for fp in files:
        if total >= 30:
            break
        try:
            content = fp.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        if regex.search(content):
            rel = fp.relative_to(base)
            results.append(str(rel))
            total += 1
    if not results:
        return f"没有匹配 '{pattern}'"
    return "\n".join(results)

def search_by_size(args: dict) -> str:
    """按文件大小搜索"""
    directory = args.get("directory", ".")
    min_size = args.get("min_size", 0)
    max_size = args.get("max_size", 10**9)
    base = Path(directory)
    if not base.exists():
        return f"目录不存在: {base}"
    try:
        files = list(base.glob("**/*"))
        files = [f for f in files if f.is_file() and not _should_ignore(f)]
        results = []
        for p in files:
            size = p.stat().st_size
            if min_size <= size <= max_size:
                rel = p.relative_to(base)
                results.append(f"{size}  {rel}")
        if not results:
            return f"没有匹配大小范围 {min_size}-{max_size} 字节"
        results.sort(key=lambda x: int(x.split()[0]), reverse=True)
        return "\n".join(results[:50])
    except Exception as e:
        return f"搜索失败: {e}"

def register_tools():
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import tools
    tools.register(
        name="glob",
        description="通配符搜索文件（支持 **/*.py）",
        parameters={"type": "object", "properties": {"pattern": {"type": "string"}, "path": {"type": "string"}}, "required": ["pattern"]},
        func=glob
    )
    tools.register(
        name="grep",
        description="跨文件内容搜索（正则）",
        parameters={"type": "object", "properties": {"pattern": {"type": "string"}, "file_pattern": {"type": "string"}, "path": {"type": "string"}}, "required": ["pattern"]},
        func=grep
    )
    tools.register(
        name="search_by_name",
        description="按文件名搜索",
        parameters={"type": "object", "properties": {"directory": {"type": "string"}, "pattern": {"type": "string"}, "recursive": {"type": "boolean"}}, "required": ["directory", "pattern"]},
        func=search_by_name
    )
    tools.register(
        name="search_by_content",
        description="搜索文件内容",
        parameters={"type": "object", "properties": {"directory": {"type": "string"}, "pattern": {"type": "string"}, "extensions": {"type": "string"}}, "required": ["directory", "pattern"]},
        func=search_by_content
    )
    tools.register(
        name="search_by_size",
        description="按文件大小搜索",
        parameters={"type": "object", "properties": {"directory": {"type": "string"}, "min_size": {"type": "integer"}, "max_size": {"type": "integer"}}, "required": ["directory"]},
        func=search_by_size
    )
    return 5