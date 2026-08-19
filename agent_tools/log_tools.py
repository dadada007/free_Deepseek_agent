# -*- coding: utf-8 -*-
"""
日志工具集 - 热加载示例
放到 agent_tools/ 目录下会被自动加载

用法示例：
  write_log: {"message": "测试", "level": "INFO"}
  read_log:  {"lines": 50, "keyword": "error"}
  analyze_log: {"lines": 1000}
  clear_log: {}
"""
import os
import json
import logging
from datetime import datetime
from collections import Counter

logger = logging.getLogger(__name__)

_LOG_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "agent_tools.log")


def _write_log(args: dict) -> str:
    message = args.get("message", "")
    level = args.get("level", "INFO").upper()
    if not message:
        return "错误: 请提供 message"
    try:
        with open(_LOG_FILE, "a", encoding="utf-8") as f:
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"[{ts}] [{level}] {message}\n")
        return f"✅ 已写入日志: [{level}] {message[:80]}"
    except Exception as e:
        return f"❌ 写入失败: {e}"


def _read_log(args: dict) -> str:
    lines = args.get("lines", 50)
    level = args.get("level", "")
    keyword = args.get("keyword", "")
    if not os.path.exists(_LOG_FILE):
        return "日志文件不存在"
    try:
        with open(_LOG_FILE, "r", encoding="utf-8") as f:
            all_lines = f.readlines()
        filtered = all_lines[-lines * 5:]
        if level:
            filtered = [l for l in filtered if level.upper() in l]
        if keyword:
            filtered = [l for l in filtered if keyword.lower() in l.lower()]
        return f"共 {len(all_lines)} 行，匹配 {len(filtered)} 行:\n" + "\n".join(filtered[-lines:])
    except Exception as e:
        return f"❌ 读取失败: {e}"


def _analyze_log(args: dict) -> str:
    n = args.get("lines", 1000)
    if not os.path.exists(_LOG_FILE):
        return "日志文件不存在"
    try:
        with open(_LOG_FILE, "r", encoding="utf-8") as f:
            lines = f.readlines()[-n:]
        levels = Counter()
        errors = []
        for l in lines:
            for lv in ["INFO", "WARNING", "ERROR", "DEBUG"]:
                if lv in l:
                    levels[lv] += 1
                    break
            if "ERROR" in l:
                errors.append(l.strip()[:200])
        return json.dumps({"分析行数": len(lines), "级别统计": dict(levels), "错误示例": errors[:10]},
                          ensure_ascii=False, indent=2)
    except Exception as e:
        return f"❌ 分析失败: {e}"


def _clear_log(args: dict) -> str:
    try:
        if os.path.exists(_LOG_FILE):
            with open(_LOG_FILE, "w", encoding="utf-8") as f:
                f.write("")
        return "✅ 日志已清空"
    except Exception as e:
        return f"❌ 清空失败: {e}"


def register_tools():
    """注册日志工具到 Hermes"""
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import tools

    tools.register(
        name="write_log",
        description="写入日志。参数: message(日志内容), level(INFO/WARNING/ERROR/DEBUG)",
        parameters={"type": "object", "properties": {
            "message": {"type": "string", "description": "日志内容"},
            "level": {"type": "string", "description": "日志级别"}
        }, "required": ["message"]},
        func=_write_log,
    )
    tools.register(
        name="read_log",
        description="查看日志。参数: lines(行数), level(过滤级别), keyword(关键词)",
        parameters={"type": "object", "properties": {
            "lines": {"type": "integer", "description": "显示行数"},
            "level": {"type": "string", "description": "过滤级别"},
            "keyword": {"type": "string", "description": "关键词"}
        }},
        func=_read_log,
    )
    tools.register(
        name="analyze_log",
        description="分析日志统计（级别分布、错误汇总）",
        parameters={"type": "object", "properties": {
            "lines": {"type": "integer", "description": "分析行数"}
        }},
        func=_analyze_log,
    )
    tools.register(
        name="clear_log",
        description="清空日志文件",
        parameters={"type": "object", "properties": {}},
        func=_clear_log,
    )
    return 4


def unregister_tools():
    """卸载工具（热加载重载时调用）"""
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import tools
    for name in ["write_log", "read_log", "analyze_log", "clear_log"]:
        tools.TOOLS.pop(name, None)
