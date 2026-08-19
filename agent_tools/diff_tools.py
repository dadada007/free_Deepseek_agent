# -*- coding: utf-8 -*-
"""
文件差异对比工具集 - 支持文本差异对比
"""

import json
import difflib
import os


def _diff_text(args: dict) -> str:
    text1 = args.get('text1', '')
    text2 = args.get('text2', '')
    if not text1 or not text2:
        return "❌ 请提供两段文本"
    lines1 = text1.splitlines()
    lines2 = text2.splitlines()
    diff = difflib.unified_diff(lines1, lines2, lineterm='')
    return json.dumps({'成功': True, '差异': list(diff)}, ensure_ascii=False, indent=2)


def register_tools():
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import tools
    tools.register(
        name="diff_text",
        description="对比两段文本差异。参数: text1(文本1), text2(文本2)",
        parameters={"type": "object", "properties": {
            "text1": {"type": "string", "description": "第一段文本"},
            "text2": {"type": "string", "description": "第二段文本"}
        }, "required": ["text1", "text2"]},
        func=_diff_text,
    )
    return 1


def unregister_tools():
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import tools
    for name in ["diff_text"]:
        tools.TOOLS.pop(name, None)
