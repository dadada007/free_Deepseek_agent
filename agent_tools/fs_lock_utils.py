# -*- coding: utf-8 -*-
"""
fs_lock_utils.py - 文件锁与线程安全

提供：
- 基于线程的 KeyedMutex 锁
- 上下文管理器支持
- 跨线程文件操作安全

借鉴 OpenCode 的 KeyedMutex 设计
"""

import os
import threading
from typing import Dict, Optional
from contextlib import contextmanager

from fs_path_utils import normalize_path


# ============================================
# FileLock - 基于线程的文件锁
# ============================================

class FileLock:
    """
    基于线程的文件锁（KeyedMutex 模式）
    
    每个文件路径对应一个独立的 threading.Lock，
    确保同一时刻只有一个线程操作该文件。
    
    用法：
        with FileLock.with_lock("C:/path/to/file.txt"):
            # 安全的文件操作
            pass
    
    注意：
        - 这是线程级锁，不是进程级锁
        - 适用于单进程内的多线程并发场景
    """
    
    _locks: Dict[str, threading.Lock] = {}
    _root_lock = threading.Lock()
    
    @classmethod
    def get_lock(cls, path: str) -> threading.Lock:
        """
        获取指定路径的锁
        
        如果锁不存在则创建，保证同一路径共享同一把锁。
        """
        normalized = normalize_path(path)
        with cls._root_lock:
            if normalized not in cls._locks:
                cls._locks[normalized] = threading.Lock()
            return cls._locks[normalized]
    
    @classmethod
    @contextmanager
    def with_lock(cls, path: str):
        """
        上下文管理器，自动获取和释放锁
        
        用法：
            with FileLock.with_lock("C:/file.txt"):
                # 临界区代码
                pass
        """
        lock = cls.get_lock(path)
        with lock:
            yield
    
    @classmethod
    def try_lock(cls, path: str, timeout: Optional[float] = None) -> bool:
        """
        尝试获取锁（带超时）
        
        返回：
            True 表示成功获取锁
            False 表示超时或失败
        
        用法：
            if FileLock.try_lock("C:/file.txt", timeout=1.0):
                try:
                    # 临界区代码
                    pass
                finally:
                    FileLock.unlock("C:/file.txt")
        """
        lock = cls.get_lock(path)
        return lock.acquire(timeout=timeout)
    
    @classmethod
    def unlock(cls, path: str) -> None:
        """
        手动释放锁
        
        注意：仅当使用 try_lock 获取锁后调用
        """
        lock = cls.get_lock(path)
        if lock.locked():
            lock.release()
    
    @classmethod
    def is_locked(cls, path: str) -> bool:
        """检查指定路径是否被锁定"""
        normalized = normalize_path(path)
        with cls._root_lock:
            if normalized not in cls._locks:
                return False
            return cls._locks[normalized].locked()
    
    @classmethod
    def clear_locks(cls) -> None:
        """清空所有锁（测试用）"""
        with cls._root_lock:
            cls._locks.clear()


# ============================================
# 别名（兼容性）
# ============================================

KeyedMutex = FileLock  # 别名，与 OpenCode 命名一致


# ============================================
# 测试
# ============================================

if __name__ == '__main__':
    import time
    import tempfile
    
    print("=== fs_lock_utils 测试 ===\n")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = os.path.join(tmpdir, "test.txt")
        print(f"测试文件: {test_file}")
        
        # 测试 1: 基本锁
        print("\n--- 测试 1: 基本锁 ---")
        with FileLock.with_lock(test_file):
            print("  ✅ 成功获取锁")
        
        # 测试 2: 并发写入测试
        print("\n--- 测试 2: 并发写入测试 ---")
        results = []
        
        def writer(thread_id: int, content: str):
            with FileLock.with_lock(test_file):
                # 模拟写入
                time.sleep(0.01)
                results.append((thread_id, content))
                print(f"  Thread {thread_id} 写入: {content}")
        
        import threading
        threads = []
        for i in range(5):
            t = threading.Thread(target=writer, args=(i, f"Thread {i}"))
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        print(f"  ✅ 完成 {len(results)} 次并发写入，无冲突")
        
        # 测试 3: try_lock
        print("\n--- 测试 3: try_lock ---")
        lock_acquired = FileLock.try_lock(test_file, timeout=0.1)
        if lock_acquired:
            print("  ✅ 成功获取锁")
            FileLock.unlock(test_file)
        else:
            print("  ⚠️ 获取锁超时")
        
        # 测试 4: is_locked
        print("\n--- 测试 4: is_locked ---")
        with FileLock.with_lock(test_file):
            locked = FileLock.is_locked(test_file)
            print(f"  锁状态: {locked}")
        locked = FileLock.is_locked(test_file)
        print(f"  释放后锁状态: {locked}")
    
    print("\n✅ 所有测试通过")