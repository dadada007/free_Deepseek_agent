# -*- coding: utf-8 -*-
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tools import register


def _list_dir(args):
    path = args.get("path", "").strip()
    if not path:
        return "错误: 请提供 path 参数"
    if not os.path.exists(path):
        return "路径不存在: " + path
    if not os.path.isdir(path):
        return "路径不是目录: " + path

    # 类型转换：确保 max_depth 是整数
    max_depth = args.get("max_depth", 2)
    if isinstance(max_depth, str):
        try:
            max_depth = int(max_depth)
        except ValueError:
            max_depth = 2
    if max_depth < 1:
        max_depth = 1
    if max_depth > 5:
        max_depth = 5

    show_hidden = args.get("show_hidden", False)
    show_size = args.get("show_size", True)
    show_time = args.get("show_time", False)

    lines = []
    lines.append("目录: " + path)
    lines.append("-" * 50)

    total_files = 0
    total_dirs = 0
    total_size = 0

    def _walk(dir_path, prefix="", depth=0):
        nonlocal total_files, total_dirs, total_size
        if depth > max_depth:
            return
        try:
            items = sorted(os.listdir(dir_path))
        except PermissionError:
            lines.append(prefix + "  权限不足")
            return
        for idx, item in enumerate(items):
            if not show_hidden and item.startswith("."):
                continue
            item_path = os.path.join(dir_path, item)
            is_last = (idx == len(items) - 1)
            connector = "└── " if is_last else "├── "
            try:
                is_dir = os.path.isdir(item_path)
                if is_dir:
                    total_dirs += 1
                    icon = "[DIR]"
                else:
                    total_files += 1
                    icon = "[FILE]"
                    total_size += os.path.getsize(item_path)
                line = prefix + connector + icon + " " + item
                if show_size and not is_dir:
                    size_bytes = os.path.getsize(item_path)
                    line += " (" + _format_size(size_bytes) + ")"
                if show_time:
                    mtime = os.path.getmtime(item_path)
                    time_str = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M")
                    line += " [" + time_str + "]"
                lines.append(line)
                if is_dir and depth < max_depth:
                    next_prefix = prefix + ("    " if is_last else "│   ")
                    _walk(item_path, next_prefix, depth + 1)
            except PermissionError:
                lines.append(prefix + connector + "权限不足: " + item)

    _walk(path)
    lines.append("-" * 50)
    lines.append("总计: " + str(total_files) + " 个文件, " + str(total_dirs) + " 个目录, 总大小 " + _format_size(total_size))
    lines.append("显示深度: " + str(max_depth) + " 层")

    return os.linesep.join(lines)


def _format_size(size_bytes):
    if size_bytes < 1024:
        return str(size_bytes) + " B"
    if size_bytes < 1024 * 1024:
        return str(round(size_bytes / 1024, 1)) + " KB"
    if size_bytes < 1024 * 1024 * 1024:
        return str(round(size_bytes / (1024 * 1024), 1)) + " MB"
    return str(round(size_bytes / (1024 * 1024 * 1024), 2)) + " GB"


def register_tools():
    register(
        name="list_dir",
        description="列出目录内容（树形结构），支持深度控制、显示隐藏文件、文件大小和修改时间",
        parameters={
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "目录路径，使用正斜杠或双反斜杠"
                },
                "max_depth": {
                    "type": ["integer", "string"],
                    "description": "递归显示的最大深度（1~5），默认 2",
                    "default": 2,
                    "minimum": 1,
                    "maximum": 5
                },
                "show_hidden": {
                    "type": "boolean",
                    "description": "是否显示隐藏文件（以 . 开头的文件），默认 false",
                    "default": False
                },
                "show_size": {
                    "type": "boolean",
                    "description": "是否显示文件大小，默认 true",
                    "default": True
                },
                "show_time": {
                    "type": "boolean",
                    "description": "是否显示修改时间，默认 false",
                    "default": False
                }
            },
            "required": ["path"]
        },
        func=_list_dir
    )
    return 1
