# -*- coding: utf-8 -*-
"""
记忆工具 - 手动保存 / 检索 / 总结 / 删除 / 状态（可热加载）
放于 agent_tools/ 目录，启动时由 HotReloader 自动扫描注册；修改本文件保存即热更新。
"""
import json
import os
import sys

# 复用 hermes 包内的记忆服务（memory.py / memory_db.py）
_hermes_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _hermes_dir not in sys.path:
    sys.path.insert(0, _hermes_dir)

import memory  # noqa: E402


def _memory_save(args: dict) -> str:
    content = args.get("content", "")
    category = args.get("category", "general")
    importance = int(args.get("importance", 5))
    if not content or not content.strip():
        return "错误: 缺少 content 参数"
    mid = memory.get_service().save(
        content=content, category=category,
        importance=min(10, max(1, importance)),
    )
    return json.dumps(
        {"success": True, "memory_id": mid, "message": f"已记住: {content[:50]}..."},
        ensure_ascii=False, indent=2,
    )


def _memory_search(args: dict) -> str:
    query = args.get("query", "")
    limit = int(args.get("limit", 10))
    if not query:
        return "错误: 缺少 query 参数"
    mems = memory.get_service().search(query, limit=limit)
    return json.dumps(
        {"success": True, "count": len(mems),
         "memories": [m.to_dict() for m in mems]},
        ensure_ascii=False, indent=2,
    )


def _memory_summary(args: dict) -> str:
    svc = memory.get_service()
    total = svc.db.count()
    recent = svc.db.search_by_time(days=7, limit=100)
    cats = {}
    for m in recent:
        cats[m.category] = cats.get(m.category, 0) + 1
    top = svc.db.search_by_importance(min_importance=8, limit=5)
    return json.dumps(
        {
            "success": True,
            "total_memories": total,
            "recent_7days": len(recent),
            "categories": cats,
            "top_memories": [
                {"content": m.content[:100], "importance": m.importance,
                 "time": m.to_dict()["time"]} for m in top
            ],
        },
        ensure_ascii=False, indent=2,
    )


def _memory_forget(args: dict) -> str:
    mid = int(args.get("memory_id", 0))
    if not mid:
        return "错误: 缺少 memory_id 参数"
    svc = memory.get_service()
    if svc.db.get(mid) is None:
        return f"错误: 记忆 ID {mid} 不存在"
    svc.db.update_importance(mid, 0)  # 软删除
    return json.dumps({"success": True, "message": f"已遗忘记忆 ID: {mid}"},
                      ensure_ascii=False, indent=2)


def _memory_status(args: dict) -> str:
    return memory.memory_status()


# ==================== 热加载注册 ====================

def register_tools():
    import tools
    tools.register(
        name="memory_save",
        description="手动保存一条记忆。当用户说'记住...'或明确要求保存信息时调用。参数: content, category(general/code/task/preference/knowledge/conversation), importance(1-10, 默认5)",
        parameters={
            "type": "object",
            "properties": {
                "content": {"type": "string", "description": "要保存的记忆内容"},
                "category": {"type": "string", "description": "记忆分类，默认 general"},
                "importance": {"type": "integer", "description": "重要性 1-10，默认5"},
            },
            "required": ["content"],
        },
        func=_memory_save,
    )
    tools.register(
        name="memory_search",
        description="搜索历史记忆。当用户说'搜索记忆...'或'我记得...'时调用。参数: query, limit(默认10)",
        parameters={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "搜索关键词"},
                "limit": {"type": "integer", "description": "返回条数，默认10"},
            },
            "required": ["query"],
        },
        func=_memory_search,
    )
    tools.register(
        name="memory_summary",
        description="获取记忆系统总结（总数/最近7天/分类统计/重要记忆）。无参数",
        parameters={"type": "object", "properties": {}},
        func=_memory_summary,
    )
    tools.register(
        name="memory_forget",
        description="删除/遗忘一条记忆。当用户说'忘记...'时调用。参数: memory_id",
        parameters={
            "type": "object",
            "properties": {"memory_id": {"type": "integer", "description": "记忆 ID"}},
            "required": ["memory_id"],
        },
        func=_memory_forget,
    )
    tools.register(
        name="memory_status",
        description="查看记忆系统状态（数据库路径/后台写入线程/队列/总条数/最近捕获）。无参数",
        parameters={"type": "object", "properties": {}},
        func=_memory_status,
    )
    return 5


def unregister_tools():
    import tools
    for name in ["memory_save", "memory_search", "memory_summary",
                 "memory_forget", "memory_status"]:
        tools.TOOLS.pop(name, None)