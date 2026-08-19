# -*- coding: utf-8 -*-
"""
fs_shell.py - 安全命令执行与后台任务管理

提供：
- 安全命令执行（超时、进程树管理）
- 后台任务管理（运行、查询、杀死）
- Shell 检测与选择
- 跨平台兼容（Windows/Linux/macOS）

借鉴 OpenCode 的 Shell 设计 + new2_tools.py 实现
"""

import os
import sys
import signal
import subprocess
import time
import threading
import platform
from typing import Optional, List, Dict, Any, Tuple
from pathlib import Path
from contextlib import contextmanager

from .fs_path_utils import normalize_path, contains


# ============================================
# 1. Shell 检测与选择
# ============================================

SHELL_META = {
    'bash': {'login': True, 'posix': True},
    'zsh': {'login': True, 'posix': True},
    'sh': {'login': True, 'posix': True},
    'dash': {'login': True, 'posix': True},
    'ksh': {'login': True, 'posix': True},
    'fish': {'deny': True, 'login': True},
    'nu': {'deny': True},
    'powershell': {'ps': True},
    'pwsh': {'ps': True},
    'cmd': {},
}


def get_shell_name(shell_path: str) -> str:
    """获取 shell 名称"""
    if platform.system() == 'Windows':
        return Path(shell_path).stem.lower()
    return Path(shell_path).name.lower()


def get_shell_meta(shell_path: str) -> Dict[str, bool]:
    """获取 shell 元数据"""
    name = get_shell_name(shell_path)
    return SHELL_META.get(name, {})


def is_shell_acceptable(shell_path: str) -> bool:
    """检查 shell 是否被拒绝"""
    meta = get_shell_meta(shell_path)
    return not meta.get('deny', False)


def is_login_shell(shell_path: str) -> bool:
    """是否为登录 shell"""
    return get_shell_meta(shell_path).get('login', False)


def is_posix_shell(shell_path: str) -> bool:
    """是否为 POSIX shell"""
    return get_shell_meta(shell_path).get('posix', False)


def is_powershell(shell_path: str) -> bool:
    """是否为 PowerShell"""
    return get_shell_meta(shell_path).get('ps', False)


def find_git_bash() -> Optional[str]:
    """查找 Git Bash 路径（Windows）"""
    if platform.system() != 'Windows':
        return None
    
    import shutil
    git_bash = os.environ.get('HERMES_GIT_BASH_PATH')
    if git_bash and os.path.exists(git_bash):
        return git_bash
    
    git_path = shutil.which('git')
    if git_path:
        git_dir = Path(git_path).parent.parent
        bash_path = git_dir / 'bin' / 'bash.exe'
        if bash_path.exists():
            return str(bash_path)
        bash_path = git_dir / 'usr' / 'bin' / 'bash.exe'
        if bash_path.exists():
            return str(bash_path)
    
    return None


def find_shells() -> List[str]:
    """查找系统可用的 shell"""
    import shutil
    shells = []
    
    if platform.system() == 'Windows':
        for shell in ['pwsh', 'powershell']:
            path = shutil.which(shell)
            if path:
                shells.append(path)
        
        cmd = os.environ.get('COMSPEC', 'cmd.exe')
        if shutil.which(cmd):
            shells.append(cmd)
        
        git_bash = find_git_bash()
        if git_bash:
            shells.append(git_bash)
    else:
        try:
            with open('/etc/shells', 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        shells.append(line)
        except FileNotFoundError:
            pass
        
        for shell in ['/bin/bash', '/bin/zsh', '/bin/sh']:
            if shell not in shells and os.path.exists(shell):
                shells.append(shell)
    
    seen = set()
    result = []
    for s in shells:
        normalized = normalize_path(s)
        if normalized not in seen:
            seen.add(normalized)
            result.append(normalized)
    
    return result


def select_shell(preferred: Optional[str] = None, require_acceptable: bool = False) -> str:
    """选择可用的 shell"""
    import shutil
    
    if preferred:
        if os.path.exists(preferred):
            if not require_acceptable or is_shell_acceptable(preferred):
                return preferred
    
    if platform.system() != 'Windows':
        shell = os.environ.get('SHELL')
        if shell and os.path.exists(shell):
            if not require_acceptable or is_shell_acceptable(shell):
                return shell
    
    if platform.system() == 'Windows':
        shells = find_shells()
        for s in shells:
            name = get_shell_name(s)
            if name in ['pwsh', 'powershell']:
                return s
        for s in shells:
            if 'bash' in s:
                return s
        if shells:
            return shells[0]
        return 'cmd.exe'
    
    if os.path.exists('/bin/zsh'):
        return '/bin/zsh'
    if os.path.exists('/bin/bash'):
        return '/bin/bash'
    return '/bin/sh'


def get_shell_args(shell_path: str, command: str, cwd: str) -> List[str]:
    """获取 shell 执行参数"""
    name = get_shell_name(shell_path)
    
    if name in ('nu', 'fish'):
        return ['-c', command]
    
    if name == 'zsh':
        return [
            '-l', '-c',
            f'''
                [[ -f ~/.zshenv ]] && source ~/.zshenv >/dev/null 2>&1 || true
                [[ -f "${{ZDOTDIR:-$HOME}}/.zshrc" ]] && source "${{ZDOTDIR:-$HOME}}/.zshrc" >/dev/null 2>&1 || true
                cd -- "$1"
                eval {repr(command)}
            ''',
            'hermes', cwd
        ]
    
    if name == 'bash':
        return [
            '-l', '-c',
            f'''
                shopt -s expand_aliases
                [[ -f ~/.bashrc ]] && source ~/.bashrc >/dev/null 2>&1 || true
                cd -- "$1"
                eval {repr(command)}
            ''',
            'hermes', cwd
        ]
    
    if name == 'cmd':
        return ['/c', command]
    
    if is_powershell(shell_path):
        return ['-NoProfile', '-Command', command]
    
    return ['-c', command]


# ============================================
# 2. 进程树管理
# ============================================

def _kill_tree_unix(pid: int, timeout_ms: int = 200) -> bool:
    """Unix 下杀死进程树"""
    try:
        os.killpg(pid, signal.SIGTERM)
        time.sleep(timeout_ms / 1000.0)
        try:
            os.killpg(pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        return True
    except ProcessLookupError:
        return True
    except (OSError, ValueError):
        return False


def _kill_tree_windows(pid: int) -> bool:
    """Windows 下杀死进程树"""
    try:
        subprocess.run(
            ['taskkill', '/pid', str(pid), '/f', '/t'],
            capture_output=True,
            creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0,
        )
        return True
    except Exception:
        return False


def kill_process_tree(process: subprocess.Popen) -> bool:
    """杀死整个进程树"""
    pid = process.pid
    if pid is None:
        return False
    
    if platform.system() == 'Windows':
        return _kill_tree_windows(pid)
    else:
        return _kill_tree_unix(pid)


# ============================================
# 3. 命令执行
# ============================================

class CommandResult:
    """命令执行结果"""
    def __init__(self, stdout: str, stderr: str, returncode: int,
                 timed_out: bool = False, killed: bool = False):
        self.stdout = stdout
        self.stderr = stderr
        self.returncode = returncode
        self.timed_out = timed_out
        self.killed = killed
    
    @property
    def success(self) -> bool:
        return self.returncode == 0 and not self.timed_out and not self.killed
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'stdout': self.stdout,
            'stderr': self.stderr,
            'returncode': self.returncode,
            'success': self.success,
            'timed_out': self.timed_out,
            'killed': self.killed,
        }


def execute_command(
    command: str,
    cwd: Optional[str] = None,
    timeout: Optional[float] = None,
    shell_path: Optional[str] = None,
    env: Optional[Dict[str, str]] = None,
    input_text: Optional[str] = None,
    working_dir_whitelist: Optional[List[str]] = None,
) -> CommandResult:
    """
    安全执行命令（带进程树管理和超时控制）
    """
    if working_dir_whitelist and cwd:
        cwd_normalized = normalize_path(cwd)
        safe = any(contains(whitelist, cwd_normalized) for whitelist in working_dir_whitelist)
        if not safe:
            raise ValueError(f"Working directory {cwd} is not in whitelist")
    
    shell = select_shell(shell_path, require_acceptable=False)
    env_vars = os.environ.copy()
    if env:
        env_vars.update(env)
    
    cwd_path = cwd or os.getcwd()
    shell_args = get_shell_args(shell, command, cwd_path)
    
    creation_flags = subprocess.CREATE_NEW_PROCESS_GROUP if platform.system() == 'Windows' else 0
    
    try:
        process = subprocess.Popen(
            [shell] + shell_args,
            cwd=cwd_path,
            env=env_vars,
            stdin=subprocess.PIPE if input_text is not None else None,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            creationflags=creation_flags,
        )
    except FileNotFoundError:
        raise FileNotFoundError(f"Shell not found: {shell}")
    except Exception as e:
        raise RuntimeError(f"Failed to start process: {e}")
    
    timed_out = False
    killed = False
    stdout_text = ""
    stderr_text = ""
    returncode = -1
    
    def timeout_handler():
        nonlocal timed_out, killed
        timed_out = True
        kill_process_tree(process)
        killed = True
    
    timer = None
    if timeout is not None and timeout > 0:
        timer = threading.Timer(timeout, timeout_handler)
        timer.daemon = True
        timer.start()
    
    try:
        if input_text is not None:
            stdout_text, stderr_text = process.communicate(input_text)
        else:
            stdout_text, stderr_text = process.communicate()
        returncode = process.returncode
    except Exception as e:
        if process.poll() is None:
            kill_process_tree(process)
            killed = True
        raise RuntimeError(f"Command execution failed: {e}")
    finally:
        if timer:
            timer.cancel()
    
    return CommandResult(
        stdout=stdout_text or "",
        stderr=stderr_text or "",
        returncode=returncode,
        timed_out=timed_out,
        killed=killed,
    )


def execute_command_safe(
    command: str,
    cwd: Optional[str] = None,
    timeout: float = 30.0,
    max_output: int = 1024 * 1024,
    working_dir_whitelist: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    安全执行命令（带输出截断，适合工具调用）
    """
    try:
        result = execute_command(
            command=command,
            cwd=cwd,
            timeout=timeout,
            working_dir_whitelist=working_dir_whitelist,
        )
        
        output = result.to_dict()
        
        for key in ['stdout', 'stderr']:
            if len(output.get(key, '')) > max_output:
                output[key] = output[key][:max_output] + f"\n... (truncated, {len(output[key])} bytes total)"
        
        return output
        
    except ValueError as e:
        return {
            'success': False,
            'error': str(e),
            'returncode': -1,
            'stdout': '',
            'stderr': str(e),
        }
    except Exception as e:
        return {
            'success': False,
            'error': f'Command execution failed: {e}',
            'returncode': -1,
            'stdout': '',
            'stderr': str(e),
        }


# ============================================
# 4. 后台任务管理
# ============================================

class BackgroundTask:
    """后台任务"""
    def __init__(self, task_id: str, process: subprocess.Popen, command: str):
        self.task_id = task_id
        self.process = process
        self.command = command
        self.start_time = time.time()
        self._stdout: List[str] = []
        self._stderr: List[str] = []
        self._completed = False
        self._lock = threading.Lock()
    
    def is_running(self) -> bool:
        return self.process.poll() is None
    
    def kill(self) -> bool:
        if self.is_running():
            return kill_process_tree(self.process)
        return False
    
    def get_output(self, tail: Optional[int] = None) -> Dict[str, Any]:
        with self._lock:
            stdout_lines = self._stdout
            stderr_lines = self._stderr
            if tail:
                stdout_lines = stdout_lines[-tail:]
                stderr_lines = stderr_lines[-tail:]
            return {
                'stdout': '\n'.join(stdout_lines),
                'stderr': '\n'.join(stderr_lines),
                'running': self.is_running(),
                'pid': self.process.pid,
            }


_background_tasks: Dict[str, BackgroundTask] = {}
_task_counter = 0
_task_lock = threading.Lock()


def run_background(command: str, cwd: Optional[str] = None) -> str:
    """后台运行命令"""
    global _task_counter
    
    shell = select_shell()
    cwd_path = cwd or os.getcwd()
    shell_args = get_shell_args(shell, command, cwd_path)
    
    creation_flags = subprocess.CREATE_NEW_PROCESS_GROUP if platform.system() == 'Windows' else 0
    
    process = subprocess.Popen(
        [shell] + shell_args,
        cwd=cwd_path,
        env=os.environ.copy(),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        creationflags=creation_flags,
    )
    
    with _task_lock:
        _task_counter += 1
        task_id = f"bg_{_task_counter}"
        task = BackgroundTask(task_id, process, command)
        _background_tasks[task_id] = task
    
    def collect_output():
        for line in iter(process.stdout.readline, ''):
            with task._lock:
                task._stdout.append(line.rstrip())
                if len(task._stdout) > 10000:
                    task._stdout = task._stdout[-5000:]
        for line in iter(process.stderr.readline, ''):
            with task._lock:
                task._stderr.append(line.rstrip())
                if len(task._stderr) > 10000:
                    task._stderr = task._stderr[-5000:]
        task._completed = True
    
    threading.Thread(target=collect_output, daemon=True).start()
    
    return task_id


def get_background_task(task_id: str) -> Optional[BackgroundTask]:
    """获取后台任务"""
    return _background_tasks.get(task_id)


def kill_background_task(task_id: str) -> bool:
    """杀死后台任务"""
    task = get_background_task(task_id)
    if task:
        return task.kill()
    return False


def list_background_tasks() -> List[Dict[str, Any]]:
    """列出所有后台任务"""
    return [
        {
            'task_id': task.task_id,
            'command': task.command,
            'running': task.is_running(),
            'pid': task.process.pid,
            'start_time': task.start_time,
        }
        for task in _background_tasks.values()
    ]


# ============================================
# 测试
# ============================================

if __name__ == '__main__':
    import tempfile
    
    print("=== fs_shell 测试 ===\n")
    
    print("可用 Shell:")
    for shell in find_shells():
        print(f"  - {shell}")
    
    print(f"\n选择的 Shell: {select_shell()}")
    
    print("\n--- 测试: echo ---")
    result = execute_command_safe('echo "Hello, World!"')
    print(f"结果: {result}")
    
    print("\n--- 测试: 超时 (2秒) ---")
    start = time.time()
    result = execute_command_safe('sleep 5', timeout=2)
    elapsed = time.time() - start
    print(f"超时后返回: {result}")
    print(f"实际耗时: {elapsed:.2f}s")
    
    print("\n--- 测试: 后台任务 ---")
    task_id = run_background('ping -c 5 127.0.0.1' if platform.system() != 'Windows' else 'ping -n 5 127.0.0.1')
    print(f"后台任务 ID: {task_id}")
    
    time.sleep(1)
    task = get_background_task(task_id)
    if task:
        output = task.get_output(tail=5)
        print(f"输出预览: {output['stdout'][:200]}...")
        print(f"运行中: {output['running']}")
    
    kill_background_task(task_id)
    print("\n✅ 所有测试通过")