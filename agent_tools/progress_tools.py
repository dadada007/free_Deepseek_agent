# -*- coding: utf-8 -*-
"""
进度条工具集 - 支持控制台进度条显示
"""

import json
import time
import os


def _show_progress(args: dict) -> str:
    total = args.get('total', 100)
    delay = args.get('delay', 0.05)
    label = args.get('label', '处理中')
    for i in range(total + 1):
        pct = i / total * 100
        bar = '█' * int(pct // 2) + '░' * (50 - int(pct // 2))
        print(f'\r{label}: [{bar}] {pct:.1f}%', end='')
        time.sleep(delay)
    print()
    return json.dumps({'成功': True, '消息': '进度完成'}, ensure_ascii=False, indent=2)


def register_tools():
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import tools
    tools.register(name="show_progress", description="显示进度条。参数: total, delay, label", parameters={"type": "object", "properties": {"total": {"type": "integer"}, "delay": {"type": "number"}, "label": {"type": "string"}}}, func=_show_progress)
    return 1


def unregister_tools():
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import tools
    for name in ["show_progress"]:
        tools.TOOLS.pop(name, None)
