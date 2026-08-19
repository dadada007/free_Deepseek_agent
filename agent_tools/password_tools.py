# -*- coding: utf-8 -*-
"""
密码生成工具集 - 支持生成强密码、密码强度检测
"""

import json
import random
import string
import re
import os


def _generate_password(args: dict) -> str:
    length = args.get('length', 16)
    include_upper = args.get('upper', True)
    include_lower = args.get('lower', True)
    include_digits = args.get('digits', True)
    include_symbols = args.get('symbols', True)
    chars = ''
    if include_upper:
        chars += string.ascii_uppercase
    if include_lower:
        chars += string.ascii_lowercase
    if include_digits:
        chars += string.digits
    if include_symbols:
        chars += '!@#$%^&*()_+-=[]{}|;:,.<>?'
    if not chars:
        return "❌ 至少选择一种字符类型"
    password = ''.join(random.choices(chars, k=length))
    return json.dumps({'成功': True, '密码': password}, ensure_ascii=False, indent=2)


def _check_password_strength(args: dict) -> str:
    password = args.get('password', '')
    if not password:
        return "❌ 请提供密码"
    score = 0
    if len(password) >= 8:
        score += 1
    if re.search(r'[A-Z]', password):
        score += 1
    if re.search(r'[a-z]', password):
        score += 1
    if re.search(r'\d', password):
        score += 1
    if re.search(r'[!@#$%^&*()]', password):
        score += 1
    levels = ['极弱', '弱', '一般', '强', '极强']
    return json.dumps({'成功': True, '强度': levels[score], '得分': score}, ensure_ascii=False, indent=2)


def register_tools():
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import tools
    tools.register(name="generate_password", description="生成强密码。参数: length, upper, lower, digits, symbols", parameters={"type": "object", "properties": {"length": {"type": "integer"}, "upper": {"type": "boolean"}, "lower": {"type": "boolean"}, "digits": {"type": "boolean"}, "symbols": {"type": "boolean"}}}, func=_generate_password)
    tools.register(name="check_password_strength", description="检测密码强度。参数: password", parameters={"type": "object", "properties": {"password": {"type": "string"}}, "required": ["password"]}, func=_check_password_strength)
    return 2


def unregister_tools():
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import tools
    for name in ["generate_password", "check_password_strength"]:
        tools.TOOLS.pop(name, None)
