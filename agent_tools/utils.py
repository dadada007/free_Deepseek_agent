# -*- coding: utf-8 -*-
"""通用工具模块 - 计算、时间等"""
import ast
import operator as _op
import re
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def calculate(args: dict) -> str:
    """安全数学计算"""
    expr = args.get("expression", "").strip()
    if not expr:
        return "请提供表达式"
    if not re.match(r'^[\d+\-*/%.()\s]+$', expr):
        return f"非法字符: {expr}"
    try:
        ops = {
            ast.Add: _op.add, ast.Sub: _op.sub, ast.Mult: _op.mul,
            ast.Div: _op.truediv, ast.Mod: _op.mod,
            ast.USub: _op.neg, ast.UAdd: _op.pos,
            ast.Pow: _op.pow, ast.FloorDiv: _op.floordiv,
        }
        def eval_node(n):
            if isinstance(n, ast.Expression): return eval_node(n.body)
            if isinstance(n, ast.Constant): return n.value
            if isinstance(n, ast.BinOp): return ops[type(n.op)](eval_node(n.left), eval_node(n.right))
            if isinstance(n, ast.UnaryOp): return ops[type(n.op)](eval_node(n.operand))
            raise ValueError(f"不支持: {type(n).__name__}")
        result = eval_node(ast.parse(expr, mode='eval'))
        if isinstance(result, float) and result.is_integer():
            return str(int(result))
        return str(result)
    except ZeroDivisionError:
        return "除以零"
    except Exception as e:
        return f"计算错误: {e}"

def get_time(args: dict) -> str:
    """获取当前时间"""
    tz_name = args.get("timezone", "Asia/Shanghai")
    try:
        import pytz
        tz_obj = pytz.timezone(tz_name)
        return datetime.now(tz_obj).strftime("%Y-%m-%d %H:%M:%S %Z")
    except Exception:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def now_time(args: dict) -> str:
    """获取当前时间（多种格式）"""
    fmt = args.get("format", "full")
    now = datetime.now()
    formats = {
        "full": "%Y-%m-%d %H:%M:%S",
        "date": "%Y-%m-%d",
        "time": "%H:%M:%S",
        "iso": "%Y-%m-%dT%H:%M:%S",
        "timestamp": "%s",
    }
    try:
        return now.strftime(formats.get(fmt, formats["full"]))
    except Exception:
        return now.strftime("%Y-%m-%d %H:%M:%S")

def date_calc(args: dict) -> str:
    """日期加减计算"""
    date_str = args.get("date", "")
    days = args.get("days", 0)
    fmt = args.get("format", "%Y-%m-%d")
    if not date_str:
        date_str = datetime.now().strftime("%Y-%m-%d")
    try:
        d = datetime.strptime(date_str, "%Y-%m-%d")
        from datetime import timedelta
        result = d + timedelta(days=days)
        return result.strftime(fmt)
    except Exception as e:
        return f"日期计算错误: {e}"

def date_diff(args: dict) -> str:
    """计算日期差"""
    start = args.get("start", "")
    end = args.get("end", "")
    if not start or not end:
        return "需要 start 和 end 参数"
    try:
        d1 = datetime.strptime(start, "%Y-%m-%d")
        d2 = datetime.strptime(end, "%Y-%m-%d")
        diff = (d2 - d1).days
        return f"相差 {diff} 天"
    except Exception as e:
        return f"日期差计算错误: {e}"

def text_stats(args: dict) -> str:
    """统计文本信息"""
    text = args.get("text", "")
    if not text:
        return "请提供文本内容"
    lines = text.count('\n') + 1
    chars = len(text)
    words = len(text.split())
    return f"行数: {lines}, 词数: {words}, 字符数: {chars}"

def register_tools():
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import tools
    tools.register(
        name="calculate",
        description="安全数学计算",
        parameters={"type": "object", "properties": {"expression": {"type": "string"}}, "required": ["expression"]},
        func=calculate
    )
    tools.register(
        name="get_time",
        description="获取当前时间",
        parameters={"type": "object", "properties": {"timezone": {"type": "string"}}},
        func=get_time
    )
    tools.register(
        name="now_time",
        description="获取当前时间（多种格式）",
        parameters={"type": "object", "properties": {"format": {"type": "string", "enum": ["full", "date", "time", "iso", "timestamp"]}}},
        func=now_time
    )
    tools.register(
        name="date_calc",
        description="日期加减计算",
        parameters={"type": "object", "properties": {"date": {"type": "string"}, "days": {"type": "integer"}, "format": {"type": "string"}}},
        func=date_calc
    )
    tools.register(
        name="date_diff",
        description="计算日期差",
        parameters={"type": "object", "properties": {"start": {"type": "string"}, "end": {"type": "string"}}, "required": ["start", "end"]},
        func=date_diff
    )
    tools.register(
        name="text_stats",
        description="统计文本信息",
        parameters={"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]},
        func=text_stats
    )
    return 6