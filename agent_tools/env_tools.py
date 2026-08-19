# -*- coding: utf-8 -*-
"""
环境变量管理工具集 - 支持查看、设置、删除环境变量
"""

import os
import json


def _get_env(args: dict) -> str:
    try:
        key = args.get('key', '')
        if key:
            value = os.environ.get(key)
            if value is None:
                return f"❌ 环境变量 '{key}' 不存在"
            return json.dumps({'成功': True, '键': key, '值': value}, ensure_ascii=False, indent=2)
        else:
            env = {}
            sensitive = ['PASSWORD', 'SECRET', 'KEY', 'TOKEN', 'AUTH']
            for k, v in os.environ.items():
                if any(s in k.upper() for s in sensitive):
                    env[k] = '***已隐藏***'
                else:
                    env[k] = v[:200] + '...' if len(v) > 200 else v
            return json.dumps({'成功': True, '环境变量数量': len(env), '变量': env}, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"❌ 查看环境变量失败: {e}"


def _set_env(args: dict) -> str:
    try:
        key = args.get('key', '')
        value = args.get('value', '')
        if not key:
            return "❌ 请提供环境变量名"
        os.environ[key] = value
        return json.dumps({'成功': True, '键': key, '值': value[:50] + '...' if len(value) > 50 else value}, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"❌ 设置环境变量失败: {e}"


def _delete_env(args: dict) -> str:
    try:
        key = args.get('key', '')
        if not key:
            return "❌ 请提供环境变量名"
        if key in os.environ:
            del os.environ[key]
            return json.dumps({'成功': True, '键': key, '状态': '已删除'}, ensure_ascii=False, indent=2)
        else:
            return f"❌ 环境变量 '{key}' 不存在"
    except Exception as e:
        return f"❌ 删除环境变量失败: {e}"


def register_tools():
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import tools
    tools.register(name="get_env", description="查看环境变量。参数: key(可选)", parameters={"type": "object", "properties": {"key": {"type": "string"}}}, func=_get_env)
    tools.register(name="set_env", description="设置环境变量。参数: key, value", parameters={"type": "object", "properties": {"key": {"type": "string"}, "value": {"type": "string"}}, "required": ["key", "value"]}, func=_set_env)
    tools.register(name="delete_env", description="删除环境变量。参数: key", parameters={"type": "object", "properties": {"key": {"type": "string"}}, "required": ["key"]}, func=_delete_env)
    return 3


def unregister_tools():
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import tools
    for name in ["get_env", "set_env", "delete_env"]:
        tools.TOOLS.pop(name, None)
