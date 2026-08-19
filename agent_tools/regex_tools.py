# -*- coding: utf-8 -*-
"""
正则表达式工具集 - 支持匹配、替换、提取
"""

import json
import re
import os


def _regex_match(args: dict) -> str:
    text = args.get('text', '')
    pattern = args.get('pattern', '')
    if not text or not pattern:
        return "❌ 请提供文本和正则表达式"
    matches = re.findall(pattern, text)
    return json.dumps({'成功': True, '匹配数': len(matches), '结果': matches}, ensure_ascii=False, indent=2)


def _regex_replace(args: dict) -> str:
    text = args.get('text', '')
    pattern = args.get('pattern', '')
    replacement = args.get('replacement', '')
    if not text or not pattern:
        return "❌ 请提供文本和正则表达式"
    result = re.sub(pattern, replacement, text)
    return json.dumps({'成功': True, '结果': result}, ensure_ascii=False, indent=2)


def register_tools():
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import tools
    tools.register(name="regex_match", description="正则匹配文本。参数: text, pattern", parameters={"type": "object", "properties": {"text": {"type": "string"}, "pattern": {"type": "string"}}, "required": ["text", "pattern"]}, func=_regex_match)
    tools.register(name="regex_replace", description="正则替换文本。参数: text, pattern, replacement", parameters={"type": "object", "properties": {"text": {"type": "string"}, "pattern": {"type": "string"}, "replacement": {"type": "string"}}, "required": ["text", "pattern"]}, func=_regex_replace)
    return 2


def unregister_tools():
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import tools
    for name in ["regex_match", "regex_replace"]:
        tools.TOOLS.pop(name, None)
