# -*- coding: utf-8 -*-
"""文件变更层 - 极简版（不做任何转义处理）"""

import os
import tempfile
import shutil
import logging

logger = logging.getLogger(__name__)


class FileMutation:
    """文件变更操作 - 极简版，只做原子写入，不做转义"""

    @staticmethod
    def _atomic_write(path: str, content: str, encoding: str = 'utf-8') -> dict:
        """原子写入：先写临时文件，再替换；失败时回退到直接写入"""
        existed = os.path.exists(path)
        tmp_path = None
        
        try:
            dirname = os.path.dirname(path) or '.'
            os.makedirs(dirname, exist_ok=True)
            
            with tempfile.NamedTemporaryFile(
                dir=dirname,
                prefix='.tmp_',
                suffix='.tmp',
                delete=False,
                mode='w',
                encoding=encoding
            ) as tmp:
                tmp_path = tmp.name
                tmp.write(content)
                tmp.flush()
                os.fsync(tmp.fileno())
            
            try:
                os.replace(tmp_path, path)
            except Exception as replace_error:
                # 原子替换失败，回退到直接覆盖写入
                logger.warning(f"原子替换失败 ({replace_error})，回退到直接写入")
                try:
                    with open(path, 'w', encoding=encoding) as f:
                        f.write(content)
                    # 删除临时文件
                    if tmp_path and os.path.exists(tmp_path):
                        os.unlink(tmp_path)
                    return {
                        'success': True,
                        'path': path,
                        'existed': existed,
                        'size': len(content),
                        'fallback': True,
                    }
                except Exception as direct_error:
                    return {
                        'success': False,
                        'path': path,
                        'error': f'原子替换失败: {replace_error}, 直接写入也失败: {direct_error}',
                    }
            
            return {
                'success': True,
                'path': path,
                'existed': existed,
                'size': len(content),
            }
            
        except Exception as e:
            if tmp_path and os.path.exists(tmp_path):
                try:
                    os.unlink(tmp_path)
                except OSError:
                    pass
            return {
                'success': False,
                'path': path,
                'error': str(e),
            }

    @staticmethod
    def write(path: str, content: str, encoding: str = 'utf-8') -> dict:
        """写入文件 - 直接写入，不做任何转义"""
        return FileMutation._atomic_write(path, content, encoding)

    @staticmethod
    def append(path: str, content: str, encoding: str = 'utf-8') -> dict:
        """追加内容到文件"""
        try:
            dirname = os.path.dirname(path) or '.'
            os.makedirs(dirname, exist_ok=True)
            
            existed = os.path.exists(path)
            with open(path, 'a', encoding=encoding) as f:
                f.write(content)
            
            return {
                'success': True,
                'path': path,
                'existed': existed,
                'size': len(content),
            }
        except Exception as e:
            return {
                'success': False,
                'path': path,
                'error': str(e),
            }

    @staticmethod
    def delete(path: str) -> dict:
        """删除文件"""
        try:
            existed = os.path.exists(path)
            if existed:
                os.remove(path)
            return {
                'success': True,
                'path': path,
                'existed': existed,
            }
        except Exception as e:
            return {
                'success': False,
                'path': path,
                'error': str(e),
            }

    @staticmethod
    def copy(src: str, dst: str, overwrite: bool = True) -> dict:
        """复制文件"""
        try:
            if os.path.exists(dst) and not overwrite:
                return {
                    'success': False,
                    'src': src,
                    'dst': dst,
                    'error': '目标文件已存在',
                }
            dirname = os.path.dirname(dst) or '.'
            os.makedirs(dirname, exist_ok=True)
            shutil.copy2(src, dst)
            return {
                'success': True,
                'src': src,
                'dst': dst,
            }
        except Exception as e:
            return {
                'success': False,
                'src': src,
                'dst': dst,
                'error': str(e),
            }

    @staticmethod
    def move(src: str, dst: str, overwrite: bool = True) -> dict:
        """移动文件"""
        try:
            if os.path.exists(dst) and not overwrite:
                return {
                    'success': False,
                    'src': src,
                    'dst': dst,
                    'error': '目标文件已存在',
                }
            dirname = os.path.dirname(dst) or '.'
            os.makedirs(dirname, exist_ok=True)
            shutil.move(src, dst)
            return {
                'success': True,
                'src': src,
                'dst': dst,
            }
        except Exception as e:
            return {
                'success': False,
                'src': src,
                'dst': dst,
                'error': str(e),
            }


# ============================================
# safe_* 别名（兼容 fs_register.py）
# ============================================

def safe_write_file(path: str, content: str, preserve_bom: bool = True, encoding: str = 'utf-8') -> dict:
    """安全写入文件 - 直接写入，preserve_bom 参数忽略（保持兼容）"""
    return FileMutation.write(path, content, encoding)


def safe_append_file(path: str, content: str, encoding: str = 'utf-8') -> dict:
    """安全追加文件"""
    return FileMutation.append(path, content, encoding)


def safe_create_file(path: str, content: str, preserve_bom: bool = True, encoding: str = 'utf-8') -> dict:
    """创建文件（已存在则失败）"""
    if os.path.exists(path):
        return {
            'success': False,
            'path': path,
            'error': f'文件已存在: {path}',
        }
    return FileMutation.write(path, content, encoding)


def safe_remove_file(path: str) -> dict:
    """安全删除文件"""
    return FileMutation.delete(path)


def safe_copy_file(src: str, dst: str, overwrite: bool = True) -> dict:
    """安全复制文件"""
    return FileMutation.copy(src, dst, overwrite)


def safe_move_file(src: str, dst: str, overwrite: bool = True) -> dict:
    """安全移动文件"""
    return FileMutation.move(src, dst, overwrite)


# ============================================
# 便捷函数
# ============================================

def write_file(path: str, content: str, encoding: str = 'utf-8') -> dict:
    """写入文件"""
    return FileMutation.write(path, content, encoding)


def append_file(path: str, content: str, encoding: str = 'utf-8') -> dict:
    """追加内容"""
    return FileMutation.append(path, content, encoding)


def delete_file(path: str) -> dict:
    """删除文件"""
    return FileMutation.delete(path)


def copy_file(src: str, dst: str, overwrite: bool = True) -> dict:
    """复制文件"""
    return FileMutation.copy(src, dst, overwrite)


def move_file(src: str, dst: str, overwrite: bool = True) -> dict:
    """移动文件"""
    return FileMutation.move(src, dst, overwrite)


# ============================================
# 导出
# ============================================

__all__ = [
    'FileMutation',
    'safe_write_file',
    'safe_append_file',
    'safe_create_file',
    'safe_remove_file',
    'safe_copy_file',
    'safe_move_file',
    'write_file',
    'append_file',
    'delete_file',
    'copy_file',
    'move_file',
]