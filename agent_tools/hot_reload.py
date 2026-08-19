# -*- coding: utf-8 -*-
"""
工具热加载器 - 监听 agent_tools/ 目录，动态注册/更新工具，无需重启
适配 Hermes tools.register() 系统
"""
import os
import sys
import time
import importlib
import importlib.util
import threading
import logging
from pathlib import Path
from typing import Dict, Optional, Set

logger = logging.getLogger(__name__)

_SKIP_FILES = {"__init__.py", "hot_reload.py", ".gitkeep"}


class HotReloader:
    """工具热加载器 - 轮询 agent_tools/ 目录，文件变化时自动重新加载"""

    def __init__(self, watch_dir: str = None, interval: int = 3):
        self.watch_dir = watch_dir or os.path.join(
            os.path.dirname(os.path.abspath(__file__)))
        self.interval = interval
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._file_times: Dict[str, float] = {}
        self._loaded_modules: Dict[str, str] = {}   # module_name -> file_path
        self._registered_tools: Set[str] = set()     # 已注册的工具名
        self._lock = threading.Lock()

    def start(self):
        if self._running:
            return
        self._running = True
        self._scan_initial()
        self._thread = threading.Thread(target=self._watch_loop, daemon=True)
        self._thread.start()
        logger.info(f"🔥 热加载器已启动: {self.watch_dir} (间隔 {self.interval}s)")

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=3)
        logger.info("🛑 热加载器已停止")

    def _scan_initial(self):
        """首次扫描，加载所有工具模块"""
        for f in Path(self.watch_dir).glob("*.py"):
            if f.name in _SKIP_FILES:
                continue
            self._file_times[str(f)] = f.stat().st_mtime
            self._loaded_modules[f.stem] = str(f)
            logger.info(f"   📦 发现工具模块: {f.stem}")
            # 首次扫描就加载模块并注册工具
            try:
                self._reload_module(f.stem, str(f))
            except Exception as e:
                logger.error(f"❌ 初始加载失败 [{f.stem}]: {e}")

    def _watch_loop(self):
        while self._running:
            try:
                self._check_files()
            except Exception as e:
                logger.error(f"⚠️ 热加载异常: {e}")
            time.sleep(self.interval)

    def _check_files(self):
        """检查文件变化，加载新模块或重载变化模块"""
        current_files = set()
        for f in Path(self.watch_dir).glob("*.py"):
            if f.name in _SKIP_FILES:
                continue
            file_path = str(f)
            current_files.add(file_path)
            mtime = f.stat().st_mtime
            old_mtime = self._file_times.get(file_path, 0)

            if mtime > old_mtime:
                self._file_times[file_path] = mtime
                logger.info(f"🔄 检测到变化: {f.name}")
                self._reload_module(f.stem, file_path)

        # 检测已删除的文件
        for deleted in set(self._loaded_modules.values()) - current_files:
            mod_name = [k for k, v in self._loaded_modules.items() if v == deleted]
            if mod_name:
                logger.info(f"🗑️ 文件已删除: {os.path.basename(deleted)}")
                self._loaded_modules.pop(mod_name[0], None)

    def _reload_module(self, module_name: str, file_path: str):
        """重新加载模块并调用 register_tools()"""
        try:
            # 卸载旧工具
            old_tools = {t for t in self._registered_tools}
            if module_name in sys.modules:
                old_mod = sys.modules[module_name]
                if hasattr(old_mod, 'unregister_tools'):
                    try:
                        old_mod.unregister_tools()
                    except Exception:
                        pass

            # 加载新模块
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            if spec is None or spec.loader is None:
                logger.error(f"❌ 无法加载: {module_name}")
                return
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            sys.modules[module_name] = module

            # 调用注册
            if hasattr(module, 'register_tools'):
                count = module.register_tools()
                logger.info(f"✅ 已注册 {count or '?'} 个工具: {module_name}")
            else:
                logger.info(f"ℹ️ {module_name} 无 register_tools()，跳过")

            self._loaded_modules[module_name] = file_path

        except Exception as e:
            logger.error(f"❌ 热加载失败 [{module_name}]: {e}")

    def reload_all(self):
        """手动重载所有模块"""
        for name, path in list(self._loaded_modules.items()):
            self._reload_module(name, path)

    def get_status(self) -> str:
        lines = [
            f"🔥 热加载器: {'运行中' if self._running else '已停止'}",
            f"   目录: {self.watch_dir}",
            f"   模块: {len(self._loaded_modules)} 个",
        ]
        for name in self._loaded_modules:
            lines.append(f"     - {name}")
        return "\n".join(lines)


# ==================== 全局实例 ====================

_reloader: Optional[HotReloader] = None


def start_hot_reload(watch_dir: str = None, interval: int = 3) -> HotReloader:
    global _reloader
    if _reloader is None:
        _reloader = HotReloader(watch_dir, interval)
        _reloader.start()
    return _reloader


def stop_hot_reload():
    global _reloader
    if _reloader:
        _reloader.stop()
        _reloader = None


def get_hot_reload_status() -> str:
    if _reloader:
        return _reloader.get_status()
    return "⚠️ 热加载器未启动"
