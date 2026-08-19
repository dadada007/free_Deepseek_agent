# -*- coding: utf-8 -*-
"""
文件同步工具集 - 目录同步、增量备份
"""

import json
import os
import shutil
import filecmp


def _sync_dirs(args: dict) -> str:
    src = args.get('src', '')
    dst = args.get('dst', '')
    if not src or not dst:
        return "❌ 请提供源和目标目录"
    if not os.path.exists(src):
        return "❌ 源目录不存在"
    try:
        os.makedirs(dst, exist_ok=True)
        synced = []
        for root, dirs, files in os.walk(src):
            rel_path = os.path.relpath(root, src)
            dest_dir = os.path.join(dst, rel_path)
            os.makedirs(dest_dir, exist_ok=True)
            for file in files:
                src_file = os.path.join(root, file)
                dst_file = os.path.join(dest_dir, file)
                if not os.path.exists(dst_file) or not filecmp.cmp(src_file, dst_file):
                    shutil.copy2(src_file, dst_file)
                    synced.append(dst_file)
        return json.dumps({'成功': True, '同步文件数': len(synced), '文件列表': synced[:20]}, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"❌ 同步失败: {e}"


def register_tools():
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import tools
    tools.register(name="sync_dirs", description="目录同步。参数: src(源目录), dst(目标目录)", parameters={"type": "object", "properties": {"src": {"type": "string"}, "dst": {"type": "string"}}, "required": ["src", "dst"]}, func=_sync_dirs)
    return 1


def unregister_tools():
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import tools
    for name in ["sync_dirs"]:
        tools.TOOLS.pop(name, None)
