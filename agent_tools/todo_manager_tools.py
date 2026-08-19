# -*- coding: utf-8 -*-
"""待办管理模块"""
import os
import json
import logging
from datetime import datetime
from typing import List, Dict

logger = logging.getLogger(__name__)

_TODO_FILE = "hermes_todos.json"
_todos: List[Dict] = []

def _load_todos():
    """加载待办列表"""
    global _todos
    if os.path.exists(_TODO_FILE):
        try:
            with open(_TODO_FILE, 'r', encoding='utf-8') as f:
                _todos = json.load(f)
                return
        except Exception:
            pass
    _todos = []

def _save_todos():
    """保存待办列表"""
    try:
        with open(_TODO_FILE, 'w', encoding='utf-8') as f:
            json.dump(_todos, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"保存待办失败: {e}")

def _find_todo(content: str) -> int:
    """查找待办项"""
    _load_todos()
    for i, t in enumerate(_todos):
        if t.get("content", "") == content:
            return i
    return -1

def _todo_add(args: dict) -> str:
    """添加待办"""
    content = args.get("content", "")
    if not content:
        return "错误: 缺少 content 参数"
    _load_todos()
    if _find_todo(content) != -1:
        return f"待办已存在: {content}"
    _todos.append({
        "content": content,
        "status": "pending",
        "created": datetime.now().isoformat()
    })
    _save_todos()
    return f"已添加待办: {content}"

def _todo_start(args: dict) -> str:
    """开始执行待办"""
    content = args.get("content", "")
    if not content:
        return "错误: 缺少 content 参数"
    _load_todos()
    idx = _find_todo(content)
    if idx == -1:
        return f"待办不存在: {content}"
    _todos[idx]["status"] = "in_progress"
    _todos[idx]["started"] = datetime.now().isoformat()
    _save_todos()
    return f"已开始执行: {content}"

def _todo_complete(args: dict) -> str:
    """标记待办完成"""
    content = args.get("content", "")
    if not content:
        return "错误: 缺少 content 参数"
    _load_todos()
    idx = _find_todo(content)
    if idx == -1:
        return f"待办不存在: {content}"
    _todos[idx]["status"] = "completed"
    _todos[idx]["completed"] = datetime.now().isoformat()
    _save_todos()
    return f"已完成: {content}"

def _todo_list_fn(args: dict) -> str:
    """查看所有待办"""
    _load_todos()
    if not _todos:
        return "暂无待办"
    result = []
    for t in _todos:
        status = t.get("status", "pending")
        content = t.get("content", "")
        icon = {"pending": "⏳", "in_progress": "🔄", "completed": "✅"}.get(status, "❓")
        result.append(f"{icon} [{status}] {content}")
    return "\n".join(result)

def register_tools():
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import tools
    tools.register(
        name="todo_add",
        description="添加待办",
        parameters={"type": "object", "properties": {"content": {"type": "string"}}, "required": ["content"]},
        func=_todo_add
    )
    tools.register(
        name="todo_start",
        description="开始执行待办",
        parameters={"type": "object", "properties": {"content": {"type": "string"}}, "required": ["content"]},
        func=_todo_start
    )
    tools.register(
        name="todo_complete",
        description="标记待办完成",
        parameters={"type": "object", "properties": {"content": {"type": "string"}}, "required": ["content"]},
        func=_todo_complete
    )
    tools.register(
        name="todo_list",
        description="查看所有待办",
        parameters={"type": "object", "properties": {}},
        func=_todo_list_fn
    )
    return 4