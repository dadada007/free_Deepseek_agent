# -*- coding: utf-8 -*-
"""
文件权限工具集 - 支持查看、修改文件权限
"""

import json
import os
import stat


def _get_file_permission(args: dict) -> str:
    path = args.get('path', '')
    if not path or not os.path.exists(path):
        return "❌ 文件不存在"
    try:
        mode = os.stat(path).st_mode
        perms = {
            '可读': bool(mode & stat.S_IREAD),
            '可写': bool(mode & stat.S_IWRITE),
            '可执行': bool(mode & stat.S_IEXEC),
            '八进制': oct(mode)[-3:]
        }
        return json.dumps({'成功': True, '路径': path, '权限': perms}, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"❌ 查看权限失败: {e}"


def register_tools():
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import tools
    tools.register(name="get_file_permission", description="查看文件权限。参数: path(文件路径)", parameters={"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}, func=_get_file_permission)
    return 1


def unregister_tools():
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import tools
    for name in ["get_file_permission"]:
        tools.TOOLS.pop(name, None)
