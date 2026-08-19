# -*- coding: utf-8 -*-
"""
定时任务调度工具集 - 支持定时执行、周期性任务
"""

import os
import json
import time
import threading
import subprocess
from datetime import datetime
from collections import deque


_tasks = {}
_task_id_counter = 0
_task_lock = threading.Lock()
_scheduler_running = False
_scheduler_thread = None


def _get_next_id():
    global _task_id_counter
    with _task_lock:
        _task_id_counter += 1
        return f"task_{_task_id_counter}"


def _execute_task(task_id):
    with _task_lock:
        task = _tasks.get(task_id)
        if not task:
            return
    try:
        command = task.get('command', '')
        if not command:
            task['status'] = 'failed'
            task['error'] = '无命令'
            return
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=task.get('timeout', 300))
        task['status'] = 'completed' if result.returncode == 0 else 'failed'
        task['last_run'] = datetime.now().isoformat()
        task['output'] = result.stdout
        task['error'] = result.stderr if result.returncode != 0 else None
        task['run_count'] = task.get('run_count', 0) + 1
    except subprocess.TimeoutExpired:
        task['status'] = 'failed'
        task['error'] = f'执行超时'
    except Exception as e:
        task['status'] = 'failed'
        task['error'] = str(e)


def _create_task(args: dict) -> str:
    try:
        name = args.get('name', '未命名任务')
        command = args.get('command', '')
        schedule_config = args.get('schedule', {})
        timeout = args.get('timeout', 300)
        if not command:
            return "❌ 请提供命令 (command)"
        if not schedule_config:
            return "❌ 请提供调度配置 (schedule)"
        task_id = _get_next_id()
        with _task_lock:
            _tasks[task_id] = {
                'id': task_id, 'name': name, 'command': command,
                'schedule': schedule_config, 'timeout': timeout,
                'status': 'pending', 'created_at': datetime.now().isoformat(),
                'last_run': None, 'run_count': 0, 'output': None, 'error': None
            }
        return json.dumps({'success': True, 'task_id': task_id, 'name': name, 'message': f'任务 {task_id} 已创建'}, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"❌ 创建任务失败: {e}"


def _list_tasks(args: dict) -> str:
    try:
        status_filter = args.get('status', None)
        with _task_lock:
            tasks = list(_tasks.values())
        if status_filter:
            tasks = [t for t in tasks if t.get('status') == status_filter]
        result = {'total': len(tasks), 'tasks': []}
        for task in tasks:
            result['tasks'].append({
                'id': task.get('id'), 'name': task.get('name'),
                'command': task.get('command', '')[:50],
                'status': task.get('status'), 'run_count': task.get('run_count', 0),
            })
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"❌ 获取任务列表失败: {e}"


def _run_task(args: dict) -> str:
    try:
        task_id = args.get('task_id', '')
        if not task_id:
            return "❌ 请提供任务ID (task_id)"
        with _task_lock:
            task = _tasks.get(task_id)
            if not task:
                return f"❌ 任务不存在: {task_id}"
        thread = threading.Thread(target=_execute_task, args=(task_id,), daemon=True)
        thread.start()
        return json.dumps({'success': True, 'task_id': task_id, 'message': f'任务 {task_id} 已启动执行'}, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"❌ 执行任务失败: {e}"


def _delete_task(args: dict) -> str:
    try:
        task_id = args.get('task_id', '')
        if not task_id:
            return "❌ 请提供任务ID (task_id)"
        with _task_lock:
            if task_id not in _tasks:
                return f"❌ 任务不存在: {task_id}"
            del _tasks[task_id]
        return json.dumps({'success': True, 'task_id': task_id, 'message': f'任务 {task_id} 已删除'}, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"❌ 删除任务失败: {e}"


def _toggle_task(args: dict) -> str:
    try:
        task_id = args.get('task_id', '')
        enabled = args.get('enabled', True)
        if not task_id:
            return "❌ 请提供任务ID (task_id)"
        with _task_lock:
            task = _tasks.get(task_id)
            if not task:
                return f"❌ 任务不存在: {task_id}"
            task['enabled'] = enabled
        return json.dumps({'success': True, 'task_id': task_id, 'enabled': enabled}, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"❌ 操作失败: {e}"


def register_tools():
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import tools
    tools.register(name="create_task", description="创建定时任务。参数: name, command, schedule, timeout", parameters={"type": "object", "properties": {"name": {"type": "string"}, "command": {"type": "string"}, "schedule": {"type": "object"}, "timeout": {"type": "integer"}}, "required": ["command", "schedule"]}, func=_create_task)
    tools.register(name="list_tasks", description="查看所有任务。参数: status(可选过滤)", parameters={"type": "object", "properties": {"status": {"type": "string"}}}, func=_list_tasks)
    tools.register(name="run_task", description="立即执行任务。参数: task_id", parameters={"type": "object", "properties": {"task_id": {"type": "string"}}, "required": ["task_id"]}, func=_run_task)
    tools.register(name="delete_task", description="删除任务。参数: task_id", parameters={"type": "object", "properties": {"task_id": {"type": "string"}}, "required": ["task_id"]}, func=_delete_task)
    tools.register(name="toggle_task", description="暂停或恢复任务。参数: task_id, enabled", parameters={"type": "object", "properties": {"task_id": {"type": "string"}, "enabled": {"type": "boolean"}}, "required": ["task_id"]}, func=_toggle_task)
    return 5


def unregister_tools():
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import tools
    for name in ["create_task", "list_tasks", "run_task", "delete_task", "toggle_task"]:
        tools.TOOLS.pop(name, None)
