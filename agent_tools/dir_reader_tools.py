# -*- coding: utf-8 -*-
"""
友好目录阅读工具
功能：以树形结构展示目录内容，包含文件大小、修改时间、类型统计等
"""

import os
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Tuple

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tools import register

# 文件类型图标
FILE_ICONS = {
    '.py': '🐍',
    '.js': '📜',
    '.ts': '📘',
    '.jsx': '⚛️',
    '.tsx': '⚛️',
    '.go': '🐹',
    '.rs': '🦀',
    '.c': '⚙️',
    '.cpp': '⚙️',
    '.h': '📋',
    '.java': '☕',
    '.kt': '🎯',
    '.swift': '🦅',
    '.html': '🌐',
    '.css': '🎨',
    '.scss': '🎨',
    '.json': '📦',
    '.yaml': '📋',
    '.yml': '📋',
    '.toml': '⚙️',
    '.md': '📝',
    '.txt': '📄',
    '.csv': '📊',
    '.xml': '📰',
    '.sql': '🗄️',
    '.sh': '🖥️',
    '.bat': '🖥️',
    '.ps1': '🖥️',
    '.exe': '⚡',
    '.dll': '🔧',
    '.so': '🔧',
    '.dylib': '🔧',
    '.zip': '📦',
    '.tar': '📦',
    '.gz': '📦',
    '.7z': '📦',
    '.rar': '📦',
    '.png': '🖼️',
    '.jpg': '🖼️',
    '.jpeg': '🖼️',
    '.gif': '🖼️',
    '.svg': '🖼️',
    '.ico': '🖼️',
    '.pdf': '📕',
    '.doc': '📘',
    '.docx': '📘',
    '.xls': '📗',
    '.xlsx': '📗',
    '.ppt': '📙',
    '.pptx': '📙',
    '.mp3': '🎵',
    '.wav': '🎵',
    '.flac': '🎵',
    '.mp4': '🎬',
    '.avi': '🎬',
    '.mkv': '🎬',
    '.mov': '🎬',
    '.log': '📋',
    '.lock': '🔒',
    '.tmp': '🗑️',
    '.bak': '📋',
}


def _format_size(size: int) -> str:
    """格式化文件大小"""
    if size < 1024:
        return f"{size}B"
    elif size < 1024 * 1024:
        return f"{size / 1024:.1f}KB"
    elif size < 1024 * 1024 * 1024:
        return f"{size / 1024 / 1024:.1f}MB"
    else:
        return f"{size / 1024 / 1024 / 1024:.2f}GB"


def _format_time(mtime: float) -> str:
    """格式化修改时间"""
    try:
        dt = datetime.fromtimestamp(mtime)
        return dt.strftime('%Y-%m-%d %H:%M')
    except Exception:
        return ''


def _get_icon(name: str, is_dir: bool) -> str:
    """获取文件/目录图标"""
    if is_dir:
        return '📁'
    ext = os.path.splitext(name)[1].lower()
    return FILE_ICONS.get(ext, '📄')


def _tree_walk(
    path: str,
    prefix: str = '',
    max_depth: int = 3,
    current_depth: int = 0,
    show_hidden: bool = False,
    max_items: int = 200
) -> Tuple[List[str], Dict]:
    """递归遍历目录，生成树形结构"""
    lines = []
    stats = {
        'total_files': 0,
        'total_dirs': 0,
        'total_size': 0,
        'extensions': {},
        'skipped': 0
    }

    if current_depth > max_depth:
        return lines, stats

    try:
        entries = list(Path(path).iterdir())
        # 排序：目录在前，文件在后，按名称排序
        entries.sort(key=lambda x: (not x.is_dir(), x.name.lower()))
    except PermissionError:
        lines.append(f"{prefix}🔒 权限不足: {os.path.basename(path)}")
        return lines, stats
    except Exception as e:
        lines.append(f"{prefix}❌ 读取失败: {str(e)}")
        return lines, stats

    # 过滤隐藏文件
    if not show_hidden:
        entries = [e for e in entries if not e.name.startswith('.')]

    # 限制条目数
    if len(entries) > max_items:
        skipped = len(entries) - max_items
        entries = entries[:max_items]
        stats['skipped'] = skipped

    for i, entry in enumerate(entries):
        is_last = (i == len(entries) - 1)
        connector = '└── ' if is_last else '├── '
        new_prefix = prefix + ('    ' if is_last else '│   ')

        try:
            stat = entry.stat()
            size = stat.st_size if not entry.is_dir() else 0
            mtime = stat.st_mtime
        except Exception:
            size = 0
            mtime = 0

        icon = _get_icon(entry.name, entry.is_dir())
        size_str = _format_size(size) if not entry.is_dir() else ''
        time_str = _format_time(mtime) if mtime else ''

        if entry.is_dir():
            stats['total_dirs'] += 1
            line = f"{prefix}{connector}{icon} {entry.name}/"
            if current_depth < max_depth:
                sub_lines, sub_stats = _tree_walk(
                    str(entry),
                    new_prefix,
                    max_depth,
                    current_depth + 1,
                    show_hidden,
                    max_items
                )
                lines.append(line)
                lines.extend(sub_lines)
                # 合并子统计
                for k in ['total_files', 'total_dirs', 'total_size', 'skipped']:
                    stats[k] += sub_stats.get(k, 0)
                for ext, count in sub_stats.get('extensions', {}).items():
                    stats['extensions'][ext] = stats['extensions'].get(ext, 0) + count
            else:
                lines.append(f"{line}  (深度限制)")
        else:
            stats['total_files'] += 1
            stats['total_size'] += size
            ext = os.path.splitext(entry.name)[1].lower() or '无扩展名'
            stats['extensions'][ext] = stats['extensions'].get(ext, 0) + 1

            # 如果是最后一个且没有子目录，直接显示
            if is_last and current_depth == 0:
                # 判断是否需要显示详细信息
                lines.append(f"{prefix}{connector}{icon} {entry.name}  ({size_str})  {time_str}")
            else:
                lines.append(f"{prefix}{connector}{icon} {entry.name}  ({size_str})")

    return lines, stats


def _read_directory(args: dict) -> str:
    """
    读取目录内容，以树形结构展示。
    参数:
        path: 目录路径
        depth: 扫描深度（默认 3，范围 1-6）
        show_hidden: 是否显示隐藏文件（默认 False）
        max_items: 每层最多显示条目数（默认 200）
    """
    path = args.get('path', '').strip()
    if not path:
        return "❌ 错误: 请提供 path 参数"

    depth = args.get('depth', 3)
    if not isinstance(depth, int):
        try:
            depth = int(depth)
        except (ValueError, TypeError):
            depth = 3
    depth = max(1, min(6, depth))

    show_hidden = args.get('show_hidden', False)
    max_items = args.get('max_items', 200)
    if not isinstance(max_items, int):
        try:
            max_items = int(max_items)
        except (ValueError, TypeError):
            max_items = 200
    max_items = max(10, min(1000, max_items))

    # 检查路径
    if not os.path.exists(path):
        return f"❌ 目录不存在: {path}"
    if not os.path.isdir(path):
        return f"❌ 路径不是目录: {path}"

    # 生成树
    lines, stats = _tree_walk(
        path,
        max_depth=depth,
        show_hidden=show_hidden,
        max_items=max_items
    )

    # 如果没有内容
    if not lines:
        return f"📂 {path}(目录为空或无法读取)"

    # 构建输出
    result = [
        f"📂 {path}",
        "=" * 50,
        *lines,
        "",
        "=" * 50,
        "📊 统计:",
        f"  • 目录: {stats['total_dirs']} 个",
        f"  • 文件: {stats['total_files']} 个",
        f"  • 总大小: {_format_size(stats['total_size'])}",
    ]

    if stats['skipped']:
        result.append(f"  • ⚠️ 已省略 {stats['skipped']} 个条目（达到显示上限）")

    if stats['extensions']:
        result.append("  • 文件类型:")
        sorted_ext = sorted(stats['extensions'].items(), key=lambda x: x[1], reverse=True)
        for ext, count in sorted_ext[:8]:
            result.append(f"      - {ext}: {count} 个")
        if len(sorted_ext) > 8:
            result.append(f"      - ... 还有 {len(sorted_ext) - 8} 种类型")

    return "".join(result)


def register_tools() -> int:
    """注册所有工具"""
    register(
        name="read_directory",
        description=(
            "以树形结构展示目录内容，清晰直观。显示每个文件的图标、大小、修改时间，"
            "底部统计总文件数、总大小、文件类型分布。比普通 ls/list 更友好。"
        ),
        parameters={
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "要读取的目录路径"
                },
                "depth": {
                    "type": "integer",
                    "description": "扫描子目录的最大深度（默认 3，范围 1-6）",
                    "default": 3
                },
                "show_hidden": {
                    "type": "boolean",
                    "description": "是否显示隐藏文件（默认 False）",
                    "default": False
                },
                "max_items": {
                    "type": "integer",
                    "description": "每层最多显示条目数（默认 200，范围 10-1000）",
                    "default": 200
                }
            },
            "required": ["path"]
        },
        func=_read_directory
    )
    return 1


if __name__ == "__main__":
    register_tools()
    print("✅ dir_reader_tools 已加载")
    print("测试: read_directory(path='D:/9/hermes', depth=2)")
    print(_read_directory({"path": "D:/9/hermes", "depth": 2}))
