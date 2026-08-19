# -*- coding: utf-8 -*-
"""
fs_io_core.py - 文件系统核心 I/O

提供：
- 文件读写（字符串/字节）
- 目录操作（创建/删除/遍历）
- 文件查询（glob/grep/find_up）
- 文件信息（stat）

借鉴 OpenCode 的 FSUtil 设计
"""

import os
import re
import json
import hashlib
import tempfile
import shutil
from pathlib import Path
from typing import Optional, Union, List, Dict, Any, Tuple

from .fs_path_utils import normalize_path, contains, resolve_safe, to_posix_path
from .fs_bom_utils import read_text_with_bom, write_text_with_bom, split_bom, detect_bom_from_file


# ============================================
# 异常类
# ============================================

class FSError(Exception):
    """文件系统操作错误"""
    pass


# ============================================
# FSUtil - 核心文件操作类
# ============================================

class FSUtil:
    """
    文件系统工具类
    借鉴 OpenCode 的 FSUtil 设计
    """
    
    # ======== 存在性检查 ========
    
    @staticmethod
    def exists(path: str) -> bool:
        """检查路径是否存在"""
        return os.path.exists(path)
    
    @staticmethod
    def is_file(path: str) -> bool:
        """检查是否为文件"""
        return os.path.isfile(path)
    
    @staticmethod
    def is_dir(path: str) -> bool:
        """检查是否为目录"""
        return os.path.isdir(path)
    
    @staticmethod
    def is_symlink(path: str) -> bool:
        """检查是否为符号链接"""
        return os.path.islink(path)
    
    @staticmethod
    def is_absolute(path: str) -> bool:
        """检查是否为绝对路径"""
        return os.path.isabs(path)
    
    # ======== 目录操作 ========
    
    @staticmethod
    def ensure_dir(path: str) -> None:
        """确保目录存在，自动创建父目录"""
        if not path:
            return
        os.makedirs(path, exist_ok=True)
    
    @staticmethod
    def mkdir(path: str, mode: int = 0o755) -> None:
        """创建目录（父目录必须存在）"""
        os.mkdir(path, mode)
    
    @staticmethod
    def mkdirs(path: str, mode: int = 0o755) -> None:
        """创建目录（自动创建父目录）"""
        os.makedirs(path, mode, exist_ok=True)
    
    @staticmethod
    def rmdir(path: str) -> None:
        """删除空目录"""
        os.rmdir(path)
    
    @staticmethod
    def rmtree(path: str) -> None:
        """递归删除目录"""
        shutil.rmtree(path)
    
    @staticmethod
    def list_dir(path: str) -> List[str]:
        """列出目录内容（仅名称）"""
        return os.listdir(path)
    
    @staticmethod
    def list_dir_with_info(path: str) -> List[Dict[str, Any]]:
        """
        列出目录内容（带详细信息）
        
        返回每个条目的：
            - name: 名称
            - path: 完整路径
            - type: file/directory/symlink/other
            - size: 大小（字节）
            - mtime: 修改时间
        """
        if not os.path.isdir(path):
            raise FSError(f"Not a directory: {path}")
        
        entries = []
        for name in os.listdir(path):
            full_path = os.path.join(path, name)
            
            if os.path.isdir(full_path):
                entry_type = 'directory'
            elif os.path.islink(full_path):
                entry_type = 'symlink'
            elif os.path.isfile(full_path):
                entry_type = 'file'
            else:
                entry_type = 'other'
            
            try:
                stat = os.stat(full_path)
                size = stat.st_size
                mtime = stat.st_mtime
            except OSError:
                size = 0
                mtime = 0
            
            entries.append({
                'name': name,
                'path': full_path,
                'type': entry_type,
                'size': size,
                'mtime': mtime,
            })
        
        # 排序：目录优先，然后按名称
        entries.sort(key=lambda e: (0 if e['type'] == 'directory' else 1, e['name']))
        return entries
    
    # ======== 文件读取 ========
    
    @staticmethod
    def read_file_bytes(path: str) -> bytes:
        """读取文件为字节"""
        try:
            with open(path, 'rb') as f:
                return f.read()
        except FileNotFoundError:
            raise FSError(f"File not found: {path}")
        except PermissionError:
            raise FSError(f"Permission denied: {path}")
        except Exception as e:
            raise FSError(f"Failed to read file {path}: {e}")
    
    @staticmethod
    def read_file_string(path: str, encoding: str = 'utf-8') -> str:
        """
        读取文件为字符串，自动处理 BOM
        """
        _, content, _ = read_text_with_bom(path, encoding)
        return content
    
    @staticmethod
    def read_file_string_safe(path: str, encoding: str = 'utf-8') -> Optional[str]:
        """安全读取，文件不存在返回 None"""
        try:
            return FSUtil.read_file_string(path, encoding)
        except (FSError, FileNotFoundError):
            return None
    
    @staticmethod
    def read_json(path: str) -> Dict[str, Any]:
        """读取 JSON 文件"""
        content = FSUtil.read_file_string(path)
        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            raise FSError(f"Invalid JSON in {path}: {e}")
    
    # ======== 文件写入 ========
    
    @staticmethod
    def write_file_bytes(path: str, content: bytes, mode: Optional[int] = None) -> None:
        """写入字节文件"""
        try:
            with open(path, 'wb') as f:
                f.write(content)
            if mode is not None:
                os.chmod(path, mode)
        except Exception as e:
            raise FSError(f"Failed to write file {path}: {e}")
    
    @staticmethod
    def write_file_string(
        path: str,
        content: str,
        encoding: str = 'utf-8',
        preserve_bom: bool = False,
        mode: Optional[int] = None
    ) -> None:
        """写入字符串文件，支持 BOM"""
        try:
            write_text_with_bom(path, content, preserve_bom=preserve_bom, encoding=encoding)
            if mode is not None:
                os.chmod(path, mode)
        except Exception as e:
            raise FSError(f"Failed to write file {path}: {e}")
    
    @staticmethod
    def write_with_dirs(
        path: str,
        content: Union[str, bytes],
        encoding: str = 'utf-8',
        preserve_bom: bool = False,
        mode: Optional[int] = None
    ) -> None:
        """
        写入文件，自动创建父目录
        借鉴 OpenCode 的 writeWithDirs
        """
        parent = os.path.dirname(path)
        if parent:
            FSUtil.ensure_dir(parent)
        
        if isinstance(content, bytes):
            FSUtil.write_file_bytes(path, content, mode)
        else:
            FSUtil.write_file_string(path, content, encoding, preserve_bom, mode)
    
    @staticmethod
    def write_text_preserving_bom(path: str, content: str, encoding: str = 'utf-8') -> None:
        """
        写入文本，保留原有的 BOM 状态
        借鉴 OpenCode 的 writeTextPreservingBom
        """
        if os.path.exists(path):
            has_bom = detect_bom_from_file(path)
        else:
            has_bom = False
        
        FSUtil.write_with_dirs(path, content, encoding, preserve_bom=has_bom)
    
    # ======== 条件写入 ========
    
    @staticmethod
    def write_if_unchanged(
        path: str,
        content: Union[str, bytes],
        expected_content: Union[str, bytes],
        encoding: str = 'utf-8',
        preserve_bom: bool = False
    ) -> bool:
        """
        条件写入：只有当当前内容与 expected_content 一致时才写入
        
        返回：
            True 表示写入成功
            False 表示内容已变化，未写入
        
        借鉴 OpenCode 的 writeIfUnchanged
        """
        if not os.path.exists(path):
            raise FSError(f"File does not exist: {path}")
        
        if isinstance(expected_content, bytes):
            current = FSUtil.read_file_bytes(path)
            if current != expected_content:
                return False
            FSUtil.write_with_dirs(path, content)
            return True
        else:
            current = FSUtil.read_file_string(path, encoding)
            # 比较时忽略 BOM 差异
            _, stripped_current = split_bom(current)
            _, stripped_expected = split_bom(expected_content)
            
            if stripped_current != stripped_expected:
                return False
            
            # 写入时保留原有的 BOM 状态
            FSUtil.write_file_string(path, content, encoding, preserve_bom=preserve_bom)
            return True
    
    # ======== 文件删除 ========
    
    @staticmethod
    def remove(path: str) -> bool:
        """
        删除文件或空目录
        
        返回：
            True 表示存在并删除
            False 表示不存在
        """
        if not os.path.exists(path):
            return False
        
        try:
            if os.path.isdir(path):
                os.rmdir(path)
            else:
                os.remove(path)
            return True
        except OSError as e:
            raise FSError(f"Failed to remove {path}: {e}")
    
    @staticmethod
    def remove_recursive(path: str) -> bool:
        """递归删除目录或文件"""
        if not os.path.exists(path):
            return False
        
        try:
            if os.path.isdir(path):
                shutil.rmtree(path)
            else:
                os.remove(path)
            return True
        except Exception as e:
            raise FSError(f"Failed to remove {path}: {e}")
    
    # ======== 文件信息 ========
    
    @staticmethod
    def stat(path: str) -> Dict[str, Any]:
        """获取文件信息"""
        try:
            st = os.stat(path)
            return {
                'size': st.st_size,
                'mtime': st.st_mtime,
                'ctime': st.st_ctime,
                'atime': st.st_atime,
                'mode': st.st_mode,
                'is_file': os.path.isfile(path),
                'is_dir': os.path.isdir(path),
                'is_symlink': os.path.islink(path),
            }
        except FileNotFoundError:
            raise FSError(f"File not found: {path}")
    
    @staticmethod
    def file_size(path: str) -> int:
        """获取文件大小（字节）"""
        stat = FSUtil.stat(path)
        return stat['size']
    
    @staticmethod
    def file_hash(path: str, algorithm: str = 'sha256') -> str:
        """计算文件哈希"""
        hasher = hashlib.new(algorithm)
        with open(path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                hasher.update(chunk)
        return hasher.hexdigest()
    
    # ======== 文件搜索 ========
    
    @staticmethod
    def glob(pattern: str, root: str = '.', recursive: bool = True) -> List[str]:
        """
        通配符搜索
        返回匹配文件相对于 root 的路径列表
        """
        import glob as glob_module
        root = normalize_path(root)
        search_pattern = os.path.join(root, '**' if recursive else '', pattern)
        matches = glob_module.glob(search_pattern, recursive=recursive)
        return [os.path.relpath(m, root) for m in matches]
    
    @staticmethod
    def grep(
        pattern: str,
        root: str,
        file_pattern: Optional[str] = None,
        max_results: int = 100,
        ignore_case: bool = True
    ) -> List[Dict[str, Any]]:
        """
        跨文件搜索内容（正则）
        
        返回：
            [
                {'file': 'src/main.py', 'line': 10, 'content': '...'},
                ...
            ]
        """
        results = []
        root = normalize_path(root)
        
        # 确定要搜索的文件
        if file_pattern:
            files = FSUtil.glob(file_pattern, root, recursive=True)
        else:
            # 默认搜索所有非二进制文件
            files = FSUtil.glob('**/*', root, recursive=True)
            files = [f for f in files if os.path.isfile(os.path.join(root, f))]
        
        flags = re.IGNORECASE if ignore_case else 0
        compiled = re.compile(pattern, flags)
        
        for rel_path in files:
            if len(results) >= max_results:
                break
            
            full_path = os.path.join(root, rel_path)
            if not os.path.isfile(full_path):
                continue
            
            try:
                content = FSUtil.read_file_string_safe(full_path)
                if content is None:
                    continue
                
                lines = content.splitlines()
                for i, line in enumerate(lines):
                    if compiled.search(line):
                        results.append({
                            'file': rel_path,
                            'line': i + 1,
                            'content': line.strip(),
                        })
                        if len(results) >= max_results:
                            break
            except (FSError, UnicodeDecodeError):
                continue
        
        return results
    
    @staticmethod
    def find_up(target: str, start: str, stop: Optional[str] = None) -> List[str]:
        """
        向上查找文件
        
        从 start 目录开始向上查找，找到所有匹配 target 的路径。
        
        示例：
            find_up('package.json', '/project/src', '/project')
        """
        results = []
        current = normalize_path(start)
        stop_path = normalize_path(stop) if stop else None
        
        while True:
            search_path = os.path.join(current, target)
            if os.path.exists(search_path):
                results.append(search_path)
            
            if stop_path and current == stop_path:
                break
            
            parent = os.path.dirname(current)
            if parent == current:
                break
            current = parent
        
        return results
    
    # ======== 文件复制/移动 ========
    
    @staticmethod
    def copy(src: str, dst: str, overwrite: bool = True) -> None:
        """复制文件或目录"""
        if not overwrite and os.path.exists(dst):
            raise FSError(f"Destination already exists: {dst}")
        
        src = normalize_path(src)
        dst = normalize_path(dst)
        
        try:
            if os.path.isdir(src):
                shutil.copytree(src, dst, dirs_exist_ok=overwrite)
            else:
                FSUtil.ensure_dir(os.path.dirname(dst))
                shutil.copy2(src, dst)
        except Exception as e:
            raise FSError(f"Failed to copy {src} to {dst}: {e}")
    
    @staticmethod
    def move(src: str, dst: str, overwrite: bool = True) -> None:
        """移动文件或目录"""
        if not overwrite and os.path.exists(dst):
            raise FSError(f"Destination already exists: {dst}")
        
        src = normalize_path(src)
        dst = normalize_path(dst)
        
        try:
            FSUtil.ensure_dir(os.path.dirname(dst))
            shutil.move(src, dst)
        except Exception as e:
            raise FSError(f"Failed to move {src} to {dst}: {e}")


# ============================================
# 便捷函数
# ============================================

def read_file_safe(path: str) -> Optional[str]:
    """安全读取文件内容（自动处理 BOM）"""
    return FSUtil.read_file_string_safe(path)


def write_file_safe(path: str, content: str, preserve_bom: bool = True) -> bool:
    """安全写入文件（自动创建目录）"""
    try:
        FSUtil.write_with_dirs(path, content, preserve_bom=preserve_bom)
        return True
    except Exception:
        return False


# ============================================
# 测试
# ============================================

if __name__ == '__main__':
    import tempfile
    
    print("=== fs_io_core 测试 ===\n")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        print(f"测试目录: {tmpdir}")
        
        # 测试 1: 写入文件
        test_file = os.path.join(tmpdir, 'sub', 'test.txt')
        FSUtil.write_with_dirs(test_file, 'Hello, 世界!')
        print(f"✅ 写入: {test_file}")
        
        # 测试 2: 读取文件
        content = FSUtil.read_file_string(test_file)
        print(f"✅ 读取: {content}")
        
        # 测试 3: 文件信息
        stat = FSUtil.stat(test_file)
        print(f"✅ 文件信息: size={stat['size']} bytes")
        
        # 测试 4: glob 搜索
        files = FSUtil.glob('*.txt', root=tmpdir, recursive=True)
        print(f"✅ glob 搜索: {files}")
        
        # 测试 5: grep 搜索
        results = FSUtil.grep('世界', root=tmpdir)
        print(f"✅ grep 搜索: {len(results)} 条结果")
        
        # 测试 6: 删除
        FSUtil.remove(test_file)
        print(f"✅ 删除: {test_file}")
        
        # 测试 7: 复制
        src_file = os.path.join(tmpdir, 'src.txt')
        dst_file = os.path.join(tmpdir, 'dst.txt')
        FSUtil.write_with_dirs(src_file, '复制测试')
        FSUtil.copy(src_file, dst_file)
        copied = FSUtil.read_file_string(dst_file)
        print(f"✅ 复制: {copied}")
    
    print("\n✅ 所有测试通过")