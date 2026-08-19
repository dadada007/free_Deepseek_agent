# -*- coding: utf-8 -*-
"""
系统监控工具集 - 支持 CPU、内存、磁盘、网络、进程监控
"""

import os
import json
import time
from datetime import datetime


def _import_psutil():
    try:
        import psutil
        return psutil
    except ImportError:
        return None


def _format_bytes(bytes_val):
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_val < 1024:
            return f"{bytes_val:.1f} {unit}"
        bytes_val /= 1024
    return f"{bytes_val:.1f} PB"


def _system_info(args: dict) -> str:
    try:
        detail = args.get('detail', False)
        psutil = _import_psutil()
        if not psutil:
            return "❌ 请安装 psutil: pip install psutil"
        import platform as plt
        result = {
            '时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            '主机名': plt.node(),
            '系统': plt.system(),
        }
        cpu_percent = psutil.cpu_percent(interval=1)
        result['CPU'] = {'使用率': f"{cpu_percent:.1f}%", '核心数': psutil.cpu_count()}
        mem = psutil.virtual_memory()
        result['内存'] = {'总内存': _format_bytes(mem.total), '已用': _format_bytes(mem.used), '使用率': f"{mem.percent:.1f}%"}
        result['磁盘'] = []
        for partition in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                result['磁盘'].append({'挂载点': partition.mountpoint, '总': _format_bytes(usage.total), '使用率': f"{usage.percent:.1f}%"})
            except:
                pass
        net = psutil.net_io_counters()
        result['网络'] = {'发送': _format_bytes(net.bytes_sent), '接收': _format_bytes(net.bytes_recv)}
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"❌ 获取系统信息失败: {e}"


def _process_list(args: dict) -> str:
    try:
        top_n = args.get('top', 10)
        sort_by = args.get('sort', 'cpu')
        psutil = _import_psutil()
        if not psutil:
            return "❌ 请安装 psutil: pip install psutil"
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'memory_info', 'status']):
            try:
                info = proc.info
                processes.append({
                    'pid': info['pid'], 'name': info['name'],
                    'cpu': round(info['cpu_percent'] or 0, 1),
                    'memory_mb': round((info['memory_info'].rss / 1024 / 1024) if info['memory_info'] else 0, 1),
                })
            except:
                continue
        if sort_by == 'cpu':
            processes.sort(key=lambda x: x['cpu'], reverse=True)
        elif sort_by == 'memory':
            processes.sort(key=lambda x: x['memory_mb'], reverse=True)
        return json.dumps({'总进程数': len(processes), '进程': processes[:top_n]}, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"❌ 获取进程列表失败: {e}"


def _kill_process(args: dict) -> str:
    try:
        pid = args.get('pid')
        name = args.get('name')
        psutil = _import_psutil()
        if not psutil:
            return "❌ 请安装 psutil: pip install psutil"
        killed = []
        if pid:
            try:
                proc = psutil.Process(pid)
                proc.terminate()
                killed.append(f"PID {pid}")
            except psutil.NoSuchProcess:
                return f"❌ 进程不存在: PID {pid}"
        if name:
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    if proc.info['name'] == name:
                        proc.terminate()
                        killed.append(f"PID {proc.info['pid']} ({name})")
                except:
                    continue
        return json.dumps({'成功终止': killed}, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"❌ 终止进程失败: {e}"


def _disk_analysis(args: dict) -> str:
    try:
        path = args.get('path', os.path.abspath(os.sep))
        psutil = _import_psutil()
        if not psutil:
            return "❌ 请安装 psutil: pip install psutil"
        usage = psutil.disk_usage(path)
        result = {'路径': path, '总空间': _format_bytes(usage.total), '已用': _format_bytes(usage.used), '可用': _format_bytes(usage.free), '使用率': f"{usage.percent:.1f}%"}
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"❌ 磁盘分析失败: {e}"


def _uptime(args: dict) -> str:
    try:
        psutil = _import_psutil()
        if not psutil:
            return "❌ 请安装 psutil: pip install psutil"
        boot_time = psutil.boot_time()
        uptime_seconds = time.time() - boot_time
        days = int(uptime_seconds // 86400)
        hours = int((uptime_seconds % 86400) // 3600)
        minutes = int((uptime_seconds % 3600) // 60)
        return json.dumps({'启动时间': datetime.fromtimestamp(boot_time).strftime('%Y-%m-%d %H:%M:%S'), '运行时间': f"{days}天 {hours}小时 {minutes}分钟"}, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"❌ 获取运行时间失败: {e}"


def register_tools():
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import tools
    tools.register(name="system_info", description="获取系统概况。参数: detail(详细信息)", parameters={"type": "object", "properties": {"detail": {"type": "boolean"}}}, func=_system_info)
    tools.register(name="process_list", description="获取进程列表。参数: top, sort(cpu/memory)", parameters={"type": "object", "properties": {"top": {"type": "integer"}, "sort": {"type": "string"}}}, func=_process_list)
    tools.register(name="kill_process", description="终止进程。参数: pid 或 name", parameters={"type": "object", "properties": {"pid": {"type": "integer"}, "name": {"type": "string"}}}, func=_kill_process)
    tools.register(name="disk_analysis", description="分析磁盘使用。参数: path", parameters={"type": "object", "properties": {"path": {"type": "string"}}}, func=_disk_analysis)
    tools.register(name="uptime", description="获取系统运行时间", parameters={"type": "object", "properties": {}}, func=_uptime)
    return 5


def unregister_tools():
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import tools
    for name in ["system_info", "process_list", "kill_process", "disk_analysis", "uptime"]:
        tools.TOOLS.pop(name, None)
