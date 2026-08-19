# -*- coding: utf-8 -*-
"""
fs_register.py - 统一注册所有文件系统工具到 Hermes

注册约 30+ 个工具到 Hermes 工具系统。
采用动态导入，确保热加载环境下闭包正常工作。
"""

import sys
import os
import importlib

# 确保当前目录在 sys.path 中
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)


def _get_module(name):
    """动态导入模块，确保每次调用时重新获取"""
    try:
        return importlib.import_module(f'.{name}', package='agent_tools')
    except ImportError:
        try:
            return importlib.import_module(name)
        except ImportError:
            return None


def _safe_call(module_name, func_path, args):
    mod = _get_module(module_name)
    if mod is None:
        return f"错误: 无法导入模块 {module_name}"
    
    # 逐级解析：FSUtil.list_dir_with_info
    obj = mod
    for part in func_path.split('.'):
        obj = getattr(obj, part, None)
        if obj is None:
            return f"错误: 无法解析 {func_path}"
    
    try:
        # 对于 edit_file_v2，它接受一个 dict 参数，使用位置参数调用
        # 对于其他函数，使用关键字参数解包
        if func_path == 'edit_file_v2':
            result = obj(args)
        else:
            result = obj(**args)
        return result
    except Exception as e:
        return f"错误: {e}"


def _smart_read_file(args):
    """
    智能读取文件 - 直接使用 file_operations_tools 中的 read_file
    支持分块参数：chunk_index, chunk_size, raw
    """
    try:
        # 动态导入，避免循环依赖
        mod = _get_module('file_operations_tools')
        if mod is None:
            return "错误: 无法导入 file_operations_tools 模块"
        # 直接调用 file_operations_tools 中的 read_file
        return mod.read_file(args)
    except Exception as e:
        return f"错误: 智能读取失败 - {e}"


def register_fs_tools():
    """注册所有文件系统工具到 Hermes"""
    try:
        import tools
    except ImportError:
        print("警告: 无法导入 tools 模块")
        return 0

    registered = 0

    # ========================================
    # 1. 路径工具
    # ========================================

    tools.register(
        name="fs_normalize_path",
        description="标准化路径（处理 .. 和 . ，解析符号链接）",
        parameters={
            "type": "object",
            "properties": {"path": {"type": "string"}},
            "required": ["path"]
        },
        func=lambda args: _safe_call('fs_path_utils', 'normalize_path', {'p': args.get('path', '')})
    )
    registered += 1

    tools.register(
        name="fs_resolve_safe",
        description="安全解析路径，防止越界",
        parameters={
            "type": "object",
            "properties": {
                "base_dir": {"type": "string"},
                "target": {"type": "string"}
            },
            "required": ["base_dir", "target"]
        },
        func=lambda args: _safe_call('fs_path_utils', 'resolve_safe', args)
    )
    registered += 1

    tools.register(
        name="fs_is_inside",
        description="检查路径是否在指定目录内",
        parameters={
            "type": "object",
            "properties": {
                "parent": {"type": "string"},
                "child": {"type": "string"}
            },
            "required": ["parent", "child"]
        },
        func=lambda args: _safe_call('fs_path_utils', 'contains', args)
    )
    registered += 1

    tools.register(
        name="fs_get_relative",
        description="获取相对路径",
        parameters={
            "type": "object",
            "properties": {
                "base": {"type": "string"},
                "target": {"type": "string"}
            },
            "required": ["base", "target"]
        },
        func=lambda args: _safe_call('fs_path_utils', 'get_relative_path', args)
    )
    registered += 1

    tools.register(
        name="fs_glob",
        description="通配符搜索文件",
        parameters={
            "type": "object",
            "properties": {
                "pattern": {"type": "string"},
                "root": {"type": "string", "default": "."},
                "recursive": {"type": "boolean", "default": True}
            },
            "required": ["pattern"]
        },
        func=lambda args: _safe_call('fs_io_core', 'FSUtil.glob', args)
    )
    registered += 1

    tools.register(
        name="fs_find_up",
        description="向上查找文件",
        parameters={
            "type": "object",
            "properties": {
                "target": {"type": "string"},
                "start": {"type": "string"},
                "stop": {"type": "string", "default": ""}
            },
            "required": ["target", "start"]
        },
        func=lambda args: _safe_call('fs_io_core', 'FSUtil.find_up', args)
    )
    registered += 1

    # ========================================
    # 2. 文件读写 - 使用智能分块版本
    # ========================================

    # 注意：fs_read 现在使用 file_operations_tools 中的 read_file（支持智能分块）
    tools.register(
        name="fs_read",
        description="读取文件内容（智能分块）。小文件直接返回完整内容，大文件自动分块返回摘要+内容块。可通过 chunk_index 参数读取指定块。",
        parameters={
            "type": "object",
            "properties": {
                "file_path": {"type": "string", "description": "文件路径"},
                "raw": {"type": "boolean", "description": "是否返回原始完整内容（跳过智能分块）", "default": False},
                "chunk_index": {"type": "integer", "description": "读取第几块（从1开始），仅大文件有效", "default": 1},
                "chunk_size": {"type": "integer", "description": "每块大小（字符数），默认 2000", "default": 2000}
            },
            "required": ["file_path"]
        },
        func=_smart_read_file
    )
    registered += 1

    tools.register(
        name="fs_write",
        description="写入文件（自动创建目录，支持 BOM）",
        parameters={
            "type": "object",
            "properties": {
                "file_path": {"type": "string"},
                "content": {"type": "string"},
                "preserve_bom": {"type": "boolean", "default": True}
            },
            "required": ["file_path", "content"]
        },
        func=lambda args: _safe_call('fs_mutation', 'safe_write_file', {'path': args.get('file_path', ''), 'content': args.get('content', ''), 'preserve_bom': args.get('preserve_bom', True)})
    )
    registered += 1

    tools.register(
        name="fs_append",
        description="追加内容到文件末尾",
        parameters={
            "type": "object",
            "properties": {
                "file_path": {"type": "string"},
                "content": {"type": "string"}
            },
            "required": ["file_path", "content"]
        },
        func=lambda args: _safe_call('fs_mutation', 'safe_append_file', {'path': args.get('file_path', ''), 'content': args.get('content', '')})
    )
    registered += 1

    tools.register(
        name="fs_create",
        description="创建文件（已存在则失败）",
        parameters={
            "type": "object",
            "properties": {
                "file_path": {"type": "string"},
                "content": {"type": "string"},
                "preserve_bom": {"type": "boolean", "default": True}
            },
            "required": ["file_path", "content"]
        },
        func=lambda args: _safe_call('fs_mutation', 'safe_create_file', {'path': args.get('file_path', ''), 'content': args.get('content', ''), 'preserve_bom': args.get('preserve_bom', True)})
    )
    registered += 1

    tools.register(
        name="fs_delete",
        description="删除文件或空目录",
        parameters={
            "type": "object",
            "properties": {"path": {"type": "string"}},
            "required": ["path"]
        },
        func=lambda args: _safe_call('fs_mutation', 'safe_remove_file', args)
    )
    registered += 1

    tools.register(
        name="fs_delete_tree",
        description="递归删除目录或文件",
        parameters={
            "type": "object",
            "properties": {"path": {"type": "string"}},
            "required": ["path"]
        },
        func=lambda args: _safe_call('fs_io_core', 'FSUtil.remove_recursive', args)
    )
    registered += 1

    tools.register(
        name="fs_mkdir",
        description="创建目录（自动创建父目录）",
        parameters={
            "type": "object",
            "properties": {"path": {"type": "string"}},
            "required": ["path"]
        },
        func=lambda args: _safe_call('fs_io_core', 'FSUtil.ensure_dir', args)
    )
    registered += 1

    tools.register(
        name="fs_copy",
        description="复制文件或目录",
        parameters={
            "type": "object",
            "properties": {
                "src": {"type": "string"},
                "dst": {"type": "string"},
                "overwrite": {"type": "boolean", "default": True}
            },
            "required": ["src", "dst"]
        },
        func=lambda args: _safe_call('fs_io_core', 'FSUtil.copy', args)
    )
    registered += 1

    # ========================================
    # 3. 文件编辑
    # ========================================

    tools.register(
        name="fs_edit",
        description="统一文件编辑接口（支持 replace/regex_replace/replace_lines/insert/delete/append/write）",
        parameters={
            "type": "object",
            "properties": {
                "file_path": {"type": "string"},
                "mode": {"type": "string"},
                "old_string": {"type": "string"},
                "new_string": {"type": "string"},
                "pattern": {"type": "string"},
                "replacement": {"type": "string"},
                "old_line": {"type": "string"},
                "new_line": {"type": "string"},
                "content": {"type": "string"},
                "replace_all": {"type": "boolean", "default": True},
                "after": {"type": "string"},
                "before": {"type": "string"},
                "start_line": {"type": "integer"},
                "end_line": {"type": "integer"},
                "expected_content": {"type": "string"}
            },
            "required": ["file_path", "mode"]
        },
        func=lambda args: _safe_call('fs_editor', 'edit_file_v2', args)
    )
    registered += 1

    tools.register(
        name="fs_replace",
        description="字符串替换（精确）",
        parameters={
            "type": "object",
            "properties": {
                "file_path": {"type": "string"},
                "old_string": {"type": "string"},
                "new_string": {"type": "string"},
                "replace_all": {"type": "boolean", "default": True}
            },
            "required": ["file_path", "old_string", "new_string"]
        },
        func=lambda args: _safe_call('fs_editor', 'replace_string', args)
    )
    registered += 1

    tools.register(
        name="fs_regex_replace",
        description="正则替换",
        parameters={
            "type": "object",
            "properties": {
                "file_path": {"type": "string"},
                "pattern": {"type": "string"},
                "replacement": {"type": "string"}
            },
            "required": ["file_path", "pattern", "replacement"]
        },
        func=lambda args: _safe_call('fs_editor', 'regex_replace', args)
    )
    registered += 1

    tools.register(
        name="fs_insert_lines",
        description="插入行",
        parameters={
            "type": "object",
            "properties": {
                "file_path": {"type": "string"},
                "content": {"type": "array"},
                "after": {"type": "string"},
                "before": {"type": "string"}
            },
            "required": ["file_path", "content"]
        },
        func=lambda args: _safe_call('fs_editor', 'insert_lines', args)
    )
    registered += 1

    tools.register(
        name="fs_delete_lines",
        description="删除行（按行号或模式）",
        parameters={
            "type": "object",
            "properties": {
                "file_path": {"type": "string"},
                "start_line": {"type": "integer"},
                "end_line": {"type": "integer"},
                "pattern": {"type": "string"}
            },
            "required": ["file_path"]
        },
        func=lambda args: _safe_call('fs_editor', 'delete_lines', args)
    )
    registered += 1

    tools.register(
        name="fs_safe_edit",
        description="条件写入（只有内容一致时才写入）",
        parameters={
            "type": "object",
            "properties": {
                "file_path": {"type": "string"},
                "new_content": {"type": "string"},
                "expected_content": {"type": "string"}
            },
            "required": ["file_path", "new_content", "expected_content"]
        },
        func=lambda args: _safe_call('fs_editor', 'safe_edit', args)
    )
    registered += 1

    # ========================================
    # 4. Shell 执行
    # ========================================

    tools.register(
        name="fs_exec",
        description="执行命令（带超时和进程树管理）",
        parameters={
            "type": "object",
            "properties": {
                "command": {"type": "string"},
                "cwd": {"type": "string"},
                "timeout": {"type": "number", "default": 30},
                "input_text": {"type": "string"}
            },
            "required": ["command"]
        },
        func=lambda args: _safe_call('fs_shell', 'execute_command_safe', args)
    )
    registered += 1

    tools.register(
        name="fs_bg_run",
        description="后台运行命令",
        parameters={
            "type": "object",
            "properties": {
                "command": {"type": "string"},
                "cwd": {"type": "string"}
            },
            "required": ["command"]
        },
        func=lambda args: _safe_call('fs_shell', 'run_background', args)
    )
    registered += 1

    tools.register(
        name="fs_bg_kill",
        description="杀死后台任务",
        parameters={
            "type": "object",
            "properties": {"task_id": {"type": "string"}},
            "required": ["task_id"]
        },
        func=lambda args: _safe_call('fs_shell', 'kill_background_task', args)
    )
    registered += 1

    tools.register(
        name="fs_bg_status",
        description="获取后台任务状态",
        parameters={
            "type": "object",
            "properties": {"task_id": {"type": "string"}},
            "required": ["task_id"]
        },
        func=lambda args: _safe_call('fs_shell', 'get_background_task', args)
    )
    registered += 1

    tools.register(
        name="fs_bg_list",
        description="列出所有后台任务",
        parameters={"type": "object", "properties": {}},
        func=lambda args: _safe_call('fs_shell', 'list_background_tasks', args)
    )
    registered += 1

    tools.register(
        name="fs_shells",
        description="列出可用的 Shell",
        parameters={"type": "object", "properties": {}},
        func=lambda args: _safe_call('fs_shell', 'find_shells', args)
    )
    registered += 1

    # ========================================
    # 5. 文件信息查询
    # ========================================

    tools.register(
        name="fs_stat",
        description="获取文件信息（大小、时间、权限等）",
        parameters={
            "type": "object",
            "properties": {"path": {"type": "string"}},
            "required": ["path"]
        },
        func=lambda args: _safe_call('fs_io_core', 'FSUtil.stat', args)
    )
    registered += 1

    tools.register(
        name="fs_list",
        description="列出目录内容",
        parameters={
            "type": "object",
            "properties": {"path": {"type": "string"}},
            "required": ["path"]
        },
        func=lambda args: _safe_call('fs_io_core', 'FSUtil.list_dir_with_info', args)
    )
    registered += 1

    tools.register(
        name="fs_grep",
        description="在文件中搜索内容",
        parameters={
            "type": "object",
            "properties": {
                "pattern": {"type": "string"},
                "root": {"type": "string"},
                "file_pattern": {"type": "string"},
                "max_results": {"type": "integer", "default": 100}
            },
            "required": ["pattern", "root"]
        },
        func=lambda args: _safe_call('fs_io_core', 'FSUtil.grep', args)
    )
    registered += 1

    tools.register(
        name="fs_hash",
        description="计算文件哈希值",
        parameters={
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "algorithm": {"type": "string", "default": "sha256"}
            },
            "required": ["path"]
        },
        func=lambda args: _safe_call('fs_io_core', 'FSUtil.file_hash', args)
    )
    registered += 1

    # 移除 emoji，避免 Windows GBK 编码错误
    print(f"[OK] 成功注册 {registered} 个文件系统工具")
    return registered


# ============================================
# 自动注册（当被导入时）
# ============================================

if __name__ == '__main__':
    register_fs_tools()
else:
    register_fs_tools()
