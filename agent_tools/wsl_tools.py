# -*- coding: utf-8 -*-
"""
WSL2 工具封装 - 让 Hermes 原生支持 Linux 命令
"""

import os
import sys
import subprocess
import json
import re

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tools import register


# ==================== 辅助函数 ====================

def _wsl_path_to_win(wsl_path: str) -> str:
    """将 WSL 路径转换为 Windows 可访问的网络路径"""
    if wsl_path.startswith('/'):
        wsl_path = wsl_path[1:]
    return f"//wsl$/Ubuntu/{wsl_path}"


def _win_path_to_wsl(win_path: str) -> str:
    """将 Windows 路径转换为 WSL 路径（通过 wslpath 命令）"""
    try:
        result = subprocess.run(
            ['wsl', 'wslpath', win_path],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    return win_path


def _run_wsl(command: str, cwd: str = None, timeout: int = 60) -> dict:
    """在 WSL 中执行命令，返回 {stdout, stderr, returncode, success}"""
    # 使用 bash -c 执行命令，支持管道、重定向、&& 等 shell 语法
    full_cmd = ['wsl']
    if cwd:
        full_cmd.extend(['--cd', cwd])
    full_cmd.extend(['bash', '-c', command])

    try:
        result = subprocess.run(
            full_cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            encoding='utf-8',
            errors='replace'
        )
        return {
            'stdout': result.stdout,
            'stderr': result.stderr,
            'returncode': result.returncode,
            'success': result.returncode == 0
        }
    except subprocess.TimeoutExpired:
        return {'stdout': '', 'stderr': f'命令执行超时 ({timeout}s)', 'returncode': -1, 'success': False}
    except Exception as e:
        return {'stdout': '', 'stderr': str(e), 'returncode': -1, 'success': False}


# ==================== 工具实现 ====================

def wsl_exec(args: dict) -> str:
    """在 WSL Ubuntu 中执行任意 Linux 命令"""
    command = args.get('command', '').strip()
    if not command:
        return '❌ 错误: 请提供 command 参数'

    cwd = args.get('cwd', '')
    timeout = args.get('timeout', 60)

    result = _run_wsl(command, cwd, timeout)

    output = []
    output.append(f"📌 命令: {command}")
    if cwd:
        output.append(f"📂 工作目录: {cwd}")
    output.append(f"🔢 返回码: {result['returncode']}")

    if result['stdout']:
        output.append("\n--- stdout ---")
        output.append(result['stdout'].rstrip())
    if result['stderr']:
        output.append("\n--- stderr ---")
        output.append(result['stderr'].rstrip())

    if result['success']:
        output.insert(0, "✅ 命令执行成功")
    else:
        output.insert(0, "❌ 命令执行失败")

    return '\n'.join(output)


def wsl_read(args: dict) -> str:
    """读取 WSL 中的文件内容"""
    path = args.get('path', '').strip()
    if not path:
        return '❌ 错误: 请提供 path 参数'

    win_path = _wsl_path_to_win(path)

    try:
        with open(win_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return f"✅ 读取成功: {path}\n\n{content}"
    except FileNotFoundError:
        return f"❌ 文件不存在: {path}"
    except PermissionError:
        return f"❌ 权限不足: {path}"
    except Exception as e:
        return f"❌ 读取失败: {str(e)}"


def wsl_write(args: dict) -> str:
    """写入内容到 WSL 中的文件"""
    path = args.get('path', '').strip()
    content = args.get('content', '')
    if not path:
        return '❌ 错误: 请提供 path 参数'

    win_path = _wsl_path_to_win(path)

    try:
        os.makedirs(os.path.dirname(win_path), exist_ok=True)
        with open(win_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"✅ 写入成功: {path} (已写入 {len(content)} 字符)"
    except Exception as e:
        return f"❌ 写入失败: {str(e)}"


def wsl_list(args: dict) -> str:
    """列出 WSL 目录内容"""
    path = args.get('path', '/root').strip()
    show_hidden = args.get('show_hidden', False)

    cmd = 'ls -la' if show_hidden else 'ls -l'
    result = _run_wsl(f'{cmd} {path}', timeout=30)

    if result['success']:
        return f"📂 目录: {path}\n\n{result['stdout']}"
    else:
        return f"❌ 列出失败: {path}\n{result['stderr']}"


def wsl_install(args: dict) -> str:
    """通过 apt 在 WSL Ubuntu 中安装软件包"""
    package = args.get('package', '').strip()
    if not package:
        return '❌ 错误: 请提供 package 参数'

    result1 = _run_wsl('apt update -y', timeout=120)
    if not result1['success']:
        return f"❌ apt update 失败:\n{result1['stderr']}"

    result2 = _run_wsl(f'apt install -y {package}', timeout=300)
    if result2['success']:
        return f"✅ 安装成功: {package}\n\n{result2['stdout'][:500]}"
    else:
        return f"❌ 安装失败: {package}\n{result2['stderr']}"


def wsl_status(args: dict) -> str:
    """查看 WSL 运行状态和系统信息"""
    output = []
    output.append("📊 WSL 状态报告")
    output.append("=" * 40)

    result = _run_wsl('--version', timeout=10)
    if result['success']:
        output.append(f"版本信息:\n{result['stdout']}")

    result = _run_wsl('cat /etc/os-release | head -3', timeout=10)
    if result['success']:
        output.append(f"系统版本:\n{result['stdout']}")

    result = _run_wsl('uname -a', timeout=10)
    if result['success']:
        output.append(f"内核: {result['stdout'].strip()}")

    result = _run_wsl('df -h /', timeout=10)
    if result['success']:
        output.append(f"磁盘:\n{result['stdout']}")

    return '\n'.join(output)


# ==================== 工具注册 ====================

def register_tools() -> int:
    count = 0

    register(
        name="wsl_exec",
        description="在 WSL Ubuntu 中直接执行 Linux 命令，无需 wsl 前缀。支持管道、重定向等复杂命令。",
        parameters={
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "要执行的 Linux 命令"},
                "cwd": {"type": "string", "description": "WSL 工作目录，如 /root"},
                "timeout": {"type": "integer", "description": "超时秒数，默认 60", "default": 60}
            },
            "required": ["command"]
        },
        func=wsl_exec
    )
    count += 1

    register(
        name="wsl_read",
        description="读取 WSL Ubuntu 中的文件内容",
        parameters={
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "WSL 文件路径，如 /root/.bashrc"}
            },
            "required": ["path"]
        },
        func=wsl_read
    )
    count += 1

    register(
        name="wsl_write",
        description="写入内容到 WSL Ubuntu 中的文件",
        parameters={
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "WSL 文件路径，如 /root/test.txt"},
                "content": {"type": "string", "description": "要写入的内容"}
            },
            "required": ["path", "content"]
        },
        func=wsl_write
    )
    count += 1

    register(
        name="wsl_list",
        description="列出 WSL Ubuntu 中的目录内容",
        parameters={
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "WSL 目录路径，默认 /root", "default": "/root"},
                "show_hidden": {"type": "boolean", "description": "是否显示隐藏文件", "default": False}
            },
            "required": []
        },
        func=wsl_list
    )
    count += 1

    register(
        name="wsl_install",
        description="在 WSL Ubuntu 中通过 apt 安装软件包",
        parameters={
            "type": "object",
            "properties": {
                "package": {"type": "string", "description": "要安装的软件包名称，如 python3, git, ffmpeg"}
            },
            "required": ["package"]
        },
        func=wsl_install
    )
    count += 1

    register(
        name="wsl_status",
        description="查看 WSL 运行状态、系统版本、内核和磁盘信息",
        parameters={"type": "object", "properties": {}, "required": []},
        func=wsl_status
    )
    count += 1

    return count