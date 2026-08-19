# -*- coding: utf-8 -*-
"""
单位转换工具集 - 支持长度、重量、温度转换
"""

import json
import os


def _convert_length(args: dict) -> str:
    value = args.get('value', 0)
    from_unit = args.get('from', 'm')
    to_unit = args.get('to', 'km')
    units = {'m': 1, 'km': 1000, 'cm': 0.01, 'mm': 0.001, 'ft': 0.3048, 'in': 0.0254, 'mi': 1609.34}
    if from_unit not in units or to_unit not in units:
        return "❌ 不支持的单位"
    result = value * units[from_unit] / units[to_unit]
    return json.dumps({'成功': True, '结果': result}, ensure_ascii=False, indent=2)


def _convert_temp(args: dict) -> str:
    value = args.get('value', 0)
    from_unit = args.get('from', 'C')
    to_unit = args.get('to', 'F')
    if from_unit == 'C' and to_unit == 'F':
        result = value * 9/5 + 32
    elif from_unit == 'F' and to_unit == 'C':
        result = (value - 32) * 5/9
    elif from_unit == 'C' and to_unit == 'K':
        result = value + 273.15
    elif from_unit == 'K' and to_unit == 'C':
        result = value - 273.15
    else:
        result = value
    return json.dumps({'成功': True, '结果': round(result, 2)}, ensure_ascii=False, indent=2)


def register_tools():
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import tools
    tools.register(
        name="convert_length",
        description="长度单位转换。参数: value(数值), from(源单位), to(目标单位)",
        parameters={"type": "object", "properties": {
            "value": {"type": "number", "description": "要转换的数值"},
            "from": {"type": "string", "description": "源单位: m, km, cm, mm, ft, in, mi"},
            "to": {"type": "string", "description": "目标单位"}
        }, "required": ["value", "from", "to"]},
        func=_convert_length,
    )
    tools.register(
        name="convert_temp",
        description="温度单位转换。参数: value(数值), from(源单位C/F/K), to(目标单位)",
        parameters={"type": "object", "properties": {
            "value": {"type": "number", "description": "要转换的数值"},
            "from": {"type": "string", "description": "源单位: C, F, K"},
            "to": {"type": "string", "description": "目标单位"}
        }, "required": ["value", "from", "to"]},
        func=_convert_temp,
    )
    return 2


def unregister_tools():
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import tools
    for name in ["convert_length", "convert_temp"]:
        tools.TOOLS.pop(name, None)
