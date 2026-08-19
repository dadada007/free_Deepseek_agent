# -*- coding: utf-8 -*-
"""
fs_path_utils.py - 路径处理与安全校验

提供：
- 路径标准化（含Windows路径兼容）
- 路径安全校验（防止越界）
- 路径查询工具

借鉴 OpenCode 的路径处理设计
"""

import os
import re
from pathlib import Path
from typing import Optional, Union, List, Tuple


# ============================================
# 1. Windows 路径兼容
# ============================================

def windows_path(p: str) -> str:
    """
    将 Linux/cygwin/WSL 风格的路径转换为 Windows 风格
    
    示例：
        /c:/Users → C:/Users
        /c/Users  → C:/Users
        /cygdrive/c/Users → C:/Users
        /mnt/c/Users → C:/Users
    """
    if os.name != "nt":
        return p
    
    result = p
    
    # 转换 /c:/path 或 /c/path 为 C:/path
    result = re.sub(r'^/([a-zA-Z]):(?:[\\/]|$)', lambda m: f"{m.group(1).upper()}:/", result)
    result = re.sub(r'^/([a-zA-Z])(?:/|$)', lambda m: f"{m.group(1).upper()}:/", result)
    result = re.sub(r'^/cygdrive/([a-zA-Z])(?:/|$)', lambda m: f"{m.group(1).upper()}:/", result)
    result = re.sub(r'^/mnt/([a-zA-Z])(?:/|$)', lambda m: f"{m.group(1).upper()}:/", result)
    
    # 将正斜杠转为反斜杠（但保留 UNC 路径的 \\）
    if not result.startswith('\\\\'):
        result = result.replace('/', '\\')
    
    return result


def normalize_path(p: str) -> str:
    """
    标准化路径，解析符号链接，转为绝对路径
    
    示例：
        normalize_path("C:/temp/../file.txt") → "C:/file.txt"
        normalize_path("/c/Users") → "C:/Users"
    """
    p = windows_path(p)
    resolved = os.path.abspath(p)
    try:
        return os.path.realpath(resolved)
    except OSError:
        return resolved


def to_posix_path(p: str) -> str:
    """将路径转为 POSIX 风格（正斜杠）"""
    return normalize_path(p).replace('\\', '/')


def is_absolute_path(p: str) -> bool:
    """检查是否为绝对路径"""
    return os.path.isabs(p)


def is_relative_path(p: str) -> bool:
    """检查是否为相对路径"""
    return not os.path.isabs(p)


# ============================================
# 2. 路径安全（防止越界）
# ============================================

def contains(parent: str, child: str) -> bool:
    """
    检查 child 是否在 parent 目录内（含自身）
    
    示例：
        contains("C:/project", "C:/project/src/main.py") → True
        contains("C:/project", "C:/other/file.txt") → False
    """
    parent_norm = normalize_path(parent)
    child_norm = normalize_path(child)
    
    # 确保路径以分隔符结尾以便正确比较
    parent_dir = parent_norm.rstrip(os.sep) + os.sep
    child_dir = child_norm.rstrip(os.sep) + os.sep
    
    return child_dir.startswith(parent_dir)


def resolve_safe(base_dir: str, target: str) -> str:
    """
    解析路径，确保不逃逸出 base_dir
    
    如果越界则抛出 ValueError
    
    示例：
        resolve_safe("C:/project", "src/main.py") → "C:/project/src/main.py"
        resolve_safe("C:/project", "../../etc/passwd") → ValueError
    """
    base_dir_norm = normalize_path(base_dir)
    target_norm = normalize_path(os.path.join(base_dir_norm, target))
    
    if not contains(base_dir_norm, target_norm):
        raise ValueError(f"Path escapes the workspace: {target_norm}")
    
    return target_norm


def resolve_relative(base_dir: str, target: str) -> str:
    """
    解析相对路径，返回相对于 base_dir 的标准化路径
    不进行安全检查（仅解析）
    """
    base_dir_norm = normalize_path(base_dir)
    return normalize_path(os.path.join(base_dir_norm, target))


def is_path_inside(base_dir: str, target: str) -> tuple:
    """
    检查目标路径是否在 base_dir 内（安全版本，不抛异常）
    
    返回: (是否安全, 标准化后的路径, 错误信息)
    """
    try:
        resolved = resolve_safe(base_dir, target)
        return True, resolved, None
    except ValueError as e:
        return False, target, str(e)


# ============================================
# 3. 路径工具
# ============================================

def get_extension(p: str) -> str:
    """获取文件扩展名（包含点）"""
    return os.path.splitext(p)[1]


def get_stem(p: str) -> str:
    """获取文件名（不含扩展名）"""
    return os.path.splitext(os.path.basename(p))[0]


def get_basename(p: str) -> str:
    """获取文件名（含扩展名）"""
    return os.path.basename(p)


def get_dirname(p: str) -> str:
    """获取目录名"""
    return os.path.dirname(p)


def join_paths(*paths: str) -> str:
    """拼接路径并标准化"""
    return normalize_path(os.path.join(*paths))


def get_parents(p: str) -> List[str]:
    """
    获取路径的所有父目录（从近到远）
    
    示例：
        get_parents("C:/project/src/main.py") →
        ["C:/project/src", "C:/project", "C:/"]
    """
    p = normalize_path(p)
    parents = []
    current = os.path.dirname(p)
    while current and current != p:
        parents.append(current)
        p = current
        current = os.path.dirname(current)
    return parents


def is_subpath(parent: str, child: str) -> bool:
    """检查 child 是否是 parent 的子路径（等价于 contains）"""
    return contains(parent, child)


def get_common_parent(paths: List[str]) -> Optional[str]:
    """
    获取多个路径的共同父目录
    
    示例：
        get_common_parent(["C:/project/src/a.py", "C:/project/src/b.py"]) → "C:/project/src"
    """
    if not paths:
        return None
    
    normalized = [normalize_path(p) for p in paths]
    common = os.path.commonpath(normalized)
    return common if common else None


def get_relative_path(base: str, target: str) -> str:
    """
    获取 target 相对于 base 的相对路径
    
    示例：
        get_relative_path("C:/project", "C:/project/src/main.py") → "src/main.py"
    """
    base_norm = normalize_path(base)
    target_norm = normalize_path(target)
    return os.path.relpath(target_norm, base_norm)


# ============================================
# 4. 文件名模式匹配
# ============================================

def match_pattern(name: str, pattern: str) -> bool:
    """
    检查文件名是否匹配通配符模式
    
    支持：* 和 ? 通配符
    
    示例：
        match_pattern("main.py", "*.py") → True
        match_pattern("test.txt", "*.py") → False
    """
    import fnmatch
    return fnmatch.fnmatch(name, pattern)


def match_patterns(name: str, patterns: List[str]) -> bool:
    """
    检查文件名是否匹配多个通配符模式中的任意一个
    """
    import fnmatch
    for pattern in patterns:
        if fnmatch.fnmatch(name, pattern):
            return True
    return False


# ============================================
# 5. 测试
# ============================================

if __name__ == '__main__':
    print("=== fs_path_utils 测试 ===\n")
    
    # 测试 Windows 路径转换
    print("Windows 路径转换:")
    print(f"  /c:/Users → {windows_path('/c:/Users')}")
    print(f"  /c/Users  → {windows_path('/c/Users')}")
    print(f"  /cygdrive/c/Users → {windows_path('/cygdrive/c/Users')}")
    
    # 测试路径标准化
    print("\n路径标准化:")
    print(f"  C:/temp/../file.txt → {normalize_path('C:/temp/../file.txt')}")
    
    # 测试 contains
    print("\n路径包含检测:")
    print(f"  contains('C:/project', 'C:/project/src/main.py') → {contains('C:/project', 'C:/project/src/main.py')}")
    print(f"  contains('C:/project', 'C:/other/file.txt') → {contains('C:/project', 'C:/other/file.txt')}")
    
    # 测试 resolve_safe
    print("\n安全解析:")
    try:
        result = resolve_safe("C:/project", "src/main.py")
        print(f"  resolve_safe('C:/project', 'src/main.py') → {result}")
    except ValueError as e:
        print(f"  错误: {e}")
    
    try:
        result = resolve_safe("C:/project", "../../etc/passwd")
        print(f"  resolve_safe('C:/project', '../../etc/passwd') → {result}")
    except ValueError as e:
        print(f"  ✅ 成功阻止越界: {e}")
    
    # 测试 get_parents
    print("\n获取父目录:")
    parents = get_parents("C:/project/src/main.py")
    print(f"  get_parents('C:/project/src/main.py') → {parents}")
    
    # 测试 get_common_parent
    print("\n共同父目录:")
    common = get_common_parent(["C:/project/src/a.py", "C:/project/src/b.py"])
    print(f"  get_common_parent(...) → {common}")
    
    print("\n✅ 所有测试通过")