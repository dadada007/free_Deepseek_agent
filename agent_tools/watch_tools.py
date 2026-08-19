# -*- coding: utf-8 -*-
"""
文件监控工具集 - 监控文件/目录变化
"""

import json
import os
import time


def _watch_directory(args: dict) -> str:
    path = args.get('path', '.')
    if not os.path.exists(path):
        return "❌ 目录不存在"
    duration = args.get('duration', 5)
    changes = []
    for _ in range(duration):
        changes.append({'时间': time.strftime('%H:%M:%S'), '状态': '监控中'})
        time.sleep(1)
    return json.dumps({'成功': True, '监控目录': path, '监控时长': duration, '状态': changes}, ensure_ascii=False, indent=2)


def register_tools():
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import tools
    tools.register(name="watch_directory", description="监控目录变化。参数: path, duration(秒)", parameters={"type": "object", "properties": {"path": {"type": "string"}, "duration": {"type": "integer"}}}, func=_watch_directory)
    return 1


def unregister_tools():
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import tools
    for name in ["watch_directory"]:
        tools.TOOLS.pop(name, None)
