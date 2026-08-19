# -*- coding: utf-8 -*-
"""
文件搜索工具集 - 支持按名称、内容、大小搜索
"""

import os
import re
import json
from datetime import datetime


def _format_size(size):
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"


def _search_by_name(args: dict) -> str:
    try:
        directory = args.get('directory', '.')
        pattern = args.get('pattern', '*')
        recursive = args.get('recursive', True)
        max_results = args.get('max_results', 100)
        if not os.path.exists(directory):
            return f"❌ 目录不存在: {directory}"
        results = []
        if recursive:
            for root, _, files in os.walk(directory):
                for file in files:
                    if len(results) >= max_results:
                        break
                    if re.match(re.escape(pattern).replace('\\*', '.*').replace('\\?', '.'), file):
                        path = os.path.join(root, file)
                        results.append({'名称': file, '路径': path, '大小': _format_size(os.path.getsize(path))})
                if len(results) >= max_results:
                    break
        else:
            for file in os.listdir(directory):
                if len(results) >= max_results:
                    break
                path = os.path.join(directory, file)
                if os.path.isfile(path) and re.match(re.escape(pattern).replace('\\*', '.*').replace('\\?', '.'), file):
                    results.append({'名称': file, '路径': path, '大小': _format_size(os.path.getsize(path))})
        return json.dumps({'成功': True, '匹配数量': len(results), '文件列表': results}, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"❌ 搜索失败: {e}"


def _search_by_content(args: dict) -> str:
    try:
        directory = args.get('directory', '.')
        pattern = args.get('pattern', '')
        extensions = args.get('extensions', ['.py', '.txt', '.js', '.html', '.css', '.json', '.md'])
        max_results = args.get('max_results', 50)
        if not pattern:
            return "❌ 请提供搜索内容"
        if not os.path.exists(directory):
            return f"❌ 目录不存在: {directory}"
        regex = re.compile(pattern, re.IGNORECASE)
        results = []
        for root, _, files in os.walk(directory):
            for file in files:
                if len(results) >= max_results:
                    break
                ext = os.path.splitext(file)[1].lower()
                if ext not in extensions:
                    continue
                path = os.path.join(root, file)
                try:
                    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    matches = []
                    for line_num, line in enumerate(content.split('\n'), 1):
                        if regex.search(line):
                            matches.append({'行号': line_num, '内容': line.strip()[:200]})
                    if matches:
                        results.append({'文件': path, '匹配数': len(matches), '匹配': matches[:10]})
                except:
                    continue
        return json.dumps({'成功': True, '匹配文件': len(results), '结果': results}, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"❌ 搜索失败: {e}"


def _search_by_size(args: dict) -> str:
    try:
        directory = args.get('directory', '.')
        min_size = args.get('min_size', 0)
        max_size = args.get('max_size', float('inf'))
        max_results = args.get('max_results', 100)
        if not os.path.exists(directory):
            return f"❌ 目录不存在: {directory}"
        results = []
        for root, _, files in os.walk(directory):
            for file in files:
                if len(results) >= max_results:
                    break
                path = os.path.join(root, file)
                size = os.path.getsize(path)
                if min_size <= size <= max_size:
                    results.append({'名称': file, '路径': path, '大小': _format_size(size)})
            if len(results) >= max_results:
                break
        return json.dumps({'成功': True, '匹配数量': len(results), '文件列表': results}, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"❌ 搜索失败: {e}"


def register_tools():
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import tools
    tools.register(name="search_by_name", description="按文件名搜索。参数: directory, pattern, recursive", parameters={"type": "object", "properties": {"directory": {"type": "string"}, "pattern": {"type": "string"}, "recursive": {"type": "boolean"}}}, func=_search_by_name)
    tools.register(name="search_by_content", description="搜索文件内容。参数: directory, pattern, extensions", parameters={"type": "object", "properties": {"directory": {"type": "string"}, "pattern": {"type": "string"}, "extensions": {"type": "array"}}}, func=_search_by_content)
    tools.register(name="search_by_size", description="按文件大小搜索。参数: directory, min_size, max_size", parameters={"type": "object", "properties": {"directory": {"type": "string"}, "min_size": {"type": "integer"}, "max_size": {"type": "integer"}}}, func=_search_by_size)
    return 3


def unregister_tools():
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import tools
    for name in ["search_by_name", "search_by_content", "search_by_size"]:
        tools.TOOLS.pop(name, None)
