# -*- coding: utf-8 -*-
"""后台任务管理模块"""
import os
import subprocess
import threading
import time
import logging
import uuid
from typing import Dict

logger = logging.getLogger(__name__)

# 全局任务存储
_tasks: Dict[str, dict] = {}

def _run_background(args: dict) -> str:
    """后台运行命令，返回任务ID"""
    command = args.get("command", "")
    if not command:
        return "错误: 缺少 command 参数"
    task_id = str(uuid.uuid4())[:8]
    try:
        process = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8',
            errors='replace'
        )
        _tasks[task_id] = {
            "process": process,
            "command": command,
            "start_time": time.time(),
            "output": [],
            "status": "running"
        }
        # 启动输出收集线程
        def collect_output():
            try:
                stdout, stderr = process.communicate(timeout=3600)
                if stdout:
                    _tasks[task_id]["output"].append(stdout)
                if stderr:
                    _tasks[task_id]["output"].append("[STDERR]\n" + stderr)
                _tasks[task_id]["status"] = "completed"
            except subprocess.TimeoutExpired:
                process.kill()
                _tasks[task_id]["status"] = "timeout"
            except Exception as e:
                _tasks[task_id]["output"].append(f"错误: {e}")
                _tasks[task_id]["status"] = "failed"
        threading.Thread(target=collect_output, daemon=True).start()
        return f"任务已启动: {task_id}\n命令: {command}"
    except Exception as e:
        return f"启动失败: {e}"

def _task_output(args: dict) -> str:
    """查看后台任务输出"""
    task_id = args.get("task_id", "")
    tail = args.get("tail", 0)
    if not task_id:
        return "错误: 缺少 task_id 参数"
    if task_id not in _tasks:
        return f"错误: 任务不存在 - {task_id}"
    task = _tasks[task_id]
    output = "".join(task.get("output", []))
    status = task.get("status", "unknown")
    if tail > 0:
        lines = output.split('\n')
        output = '\n'.join(lines[-tail:])
    result = f"任务状态: {status}\n"
    if output:
        result += f"输出:\n{output}"
    else:
        result += "暂无输出"
    return result

def _kill_task(args: dict) -> str:
    """终止后台任务"""
    task_id = args.get("task_id", "")
    if not task_id:
        return "错误: 缺少 task_id 参数"
    if task_id not in _tasks:
        return f"错误: 任务不存在 - {task_id}"
    task = _tasks[task_id]
    try:
        process = task.get("process")
        if process and process.poll() is None:
            process.terminate()
            time.sleep(0.5)
            if process.poll() is None:
                process.kill()
            task["status"] = "killed"
            return f"任务 {task_id} 已终止"
        else:
            return f"任务 {task_id} 已结束"
    except Exception as e:
        return f"终止失败: {e}"

def register_tools():
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import tools
    tools.register(
        name="run_background",
        description="后台运行命令，返回任务ID",
        parameters={"type": "object", "properties": {"command": {"type": "string"}}, "required": ["command"]},
        func=_run_background
    )
    tools.register(
        name="task_output",
        description="查看后台任务输出",
        parameters={"type": "object", "properties": {"task_id": {"type": "string"}, "tail": {"type": "integer"}}, "required": ["task_id"]},
        func=_task_output
    )
    tools.register(
        name="kill_task",
        description="终止后台任务",
        parameters={"type": "object", "properties": {"task_id": {"type": "string"}}, "required": ["task_id"]},
        func=_kill_task
    )
    return 3