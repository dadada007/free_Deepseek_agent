# -*- coding: utf-8 -*-
"""
视频处理工具集 - 获取视频信息
"""

import json
import os


def _video_info(args: dict) -> str:
    path = args.get('path', '')
    if not path or not os.path.exists(path):
        return "❌ 视频文件不存在"
    try:
        from moviepy.editor import VideoFileClip
        clip = VideoFileClip(path)
        info = {
            '文件': path,
            '大小': f"{os.path.getsize(path) / (1024*1024):.2f} MB",
            '时长': f"{clip.duration:.2f} 秒",
            '宽度': clip.w,
            '高度': clip.h,
            '帧率': clip.fps
        }
        clip.close()
        return json.dumps({'成功': True, '信息': info}, ensure_ascii=False, indent=2)
    except ImportError:
        return "❌ 请安装 moviepy: pip install moviepy"
    except Exception as e:
        return f"❌ 获取失败: {e}"


def register_tools():
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import tools
    tools.register(name="video_info", description="获取视频信息。参数: path(视频文件路径)", parameters={"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}, func=_video_info)
    return 1


def unregister_tools():
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import tools
    for name in ["video_info"]:
        tools.TOOLS.pop(name, None)
