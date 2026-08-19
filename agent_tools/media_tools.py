# -*- coding: utf-8 -*-
"""
音频和数据库工具
"""
import os
import sys
import sqlite3
import json
import platform
import subprocess

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tools import register


# ============ sql_execute ============

def _sql_execute(args: dict) -> str:
    sql = args.get('sql', '').strip()
    if not sql:
        return "❌ 错误: 请提供 sql 参数"

    db_path = args.get('db_path', 'data/query.db')
    params = args.get('params', None)

    # 确保目录存在
    db_dir = os.path.dirname(db_path)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir)

    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        if params:
            cursor.execute(sql, params)
        else:
            cursor.execute(sql)

        sql_upper = sql.strip().upper()
        if sql_upper.startswith("SELECT") or sql_upper.startswith("PRAGMA"):
            rows = cursor.fetchall()
            if not rows:
                return "查询结果为空"
            return json.dumps([dict(row) for row in rows], ensure_ascii=False, indent=2)
        else:
            conn.commit()
            return f"✅ 执行成功，影响 {cursor.rowcount} 行"
    except Exception as e:
        return f"❌ SQL 执行失败: {e}"
    finally:
        conn.close()


# ============ play_sound ============

def _play_sound(args: dict) -> str:
    file_path = args.get('file_path', '').strip()
    if not file_path:
        return "❌ 错误: 请提供 file_path 参数"

    if not os.path.exists(file_path):
        return f"❌ 文件不存在: {file_path}"

    system = platform.system()
    try:
        if system == "Windows":
            import winsound
            if file_path.lower().endswith(".wav"):
                winsound.PlaySound(file_path, winsound.SND_FILENAME)
                return f"✅ 播放成功（WAV）: {file_path}"
            else:
                os.startfile(file_path)
                return f"✅ 已调用默认播放器: {file_path}"
        elif system == "Darwin":
            subprocess.run(["afplay", file_path], check=True)
            return f"✅ 播放成功（afplay）: {file_path}"
        else:
            for player in ["aplay", "mpg123", "ffplay"]:
                if subprocess.run(["which", player], capture_output=True).returncode == 0:
                    subprocess.run([player, file_path], check=True)
                    return f"✅ 播放成功（{player}）: {file_path}"
            return "❌ 错误: 未找到可用的音频播放器（aplay/mpg123/ffplay）"
    except Exception as e:
        return f"❌ 播放失败: {e}"


# ============ 注册 ============

def register_tools() -> int:
    register(
        name="sql_execute",
        description="执行 SQL 语句（支持 SELECT/INSERT/UPDATE/DELETE），默认使用 data/query.db",
        parameters={
            "type": "object",
            "properties": {
                "sql": {
                    "type": "string",
                    "description": "SQL 语句"
                },
                "db_path": {
                    "type": "string",
                    "description": "数据库文件路径，默认 data/query.db",
                    "default": "data/query.db"
                },
                "params": {
                    "type": "array",
                    "description": "参数列表（预编译防注入）",
                    "default": None
                }
            },
            "required": ["sql"]
        },
        func=_sql_execute
    )

    register(
        name="play_sound",
        description="播放本地音频文件（WAV/MP3 等格式）",
        parameters={
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "音频文件路径，使用正斜杠或双反斜杠"
                }
            },
            "required": ["file_path"]
        },
        func=_play_sound
    )

    return 2