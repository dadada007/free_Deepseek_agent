# -*- coding: utf-8 -*-
"""精准编辑模块 - 极简版（不做任何转义处理）"""

import os
import re
import logging

logger = logging.getLogger(__name__)


def edit_file(args: dict) -> str:
    """
    精准编辑文件
    
    支持模式:
    - replace: 字面字符串替换 (old_string, new_string, replace_all)
    - regex_replace: 正则替换 (pattern, replacement)
    - replace_lines: 行替换 (start_line, end_line, content)
    - insert: 插入行 (start_line, content)
    - delete: 删除行 (start_line, end_line)
    - append: 追加内容 (content)
    
    注意：当 replace_all=False 时，只替换第一个匹配项
    """
    """
    精准编辑文件
    
    支持模式:
    - replace: 字面字符串替换 (old_string, new_string, replace_all)
    - regex_replace: 正则替换 (pattern, replacement)  
    - replace_lines: 行替换 (start_line, end_line, content)
    - insert: 插入行 (start_line, content)
    - delete: 删除行 (start_line, end_line)
    - append: 追加内容 (content)
    """
    path = args.get("file_path", "")
    mode = args.get("mode", "")
    
    if not path or not mode:
        return "错误: 需要 file_path 和 mode"
    
    path = os.path.expanduser(path)
    if not os.path.exists(path):
        return f"错误: 文件不存在 - {path}"
    
    try:
        with open(path, 'r', encoding='utf-8', errors='replace') as f:
            original = f.read()
    except Exception as e:
        return f"错误: 读取失败 - {e}"
    
    lines = original.splitlines()
    content = args.get("content", "")
    
    # ===== replace: 字面字符串替换 =====
    if mode == "replace":
        old = args.get("old_string", "")
        new = args.get("new_string", "") or args.get("content", "")
        if not old:
            return "请提供 old_string"
        if not new:
            return "请提供 new_string 或 content"
        if old == new:
            return f"警告: old_string 与 new_string 相同，未发生任何修改（{path}）"
        
        count = original.count(old)
        if count == 0:
            return f"未找到匹配: {old[:50]}"
        
        replace_all = args.get("replace_all", False)
        n = count if replace_all else 1
        new_content = original.replace(old, new, n)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        return f"已替换 {n} 处（{path}）"
    
    # ===== regex_replace: 正则替换 =====
    if mode == "regex_replace":
        pattern = args.get("pattern", "")
        replacement = args.get("replacement", "") or args.get("content", "")
        if not pattern:
            return "请提供 pattern（正则表达式）"
        if not replacement:
            return "请提供 replacement 或 content"
        
        try:
            regex = re.compile(pattern, re.MULTILINE | re.DOTALL)
        except re.error as e:
            return f"正则表达式错误: {e}"
        
        new_content, count = regex.subn(replacement, original)
        if count == 0:
            return f"未找到匹配: {pattern}"
        with open(path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        return f"已正则替换 {count} 处（{path}）"
    
    # ===== insert: 插入行 =====
    if mode == "insert":
        start = args.get("start_line") or args.get("line")
        if start is None:
            return "错误: insert 模式需要提供 start_line 或 line 参数"
        
        try:
            start = int(start)
        except (ValueError, TypeError):
            return f"错误: start_line 必须是数字，当前值: {start}"
        
        total_lines = len(lines)
        if start < 1 or start > total_lines + 1:
            return f"行号越界: start_line={start}，必须在 1 到 {total_lines + 1} 之间"
        
        idx = start - 1
        new_lines = content.split('\n') if content else []
        lines[idx:idx] = new_lines
        with open(path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        
        location = "文件开头" if idx == 0 else f"第 {start} 行前"
        return f"已在 {location} 插入 {len(new_lines)} 行（{path}）"
    
    # ===== delete: 删除行 =====
    if mode == "delete":
        start = args.get("start_line") or args.get("line")
        if start is None:
            return "错误: delete 模式需要提供 start_line 或 line 参数"
        
        try:
            start = int(start)
        except (ValueError, TypeError):
            return f"错误: start_line 必须是数字，当前值: {start}"
        
        end = args.get("end_line", start)
        try:
            end = int(end)
        except (ValueError, TypeError):
            end = start
        
        total_lines = len(lines)
        if start < 1 or start > total_lines:
            return f"行号越界: start_line={start}，文件共 {total_lines} 行"
        end = end if end >= start else start
        if end > total_lines:
            end = total_lines
        del lines[start-1:end]
        with open(path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        return f"已删除第 {start}-{end} 行（{path}）"
    
    # ===== replace_lines: 行替换 =====
    if mode == "replace_lines":
        start = args.get("start_line") or args.get("line")
        if start is None:
            return "错误: replace_lines 模式需要提供 start_line 或 line 参数"
        
        try:
            start = int(start)
        except (ValueError, TypeError):
            return f"错误: start_line 必须是数字，当前值: {start}"
        
        end = args.get("end_line", start)
        try:
            end = int(end)
        except (ValueError, TypeError):
            end = start
        
        total_lines = len(lines)
        if start < 1 or start > total_lines:
            return f"行号越界: start_line={start}，文件共 {total_lines} 行"
        end = end if end >= start else start
        if end > total_lines:
            end = total_lines
        
        new_lines = content.split('\n') if content else []
        lines[start-1:end] = new_lines
        with open(path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        return f"已替换第 {start}-{end} 行（{path}）"
    
    # ===== append: 追加 =====
    if mode == "append":
        if not content :
            return "错误: 缺少 content 参数"
        
        if original and not original.endswith('\n'):
            content_to_append = '\n' + content
        else:
            content_to_append = content
        with open(path, 'a', encoding='utf-8') as f:
            f.write(content_to_append)
        return f"已追加到文件末尾（{path}）"
    
    return f"未知模式: {mode}，支持 replace/regex_replace/replace_lines/insert/delete/append"


# ============================================
# 注册函数（使用位置参数，与 file_operations_tools.py 保持一致）
# ============================================

def register_tools(tools_module):
    """注册所有工具到 tools 模块"""
    
    tools_module.register(
        "edit_file",
        "精准编辑文件。支持 replace/regex_replace/replace_lines/insert/delete/append 模式。content 原样写入，不做转义。",
        {
            "type": "object",
            "properties": {
                "file_path": {"type": "string", "description": "文件路径"},
                "mode": {
                    "type": "string",
                    "enum": ["replace", "regex_replace", "replace_lines", "insert", "delete", "append"],
                    "description": "编辑模式"
                },
                "old_string": {"type": "string", "description": "replace 模式：要替换的字符串"},
                "new_string": {"type": "string", "description": "replace 模式：新字符串"},
                "pattern": {"type": "string", "description": "regex_replace 模式：正则表达式"},
                "replacement": {"type": "string", "description": "regex_replace 模式：替换内容"},
                "start_line": {"type": "integer", "description": "起始行号（从1开始）"},
                "end_line": {"type": "integer", "description": "结束行号"},
                "content": {"type": "string", "description": "要插入/替换/追加的内容"},
                "replace_all": {"type": "boolean", "description": "是否替换全部匹配", "default": False}
            },
            "required": ["file_path", "mode"]
        },
        edit_file
    )
    
    logger.info("[OK] file_edit_tools 已注册到全局 tools.TOOLS")
    return 1


# ============================================
# 自动注册（当被导入时）
# ============================================

# 导入 tools 模块并自动注册
import sys
import os

# 确保父目录在 sys.path 中
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

try:
    import tools
    register_tools(tools)
    print("[OK] edit_file 工具已自动注册")
except ImportError:
    print("警告: 无法导入 tools 模块，edit_file 工具未注册")
