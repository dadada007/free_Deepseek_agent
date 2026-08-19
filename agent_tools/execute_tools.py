# -*- coding: utf-8 -*-
"""执行命令工具 - 支持后台运行和输出查看"""

import sys
import os
import subprocess
import threading
import time
import json
from collections import deque
from typing import Dict, Optional
import uuid

# 存储后台任务
background_tasks: Dict[str, dict] = {}

class BackgroundTask:
    """后台任务管理类"""
    
    def __init__(self, command: str, cwd: Optional[str] = None, task_id: Optional[str] = None):
        self.task_id = task_id or str(uuid.uuid4())[:8]
        self.command = command
        self.cwd = cwd
        self.process: Optional[subprocess.Popen] = None
        self.stdout_buffer = deque(maxlen=10000)
        self.stderr_buffer = deque(maxlen=10000)
        self.is_running = False
        self.is_finished = False
        self.returncode = None
        self.start_time = None
        self.end_time = None
        self._thread = None
        
    def start(self):
        """启动后台任务"""
        if self.is_running:
            return False
        
        try:
            self.process = subprocess.Popen(
                self.command,
                shell=True,
                cwd=self.cwd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                errors='replace',
                bufsize=1
            )
            self.is_running = True
            self.start_time = time.time()
            
            self._thread = threading.Thread(target=self._read_output, daemon=True)
            self._thread.start()
            return True
        except Exception as e:
            self.stderr_buffer.append(f"启动失败: {str(e)}")
            self.is_finished = True
            return False
    
    def _read_output(self):
        """读取输出（在后台线程中运行）"""
        try:
            def read_stdout():
                for line in iter(self.process.stdout.readline, ''):
                    if line:
                        self.stdout_buffer.append(line.rstrip())
            
            def read_stderr():
                for line in iter(self.process.stderr.readline, ''):
                    if line:
                        self.stderr_buffer.append(line.rstrip())
            
            stdout_thread = threading.Thread(target=read_stdout, daemon=True)
            stderr_thread = threading.Thread(target=read_stderr, daemon=True)
            stdout_thread.start()
            stderr_thread.start()
            
            self.returncode = self.process.wait()
            stdout_thread.join(timeout=1)
            stderr_thread.join(timeout=1)
            
        except Exception as e:
            self.stderr_buffer.append(f"读取输出错误: {str(e)}")
        finally:
            self.is_running = False
            self.is_finished = True
            self.end_time = time.time()
    
    def get_output(self, lines: int = 100, stream: str = 'both'):
        """获取输出"""
        result = {
            "task_id": self.task_id,
            "command": self.command,
            "is_running": self.is_running,
            "is_finished": self.is_finished,
            "returncode": self.returncode,
            "duration": None
        }
        
        if self.start_time and self.end_time:
            result["duration"] = round(self.end_time - self.start_time, 2)
        elif self.start_time:
            result["duration"] = round(time.time() - self.start_time, 2)
        
        if stream in ['stdout', 'both']:
            stdout_lines = list(self.stdout_buffer)[-lines:] if self.stdout_buffer else []
            result["stdout"] = stdout_lines
        
        if stream in ['stderr', 'both']:
            stderr_lines = list(self.stderr_buffer)[-lines:] if self.stderr_buffer else []
            result["stderr"] = stderr_lines
        
        return result
    
    def get_full_output(self):
        """获取完整输出"""
        return {
            "task_id": self.task_id,
            "command": self.command,
            "is_running": self.is_running,
            "is_finished": self.is_finished,
            "returncode": self.returncode,
            "stdout": list(self.stdout_buffer),
            "stderr": list(self.stderr_buffer)
        }
    
    def stop(self):
        """停止任务"""
        if self.process and self.is_running:
            self.process.terminate()
            time.sleep(0.5)
            if self.process.poll() is None:
                self.process.kill()
            return True
        return False


def _execute_command(args: dict) -> str:
    """执行命令，支持同步和后台模式"""
    command = args.get("command", "")
    if not command:
        return "错误: 缺少 command 参数"
    
    background = args.get("background", False)
    cwd = args.get("cwd", None)
    task_id = args.get("task_id", None)
    
    # 后台模式
    if background:
        task = BackgroundTask(command, cwd, task_id)
        success = task.start()
        
        if success:
            background_tasks[task.task_id] = task
            return json.dumps({
                "success": True,
                "task_id": task.task_id,
                "command": command,
                "background": True,
                "message": f"任务已在后台运行，使用 task_id={task.task_id} 查看输出"
            }, ensure_ascii=False, indent=2)
        else:
            return json.dumps({
                "success": False,
                "error": "启动任务失败",
                "output": list(task.stderr_buffer)
            }, ensure_ascii=False, indent=2)
    
    # 同步模式（原有逻辑）
    timeout = args.get("timeout", 30)
    input_text = args.get("input_text", None)
    
    try:
        process = subprocess.Popen(
            command,
            shell=True,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8',
            errors='replace'
        )
        stdout, stderr = process.communicate(input=input_text, timeout=timeout)
        result = {
            "stdout": stdout,
            "stderr": stderr,
            "returncode": process.returncode,
            "success": process.returncode == 0,
            "background": False
        }
        return json.dumps(result, ensure_ascii=False, indent=2)
    except subprocess.TimeoutExpired:
        process.kill()
        return '{"error": "命令执行超时", "timeout": true}'
    except Exception as e:
        return f'{{"error": "{str(e)}"}}'


def _get_task_output(args: dict) -> str:
    """获取后台任务输出"""
    task_id = args.get("task_id", "")
    if not task_id:
        # 列出所有任务
        if not background_tasks:
            return json.dumps({"tasks": []}, ensure_ascii=False, indent=2)
        
        tasks_info = []
        for tid, task in background_tasks.items():
            tasks_info.append({
                "task_id": tid,
                "command": task.command[:100],
                "is_running": task.is_running,
                "is_finished": task.is_finished,
                "returncode": task.returncode,
                "duration": round(time.time() - task.start_time, 2) if task.start_time else None
            })
        return json.dumps({"tasks": tasks_info}, ensure_ascii=False, indent=2)
    
    task = background_tasks.get(task_id)
    if not task:
        return json.dumps({"error": f"任务 {task_id} 不存在"}, ensure_ascii=False, indent=2)
    
    lines = args.get("lines", 100)
    stream = args.get("stream", "both")
    full = args.get("full", False)
    
    if full:
        result = task.get_full_output()
    else:
        result = task.get_output(lines, stream)
    
    return json.dumps(result, ensure_ascii=False, indent=2)


def _stop_task(args: dict) -> str:
    """停止后台任务"""
    task_id = args.get("task_id", "")
    if not task_id:
        return "错误: 缺少 task_id 参数"
    
    task = background_tasks.get(task_id)
    if not task:
        return json.dumps({"error": f"任务 {task_id} 不存在"}, ensure_ascii=False, indent=2)
    
    if task.is_finished:
        return json.dumps({
            "task_id": task_id,
            "message": "任务已经完成",
            "returncode": task.returncode
        }, ensure_ascii=False, indent=2)
    
    success = task.stop()
    return json.dumps({
        "task_id": task_id,
        "success": success,
        "message": "任务已停止" if success else "停止失败"
    }, ensure_ascii=False, indent=2)


def _clean_tasks(args: dict) -> str:
    """清理已完成的任务"""
    cleaned = 0
    for task_id in list(background_tasks.keys()):
        task = background_tasks[task_id]
        if task.is_finished:
            del background_tasks[task_id]
            cleaned += 1
    
    return json.dumps({
        "cleaned": cleaned,
        "remaining": len(background_tasks)
    }, ensure_ascii=False, indent=2)


def register_tools():
    try:
        import tools
    except ImportError:
        print("⚠️ 无法导入 tools 模块")
        return 0
    
    # 主命令 - 通过 background 参数控制同步/后台
    tools.register(
        name="execute_command",
        description="执行终端命令。background=false(默认)同步执行并返回结果；background=true后台执行，立即返回task_id",
        parameters={
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "要执行的命令"},
                "background": {"type": "boolean", "description": "是否后台运行，默认false"},
                "cwd": {"type": "string", "description": "工作目录（可选）"},
                "timeout": {"type": "number", "description": "同步模式超时秒数，默认30"},
                "input_text": {"type": "string", "description": "标准输入内容（可选）"},
                "task_id": {"type": "string", "description": "后台模式自定义任务ID（可选）"}
            },
            "required": ["command"]
        },
        func=_execute_command
    )
    
    # 查看后台任务输出
    tools.register(
        name="get_task_output",
        description="查看后台任务的输出。不提供task_id则列出所有任务",
        parameters={
            "type": "object",
            "properties": {
                "task_id": {"type": "string", "description": "任务ID（可选）"},
                "lines": {"type": "number", "description": "显示最近N行，默认100"},
                "stream": {"type": "string", "description": "输出流：stdout/stderr/both，默认both"},
                "full": {"type": "boolean", "description": "是否显示完整输出，默认false"}
            }
        },
        func=_get_task_output
    )
    
    # 停止后台任务
    tools.register(
        name="stop_task",
        description="停止正在运行的后台任务",
        parameters={
            "type": "object",
            "properties": {
                "task_id": {"type": "string", "description": "任务ID"}
            },
            "required": ["task_id"]
        },
        func=_stop_task
    )
    
    # 清理已完成任务
    tools.register(
        name="clean_tasks",
        description="清理所有已完成的后台任务，释放内存",
        parameters={
            "type": "object",
            "properties": {}
        },
        func=_clean_tasks
    )
    
    print("✅ 已注册 execute_command (支持同步/后台模式)")
    print("✅ 已注册 get_task_output (查看后台输出)")
    print("✅ 已注册 stop_task (停止后台任务)")
    print("✅ 已注册 clean_tasks (清理已完成任务)")
    return 4


# 自动注册
if __name__ != '__main__':
    register_tools()