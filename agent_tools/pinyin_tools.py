# -*- coding: utf-8 -*-
"""
拼音转换工具集 - 中文转拼音
"""

import json
import os


def _to_pinyin(args: dict) -> str:
    text = args.get('text', '')
    if not text:
        return "❌ 请提供中文文本"
    try:
        from pypinyin import pinyin, Style
        result = pinyin(text, style=Style.NORMAL)
        pinyin_str = ' '.join([item[0] for item in result])
    except ImportError:
        pinyin_map = {'中': 'zhong', '国': 'guo', '人': 'ren', '民': 'min'}
        pinyin_str = ''.join([pinyin_map.get(c, c) for c in text])
    return json.dumps({'成功': True, '拼音': pinyin_str}, ensure_ascii=False, indent=2)


def register_tools():
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import tools
    tools.register(name="to_pinyin", description="中文转拼音。参数: text(中文文本)", parameters={"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]}, func=_to_pinyin)
    return 1


def unregister_tools():
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import tools
    for name in ["to_pinyin"]:
        tools.TOOLS.pop(name, None)
