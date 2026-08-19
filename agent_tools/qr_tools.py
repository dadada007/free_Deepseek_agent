# -*- coding: utf-8 -*-
"""
二维码工具集 - 支持生成二维码、识别二维码、批量生成
"""

import os
import json


def _ensure_dir(path):
    dirname = os.path.dirname(path)
    if dirname and not os.path.exists(dirname):
        os.makedirs(dirname, exist_ok=True)


def _generate_qr(args: dict) -> str:
    try:
        content = args.get('data', '')
        output = args.get('output', 'qrcode.png')
        size = args.get('size', 10)
        color = args.get('color', 'black')
        bg_color = args.get('bg_color', 'white')
        if not content:
            return "❌ 请提供二维码内容 (data)"
        try:
            import qrcode
        except ImportError:
            return "❌ 请安装 qrcode: pip install qrcode[pil]"
        _ensure_dir(output)
        qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_H, box_size=size, border=4)
        qr.add_data(content)
        qr.make(fit=True)
        img = qr.make_image(fill_color=color, back_color=bg_color)
        img.save(output)
        return json.dumps({'success': True, '输出': output, '内容': content[:50]}, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"❌ 生成二维码失败: {e}"


def _decode_qr(args: dict) -> str:
    try:
        path = args.get('path', '')
        if not path:
            return "❌ 请提供图片路径 (path)"
        if not os.path.exists(path):
            return f"❌ 文件不存在: {path}"
        try:
            from pyzbar import pyzbar
            from PIL import Image
        except ImportError:
            return "❌ 请安装 pyzbar: pip install pyzbar"
        img = Image.open(path)
        decoded = pyzbar.decode(img)
        if not decoded:
            return "❌ 未检测到二维码"
        results = []
        for obj in decoded:
            results.append({'数据': obj.data.decode('utf-8'), '类型': obj.type})
        return json.dumps({'success': True, '二维码数量': len(results), '结果': results}, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"❌ 识别二维码失败: {e}"


def _batch_generate_qr(args: dict) -> str:
    try:
        content_list = args.get('data', [])
        output_dir = args.get('output_dir', './qrcodes')
        prefix = args.get('prefix', 'qr_')
        if not content_list:
            return "❌ 请提供内容列表 (data)"
        try:
            import qrcode
        except ImportError:
            return "❌ 请安装 qrcode: pip install qrcode[pil]"
        _ensure_dir(output_dir)
        results = []
        for idx, content in enumerate(content_list):
            filename = f"{prefix}{idx+1}.png"
            output_path = os.path.join(output_dir, filename)
            qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_H, box_size=8, border=4)
            qr.add_data(content)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            img.save(output_path)
            results.append({'index': idx + 1, '输出': output_path})
        return json.dumps({'success': True, '输出目录': output_dir, '生成数量': len(results)}, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"❌ 批量生成失败: {e}"


def register_tools():
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import tools
    tools.register(name="generate_qr", description="生成二维码。参数: data(内容), output(输出路径), size(大小)", parameters={"type": "object", "properties": {"data": {"type": "string"}, "output": {"type": "string"}, "size": {"type": "integer"}}, "required": ["data"]}, func=_generate_qr)
    tools.register(name="decode_qr", description="识别二维码。参数: path(图片路径)", parameters={"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}, func=_decode_qr)
    tools.register(name="batch_generate_qr", description="批量生成二维码。参数: data(内容列表), output_dir(输出目录)", parameters={"type": "object", "properties": {"data": {"type": "array"}, "output_dir": {"type": "string"}}, "required": ["data"]}, func=_batch_generate_qr)
    return 3


def unregister_tools():
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import tools
    for name in ["generate_qr", "decode_qr", "batch_generate_qr"]:
        tools.TOOLS.pop(name, None)
