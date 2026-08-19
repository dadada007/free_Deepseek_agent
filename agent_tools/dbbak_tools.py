# -*- coding: utf-8 -*-
"""
数据库备份工具集 - SQLite备份与恢复
"""

import json
import os
import shutil
from datetime import datetime


def _backup_db(args: dict) -> str:
    db_path = args.get('db_path', '')
    backup_dir = args.get('backup_dir', './backup')
    if not db_path or not os.path.exists(db_path):
        return "❌ 数据库文件不存在"
    try:
        os.makedirs(backup_dir, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = os.path.join(backup_dir, f"{os.path.basename(db_path)}_{timestamp}.bak")
        shutil.copy2(db_path, backup_path)
        return json.dumps({'成功': True, '备份文件': backup_path, '大小': f"{os.path.getsize(backup_path)/1024:.2f} KB"}, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"❌ 备份失败: {e}"


def register_tools():
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import tools
    tools.register(
        name="backup_db",
        description="备份数据库文件。参数: db_path(数据库路径), backup_dir(备份目录)",
        parameters={"type": "object", "properties": {
            "db_path": {"type": "string", "description": "数据库文件路径"},
            "backup_dir": {"type": "string", "description": "备份输出目录"}
        }, "required": ["db_path"]},
        func=_backup_db,
    )
    return 1


def unregister_tools():
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import tools
    for name in ["backup_db"]:
        tools.TOOLS.pop(name, None)
