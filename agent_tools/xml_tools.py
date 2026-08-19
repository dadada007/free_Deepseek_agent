# -*- coding: utf-8 -*-
"""
XML处理工具集 - 支持解析、生成、查询
"""

import json
import os
import xml.etree.ElementTree as ET


def _parse_xml(args: dict) -> str:
    xml_str = args.get('xml', '')
    if not xml_str:
        return "❌ 请提供XML内容"
    try:
        root = ET.fromstring(xml_str)
        result = {'根元素': root.tag}
        for child in root:
            result[child.tag] = child.text
        return json.dumps({'成功': True, '结果': result}, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"❌ 解析失败: {e}"


def _create_xml(args: dict) -> str:
    root_tag = args.get('root', 'root')
    elements = args.get('elements', {})
    try:
        root = ET.Element(root_tag)
        for key, value in elements.items():
            child = ET.SubElement(root, key)
            child.text = str(value)
        xml_str = ET.tostring(root, encoding='unicode')
        return json.dumps({'成功': True, 'XML': xml_str}, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"❌ 生成失败: {e}"


def register_tools():
    """注册工具到 Hermes"""
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import tools

    tools.register(
        name="parse_xml",
        description="解析XML内容。参数: xml(XML字符串)",
        parameters={"type": "object", "properties": {
            "xml": {"type": "string", "description": "XML字符串"}
        }, "required": ["xml"]},
        func=_parse_xml,
    )
    tools.register(
        name="create_xml",
        description="生成XML内容。参数: root(根元素名), elements(键值对)",
        parameters={"type": "object", "properties": {
            "root": {"type": "string", "description": "根元素名"},
            "elements": {"type": "object", "description": "元素键值对"}
        }},
        func=_create_xml,
    )
    return 2


def unregister_tools():
    """卸载工具"""
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import tools
    for name in ["parse_xml", "create_xml"]:
        tools.TOOLS.pop(name, None)
