# -*- coding: utf-8 -*-
"""
GIF处理工具集 - 生成GIF动图
"""

import json
import os


def _create_gif(args: dict) -> str:
    images = args.get('images', [])
    output = args.get('output', 'output.gif')
    duration = args.get('duration', 500)
    if not images:
        return "❌ 请提供图片列表"
    try:
        from PIL import Image
        frames = []
        for img_path in images:
            img = Image.open(img_path)
            frames.append(img)
        frames[0].save(output, save_all=True, append_images=frames[1:], duration=duration, loop=0)
        return json.dumps({'成功': True, '输出': output}, ensure_ascii=False, indent=2)
    except ImportError:
        return "❌ 请安装 Pillow: pip install Pillow"
    except Exception as e:
        return f"❌ 生成失败: {e}"


def register_tools():
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import tools
    tools.register(
        name="create_gif",
        description="生成GIF动图。参数: images(图片路径列表), output(输出路径), duration(帧间隔ms)",
        parameters={"type": "object", "properties": {
            "images": {"type": "array", "description": "图片文件路径列表"},
            "output": {"type": "string", "description": "输出GIF路径"},
            "duration": {"type": "integer", "description": "帧间隔毫秒"}
        }, "required": ["images"]},
        func=_create_gif,
    )
    return 1


def unregister_tools():
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import tools
    for name in ["create_gif"]:
        tools.TOOLS.pop(name, None)
