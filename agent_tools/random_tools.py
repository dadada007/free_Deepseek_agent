# -*- coding: utf-8 -*-
"""
随机数据生成工具集 - 支持随机数、随机字符串、随机日期等
"""

import json
import random
import string
from datetime import datetime, timedelta
import os


def _random_number(args: dict) -> str:
    min_val = args.get('min', 0)
    max_val = args.get('max', 100)
    count = args.get('count', 1)
    result = [random.randint(min_val, max_val) for _ in range(count)]
    return json.dumps({'成功': True, '结果': result if count > 1 else result[0]}, ensure_ascii=False, indent=2)


def _random_string(args: dict) -> str:
    length = args.get('length', 10)
    chars = args.get('chars', string.ascii_letters + string.digits)
    result = ''.join(random.choices(chars, k=length))
    return json.dumps({'成功': True, '结果': result}, ensure_ascii=False, indent=2)


def _random_date(args: dict) -> str:
    start = args.get('start', '2020-01-01')
    end = args.get('end', '2030-12-31')
    start_dt = datetime.strptime(start, '%Y-%m-%d')
    end_dt = datetime.strptime(end, '%Y-%m-%d')
    delta = end_dt - start_dt
    random_days = random.randint(0, delta.days)
    result = start_dt + timedelta(days=random_days)
    return json.dumps({'成功': True, '结果': result.strftime('%Y-%m-%d')}, ensure_ascii=False, indent=2)


def register_tools():
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import tools
    tools.register(name="random_number", description="生成随机数。参数: min, max, count", parameters={"type": "object", "properties": {"min": {"type": "integer"}, "max": {"type": "integer"}, "count": {"type": "integer"}}}, func=_random_number)
    tools.register(name="random_string", description="生成随机字符串。参数: length, chars", parameters={"type": "object", "properties": {"length": {"type": "integer"}, "chars": {"type": "string"}}}, func=_random_string)
    tools.register(name="random_date", description="生成随机日期。参数: start, end(YYYY-MM-DD)", parameters={"type": "object", "properties": {"start": {"type": "string"}, "end": {"type": "string"}}}, func=_random_date)
    return 3


def unregister_tools():
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import tools
    for name in ["random_number", "random_string", "random_date"]:
        tools.TOOLS.pop(name, None)
