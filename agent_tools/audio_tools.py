# -*- coding: utf-8 -*-
"""
音频处理工具集 - 获取音频信息
"""

import json
import os


def _audio_info(args: dict) -> str:
    path = args.get('path', '')
    if not path or not os.path.exists(path):
        return "❌ 音频文件不存在"
    try:
        from mutagen import File
        audio = File(path)
        if audio is None:
            return "❌ 无法读取音频信息"
        info = {
            '文件': path,
            '大小': f"{os.path.getsize(path) / 1024:.2f} KB",
            '时长': audio.info.length if hasattr(audio.info, 'length') else '未知',
            '采样率': audio.info.sample_rate if hasattr(audio.info, 'sample_rate') else '未知',
            '比特率': audio.info.bitrate if hasattr(audio.info, 'bitrate') else '未知',
        }
        return json.dumps({'成功': True, '信息': info}, ensure_ascii=False, indent=2)
    except ImportError:
        return "❌ 请安装 mutagen: pip install mutagen"
    except Exception as e:
        return f"❌ 获取失败: {e}"


def register_tools():
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import tools
    tools.register(
        name="audio_info",
        description="获取音频信息。参数: path(音频文件路径)",
        parameters={"type": "object", "properties": {
            "path": {"type": "string", "description": "音频文件路径"}
        }, "required": ["path"]},
        func=_audio_info,
    )
    return 1


def unregister_tools():
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import tools
    for name in ["audio_info"]:
        tools.TOOLS.pop(name, None)
