# -*- coding: utf-8 -*-
"""
图片处理工具集 - 支持格式转换、裁剪、缩放、水印、拼接、滤镜
"""

import os
import json


def _import_PIL():
    try:
        from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
        return Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
    except ImportError:
        return None


def _get_supported_formats():
    return ['png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp', 'tiff', 'ico']


def _is_image_file(path):
    ext = os.path.splitext(path)[1].lower().replace('.', '')
    return ext in _get_supported_formats()


def _image_info(args: dict) -> str:
    try:
        path = args.get('path', '')
        if not path:
            return "❌ 请提供图片路径"
        if not os.path.exists(path):
            return f"❌ 文件不存在: {path}"
        PIL = _import_PIL()
        if not PIL:
            return "❌ 请安装 Pillow: pip install Pillow"
        Image = PIL[0]
        img = Image.open(path)
        info = {'路径': path, '尺寸': f"{img.width} x {img.height}", '格式': img.format, '模式': img.mode, '文件大小': f"{os.path.getsize(path) / 1024:.1f} KB"}
        return json.dumps(info, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"❌ 获取图片信息失败: {e}"


def _convert_image(args: dict) -> str:
    try:
        path = args.get('path', '')
        output_format = args.get('format', '').lower().replace('.', '')
        output_path = args.get('output', '')
        if not path:
            return "❌ 请提供图片路径"
        if not output_format:
            return "❌ 请提供目标格式"
        if not os.path.exists(path):
            return f"❌ 文件不存在: {path}"
        PIL = _import_PIL()
        if not PIL:
            return "❌ 请安装 Pillow: pip install Pillow"
        Image = PIL[0]
        if not output_path:
            base = os.path.splitext(path)[0]
            output_path = f"{base}.{output_format}"
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        img = Image.open(path)
        if output_format in ['jpg', 'jpeg'] and img.mode == 'RGBA':
            rgb_img = Image.new('RGB', img.size, (255, 255, 255))
            rgb_img.paste(img, mask=img.split()[3])
            img = rgb_img
        img.save(output_path, format=output_format.upper())
        return json.dumps({'success': True, '输入': path, '输出': output_path, '格式': output_format}, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"❌ 转换失败: {e}"


def _resize_image(args: dict) -> str:
    try:
        path = args.get('path', '')
        width = args.get('width', 0)
        height = args.get('height', 0)
        keep_ratio = args.get('keep_ratio', True)
        output_path = args.get('output', '')
        if not path:
            return "❌ 请提供图片路径"
        if not os.path.exists(path):
            return f"❌ 文件不存在: {path}"
        if width <= 0 and height <= 0:
            return "❌ 请提供至少一个有效的尺寸"
        PIL = _import_PIL()
        if not PIL:
            return "❌ 请安装 Pillow: pip install Pillow"
        Image = PIL[0]
        img = Image.open(path)
        orig_width, orig_height = img.size
        if width <= 0:
            ratio = height / orig_height
            width = int(orig_width * ratio)
        elif height <= 0:
            ratio = width / orig_width
            height = int(orig_height * ratio)
        elif keep_ratio:
            ratio = min(width / orig_width, height / orig_height)
            width = int(orig_width * ratio)
            height = int(orig_height * ratio)
        if not output_path:
            base = os.path.splitext(path)[0]
            ext = os.path.splitext(path)[1]
            output_path = f"{base}_resized{ext}"
        resized = img.resize((width, height), Image.LANCZOS)
        resized.save(output_path)
        return json.dumps({'success': True, '输入': path, '输出': output_path, '新尺寸': f"{width} x {height}"}, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"❌ 缩放失败: {e}"


def _crop_image(args: dict) -> str:
    try:
        path = args.get('path', '')
        x = args.get('x', 0)
        y = args.get('y', 0)
        width = args.get('width', 0)
        height = args.get('height', 0)
        output_path = args.get('output', '')
        if not path or not os.path.exists(path):
            return "❌ 图片不存在"
        if width <= 0 or height <= 0:
            return "❌ 请提供有效的裁剪尺寸"
        PIL = _import_PIL()
        if not PIL:
            return "❌ 请安装 Pillow: pip install Pillow"
        Image = PIL[0]
        img = Image.open(path)
        if not output_path:
            base = os.path.splitext(path)[0]
            ext = os.path.splitext(path)[1]
            output_path = f"{base}_cropped{ext}"
        cropped = img.crop((x, y, x + width, y + height))
        cropped.save(output_path)
        return json.dumps({'success': True, '输入': path, '输出': output_path, '裁剪区域': f"({x},{y}) {width}x{height}"}, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"❌ 裁剪失败: {e}"


def register_tools():
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import tools
    tools.register(name="image_info", description="获取图片信息。参数: path(图片路径)", parameters={"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}, func=_image_info)
    tools.register(name="convert_image", description="转换图片格式。参数: path, format, output", parameters={"type": "object", "properties": {"path": {"type": "string"}, "format": {"type": "string"}, "output": {"type": "string"}}, "required": ["path", "format"]}, func=_convert_image)
    tools.register(name="resize_image", description="缩放图片。参数: path, width, height, keep_ratio", parameters={"type": "object", "properties": {"path": {"type": "string"}, "width": {"type": "integer"}, "height": {"type": "integer"}, "keep_ratio": {"type": "boolean"}}, "required": ["path"]}, func=_resize_image)
    tools.register(name="crop_image", description="裁剪图片。参数: path, x, y, width, height", parameters={"type": "object", "properties": {"path": {"type": "string"}, "x": {"type": "integer"}, "y": {"type": "integer"}, "width": {"type": "integer"}, "height": {"type": "integer"}}, "required": ["path", "width", "height"]}, func=_crop_image)
    return 4


def unregister_tools():
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import tools
    for name in ["image_info", "convert_image", "resize_image", "crop_image"]:
        tools.TOOLS.pop(name, None)
