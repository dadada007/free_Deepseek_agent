# -*- coding: utf-8 -*-
"""
邮件解析工具集 - 解析邮件、提取附件
"""

import json
import os
from email import policy
from email.parser import BytesParser


def _parse_email(args: dict) -> str:
    path = args.get('path', '')
    if not path or not os.path.exists(path):
        return "❌ 邮件文件不存在"
    try:
        with open(path, 'rb') as f:
            msg = BytesParser(policy=policy.default).parse(f)
        result = {
            '发件人': msg.get('From', ''),
            '收件人': msg.get('To', ''),
            '主题': msg.get('Subject', ''),
            '日期': msg.get('Date', ''),
            '正文': msg.get_body(preferencelist=('plain', 'html')).get_content()[:500] if msg.get_body() else ''
        }
        return json.dumps({'成功': True, '邮件': result}, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"❌ 解析失败: {e}"


def register_tools():
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import tools
    tools.register(name="parse_email", description="解析邮件内容。参数: path(邮件文件路径)", parameters={"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}, func=_parse_email)
    return 1


def unregister_tools():
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import tools
    for name in ["parse_email"]:
        tools.TOOLS.pop(name, None)
