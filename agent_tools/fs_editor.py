# -*- coding: utf-8 -*-
"""文件编辑 - 极简版（不做任何转义处理）"""

import os
import re
from typing import Optional, List, Dict, Any


# ============================================
# 工具函数
# ============================================

def _read_lines(path: str) -> List[str]:
    """读取文件为行列表"""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        return content.splitlines() if content else []
    except Exception:
        return []


def _write_lines(path: str, lines: List[str]) -> None:
    """将行列表写入文件"""
    with open(path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))


def _get_line_indent(line: str) -> str:
    """获取行的缩进字符串"""
    if not line:
        return ""
    match = re.match(r'^[ \t]*', line)
    return match.group(0) if match else ""


def _find_line_matching(
    lines: List[str],
    pattern: str,
    start_from: int = 0,
    match_type: str = 'exact',
) -> int:
    """在行列表中查找匹配的行"""
    for idx in range(start_from, len(lines)):
        line = lines[idx].rstrip('\n\r')
        pattern_text = pattern.rstrip('\n\r')
        
        if match_type == 'exact':
            if line == pattern_text:
                return idx
        elif match_type == 'contains':
            if pattern_text in line:
                return idx
        elif match_type == 'regex':
            try:
                if re.search(pattern_text, line):
                    return idx
            except re.error:
                if pattern_text in line:
                    return idx
        else:
            if pattern_text in line:
                return idx
    return -1


# ============================================
# 编辑操作
# ============================================

def replace_string(
    file_path: str,
    old_string: str,
    new_string: str,
    replace_all: bool = True,
) -> Dict[str, Any]:
    """字符串替换"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if replace_all:
            new_content = content.replace(old_string, new_string)
        else:
            new_content = content.replace(old_string, new_string, 1)
        
        if content == new_content:
            return {
                'success': False,
                'message': f"未找到匹配: '{old_string[:50]}'",
            }
        
        count = content.count(old_string) if replace_all else 1
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        return {
            'success': True,
            'message': f"已替换 {count} 处",
            'count': count,
        }
    except FileNotFoundError:
        return {'success': False, 'message': f"文件不存在: {file_path}"}
    except Exception as e:
        return {'success': False, 'message': f"替换失败: {e}"}


def regex_replace(
    file_path: str,
    pattern: str,
    replacement: str,
) -> Dict[str, Any]:
    """正则替换"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        compiled = re.compile(pattern, re.MULTILINE | re.DOTALL)
        new_content, count = compiled.subn(replacement, content)
        
        if count == 0:
            return {
                'success': False,
                'message': f"未找到匹配: '{pattern}'",
            }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        return {
            'success': True,
            'message': f"已替换 {count} 处",
            'count': count,
        }
    except re.error as e:
        return {'success': False, 'message': f"正则表达式错误: {e}"}
    except FileNotFoundError:
        return {'success': False, 'message': f"文件不存在: {file_path}"}
    except Exception as e:
        return {'success': False, 'message': f"替换失败: {e}"}


def insert_lines(
    file_path: str,
    content: str,
    after: Optional[str] = None,
    before: Optional[str] = None,
    at_line: Optional[int] = None,
    match_type: str = 'exact',
) -> Dict[str, Any]:
    """插入行"""
    if not content:
        return {'success': False, 'message': "没有要插入的内容"}
    
    try:
        lines = _read_lines(file_path)
        content_lines = content.split('\n')
        insert_idx = len(lines)
        
        if at_line is not None:
            if at_line < 1 or at_line > len(lines) + 1:
                return {
                    'success': False,
                    'message': f"行号 {at_line} 超出范围 (1-{len(lines)+1})"
                }
            insert_idx = at_line - 1
        
        elif after is not None:
            idx = _find_line_matching(lines, after, match_type=match_type)
            if idx == -1:
                return {'success': False, 'message': f"未找到锚点: '{after}'"}
            insert_idx = idx + 1
        
        elif before is not None:
            idx = _find_line_matching(lines, before, match_type=match_type)
            if idx == -1:
                return {'success': False, 'message': f"未找到锚点: '{before}'"}
            insert_idx = idx
        
        # 应用缩进
        if insert_idx > 0 and insert_idx <= len(lines):
            indent = _get_line_indent(lines[insert_idx - 1])
        elif len(lines) > 0:
            indent = _get_line_indent(lines[0])
        else:
            indent = ""
        
        indented_lines = []
        for line in content_lines:
            if line.strip():
                indented_lines.append(indent + line.lstrip())
            else:
                indented_lines.append(line)
        
        lines[insert_idx:insert_idx] = indented_lines
        _write_lines(file_path, lines)
        
        return {
            'success': True,
            'message': f"已插入 {len(indented_lines)} 行",
            'count': len(indented_lines),
        }
    except FileNotFoundError:
        return {'success': False, 'message': f"文件不存在: {file_path}"}
    except Exception as e:
        return {'success': False, 'message': f"插入失败: {e}"}


def delete_lines(
    file_path: str,
    start_line: Optional[int] = None,
    end_line: Optional[int] = None,
    pattern: Optional[str] = None,
    match_type: str = 'contains',
) -> Dict[str, Any]:
    """删除行"""
    try:
        lines = _read_lines(file_path)
        total_lines = len(lines)
        
        to_delete = set()
        
        if pattern is not None:
            for idx in range(len(lines)):
                if _find_line_matching(lines, pattern, start_from=idx, match_type=match_type) == idx:
                    to_delete.add(idx)
        
        elif start_line is not None:
            end = end_line if end_line is not None else start_line
            if start_line < 1 or end > total_lines:
                return {
                    'success': False,
                    'message': f"行范围 {start_line}-{end} 超出范围 (1-{total_lines})"
                }
            to_delete = set(range(start_line - 1, end))
        
        else:
            return {'success': False, 'message': "未指定删除条件"}
        
        if not to_delete:
            return {
                'success': False,
                'message': "未找到匹配的行",
            }
        
        new_lines = [line for i, line in enumerate(lines) if i not in to_delete]
        _write_lines(file_path, new_lines)
        
        return {
            'success': True,
            'message': f"已删除 {len(to_delete)} 行",
            'count': len(to_delete),
        }
    except FileNotFoundError:
        return {'success': False, 'message': f"文件不存在: {file_path}"}
    except Exception as e:
        return {'success': False, 'message': f"删除失败: {e}"}


def edit_file(args: dict) -> str:
    """
    编辑文件
    
    支持模式:
    - replace: 字符串替换 (old_string, new_string, replace_all)
    - regex_replace: 正则替换 (pattern, replacement)
    - insert: 插入行 (content, after/before/at_line)
    - delete: 删除行 (start_line/end_line/pattern)
    - append: 追加内容 (content)
    """
    file_path = args.get("file_path", "")
    mode = args.get("mode", "")
    
    if not file_path:
        return "错误: 需要 file_path"
    if not mode:
        return "错误: 需要 mode"
    
    if not os.path.exists(file_path):
        return f"错误: 文件不存在 - {file_path}"
    
    content = args.get("content", "")
    
    if mode == "replace":
        old_string = args.get("old_string", "")
        new_string = args.get("new_string", "") or content
        if not old_string:
            return "错误: replace 模式需要 old_string"
        result = replace_string(file_path, old_string, new_string, args.get("replace_all", True))
        return result.get("message", "操作完成")
    
    elif mode == "regex_replace":
        pattern = args.get("pattern", "")
        replacement = args.get("replacement", "") or content
        if not pattern:
            return "错误: regex_replace 模式需要 pattern"
        result = regex_replace(file_path, pattern, replacement)
        return result.get("message", "操作完成")
    
    elif mode == "insert":
        after = args.get("after")
        before = args.get("before")
        at_line = args.get("start_line") or args.get("line")
        if not content:
            return "错误: insert 模式需要 content"
        result = insert_lines(file_path, content, after, before, at_line, args.get("match_type", "exact"))
        return result.get("message", "操作完成")
    
    elif mode == "delete":
        result = delete_lines(
            file_path,
            args.get("start_line"),
            args.get("end_line"),
            args.get("pattern"),
            args.get("match_type", "contains")
        )
        return result.get("message", "操作完成")
    
    elif mode == "append":
        if not content:
            return "错误: append 模式需要 content"
        try:
            with open(file_path, 'a', encoding='utf-8') as f:
                f.write('\n' + content)
            return f"已追加到文件末尾（{file_path}）"
        except Exception as e:
            return f"错误: 追加失败 - {e}"
    
    else:
        return f"未知模式: {mode}，支持 replace/regex_replace/insert/delete/append"


def edit_file_v2(args: dict) -> dict:
    """
    edit_file_v2 - 兼容 fs_register.py 的接口
    
    和 edit_file 一样，但返回 dict 而不是 str
    """
    file_path = args.get("file_path", "")
    mode = args.get("mode", "")
    
    if not file_path:
        return {'success': False, 'message': "需要 file_path"}
    if not mode:
        return {'success': False, 'message': "需要 mode"}
    
    if not os.path.exists(file_path):
        return {'success': False, 'message': f"文件不存在: {file_path}"}
    
    content = args.get("content", "")
    
    if mode == "replace":
        old_string = args.get("old_string", "")
        new_string = args.get("new_string", "") or content
        if not old_string:
            return {'success': False, 'message': "replace 模式需要 old_string"}
        return replace_string(file_path, old_string, new_string, args.get("replace_all", True))
    
    elif mode == "regex_replace":
        pattern = args.get("pattern", "")
        replacement = args.get("replacement", "") or content
        if not pattern:
            return {'success': False, 'message': "regex_replace 模式需要 pattern"}
        return regex_replace(file_path, pattern, replacement)
    
    elif mode == "insert":
        after = args.get("after")
        before = args.get("before")
        at_line = args.get("start_line") or args.get("line")
        if not content:
            return {'success': False, 'message': "insert 模式需要 content"}
        return insert_lines(file_path, content, after, before, at_line, args.get("match_type", "exact"))
    
    elif mode == "delete":
        return delete_lines(
            file_path,
            args.get("start_line"),
            args.get("end_line"),
            args.get("pattern"),
            args.get("match_type", "contains")
        )
    
    elif mode == "append":
        if not content:
            return {'success': False, 'message': "append 模式需要 content"}
        try:
            with open(file_path, 'a', encoding='utf-8') as f:
                f.write('\n' + content)
            return {'success': True, 'message': f"已追加到文件末尾（{file_path}）"}
        except Exception as e:
            return {'success': False, 'message': f"追加失败: {e}"}
    
    else:
        return {
            'success': False,
            'message': f"未知模式: {mode}，支持 replace/regex_replace/insert/delete/append"
        }


# ============================================
# 注册函数
# ============================================

def register_tools(tools_module):
    """注册所有工具到 tools 模块"""
    
    tools_module.register(
        name="edit_file",
        description="编辑文件。支持 replace/regex_replace/insert/delete/append 模式。content 原样写入，不做转义。",
        parameters={
            "type": "object",
            "properties": {
                "file_path": {"type": "string", "description": "文件路径"},
                "mode": {
                    "type": "string",
                    "enum": ["replace", "regex_replace", "insert", "delete", "append"],
                    "description": "编辑模式"
                },
                "old_string": {"type": "string", "description": "replace 模式：要替换的字符串"},
                "new_string": {"type": "string", "description": "replace/regex_replace 模式：新字符串"},
                "pattern": {"type": "string", "description": "regex_replace/delete 模式：正则表达式"},
                "replacement": {"type": "string", "description": "regex_replace 模式：替换内容"},
                "content": {"type": "string", "description": "insert/append 模式：要插入或追加的内容"},
                "start_line": {"type": "integer", "description": "insert/delete 模式：起始行号（从1开始）"},
                "end_line": {"type": "integer", "description": "delete 模式：结束行号"},
                "after": {"type": "string", "description": "insert 模式：在匹配行后插入"},
                "before": {"type": "string", "description": "insert 模式：在匹配行前插入"},
                "replace_all": {"type": "boolean", "description": "replace 模式：是否替换全部", "default": True}
            },
            "required": ["file_path", "mode"]
        },
        func=edit_file
    )
    
    return 1