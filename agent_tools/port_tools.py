# -*- coding: utf-8 -*-
"""
端口扫描工具集 - 检查端口是否开放
"""

import json
import socket
import os


def _check_port(args: dict) -> str:
    host = args.get('host', '127.0.0.1')
    port = args.get('port', 80)
    timeout = args.get('timeout', 3)
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        open_status = result == 0
        return json.dumps({'成功': True, '主机': host, '端口': port, '开放': open_status}, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"❌ 检查失败: {e}"


def register_tools():
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import tools
    tools.register(name="check_port", description="检查端口是否开放。参数: host, port, timeout", parameters={"type": "object", "properties": {"host": {"type": "string"}, "port": {"type": "integer"}, "timeout": {"type": "integer"}}}, func=_check_port)
    return 1


def unregister_tools():
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import tools
    for name in ["check_port"]:
        tools.TOOLS.pop(name, None)
