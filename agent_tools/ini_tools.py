# -*- coding: utf-8 -*-
"""
INI配置文件管理工具集 - 支持读取、写入、修改配置
"""

import os
import json
import configparser


def _read_ini(args: dict) -> str:
    try:
        path = args.get('path', '')
        if not path:
            return "❌ 请提供配置文件路径"
        if not os.path.exists(path):
            return f"❌ 文件不存在: {path}"
        config = configparser.ConfigParser()
        config.read(path, encoding='utf-8')
        result = {}
        for section in config.sections():
            result[section] = dict(config.items(section))
        return json.dumps({'成功': True, '文件': path, '配置': result}, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"❌ 读取INI失败: {e}"


def _write_ini(args: dict) -> str:
    try:
        path = args.get('path', '')
        config_data = args.get('config', {})
        if not path:
            return "❌ 请提供配置文件路径"
        if not config_data:
            return "❌ 请提供配置数据"
        config = configparser.ConfigParser()
        for section, values in config_data.items():
            if not config.has_section(section):
                config.add_section(section)
            for key, value in values.items():
                config.set(section, str(key), str(value))
        with open(path, 'w', encoding='utf-8') as f:
            config.write(f)
        return json.dumps({'成功': True, '输出': path, '写入段数': len(config_data)}, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"❌ 写入INI失败: {e}"


def _set_ini_value(args: dict) -> str:
    try:
        path = args.get('path', '')
        section = args.get('section', 'DEFAULT')
        key = args.get('key', '')
        value = args.get('value', '')
        if not path:
            return "❌ 请提供配置文件路径"
        if not key:
            return "❌ 请提供配置键名"
        config = configparser.ConfigParser()
        config.read(path, encoding='utf-8')
        if not config.has_section(section):
            config.add_section(section)
        config.set(section, key, str(value))
        with open(path, 'w', encoding='utf-8') as f:
            config.write(f)
        return json.dumps({'成功': True, '文件': path, '段': section, '键': key, '值': value}, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"❌ 修改配置失败: {e}"


def register_tools():
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import tools
    tools.register(name="read_ini", description="读取INI配置文件。参数: path", parameters={"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}, func=_read_ini)
    tools.register(name="write_ini", description="写入INI配置文件。参数: path, config", parameters={"type": "object", "properties": {"path": {"type": "string"}, "config": {"type": "object"}}, "required": ["path", "config"]}, func=_write_ini)
    tools.register(name="set_ini_value", description="修改INI配置值。参数: path, section, key, value", parameters={"type": "object", "properties": {"path": {"type": "string"}, "section": {"type": "string"}, "key": {"type": "string"}, "value": {"type": "string"}}, "required": ["path", "key", "value"]}, func=_set_ini_value)
    return 3


def unregister_tools():
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import tools
    for name in ["read_ini", "write_ini", "set_ini_value"]:
        tools.TOOLS.pop(name, None)
