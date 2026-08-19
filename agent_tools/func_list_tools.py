# -*- coding: utf-8 -*-
"""列出 Python 文件中的函数/类签名"""

import os
import re
import sys
from typing import List, Dict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tools import register

SKIP_DIRS = {'.git', '__pycache__', '.idea', '.vscode', 'node_modules', 'venv', 'env', '.hermes_backup', 'dist', 'build'}


def _extract_signatures(file_path: str) -> Dict:
    """提取单个文件的函数和类签名"""
    result = {'file': file_path, 'classes': [], 'functions': [], 'errors': []}
    
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
    except Exception as e:
        result['errors'].append(str(e))
        return result

    i = 0
    in_string = False
    string_char = ''
    in_block_comment = False
    
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        
        # 简单跳过字符串和注释
        # 只做基础处理，不追求完美
        if not stripped or stripped.startswith('#') or stripped.startswith('"""') or stripped.startswith("'''"):
            i += 1
            continue
        
        # 匹配 class 定义
        class_match = re.match(r'^\s*class\s+(\w+)\s*(?:\(([^)]*)\))?\s*:', line)
        if class_match:
            name = class_match.group(1)
            parents = class_match.group(2) or ''
            # 查找类的方法
            methods = []
            j = i + 1
            while j < len(lines):
                sub_line = lines[j]
                sub_stripped = sub_line.strip()
                if sub_stripped and not sub_stripped.startswith('#'):
                    method_match = re.match(r'^\s*def\s+(\w+)\s*\(([^)]*)\)\s*[:]?', sub_line)
                    if method_match:
                        method_name = method_match.group(1)
                        params = method_match.group(2).strip()
                        # 过滤私有方法（除非是 __init__）
                        if not method_name.startswith('_') or method_name == '__init__':
                            # 处理多行参数
                            param_text = params
                            if param_text.count('(') > param_text.count(')'):
                                k = j + 1
                                while k < len(lines) and param_text.count('(') > param_text.count(')'):
                                    param_text += ' ' + lines[k].strip()
                                    k += 1
                                j = k
                            methods.append(f"  def {method_name}({param_text})")
                    elif sub_stripped.startswith('class ') or (sub_stripped and not sub_stripped.startswith('@') and not sub_stripped.startswith('#')):
                        break
                j += 1
            
            result['classes'].append({
                'name': name,
                'parents': parents,
                'methods': methods
            })
            i = j
            continue
        
        # 匹配顶层函数（不在类内）
        func_match = re.match(r'^\s*def\s+(\w+)\s*\(([^)]*)\)\s*[:]?', line)
        if func_match:
            name = func_match.group(1)
            params = func_match.group(2).strip()
            # 处理多行参数
            param_text = params
            if param_text.count('(') > param_text.count(')'):
                j = i + 1
                while j < len(lines) and param_text.count('(') > param_text.count(')'):
                    param_text += ' ' + lines[j].strip()
                    j += 1
                i = j
            result['functions'].append(f"def {name}({param_text})")
        
        i += 1
    
    return result


def list_functions(args: dict) -> str:
    """
    列出 Python 文件或项目中的函数和类签名。
    参数:
        path: 文件路径或目录路径
        depth: 扫描深度（仅目录有效，默认 3）
    """
    path = args.get('path', '').strip()
    if not path:
        return '错误: 请提供 path 参数'
    if not os.path.exists(path):
        return f'路径不存在: {path}'
    
    depth = args.get('depth', 3)
    if not isinstance(depth, int):
        try:
            depth = int(depth)
        except (ValueError, TypeError):
            depth = 3
    depth = max(1, min(6, depth))
    
    # 如果是文件，只处理该文件
    if os.path.isfile(path):
        if not path.endswith('.py'):
            return f'不是 Python 文件: {path}'
        result = _extract_signatures(path)
        return _format_result(result)
    
    # 如果是目录，扫描所有 Python 文件
    if not os.path.isdir(path):
        return f'路径不是文件或目录: {path}'
    
    all_results = []
    for root, dirs, files in os.walk(path):
        # 控制深度
        rel_path = os.path.relpath(root, path)
        current_depth = 0 if rel_path == '.' else rel_path.count(os.sep) + 1
        if current_depth > depth:
            dirs[:] = []
            continue
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith('.')]
        
        for f in files:
            if not f.endswith('.py'):
                continue
            file_path = os.path.join(root, f)
            result = _extract_signatures(file_path)
            if result['classes'] or result['functions']:
                all_results.append(result)
    
    if not all_results:
        return f'目录: {path}未找到任何函数或类定义'
    
    return _format_results(all_results, path)


def _format_result(result: Dict) -> str:
    """格式化单个文件的结果"""
    lines = []
    rel_path = os.path.basename(result['file'])
    lines.append(f'📄 {rel_path}')
    lines.append('=' * 40)
    
    if result['classes']:
        lines.append(f'📦 类 ({len(result["classes"])} 个):')
        for cls in result['classes']:
            parent_str = f'({cls["parents"]})' if cls['parents'] else ''
            lines.append(f'  class {cls["name"]}{parent_str}')
            for method in cls['methods']:
                lines.append(f'    {method}')
        lines.append('')
    
    if result['functions']:
        lines.append(f'🔧 函数 ({len(result["functions"])} 个):')
        for func in result['functions']:
            lines.append(f'  {func}')
    
    if result['errors']:
        lines.append('⚠️ 错误: ' + '; '.join(result['errors']))
    
    return '\n'.join(lines)


def _format_results(results: List[Dict], base_path: str) -> str:
    """格式化多个文件的结果"""
    total_classes = sum(len(r['classes']) for r in results)
    total_functions = sum(len(r['functions']) for r in results)
    total_files = len(results)
    
    lines = [
        f'📂 项目: {base_path}',
        '=' * 50,
        f'📊 扫描了 {total_files} 个 Python 文件',
        f'📦 共发现 {total_classes} 个类',
        f'🔧 共发现 {total_functions} 个函数',
        '',
        '-' * 50,
    ]
    
    for result in results:
        rel_path = os.path.relpath(result['file'], base_path)
        lines.append(f'📄 {rel_path}')
        
        if result['classes']:
            for cls in result['classes']:
                parent_str = f'({cls["parents"]})' if cls['parents'] else ''
                lines.append(f'  📦 class {cls["name"]}{parent_str}')
                # 最多显示前5个方法
                for method in cls['methods'][:5]:
                    lines.append(f'    {method}')
                if len(cls['methods']) > 5:
                    lines.append(f'    ... 还有 {len(cls["methods"]) - 5} 个方法')
        
        if result['functions']:
            for func in result['functions'][:5]:
                lines.append(f'  🔧 {func}')
            if len(result['functions']) > 5:
                lines.append(f'  ... 还有 {len(result["functions"]) - 5} 个函数')
        
        lines.append('')
    
    return '\n'.join(lines)


def register_tools() -> int:
    """注册工具"""
    register(
        name='list_functions',
        description='列出 Python 文件或项目中的所有函数和类签名，包含参数列表。适用于快速了解模块结构。',
        parameters={
            'type': 'object',
            'properties': {
                'path': {'type': 'string', 'description': 'Python 文件路径或项目目录路径'},
                'depth': {'type': 'integer', 'description': '扫描目录深度（默认 3，范围 1-6）', 'default': 3}
            },
            'required': ['path']
        },
        func=list_functions
    )
    return 1


if __name__ == '__main__':
    register_tools()
    print('✅ func_list_tools 已加载')
