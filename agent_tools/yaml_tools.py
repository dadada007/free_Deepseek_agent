# -*- coding: utf-8 -*-
"""
YAML处理工具集 - 支持读取、写入、转换
"""

import os
import json


def _import_yaml():
    try:
        import yaml
        return yaml
    except ImportError:
        return None


def _read_yaml(args: dict) -> str:
    path = args.get('path', '')
    if not path or not os.path.exists(path):
        return f"❌ 文件不存在: {path}"
    yaml = _import_yaml()
    if not yaml:
        return "❌ 请安装 pyyaml: pip install pyyaml"
    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = yaml.safe_load(f)
        return json.dumps({'成功': True, '数据': content}, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"❌ 读取失败: {e}"


def _write_yaml(args: dict) -> str:
    path = args.get('path', '')
    content = args.get('data', {})
    if not path:
        return "❌ 请提供输出路径"
    yaml = _import_yaml()
    if not yaml:
        return "❌ 请安装 pyyaml"
    try:
        with open(path, 'w', encoding='utf-8') as f:
            yaml.dump(content, f, allow_unicode=True)
        return json.dumps({'成功': True, '输出': path}, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"❌ 写入失败: {e}"


def register_tools():
    """注册工具到 Hermes"""
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import tools

    tools.register(
        name="read_yaml",
        description="读取YAML文件。参数: path(文件路径)",
        parameters={"type": "object", "properties": {
            "path": {"type": "string", "description": "YAML文件路径"}
        }, "required": ["path"]},
        func=_read_yaml,
    )
    tools.register(
        name="write_yaml",
        description="写入YAML文件。参数: path(输出路径), data(数据)",
        parameters={"type": "object", "properties": {
            "path": {"type": "string", "description": "输出文件路径"},
            "data": {"type": "object", "description": "要写入的数据"}
        }, "required": ["path", "data"]},
        func=_write_yaml,
    )
    return 2


def unregister_tools():
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import tools
    for name in ["read_yaml", "write_yaml"]:
        tools.TOOLS.pop(name, None)
