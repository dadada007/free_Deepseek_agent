# -*- coding: utf-8 -*-
"""代码扫描工具集"""

import os
import re
import sys
from typing import List, Dict, Tuple

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tools import register

SKIP_DIRS = {'.git', '__pycache__', '.idea', '.vscode', 'node_modules', 'venv', 'env', '.hermes_backup', 'dist', 'build'}

# ==================== scan_todos ====================

def _scan_todos_in_file(file_path: str) -> List[Dict]:
    results = []
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
    except Exception:
        return results
    patterns = [
        r'#\s*(TODO|FIXME|XXX|HACK|BUG|OPTIMIZE)\s*[:]?\s*(.*)$',
        r'//\s*(TODO|FIXME|XXX|HACK|BUG|OPTIMIZE)\s*[:]?\s*(.*)$',
    ]
    for i, line in enumerate(lines, 1):
        for p in patterns:
            m = re.search(p, line, re.IGNORECASE)
            if m:
                results.append({'line': i, 'tag': m.group(1).upper(), 'content': m.group(2).strip(), 'file': file_path})
                break
    return results

def scan_todos(args: dict) -> str:
    path = args.get('path', '').strip()
    if not path:
        return '错误: 请提供 path 参数'
    if not os.path.exists(path):
        return f'路径不存在: {path}'
    if not os.path.isdir(path):
        return f'路径不是目录: {path}'
    exts = ['.py', '.js', '.ts', '.go', '.rs', '.c', '.cpp', '.h', '.hpp', '.java', '.kt']
    all_results = []
    for root, dirs, files in os.walk(path):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith('.')]
        for f in files:
            if os.path.splitext(f)[1].lower() not in exts:
                continue
            all_results.extend(_scan_todos_in_file(os.path.join(root, f)))
    if not all_results:
        return '目录: ' + path + '\
未发现 TODO/FIXME/XXX 注释'
    groups = {}
    for r in all_results:
        groups.setdefault(r['tag'], []).append(r)
    out = ['目录: ' + path, '共发现 ' + str(len(all_results)) + ' 个待办项', '']
    for tag, items in groups.items():
        out.append('--- ' + tag + ' (' + str(len(items)) + ' 个) ---')
        for item in items:
            rel = os.path.relpath(item['file'], path)
            out.append('  ' + rel + ':' + str(item['line']) + '  ' + item['content'][:60])
        out.append('')
    return '\
'.join(out)

# ==================== count_code ====================

def _count_file(file_path: str) -> Dict:
    s = {'lines': 0, 'code': 0, 'comments': 0, 'blank': 0, 'funcs': 0, 'classes': 0}
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
    except Exception:
        return s
    s['lines'] = len(lines)
    in_block = False
    fp = re.compile(r'^\s*def\s+\w+\s*\(')
    cp = re.compile(r'^\s*class\s+\w+')
    for line in lines:
        st = line.strip()
        if not st:
            s['blank'] += 1
            continue
        if st.startswith('"""') or st.startswith("'''"):
            if st.count('"""') >= 2 or st.count("'''") >= 2:
                s['comments'] += 1
                continue
            in_block = not in_block
            s['comments'] += 1
            continue
        if in_block:
            s['comments'] += 1
            continue
        if st.startswith('#'):
            s['comments'] += 1
            continue
        s['code'] += 1
        if fp.search(line):
            s['funcs'] += 1
        elif cp.search(line):
            s['classes'] += 1
    return s

def count_code(args: dict) -> str:
    path = args.get('path', '').strip()
    if not path:
        return '错误: 请提供 path 参数'
    if not os.path.exists(path):
        return f'路径不存在: {path}'
    total = {'files': 0, 'lines': 0, 'code': 0, 'comments': 0, 'blank': 0, 'funcs': 0, 'classes': 0}
    for root, dirs, files in os.walk(path):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith('.')]
        for f in files:
            if not f.endswith('.py'):
                continue
            st = _count_file(os.path.join(root, f))
            total['files'] += 1
            for k in ['lines', 'code', 'comments', 'blank', 'funcs', 'classes']:
                total[k] += st.get(k, 0)
    if total['files'] == 0:
        return '目录: ' + path + '\
未找到 Python 文件'
    cr = total['comments'] / total['lines'] * 100 if total['lines'] > 0 else 0
    code_pct = total['code'] / total['lines'] * 100 if total['lines'] > 0 else 0
    out = [
        '目录: ' + path,
        '=' * 50,
        '文件数: ' + str(total['files']),
        '总行数: ' + str(total['lines']),
        '代码行: ' + str(total['code']) + ' (' + f'{code_pct:.1f}' + '%)',
        '注释行: ' + str(total['comments']) + ' (' + f'{cr:.1f}' + '%)',
        '空行数: ' + str(total['blank']),
        '函数数: ' + str(total['funcs']),
        '类数量: ' + str(total['classes']),
    ]
    if cr < 5:
        out.append('注释率偏低 (<5%)')
    elif cr < 15:
        out.append('注释率适中')
    else:
        out.append('注释率良好')
    return '\
'.join(out)

# ==================== analyze_imports ====================

def _extract_imports(file_path: str) -> Tuple[List[str], List[str]]:
    imps, froms = [], []
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
    except Exception:
        return imps, froms
    for m in re.finditer(r'^\s*import\s+([\w,\s.]+)', content, re.MULTILINE):
        imps.extend([x.strip() for x in m.group(1).split(',')])
    for m in re.finditer(r'^\s*from\s+([\w.]+)\s+import\s+([\w,\s]+)', content, re.MULTILINE):
        module = m.group(1)
        for item in [x.strip() for x in m.group(2).split(',')]:
            froms.append(module + '.' + item)
    return imps, froms

def analyze_imports(args: dict) -> str:
    path = args.get('path', '').strip()
    if not path:
        return '错误: 请提供 path 参数'
    if not os.path.exists(path):
        return f'路径不存在: {path}'
    all_imps, all_froms = {}, {}
    total_files = 0
    for root, dirs, files in os.walk(path):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith('.')]
        for f in files:
            if not f.endswith('.py'):
                continue
            total_files += 1
            imps, froms = _extract_imports(os.path.join(root, f))
            for imp in imps:
                all_imps[imp] = all_imps.get(imp, 0) + 1
            for imp in froms:
                all_froms[imp] = all_froms.get(imp, 0) + 1
    if total_files == 0:
        return '目录: ' + path + '\
未找到 Python 文件'
    out = [
        '目录: ' + path,
        'Python 文件: ' + str(total_files) + ' 个',
        '直接导入: ' + str(len(all_imps)) + ' 个唯一模块',
        'from导入: ' + str(len(all_froms)) + ' 个唯一项',
        '',
        '最常使用的模块:'
    ]
    combined = {**all_imps, **all_froms}
    for name, count in sorted(combined.items(), key=lambda x: x[1], reverse=True)[:10]:
        out.append('  ' + name + ': ' + str(count) + ' 次')
    return '\
'.join(out)

# ==================== find_unused ====================

def find_unused(args: dict) -> str:
    path = args.get('path', '').strip()
    if not path:
        return '错误: 请提供 path 参数'
    if not os.path.exists(path):
        return f'路径不存在: {path}'
    results = []
    for root, dirs, files in os.walk(path):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith('.')]
        for f in files:
            if not f.endswith('.py'):
                continue
            file_path = os.path.join(root, f)
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as fp:
                    content = fp.read()
            except Exception:
                continue
            imports = re.findall(r'^\s*import\s+([\w.]+)', content, re.MULTILINE)
            unused = []
            for imp in imports:
                base = imp.split('.')[0]
                used = False
                for line in content.split('\n'):
                    if ('import ' + imp) in line or ('from ' + imp) in line:
                        continue
                    if re.search(r'\b' + base + r'\b', line):
                        used = True
                        break
                if not used:
                    unused.append(imp)
            if unused:
                results.append({'file': os.path.relpath(file_path, path), 'unused': unused})
    if not results:
        return '目录: ' + path + '\
未发现明显未使用的导入'
    out = ['目录: ' + path, '发现 ' + str(len(results)) + ' 个文件可能有未使用的导入:', '']
    for r in results:
        out.append('  ' + r['file'])
        for imp in r['unused']:
            out.append('    import ' + imp)
    out.append('')
    out.append('提示: 基础检测，可能有误报')
    return '\
'.join(out)

# ==================== 注册 ====================

def register_tools() -> int:
    register(
        name='scan_todos',
        description='扫描项目中的 TODO/FIXME/XXX 注释，按标签分组展示',
        parameters={'type': 'object', 'properties': {'path': {'type': 'string', 'description': '项目目录路径'}}, 'required': ['path']},
        func=scan_todos
    )
    register(
        name='count_code',
        description='统计 Python 代码量：行数、注释率、函数数、类数等',
        parameters={'type': 'object', 'properties': {'path': {'type': 'string', 'description': '项目目录路径'}}, 'required': ['path']},
        func=count_code
    )
    register(
        name='analyze_imports',
        description='分析 Python 项目的导入依赖，列出最常使用的模块',
        parameters={'type': 'object', 'properties': {'path': {'type': 'string', 'description': '项目目录路径'}}, 'required': ['path']},
        func=analyze_imports
    )
    register(
        name='find_unused',
        description='基础检测：查找可能未使用的导入（可能有误报）',
        parameters={'type': 'object', 'properties': {'path': {'type': 'string', 'description': '项目目录路径'}}, 'required': ['path']},
        func=find_unused
    )
    return 4

if __name__ == '__main__':
    register_tools()
    print('scan_tools 已加载')
