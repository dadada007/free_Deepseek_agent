# -*- coding: utf-8 -*-
"""
任务规划与跟踪工具集（P0） - 复杂任务的基石
规划可带依赖的任务清单，持久化到 JSON，支持状态跟踪/断点续跑。
放于 agent_tools/ 目录，由 HotReloader 自动扫描注册，改文件保存即热更新。
"""
import json
import os
import sys
import time
import threading
from datetime import datetime

# agent_tools 的上一级 = hermes/，数据放 hermes/data/plans.json
_HERMES_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _HERMES_DIR not in sys.path:
    sys.path.insert(0, _HERMES_DIR)
_DATA_FILE = os.path.join(_HERMES_DIR, "data", "plans.json")

_VALID_STATUS = {"pending", "in_progress", "done", "failed", "skipped"}


class PlanManager:
    """带依赖的任务规划，JSON 原子持久化，跨会话不丢失"""

    def __init__(self, data_file: str = _DATA_FILE):
        self.data_file = data_file
        self._lock = threading.Lock()
        self.goal = ""
        self.tasks = []  # [{id, description, dependencies, status, result}]
        self._load()

    def _load(self):
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.goal = data.get("goal", "")
                self.tasks = data.get("tasks", []) or []
            except Exception:
                self.tasks = []

    def _save(self):
        os.makedirs(os.path.dirname(self.data_file) or ".", exist_ok=True)
        data = {
            "goal": self.goal,
            "updated_at": datetime.now().isoformat(),
            "tasks": self.tasks,
        }
        tmp = self.data_file + f".tmp{int(time.time() * 1000)}"
        try:
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            os.replace(tmp, self.data_file)
        except Exception:
            if os.path.exists(tmp):
                os.unlink(tmp)
            raise

    # ===== 操作 =====

    def create(self, goal: str, tasks: list) -> dict:
        if not goal or not goal.strip():
            return {"success": False, "error": "缺少 goal 参数"}
        if not tasks or not isinstance(tasks, list):
            return {"success": False, "error": "缺少 tasks 列表（每项含 id/description/dependencies）"}
        clean = []
        for t in tasks:
            if not isinstance(t, dict) or not t.get("description"):
                continue
            clean.append({
                "id": str(t.get("id", str(len(clean) + 1))),
                "description": t["description"],
                "dependencies": [str(d) for d in (t.get("dependencies") or [])],
                "status": "pending",
                "result": "",
            })
        if not clean:
            return {"success": False, "error": "tasks 列表为空或格式不正确"}
        with self._lock:
            self.goal = goal.strip()
            self.tasks = clean
            self._save()
        return {"success": True, "goal": self.goal, "task_count": len(self.tasks),
                "tasks": list(self.tasks)}

    def status(self) -> dict:
        with self._lock:
            tasks = [dict(t) for t in self.tasks]
        total = len(tasks)
        done = sum(1 for t in tasks if t["status"] == "done")
        in_prog = [t["id"] for t in tasks if t["status"] == "in_progress"]
        failed = [t["id"] for t in tasks if t["status"] == "failed"]
        next_id = self.next_id_locked(tasks)
        return {
            "success": True,
            "goal": self.goal,
            "progress": f"{done}/{total}",
            "percent": round(done * 100 / total, 1) if total else 0,
            "in_progress": in_prog,
            "failed": failed,
            "next": next_id,
            "tasks": tasks,
        }

    def next_id_locked(self, tasks: list) -> str | None:
        """下一个可执行任务：pending 且所有依赖均 done/无依赖，按顺序"""
        done_ids = {t["id"] for t in tasks if t["status"] in ("done", "skipped")}
        for t in tasks:
            if t["status"] == "pending" and all(d in done_ids for d in t.get("dependencies", [])):
                return t["id"]
        return None

    def mark(self, task_id: str, status: str, result: str = "") -> dict:
        if status not in _VALID_STATUS:
            return {"success": False, "error": f"非法状态 {status}，应为 {sorted(_VALID_STATUS)}"}
        with self._lock:
            for t in self.tasks:
                if t["id"] == str(task_id):
                    t["status"] = status
                    if result is not None:
                        t["result"] = str(result)[:2000]
                    self._save()
                    return {"success": True, "id": t["id"], "status": status,
                            "goal": self.goal, "next": self.next_id_locked(self.tasks)}
        return {"success": False, "error": f"任务 {task_id} 不存在"}

    def remove(self, task_id: str) -> dict:
        with self._lock:
            before = len(self.tasks)
            self.tasks = [t for t in self.tasks if t["id"] != str(task_id)]
            if len(self.tasks) == before:
                return {"success": False, "error": f"任务 {task_id} 不存在"}
            self._save()
        return {"success": True, "message": f"已删除任务 {task_id}", "goal": self.goal}

    def reset(self) -> dict:
        with self._lock:
            self.goal = ""
            self.tasks = []
            self._save()
        return {"success": True, "message": "任务计划已清空"}


_manager: PlanManager | None = None


def _get_manager() -> PlanManager:
    global _manager
    if _manager is None:
        _manager = PlanManager(_DATA_FILE)
    return _manager


# ==================== 工具实现 ====================

def _plan_create(args: dict) -> str:
    tasks = args.get("tasks") or args.get("task_list") or []
    goal = args.get("goal", "")
    r = _get_manager().create(goal, tasks)
    return json.dumps(r, ensure_ascii=False, indent=2)


def _plan_status(args: dict) -> str:
    return json.dumps(_get_manager().status(), ensure_ascii=False, indent=2)


def _plan_mark(args: dict) -> str:
    r = _get_manager().mark(args.get("id", ""), args.get("status", ""),
                            args.get("result", ""))
    return json.dumps(r, ensure_ascii=False, indent=2)


def _plan_next(args: dict) -> str:
    mgr = _get_manager()
    with mgr._lock:
        tasks = [dict(t) for t in mgr.tasks]
    nxt = mgr.next_id_locked(tasks)
    if not nxt:
        done = sum(1 for t in tasks if t["status"] == "done")
        total = len(tasks)
        return json.dumps({"success": True,
                           "next": None,
                           "note": f"没有可执行的任务（{done}/{total} 已完成）"},
                          ensure_ascii=False, indent=2)
    desc = next((t["description"] for t in tasks if t["id"] == nxt), "")
    return json.dumps({"success": True, "next": nxt, "description": desc,
                       "goal": mgr.goal}, ensure_ascii=False, indent=2)


def _plan_reset(args: dict) -> str:
    return json.dumps(_get_manager().reset(), ensure_ascii=False, indent=2)


def _plan_remove(args: dict) -> str:
    return json.dumps(_get_manager().remove(args.get("id", "")), ensure_ascii=False, indent=2)


# ==================== 热加载注册 ====================

def register_tools():
    import tools
    tools.register(
        name="plan_create",
        description="创建带依赖关系的任务规划（覆盖旧规划）。参数: goal(总目标), tasks(任务列表，每项含 id/description/dependencies)。复杂任务必须先从大到小分解任务再逐个执行",
        parameters={"type": "object", "properties": {
            "goal": {"type": "string", "description": "总目标"},
            "tasks": {"type": "array", "description": "任务列表：[{id, description, dependencies[任务id]}]"},
        }, "required": ["goal", "tasks"]},
        func=_plan_create,
    )
    tools.register(
        name="plan_status",
        description="查看当前任务规划进度与全部任务状态",
        parameters={"type": "object", "properties": {}},
        func=_plan_status,
    )
    tools.register(
        name="plan_mark",
        description="更新任务状态。参数: id(任务id), status(pending/in_progress/done/failed/skipped), result(可选执行结果)",
        parameters={"type": "object", "properties": {
            "id": {"type": "string"},
            "status": {"type": "string", "enum": sorted(_VALID_STATUS)},
            "result": {"type": "string"},
        }, "required": ["id", "status"]},
        func=_plan_mark,
    )
    tools.register(
        name="plan_next",
        description="获取下一个可执行任务（依赖已满足的第一条 pending 任务）",
        parameters={"type": "object", "properties": {}},
        func=_plan_next,
    )
    tools.register(
        name="plan_reset",
        description="清空当前任务规划",
        parameters={"type": "object", "properties": {}},
        func=_plan_reset,
    )
    tools.register(
        name="plan_remove",
        description="删除规划中的单个任务。参数: id",
        parameters={"type": "object", "properties": {"id": {"type": "string"}},
                    "required": ["id"]},
        func=_plan_remove,
    )
    return 6


def unregister_tools():
    import tools
    for name in ["plan_create", "plan_status", "plan_mark", "plan_next",
                 "plan_reset", "plan_remove"]:
        tools.TOOLS.pop(name, None)