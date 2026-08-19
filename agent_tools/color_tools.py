# -*- coding: utf-8 -*-
"""
颜色处理工具集 - 支持颜色格式转换、调色
"""

import json
import os


def _hex_to_rgb(args: dict) -> str:
    hex_color = args.get('hex', '#000000').lstrip('#')
    if len(hex_color) != 6:
        return "❌ 无效的十六进制颜色"
    r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
    return json.dumps({'成功': True, 'RGB': [r, g, b]}, ensure_ascii=False, indent=2)


def _rgb_to_hex(args: dict) -> str:
    rgb = args.get('rgb', [0, 0, 0])
    if len(rgb) != 3:
        return "❌ 请提供 [r, g, b] 数组"
    hex_color = f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"
    return json.dumps({'成功': True, 'HEX': hex_color}, ensure_ascii=False, indent=2)


def register_tools():
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import tools
    tools.register(
        name="hex_to_rgb",
        description="十六进制颜色转RGB。参数: hex(十六进制颜色值)",
        parameters={"type": "object", "properties": {
            "hex": {"type": "string", "description": "十六进制颜色，如 #FF0000"}
        }, "required": ["hex"]},
        func=_hex_to_rgb,
    )
    tools.register(
        name="rgb_to_hex",
        description="RGB颜色转十六进制。参数: rgb([r,g,b]数组)",
        parameters={"type": "object", "properties": {
            "rgb": {"type": "array", "description": "RGB数组，如 [255,0,0]"}
        }, "required": ["rgb"]},
        func=_rgb_to_hex,
    )
    return 2


def unregister_tools():
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import tools
    for name in ["hex_to_rgb", "rgb_to_hex"]:
        tools.TOOLS.pop(name, None)
