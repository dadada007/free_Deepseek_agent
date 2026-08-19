# -*- coding: utf-8 -*-
"""
数据验证工具集 - 验证邮箱、手机号、URL、IP等格式
"""

import json
import re
import os


def _validate_email(args: dict) -> str:
    email_addr = args.get('email', '')
    if not email_addr:
        return "❌ 请提供邮箱地址"
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    is_valid = bool(re.match(pattern, email_addr))
    return json.dumps({'成功': True, '邮箱': email_addr, '有效': is_valid}, ensure_ascii=False, indent=2)


def _validate_phone(args: dict) -> str:
    phone = args.get('phone', '')
    if not phone:
        return "❌ 请提供手机号"
    pattern = r'^1[3-9]\d{9}$'
    is_valid = bool(re.match(pattern, phone))
    return json.dumps({'成功': True, '手机号': phone, '有效': is_valid}, ensure_ascii=False, indent=2)


def _validate_url(args: dict) -> str:
    url = args.get('url', '')
    if not url:
        return "❌ 请提供URL"
    pattern = r'^https?://[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(/.*)?$'
    is_valid = bool(re.match(pattern, url))
    return json.dumps({'成功': True, 'URL': url, '有效': is_valid}, ensure_ascii=False, indent=2)


def _validate_ip(args: dict) -> str:
    ip = args.get('ip', '')
    if not ip:
        return "❌ 请提供IP地址"
    parts = ip.split('.')
    if len(parts) != 4:
        is_valid = False
    else:
        is_valid = all(p.isdigit() and 0 <= int(p) <= 255 for p in parts)
    return json.dumps({'成功': True, 'IP': ip, '有效': is_valid}, ensure_ascii=False, indent=2)


def register_tools():
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import tools
    tools.register(name="validate_email", description="验证邮箱格式。参数: email", parameters={"type": "object", "properties": {"email": {"type": "string"}}, "required": ["email"]}, func=_validate_email)
    tools.register(name="validate_phone", description="验证手机号格式。参数: phone", parameters={"type": "object", "properties": {"phone": {"type": "string"}}, "required": ["phone"]}, func=_validate_phone)
    tools.register(name="validate_url", description="验证URL格式。参数: url", parameters={"type": "object", "properties": {"url": {"type": "string"}}, "required": ["url"]}, func=_validate_url)
    tools.register(name="validate_ip", description="验证IP地址格式。参数: ip", parameters={"type": "object", "properties": {"ip": {"type": "string"}}, "required": ["ip"]}, func=_validate_ip)
    return 4


def unregister_tools():
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import tools
    for name in ["validate_email", "validate_phone", "validate_url", "validate_ip"]:
        tools.TOOLS.pop(name, None)
