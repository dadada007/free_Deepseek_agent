# -*- coding: utf-8 -*-
"""
WSL 高级工具集 - 进程管理、文件搜索、系统监控、服务管理、网络工具、用户管理、权限管理
"""

import os
import sys
import json
import re

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tools import register


# ==================== 辅助函数 ====================

def _run_wsl(command: str, cwd: str = None, timeout: int = 60) -> dict:
    """在 WSL 中执行命令，返回 {stdout, stderr, returncode, success}"""
    import subprocess
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


def _format_output(result: dict, title: str = "") -> str:
    """格式化命令输出"""
    lines = []
    if title:
        lines.append(f"📊 {title}")
        lines.append("-" * 40)
    lines.append(f"🔢 返回码: {result['returncode']}")
    if result['stdout']:
        lines.append("\n" + result['stdout'].rstrip())
    if result['stderr']:
        lines.append(f"\n⚠️ stderr:\n{result['stderr'].rstrip()}")
    return '\n'.join(lines)


# ==================== 进程管理 ====================

def wsl_ps(args: dict) -> str:
    """查看或终止 WSL 中的 Linux 进程"""
    action = args.get('action', 'list').strip().lower()
    pid = args.get('pid', '')
    keyword = args.get('keyword', '')
    username = args.get('username', '')

    if action == 'kill':
        if not pid:
            return '❌ 错误: 终止进程需要提供 pid 参数'
        # 支持多种终止方式
        if pid.isdigit():
            result = _run_wsl(f'kill -9 {pid}', timeout=10)
        else:
            # 按进程名终止
            result = _run_wsl(f'pkill -9 {pid}', timeout=10)
        if result['success']:
            return f"✅ 已终止进程: {pid}"
        else:
            return f"❌ 终止失败: {pid}\n{result['stderr']}"

    # 构建 ps 命令
    cmd = 'ps aux'
    if username:
        cmd += f" | grep -E '^\\S+\\s+\\S+\\s+\\S+\\s+\\S+\\s+\\S+\\s+\\S+\\s+\\S+\\s+\\S+\\s+\\S+\\s+.*{username}'"
    elif keyword:
        # 查找包含关键词的进程（排除 grep 自身）
        cmd = f"ps aux | grep -E '{keyword}' | grep -v grep"
    else:
        # 默认显示前 20 个进程
        cmd = 'ps aux --sort=-%mem | head -20'

    result = _run_wsl(cmd, timeout=30)
    if result['success']:
        output = ["📊 进程列表", "=" * 50]
        if keyword:
            output.append(f"🔍 关键词: {keyword}")
        elif username:
            output.append(f"👤 用户: {username}")
        output.append("")
        output.append(result['stdout'].rstrip())
        return '\n'.join(output)
    else:
        return f"❌ 进程查询失败:\n{result['stderr']}"


# ==================== 文件搜索 ====================

def wsl_find(args: dict) -> str:
    """在 WSL 中搜索文件"""
    path = args.get('path', '/').strip()
    name = args.get('name', '')
    pattern = args.get('pattern', '')
    type_filter = args.get('type', 'f')  # f: 文件, d: 目录, l: 链接
    max_depth = args.get('max_depth', 5)
    max_results = args.get('max_results', 50)
    size = args.get('size', '')

    if not name and not pattern:
        return '❌ 错误: 请提供 name 或 pattern 参数'

    # 构建 find 命令
    cmd = f'find {path} -maxdepth {max_depth}'

    # 按名称搜索
    if name:
        cmd += f' -name "{name}"'
    elif pattern:
        cmd += f' -name "{pattern}"'

    # 类型过滤
    if type_filter in ['f', 'd', 'l']:
        cmd += f' -type {type_filter}'

    # 大小过滤
    if size:
        cmd += f' -size {size}'

    # 限制结果数
    cmd += f' 2>/dev/null | head -{max_results}'

    result = _run_wsl(cmd, timeout=60)
    if result['success']:
        lines = result['stdout'].strip().split('\n') if result['stdout'].strip() else []
        output = ["📂 文件搜索结果", "=" * 50]
        output.append(f"📁 路径: {path}")
        output.append(f"🔍 搜索: {name or pattern}")
        output.append(f"📦 找到: {len(lines)} 项")
        output.append("")
        output.append(result['stdout'].rstrip())
        return '\n'.join(output)
    else:
        return f"❌ 搜索失败:\n{result['stderr']}"


# ==================== 系统监控 ====================

def wsl_top(args: dict) -> str:
    """查看 WSL 系统资源占用"""
    action = args.get('action', 'once').strip().lower()
    sort_by = args.get('sort_by', 'cpu')  # cpu, mem, time

    if action == 'once':
        # 一次性快照
        cmd = "ps aux --no-headers | sort -rn -k"
        if sort_by == 'mem':
            cmd += "4 | head -15"
        else:
            cmd += "3 | head -15"

        result = _run_wsl(cmd, timeout=30)
        if result['success']:
            # 同时获取系统信息
            sys_result = _run_wsl('uptime && free -h && df -h /', timeout=10)
            output = ["📊 系统资源监控", "=" * 50]
            if sys_result['success']:
                output.append(sys_result['stdout'].rstrip())
                output.append("")
            output.append(f"📌 按 {sort_by.upper()} 排序 (TOP 15)")
            output.append("")
            output.append(result['stdout'].rstrip())
            return '\n'.join(output)
        else:
            return f"❌ 监控失败:\n{result['stderr']}"

    elif action == 'watch':
        # 持续监控（最多 5 次）
        outputs = []
        for i in range(5):
            result = _run_wsl(f'ps aux --no-headers | sort -rn -k3 | head -10', timeout=10)
            if result['success']:
                outputs.append(f"--- 采样 {i+1} ---")
                outputs.append(result['stdout'].rstrip())
        return '\n'.join(outputs) if outputs else "❌ 监控失败"
    else:
        return f"❌ 未知操作: {action}，支持 once 和 watch"


# ==================== 服务管理 ====================

def wsl_service(args: dict) -> str:
    """启动/停止/查看 systemd 服务"""
    action = args.get('action', 'status').strip().lower()
    service = args.get('service', '').strip()

    if not service and action != 'list':
        return '❌ 错误: 服务操作需要提供 service 参数'

    if action == 'status':
        result = _run_wsl(f'systemctl status {service}', timeout=30)
    elif action == 'start':
        result = _run_wsl(f'sudo systemctl start {service}', timeout=60)
    elif action == 'stop':
        result = _run_wsl(f'sudo systemctl stop {service}', timeout=60)
    elif action == 'restart':
        result = _run_wsl(f'sudo systemctl restart {service}', timeout=60)
    elif action == 'enable':
        result = _run_wsl(f'sudo systemctl enable {service}', timeout=60)
    elif action == 'disable':
        result = _run_wsl(f'sudo systemctl disable {service}', timeout=60)
    elif action == 'list':
        result = _run_wsl('systemctl list-units --type=service --all | head -30', timeout=30)
    else:
        return f"❌ 未知操作: {action}，支持 status/start/stop/restart/enable/disable/list"

    if result['success']:
        output = [f"📌 服务操作: {action} {service}", "=" * 50]
        output.append(result['stdout'].rstrip())
        return '\n'.join(output)
    else:
        return f"❌ 操作失败:\n{result['stderr']}"


# ==================== 网络工具 ====================

def wsl_ping(args: dict) -> str:
    """网络诊断 ping"""
    host = args.get('host', '').strip()
    count = args.get('count', 4)

    if not host:
        return '❌ 错误: 请提供 host 参数'

    result = _run_wsl(f'ping -c {count} {host}', timeout=60)
    if result['success']:
        output = [f"📌 ping {host} ({count} 次)", "=" * 50]
        output.append(result['stdout'].rstrip())
        return '\n'.join(output)
    else:
        return f"❌ ping 失败:\n{result['stderr']}"


def wsl_curl(args: dict) -> str:
    """HTTP 请求 curl"""
    url = args.get('url', '').strip()
    method = args.get('method', 'GET').upper()
    headers = args.get('headers', {})
    data = args.get('data', '')
    timeout = args.get('timeout', 30)
    follow_location = args.get('follow_location', False)
    verbose = args.get('verbose', False)

    if not url:
        return '❌ 错误: 请提供 url 参数'

    cmd = 'curl'
    if method == 'POST':
        cmd += ' -X POST'
    elif method == 'PUT':
        cmd += ' -X PUT'
    elif method == 'DELETE':
        cmd += ' -X DELETE'

    if headers:
        for k, v in headers.items():
            cmd += f' -H "{k}: {v}"'

    if data:
        # 如果是 JSON 字符串，转义
        if data.startswith('{'):
            cmd += f' -d \'{data}\''
        else:
            cmd += f' -d "{data}"'

    if follow_location:
        cmd += ' -L'

    if verbose:
        cmd += ' -v'

    cmd += f' --connect-timeout {timeout}'
    cmd += f' {url}'

    result = _run_wsl(cmd, timeout=timeout + 10)
    output = [f"🌐 curl {url}", "=" * 50]
    output.append(f"方法: {method}")
    output.append(f"超时: {timeout}s")
    if result['success']:
        output.append(f"状态: ✅ 成功")
        # 限制输出长度
        stdout = result['stdout']
        if len(stdout) > 2000:
            stdout = stdout[:2000] + "\n... (截断)"
        output.append(stdout.rstrip())
    else:
        output.append(f"状态: ❌ 失败")
        output.append(result['stderr'].rstrip())
    return '\n'.join(output)


# ==================== 用户管理 ====================

def wsl_user(args: dict) -> str:
    """查看或创建 WSL 用户"""
    action = args.get('action', 'list').strip().lower()
    username = args.get('username', '')
    uid = args.get('uid', '')
    shell = args.get('shell', '/bin/bash')
    home_dir = args.get('home', '')

    if action == 'list':
        result = _run_wsl('cut -d: -f1,3,6,7 /etc/passwd | head -20', timeout=10)
        output = ["👤 用户列表 (前20)", "=" * 50]
        output.append("用户名:UID:家目录:Shell")
        output.append("-" * 40)
        output.append(result['stdout'].rstrip())
        return '\n'.join(output)

    elif action == 'create':
        if not username:
            return '❌ 错误: 创建用户需要提供 username 参数'
        cmd = f'sudo useradd -m -s {shell}'
        if uid:
            cmd += f' -u {uid}'
        if home_dir:
            cmd += f' -d {home_dir}'
        cmd += f' {username}'
        result = _run_wsl(cmd, timeout=30)
        if result['success']:
            # 设置密码
            pass_result = _run_wsl(f'echo "{username}:{username}123" | sudo chpasswd', timeout=10)
            return f"✅ 用户 {username} 创建成功\n默认密码: {username}123\n请尽快修改密码"
        else:
            return f"❌ 创建失败:\n{result['stderr']}"

    elif action == 'info':
        if not username:
            return '❌ 错误: 查看用户信息需要提供 username 参数'
        result = _run_wsl(f'id {username} && cat /etc/passwd | grep -E "^{username}:"', timeout=10)
        output = [f"👤 用户信息: {username}", "=" * 50]
        output.append(result['stdout'].rstrip())
        return '\n'.join(output)

    else:
        return f"❌ 未知操作: {action}，支持 list/create/info"


# ==================== 权限管理 ====================

def wsl_chmod(args: dict) -> str:
    """修改文件权限"""
    path = args.get('path', '').strip()
    mode = args.get('mode', '').strip()
    recursive = args.get('recursive', False)

    if not path:
        return '❌ 错误: 请提供 path 参数'
    if not mode:
        return '❌ 错误: 请提供 mode 参数'

    cmd = f'sudo chmod'
    if recursive:
        cmd += ' -R'
    cmd += f' {mode} {path}'

    result = _run_wsl(cmd, timeout=30)
    if result['success']:
        return f"✅ chmod 成功: {mode} → {path}"
    else:
        return f"❌ chmod 失败:\n{result['stderr']}"


def wsl_chown(args: dict) -> str:
    """修改文件所有者"""
    path = args.get('path', '').strip()
    owner = args.get('owner', '').strip()
    group = args.get('group', '')
    recursive = args.get('recursive', False)

    if not path:
        return '❌ 错误: 请提供 path 参数'
    if not owner:
        return '❌ 错误: 请提供 owner 参数'

    cmd = f'sudo chown'
    if recursive:
        cmd += ' -R'
    if group:
        cmd += f' {owner}:{group}'
    else:
        cmd += f' {owner}'
    cmd += f' {path}'

    result = _run_wsl(cmd, timeout=30)
    if result['success']:
        return f"✅ chown 成功: {owner}{':'+group if group else ''} → {path}"
    else:
        return f"❌ chown 失败:\n{result['stderr']}"


# ==================== 工具注册 ====================

def register_tools() -> int:
    count = 0

    # 进程管理
    register(
        name="wsl_ps",
        description="查看或终止 WSL 中的 Linux 进程。支持 list（列表）、kill（终止进程，支持 PID 或进程名）。",
        parameters={
            "type": "object",
            "properties": {
                "action": {"type": "string", "description": "操作类型: list 或 kill", "enum": ["list", "kill"], "default": "list"},
                "pid": {"type": "string", "description": "进程 PID 或进程名（kill 操作时必填）"},
                "keyword": {"type": "string", "description": "按关键词过滤进程"},
                "username": {"type": "string", "description": "按用户名过滤进程"}
            },
            "required": []
        },
        func=wsl_ps
    )
    count += 1

    # 文件搜索
    register(
        name="wsl_find",
        description="在 WSL 中搜索文件，支持按名称、类型、大小过滤。",
        parameters={
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "搜索路径，默认 /", "default": "/"},
                "name": {"type": "string", "description": "文件名（支持通配符如 *.py）"},
                "pattern": {"type": "string", "description": "文件名模式（与 name 二选一）"},
                "type": {"type": "string", "description": "文件类型: f(文件), d(目录), l(链接)", "enum": ["f", "d", "l"], "default": "f"},
                "max_depth": {"type": "integer", "description": "最大搜索深度，默认 5", "default": 5},
                "max_results": {"type": "integer", "description": "最大结果数，默认 50", "default": 50},
                "size": {"type": "string", "description": "文件大小过滤，如 +10M, -1G, 100k"}
            },
            "required": []
        },
        func=wsl_find
    )
    count += 1

    # 系统监控
    register(
        name="wsl_top",
        description="查看 WSL 系统资源占用（CPU、内存、磁盘）。",
        parameters={
            "type": "object",
            "properties": {
                "action": {"type": "string", "description": "once 一次性快照, watch 持续监控", "enum": ["once", "watch"], "default": "once"},
                "sort_by": {"type": "string", "description": "排序方式: cpu 或 mem", "enum": ["cpu", "mem"], "default": "cpu"}
            },
            "required": []
        },
        func=wsl_top
    )
    count += 1

    # 服务管理
    register(
        name="wsl_service",
        description="管理 WSL 中的 systemd 服务，支持 status/start/stop/restart/enable/disable/list",
        parameters={
            "type": "object",
            "properties": {
                "action": {"type": "string", "description": "操作类型", "enum": ["status", "start", "stop", "restart", "enable", "disable", "list"], "default": "status"},
                "service": {"type": "string", "description": "服务名称（如 nginx.service, docker）"}
            },
            "required": []
        },
        func=wsl_service
    )
    count += 1

    # 网络工具
    register(
        name="wsl_ping",
        description="在 WSL 中执行 ping 网络诊断。",
        parameters={
            "type": "object",
            "properties": {
                "host": {"type": "string", "description": "目标主机地址（域名或 IP）"},
                "count": {"type": "integer", "description": "发送次数，默认 4", "default": 4}
            },
            "required": ["host"]
        },
        func=wsl_ping
    )
    count += 1

    register(
        name="wsl_curl",
        description="在 WSL 中执行 HTTP 请求。支持 GET/POST/PUT/DELETE，可自定义 headers 和 data。",
        parameters={
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "请求 URL"},
                "method": {"type": "string", "description": "HTTP 方法", "enum": ["GET", "POST", "PUT", "DELETE"], "default": "GET"},
                "headers": {"type": "object", "description": "请求头，如 {\"Content-Type\": \"application/json\"}"},
                "data": {"type": "string", "description": "请求体数据"},
                "timeout": {"type": "integer", "description": "超时秒数，默认 30", "default": 30},
                "follow_location": {"type": "boolean", "description": "是否跟随重定向", "default": False},
                "verbose": {"type": "boolean", "description": "是否显示详细信息", "default": False}
            },
            "required": ["url"]
        },
        func=wsl_curl
    )
    count += 1

    # 用户管理
    register(
        name="wsl_user",
        description="管理 WSL 用户，支持 list（列表）、create（创建）、info（查看信息）。",
        parameters={
            "type": "object",
            "properties": {
                "action": {"type": "string", "description": "操作类型", "enum": ["list", "create", "info"], "default": "list"},
                "username": {"type": "string", "description": "用户名（创建/查看时必填）"},
                "uid": {"type": "string", "description": "指定 UID（创建时可选）"},
                "shell": {"type": "string", "description": "指定 Shell，默认 /bin/bash", "default": "/bin/bash"},
                "home": {"type": "string", "description": "指定家目录"}
            },
            "required": []
        },
        func=wsl_user
    )
    count += 1

    # 权限管理
    register(
        name="wsl_chmod",
        description="修改 WSL 中文件或目录的权限。",
        parameters={
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "文件或目录路径"},
                "mode": {"type": "string", "description": "权限模式，如 755, 644, +x"},
                "recursive": {"type": "boolean", "description": "是否递归修改", "default": False}
            },
            "required": ["path", "mode"]
        },
        func=wsl_chmod
    )
    count += 1

    register(
        name="wsl_chown",
        description="修改 WSL 中文件或目录的所有者和组。",
        parameters={
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "文件或目录路径"},
                "owner": {"type": "string", "description": "新所有者用户名"},
                "group": {"type": "string", "description": "新组名（可选）"},
                "recursive": {"type": "boolean", "description": "是否递归修改", "default": False}
            },
            "required": ["path", "owner"]
        },
        func=wsl_chown
    )
    count += 1

    return count