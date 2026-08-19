# -*- coding: utf-8 -*-
"""
项目健康检查工具
功能：分析项目目录，检查代码质量、文件完整性、依赖状态等
"""

import os
import re
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple

# 从全局 tools 注册表导入注册函数
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tools import register


def _count_lines(file_path: str) -> Tuple[int, int, int]:
    """统计文件行数：总行数、代码行数、注释行数"""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
    except Exception:
        return 0, 0, 0

    total = len(lines)
    code = 0
    comments = 0
    in_block_comment = False

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        # 处理多行注释（Python 风格）
        if stripped.startswith('"""') or stripped.startswith("'''"):
            if stripped.count('"""') >= 2 or stripped.count("'''") >= 2:
                comments += 1
                continue
            in_block_comment = not in_block_comment
            comments += 1
            continue
        if in_block_comment:
            comments += 1
            continue
        if stripped.startswith('#'):
            comments += 1
            continue
        code += 1
    return total, code, comments


def _check_requirements(dir_path: str) -> Dict:
    """检查 requirements.txt"""
    req_path = os.path.join(dir_path, 'requirements.txt')
    result = {
        'exists': False,
        'count': 0,
        'issues': [],
        'packages': []
    }

    if not os.path.exists(req_path):
        result['issues'].append('缺少 requirements.txt 文件')
        return result

    result['exists'] = True
    try:
        with open(req_path, 'r', encoding='utf-8') as f:
            lines = [l.strip() for l in f.readlines() if l.strip() and not l.startswith('#')]
        result['count'] = len(lines)
        result['packages'] = lines

        # 检查常见问题
        for pkg in lines:
            if pkg.startswith('PyQt6') or pkg.startswith('PyQt5'):
                result['issues'].append('⚠️ 检测到 PyQt 依赖，打包时需要特别处理')
                break
        if len(lines) == 0:
            result['issues'].append('requirements.txt 为空')
    except Exception as e:
        result['issues'].append(f'读取 requirements.txt 失败: {e}')

    return result


def _check_gitignore(dir_path: str) -> Dict:
    """检查 .gitignore"""
    git_path = os.path.join(dir_path, '.gitignore')
    result = {
        'exists': False,
        'issues': []
    }
    if os.path.exists(git_path):
        result['exists'] = True
        try:
            with open(git_path, 'r', encoding='utf-8') as f:
                content = f.read()
            essentials = ['__pycache__', '*.pyc', '.env', 'venv', 'dist', 'build']
            missing = [e for e in essentials if e not in content]
            if missing:
                result['issues'].append(f'建议添加: {", ".join(missing)}')
        except Exception:
            pass
    else:
        result['issues'].append('缺少 .gitignore 文件')
    return result


def _scan_project(dir_path: str, max_depth: int = 3) -> Dict:
    """扫描项目目录结构"""
    result = {
        'total_files': 0,
        'total_dirs': 0,
        'code_files': [],
        'large_files': [],
        'empty_dirs': [],
        'extensions': {},
        'size': 0
    }

    root = Path(dir_path)
    if not root.exists():
        return result

    # 要跳过的目录
    skip_dirs = {'.git', '__pycache__', '.idea', '.vscode', 'node_modules', 'venv', 'env', '.hermes_backup'}
    # 要统计的代码扩展名
    code_exts = {'.py', '.js', '.ts', '.jsx', '.tsx', '.go', '.rs', '.c', '.cpp', '.h', '.hpp', '.java', '.kt', '.swift'}

    for root_dir, dirs, files in os.walk(dir_path):
        # 跳过隐藏/系统目录
        dirs[:] = [d for d in dirs if d not in skip_dirs and not d.startswith('.')]

        rel_path = os.path.relpath(root_dir, dir_path)
        if rel_path == '.':
            rel_path = ''

        depth = rel_path.count(os.sep) if rel_path else 0
        if depth > max_depth:
            continue

        result['total_dirs'] += 1

        for f in files:
            if f.startswith('.'):
                continue
            file_path = os.path.join(root_dir, f)
            try:
                size = os.path.getsize(file_path)
                result['size'] += size
            except Exception:
                size = 0

            result['total_files'] += 1

            ext = os.path.splitext(f)[1].lower()
            result['extensions'][ext] = result['extensions'].get(ext, 0) + 1

            if ext in code_exts:
                total, code, comments = _count_lines(file_path)
                result['code_files'].append({
                    'path': os.path.relpath(file_path, dir_path),
                    'size': size,
                    'lines': total,
                    'code_lines': code,
                    'comment_lines': comments
                })

            if size > 1024 * 1024:  # >1MB
                result['large_files'].append({
                    'path': os.path.relpath(file_path, dir_path),
                    'size_mb': round(size / 1024 / 1024, 2)
                })

        # 检查空目录
        if not files and not dirs:
            result['empty_dirs'].append(rel_path or '.')

    return result


def _generate_report(dir_path: str, options: Dict = None) -> str:
    """生成健康报告"""
    if options is None:
        options = {}

    max_depth = options.get('max_depth', 3)

    # 基础检查
    dir_exists = os.path.exists(dir_path)
    if not dir_exists:
        return f"❌ 目录不存在: {dir_path}"

    is_dir = os.path.isdir(dir_path)
    if not is_dir:
        return f"❌ 路径不是目录: {dir_path}"

    # 收集数据
    req_check = _check_requirements(dir_path)
    git_check = _check_gitignore(dir_path)
    scan_result = _scan_project(dir_path, max_depth)

    # 计算代码统计
    total_lines = sum(f['lines'] for f in scan_result['code_files'])
    total_code = sum(f['code_lines'] for f in scan_result['code_files'])
    total_comments = sum(f['comment_lines'] for f in scan_result['code_files'])

    # 生成报告
    lines = [
        "=" * 60,
        f"📊 项目健康检查报告",
        f"📁 项目: {dir_path}",
        f"🕐 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "=" * 60,
        "",
        "## 📈 概览",
        f"  • 总文件数: {scan_result['total_files']}",
        f"  • 总目录数: {scan_result['total_dirs']}",
        f"  • 总大小: {scan_result['size'] / 1024 / 1024:.2f} MB",
        f"  • 代码文件数: {len(scan_result['code_files'])}",
        f"  • 总行数: {total_lines:,}",
        f"  • 代码行数: {total_code:,}",
        f"  • 注释行数: {total_comments:,}",
        f"  • 注释率: {total_comments / total_lines * 100:.1f}%" if total_lines > 0 else "  • 注释率: N/A",
        "",
        "## 📦 依赖检查",
        f"  • requirements.txt: {'✅ 存在' if req_check['exists'] else '❌ 不存在'}",
        f"  • 依赖包数量: {req_check['count']}",
    ]

    if req_check['issues']:
        lines.append("  • 问题:")
        for issue in req_check['issues']:
            lines.append(f"      - {issue}")

    lines.extend([
        "",
        "## 🔧 Git 配置",
        f"  • .gitignore: {'✅ 存在' if git_check['exists'] else '❌ 不存在'}",
    ])
    if git_check['issues']:
        for issue in git_check['issues']:
            lines.append(f"      - {issue}")

    lines.append("")
    lines.append("## 📁 文件类型分布")
    if scan_result['extensions']:
        sorted_ext = sorted(scan_result['extensions'].items(), key=lambda x: x[1], reverse=True)
        for ext, count in sorted_ext[:10]:
            ext_display = ext or '无扩展名'
            lines.append(f"  • {ext_display}: {count} 个")
    else:
        lines.append("  • 无文件")

    if scan_result['large_files']:
        lines.append("")
        lines.append("## ⚠️ 大文件 (>1MB)")
        for f in scan_result['large_files']:
            lines.append(f"  • {f['path']} ({f['size_mb']} MB)")

    if scan_result['empty_dirs']:
        empty_display = [d for d in scan_result['empty_dirs'] if d != '.']
        if empty_display:
            lines.append("")
            lines.append("## 📂 空目录")
            for d in empty_display[:10]:
                lines.append(f"  • {d}")
            if len(empty_display) > 10:
                lines.append(f"  • ... 还有 {len(empty_display) - 10} 个")

    # 健康评分
    score = 100
    issues_list = []

    if not req_check['exists']:
        score -= 15
        issues_list.append('缺少 requirements.txt')
    if not git_check['exists']:
        score -= 10
        issues_list.append('缺少 .gitignore')
    if scan_result['total_files'] == 0:
        score -= 20
        issues_list.append('项目目录为空')
    if req_check['issues']:
        score -= 5 * len(req_check['issues'])
        issues_list.extend(req_check['issues'])
    if scan_result['large_files']:
        score -= 2 * min(len(scan_result['large_files']), 5)
        issues_list.append(f'有 {len(scan_result["large_files"])} 个大文件')
    if total_lines > 0 and total_comments / total_lines < 0.05:
        score -= 10
        issues_list.append('注释率过低 (<5%)')

    score = max(0, min(100, score))

    lines.append("")
    lines.append("=" * 60)
    lines.append(f"🏥 健康评分: {score}/100")

    if score >= 80:
        lines.append("✅ 项目状态良好！")
    elif score >= 50:
        lines.append("⚠️ 项目状态一般，建议优化上述问题")
    else:
        lines.append("❌ 项目需要关注，存在多个问题")

    if issues_list:
        lines.append("")
        lines.append("📋 发现的问题:")
        for issue in set(issues_list):
            lines.append(f"  • {issue}")

    lines.append("=" * 60)

    return "\\n".join(lines)


# ==================== 工具注册 ====================

def health_check(args: dict) -> str:
    """
    执行项目健康检查。
    参数:
        path: 要检查的项目目录路径
        max_depth: 扫描深度（可选，默认3）
    """
    path = args.get('path', '').strip()
    if not path:
        return "❌ 错误: 请提供 path 参数"

    max_depth = args.get('max_depth', 3)
    if not isinstance(max_depth, int):
        try:
            max_depth = int(max_depth)
        except (ValueError, TypeError):
            max_depth = 3
    max_depth = max(1, min(10, max_depth))

    return _generate_report(path, {'max_depth': max_depth})


def register_tools() -> int:
    """注册所有工具，供热加载器调用"""
    register(
        name="health_check",
        description="对项目目录进行健康检查，分析代码质量、文件完整性、依赖状态等，生成详细报告。可用于代码审查和项目审计。",
        parameters={
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "要检查的项目目录路径"
                },
                "max_depth": {
                    "type": "integer",
                    "description": "扫描子目录的最大深度（默认 3，范围 1-10）",
                    "default": 3
                }
            },
            "required": ["path"]
        },
        func=health_check
    )
    return 1


# 如果直接运行，测试注册
if __name__ == "__main__":
    register_tools()
    print("✅ health_tools 已加载")
    print("测试: health_check(path='D:/9/hermes')")
    print(health_check({"path": "D:/9/hermes"}))
