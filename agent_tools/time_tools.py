# -*- coding: utf-8 -*-
"""
日期时间工具集 - 支持日期计算、格式转换、时区处理
"""

import json
import os
from datetime import datetime, timedelta
import calendar


def _date_calc(args: dict) -> str:
    try:
        date_str = args.get('date')
        days = args.get('days', 0)
        fmt = args.get('format', '%Y-%m-%d')
        if date_str:
            base_date = datetime.strptime(date_str, '%Y-%m-%d')
        else:
            base_date = datetime.now()
        result_date = base_date + timedelta(days=days)
        return json.dumps({'成功': True, '原始日期': base_date.strftime(fmt) if date_str else '今天', '天数变化': days, '结果日期': result_date.strftime(fmt)}, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"❌ 日期计算失败: {e}"


def _date_diff(args: dict) -> str:
    try:
        start = args.get('start', '')
        end = args.get('end', '')
        if not start:
            return "❌ 请提供开始日期"
        if not end:
            return "❌ 请提供结束日期"
        start_date = datetime.strptime(start, '%Y-%m-%d')
        end_date = datetime.strptime(end, '%Y-%m-%d')
        delta = end_date - start_date
        return json.dumps({'成功': True, '开始日期': start, '结束日期': end, '天数差': delta.days}, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"❌ 计算日期差失败: {e}"


def _now_time(args: dict) -> str:
    try:
        fmt = args.get('format', 'full')
        now = datetime.now()
        formats = {
            'full': now.strftime('%Y-%m-%d %H:%M:%S'),
            'date': now.strftime('%Y-%m-%d'),
            'time': now.strftime('%H:%M:%S'),
            'iso': now.isoformat(),
            'timestamp': int(now.timestamp())
        }
        if fmt not in formats:
            return f"❌ 不支持的格式: {fmt}"
        return json.dumps({'成功': True, '当前时间': formats[fmt], '星期': now.strftime('%A')}, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"❌ 获取时间失败: {e}"


def register_tools():
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import tools
    tools.register(name="date_calc", description="日期加减计算。参数: date, days, format", parameters={"type": "object", "properties": {"date": {"type": "string"}, "days": {"type": "integer"}, "format": {"type": "string"}}}, func=_date_calc)
    tools.register(name="date_diff", description="计算日期差。参数: start, end(YYYY-MM-DD)", parameters={"type": "object", "properties": {"start": {"type": "string"}, "end": {"type": "string"}}, "required": ["start", "end"]}, func=_date_diff)
    tools.register(name="now_time", description="获取当前时间。参数: format(full/date/time/iso/timestamp)", parameters={"type": "object", "properties": {"format": {"type": "string"}}}, func=_now_time)
    return 3


def unregister_tools():
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import tools
    for name in ["date_calc", "date_diff", "now_time"]:
        tools.TOOLS.pop(name, None)
