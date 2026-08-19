# -*- coding: utf-8 -*-
"""
代码格式化工具集 - 格式化Python、JSON、HTML代码
"""

import json
import os


def _format_code(args: dict) -> str:
    code = args.get('code', '')
    lang = args.get('lang', 'json')
    if not code:
        return "❌ 请提供代码"
    try:
        if lang == 'json':
            result = json.dumps(json.loads(code), ensure_ascii=False, indent=2)
        elif lang == 'python':
            import ast
            result = ast.unparse(ast.parse(code))
        else:
            result = code
    except Exception as e:
        return f"❌ 格式化失败: {e}"
    return json.dumps({'成功': True, '结果': result}, ensure_ascii=False, indent=2)


def register_tools():
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import tools
    tools.register(
        name="format_code",
        description="格式化代码。参数: code(代码内容), lang(语言: json/python)",
        parameters={"type": "object", "properties": {
            "code": {"type": "string", "description": "要格式化的代码"},
            "lang": {"type": "string", "description": "语言类型: json, python"}
        }, "required": ["code"]},
        func=_format_code,
    )
    return 1


def unregister_tools():
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import tools
    for name in ["format_code"]:
        tools.TOOLS.pop(name, None)
