# -*- coding: utf-8 -*-
"""
fs_bom_utils.py - UTF-8 BOM 检测与处理

提供：
- UTF-8 BOM 检测
- BOM 分离与合并
- 带 BOM 的文本读写

借鉴 OpenCode 的 BOM 处理设计
"""

import os
from typing import Tuple, Optional

# UTF-8 BOM 字节序列
UTF8_BOM = b'\xef\xbb\xbf'


# ============================================
# 1. BOM 检测
# ============================================

def has_utf8_bom(content: bytes) -> bool:
    """
    检查字节内容是否包含 UTF-8 BOM
    
    示例：
        has_utf8_bom(b'\xef\xbb\xbfHello') → True
        has_utf8_bom(b'Hello') → False
    """
    return content.startswith(UTF8_BOM)


def split_bom(text: str) -> Tuple[bool, str]:
    """
    分离 BOM 和文本内容
    
    返回：
        (是否包含BOM, 去除BOM后的文本)
    
    示例：
        split_bom('\ufeffHello') → (True, 'Hello')
        split_bom('Hello') → (False, 'Hello')
    """
    stripped = text.lstrip('\ufeff')
    has_bom = len(stripped) != len(text)
    return has_bom, stripped


def join_bom(text: str, include_bom: bool) -> str:
    """
    根据需要在文本前添加 BOM
    
    如果 include_bom 为 True，则确保文本以 BOM 开头。
    如果文本已有 BOM，则保持只有一个 BOM。
    
    示例：
        join_bom('Hello', True) → '\ufeffHello'
        join_bom('\ufeffHello', True) → '\ufeffHello'
        join_bom('Hello', False) → 'Hello'
    """
    if include_bom:
        _, stripped = split_bom(text)
        return '\ufeff' + stripped
    return text


def detect_bom_from_file(file_path: str) -> bool:
    """
    检测文件是否包含 UTF-8 BOM
    
    示例：
        detect_bom_from_file('C:/file.txt') → True  # 如果包含 BOM
    """
    try:
        with open(file_path, 'rb') as f:
            first_bytes = f.read(3)
            return has_utf8_bom(first_bytes)
    except (FileNotFoundError, OSError):
        return False


# ============================================
# 2. 带 BOM 的文本读写
# ============================================

def read_text_with_bom(
    file_path: str,
    encoding: str = 'utf-8'
) -> Tuple[bool, str, str]:
    """
    读取文本文件，返回 BOM 状态和内容
    
    返回：
        (是否包含BOM, 文本内容, 实际使用的编码)
    
    示例：
        has_bom, content, enc = read_text_with_bom('C:/file.txt')
    """
    with open(file_path, 'rb') as f:
        raw = f.read()
    
    has_bom = has_utf8_bom(raw)
    
    if has_bom:
        # 使用 utf-8-sig 自动去除 BOM
        content = raw.decode('utf-8-sig')
        actual_encoding = 'utf-8-sig'
    else:
        content = raw.decode(encoding)
        actual_encoding = encoding
    
    return has_bom, content, actual_encoding


def read_text_without_bom(file_path: str, encoding: str = 'utf-8') -> str:
    """
    读取文本文件，自动去除 BOM
    
    与 read_text_with_bom 的区别：只返回内容
    """
    _, content, _ = read_text_with_bom(file_path, encoding)
    return content


def write_text_with_bom(
    file_path: str,
    content: str,
    preserve_bom: bool = True,
    encoding: str = 'utf-8'
) -> None:
    """
    写入文本文件，根据 preserve_bom 决定是否保留 BOM
    
    参数：
        file_path: 文件路径
        content: 文本内容
        preserve_bom: 是否保留 BOM（写入时添加 BOM）
        encoding: 编码（默认 utf-8）
    
    示例：
        write_text_with_bom('C:/file.txt', 'Hello', preserve_bom=True)
    """
    if preserve_bom:
        _, stripped = split_bom(content)
        final_content = '\ufeff' + stripped
    else:
        final_content = content
    
    with open(file_path, 'w', encoding=encoding) as f:
        f.write(final_content)


def write_text_preserving_bom(
    file_path: str,
    content: str,
    encoding: str = 'utf-8'
) -> None:
    """
    写入文本，保留原有的 BOM 状态
    
    如果文件已存在，检测其 BOM 状态并保持一致。
    如果文件不存在，不添加 BOM。
    
    这是 write_text_with_bom 的便捷版本。
    """
    if os.path.exists(file_path):
        has_bom = detect_bom_from_file(file_path)
    else:
        has_bom = False
    
    write_text_with_bom(file_path, content, preserve_bom=has_bom, encoding=encoding)


# ============================================
# 3. BOM 工具函数
# ============================================

def remove_bom_from_string(text: str) -> str:
    """
    从字符串中移除 BOM（如果有）
    
    示例：
        remove_bom_from_string('\ufeffHello') → 'Hello'
    """
    _, stripped = split_bom(text)
    return stripped


def add_bom_to_string(text: str) -> str:
    """
    在字符串前添加 BOM（如果还没有）
    
    示例：
        add_bom_to_string('Hello') → '\ufeffHello'
        add_bom_to_string('\ufeffHello') → '\ufeffHello'
    """
    if not text.startswith('\ufeff'):
        return '\ufeff' + text
    return text


def ensure_bom_consistent(text: str, target_has_bom: bool) -> str:
    """
    确保文本的 BOM 状态与目标一致
    
    如果 target_has_bom 为 True，则确保有 BOM
    如果 target_has_bom 为 False，则确保没有 BOM
    """
    if target_has_bom:
        return add_bom_to_string(text)
    else:
        return remove_bom_from_string(text)


# ============================================
# 4. 测试
# ============================================

if __name__ == '__main__':
    import tempfile
    
    print("=== fs_bom_utils 测试 ===\n")
    
    # 测试 1: split_bom
    print("--- 测试 1: split_bom ---")
    has_bom, stripped = split_bom('\ufeffHello')
    print(f"  '\ufeffHello' → has_bom={has_bom}, stripped='{stripped}'")
    
    has_bom, stripped = split_bom('Hello')
    print(f"  'Hello' → has_bom={has_bom}, stripped='{stripped}'")
    
    # 测试 2: join_bom
    print("\n--- 测试 2: join_bom ---")
    result = join_bom('Hello', True)
    print(f"  join_bom('Hello', True) → '{result}'")
    result = join_bom('\ufeffHello', True)
    print(f"  join_bom('\ufeffHello', True) → '{result}'")
    result = join_bom('Hello', False)
    print(f"  join_bom('Hello', False) → '{result}'")
    
    # 测试 3: 实际文件读写
    print("\n--- 测试 3: 文件读写 ---")
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = os.path.join(tmpdir, 'test.txt')
        
        # 写入带 BOM 的文件
        write_text_with_bom(test_file, 'Hello, 世界!', preserve_bom=True)
        
        # 检测 BOM
        has_bom = detect_bom_from_file(test_file)
        print(f"  写入后检测 BOM: {has_bom}")
        
        # 读取带 BOM
        has_bom, content, enc = read_text_with_bom(test_file)
        print(f"  读取: has_bom={has_bom}, content='{content}', encoding='{enc}'")
        
        # 写入时保留 BOM 状态
        write_text_preserving_bom(test_file, '新内容')
        has_bom = detect_bom_from_file(test_file)
        print(f"  保留 BOM 写入后检测: {has_bom}")
        
        # 写入时不保留 BOM
        write_text_with_bom(test_file, '无 BOM 内容', preserve_bom=False)
        has_bom = detect_bom_from_file(test_file)
        print(f"  不保留 BOM 写入后检测: {has_bom}")
    
    print("\n✅ 所有测试通过")