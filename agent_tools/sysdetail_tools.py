# -*- coding: utf-8 -*-
"""
系统信息详情工具集 - 获取CPU、内存、磁盘详细信息
"""

import json
import os
import platform


def _sys_info_detail(args: dict) -> str:
    try:
        import psutil
    except:
        return "❌ 请安装 psutil: pip install psutil"
    result = {
        '系统': platform.system(),
        '主机名': platform.node(),
        'CPU核心数': psutil.cpu_count(),
        'CPU使用率': f"{psutil.cpu_percent(interval=0.5)}%",
        '内存总数': f"{psutil.virtual_memory().total / (1024**3):.2f} GB",
        '内存已用': f"{psutil.virtual_memory().used / (1024**3):.2f} GB",
        '内存使用率': f"{psutil.virtual_memory().percent}%",
        '磁盘': []
    }
    for partition in psutil.disk_partitions():
        try:
            usage = psutil.disk_usage(partition.mountpoint)
            result['磁盘'].append({
                '挂载点': partition.mountpoint,
                '总空间': f"{usage.total / (1024**3):.2f} GB",
                '已用': f"{usage.used / (1024**3):.2f} GB",
                '使用率': f"{usage.percent}%"
            })
        except:
            pass
    return json.dumps({'成功': True, '信息': result}, ensure_ascii=False, indent=2)


def register_tools():
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import tools
    tools.register(name="sys_info_detail", description="获取系统详细信息（CPU、内存、磁盘）", parameters={"type": "object", "properties": {}}, func=_sys_info_detail)
    return 1


def unregister_tools():
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import tools
    for name in ["sys_info_detail"]:
        tools.TOOLS.pop(name, None)
