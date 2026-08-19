# -*- coding: utf-8 -*-
"""
排序工具集 - 支持列表排序、字典排序
"""

import json
import os


def _sort_list(args: dict) -> str:
    items = args.get('items', [])
    reverse = args.get('reverse', False)
    if not items:
        return "❌ 请提供列表"
    result = sorted(items, reverse=reverse)
    return json.dumps({'成功': True, '结果': result}, ensure_ascii=False, indent=2)


def _sort_dict(args: dict) -> str:
    items = args.get('items', {})
    by = args.get('by', 'key')
    reverse = args.get('reverse', False)
    if not items:
        return "❌ 请提供字典"
    if by == 'key':
        result = dict(sorted(items.items(), reverse=reverse))
    elif by == 'value':
        result = dict(sorted(items.items(), key=lambda x: x[1], reverse=reverse))
    else:
        return "❌ 不支持的排序方式"
    return json.dumps({'成功': True, '结果': result}, ensure_ascii=False, indent=2)


def register_tools():
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import tools
    tools.register(name="sort_list", description="排序列表。参数: items(列表), reverse(是否倒序)", parameters={"type": "object", "properties": {"items": {"type": "array"}, "reverse": {"type": "boolean"}}, "required": ["items"]}, func=_sort_list)
    tools.register(name="sort_dict", description="排序字典。参数: items(字典), by(key/value), reverse", parameters={"type": "object", "properties": {"items": {"type": "object"}, "by": {"type": "string"}, "reverse": {"type": "boolean"}}, "required": ["items"]}, func=_sort_dict)
    return 2


def unregister_tools():
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import tools
    for name in ["sort_list", "sort_dict"]:
        tools.TOOLS.pop(name, None)
