# -*- coding: utf-8 -*-
"""
条形码生成工具集 - 生成条形码
"""

import json
import os


def _generate_barcode(args: dict) -> str:
    code = args.get('code', '')
    output = args.get('output', 'barcode.png')
    if not code:
        return "❌ 请提供条形码内容"
    try:
        import barcode
        from barcode.writer import ImageWriter
        ean = barcode.get_barcode_class('ean13')
        barcode_obj = ean(code.zfill(12), writer=ImageWriter())
        barcode_obj.save(output)
        return json.dumps({'成功': True, '输出': output}, ensure_ascii=False, indent=2)
    except ImportError:
        return "❌ 请安装 python-barcode: pip install python-barcode"
    except Exception as e:
        return f"❌ 生成失败: {e}"


def register_tools():
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import tools
    tools.register(
        name="generate_barcode",
        description="生成条形码。参数: code(条形码内容), output(输出文件)",
        parameters={"type": "object", "properties": {
            "code": {"type": "string", "description": "条形码数字"},
            "output": {"type": "string", "description": "输出文件路径"}
        }, "required": ["code"]},
        func=_generate_barcode,
    )
    return 1


def unregister_tools():
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import tools
    for name in ["generate_barcode"]:
        tools.TOOLS.pop(name, None)
