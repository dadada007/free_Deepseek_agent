# -*- coding: utf-8 -*-
"""
浏览器书签工具集 - 支持提取、整理书签
"""

import json
import os
import re


def _extract_bookmarks(args: dict) -> str:
    path = args.get('path', '')
    if not path or not os.path.exists(path):
        return "❌ 书签文件不存在"
    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        urls = re.findall(r'HREF="([^"]+)"', content, re.IGNORECASE)
        titles = re.findall(r'<A[^>]+>([^<]+)</A>', content, re.IGNORECASE)
        result = [{'title': titles[i] if i < len(titles) else '', 'url': urls[i]} for i in range(len(urls))]
        return json.dumps({'成功': True, '书签数': len(result), '书签': result}, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"❌ 提取失败: {e}"


def register_tools():
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import tools
    tools.register(
        name="extract_bookmarks",
        description="提取浏览器书签。参数: path(书签文件路径)",
        parameters={"type": "object", "properties": {
            "path": {"type": "string", "description": "书签HTML文件路径"}
        }, "required": ["path"]},
        func=_extract_bookmarks,
    )
    return 1


def unregister_tools():
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import tools
    for name in ["extract_bookmarks"]:
        tools.TOOLS.pop(name, None)
