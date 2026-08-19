# -*- coding: utf-8 -*-
"""
任务规划器 + 顺序执行器（精简版，JSON 持久化）
================================================
- TaskPlanner: 用 LLM 把目标拆成带依赖的任务列表，写入 JSON 文件（永不丢失）
- Pipeline: 顺序执行器 —— 一个个执行任务（串行，匹配浏览器），
  支持断点续跑、连续失败自动重新拆解剩余任务

状态机: pending -> in_progress -> done | failed | skipped
"""
import os
import re
import json
import time
import logging
import tempfile
import threading
from datetime import datetime
from typing import Optional, List

from client import Client
from agent import Agent

logger = logging.getLogger(__name__)

MAX_REPLANS = 2          # 一次计划最多重新拆解次数
REPLAN_THRESHOLD = 2     # 连续失败 N 次后触发重新拆解


class Task:
    """单个任务"""
    def __init__(self, id: str, description: str, dependencies: list = None):
        self.id = str(id)
        self.description = description
        self.dependencies = [str(d) for d in (dependencies or [])]
        self.status = "pending"  # pending | in_progress | done | failed | skipped
        self.result = ""

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "description": self.description,
            "dependencies": self.dependencies,
            "status": self.status,
            "result": self.result,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Task":
        t = cls(d["id"], d["description"], d.get("dependencies", []))
        t.status = d.get("status", "pending")
        t.result = d.get("result", "")
        return t

    def verify_completion(self) -> tuple:
        """验证任务是否真正完成。返回 (通过?, 额外信息)"""
        desc = self.description.lower()
        result_lower = (self.result or "").lower()

        # 写入/创建类任务：检查关键文件是否真实存在
        write_keywords = ["创建", "写入", "新建", "生成", "编写", "write", "create"]
        if any(kw in desc for kw in write_keywords):
            import re
            # 从描述中提取文件名（支持中文冒号、等号等格式）
            patterns = [
                r'(?:文件[名为]?|保存[到为]?|输出|写入|创建)\s*[：:=]?\s*[`"\']?([^\s`"\'：,，。、]+)',
                r'(\w+\.\w{1,5})\b',
            ]
            files_found = []
            for pat in patterns:
                files_found = re.findall(pat, self.description)
                if files_found:
                    break
            missing = [f for f in files_found if not os.path.exists(f)]
            if missing:
                return False, f"声称完成但文件不存在: {', '.join(missing)}"

        # 如果 LLM 回复包含明显失败信号
        fail_signals = ["错误", "失败", "error", "failed", "无法", "不能"]
        if any(sig in result_lower for sig in fail_signals):
            return False, f"回复包含失败信号: {self.result[:100]}"

        return True, ""


# ==================== LLM 规划 ====================

def _ask_plan_json(client: Client, prompt: str) -> dict:
    """调 LLM 并提取 {tasks:[...]} JSON。失败抛异常。"""
    try:
        result = client.chat(
            messages=[{"role": "user", "content": prompt}],
            tools=None,
            stream=False,
        )
    except Exception as e:
        raise RuntimeError(f"规划调用失败: {e}")

    answer = (result.content or "").strip()
    if not answer:
        raise RuntimeError("规划返回空回复")

    # 剥离 markdown 代码围栏
    answer = re.sub(r'```(?:json)?\s*\n([\s\S]*?)```', r'\1', answer)

    m = re.search(r'\{[\s\S]*\}', answer)
    if not m:
        raise RuntimeError(f"未找到 JSON: {answer[:200]}")
    try:
        data = json.loads(m.group())
    except json.JSONDecodeError as e:
        raise RuntimeError(f"规划 JSON 解析失败: {e}")

    raw_tasks = data.get("tasks") or data.get("tasklist") or []
    if not isinstance(raw_tasks, list) or not raw_tasks:
        raise RuntimeError("规划结果缺少 tasks 列表")
    return data


_PLAN_PROMPT = """你是软件项目规划专家。请把目标拆成**有序、可执行、可独立验证**的小任务，任务之间标注依赖。

目标：{goal}

要求：
1. 每个任务是具体开发步骤（如创建文件、写代码、装依赖、运行测试）
2. 有依赖关系的任务，把依赖任务 id 填进 dependencies
3. 不超过 15 个任务，粒度适中
4. 禁止调用任何工具，只输出 JSON

输出格式（只输出以下 JSON，不要别的文字）：
{{"tasks": [
  {{"id": "1", "description": "...", "dependencies": []}},
  {{"id": "2", "description": "...", "dependencies": ["1"]}}
]}}"""


class TaskPlanner:
    """任务规划器 - JSON 持久化，单线程互斥"""

    def __init__(self, data_file: str = "hermes_tasks.json"):
        self.data_file = data_file
        self._lock = threading.Lock()
        self.goal: str = ""
        self.replan_count: int = 0
        self.tasks: List[Task] = []
        self._load()

    # ==================== 持久化 ====================

    def _load(self):
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.goal = data.get("goal", "")
                self.replan_count = data.get("replan_count", 0)
                self.tasks = [Task.from_dict(t) for t in data.get("tasks", [])]
                logger.info(f"📋 加载任务计划: {len(self.tasks)} 个任务")
            except Exception as e:
                logger.warning(f"⚠️ 加载任务计划失败: {e}")
                self.tasks = []

    def _save(self):
        """原子写 JSON，保证永不丢失"""
        if os.path.dirname(self.data_file):
            os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
        data = {
            "goal": self.goal,
            "replan_count": self.replan_count,
            "updated_at": datetime.now().isoformat(),
            "tasks": [t.to_dict() for t in self.tasks],
        }
        fd, tmp = tempfile.mkstemp(
            dir=os.path.dirname(self.data_file) or ".", suffix=".tmp"
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            os.replace(tmp, self.data_file)
        except Exception:
            if os.path.exists(tmp):
                os.unlink(tmp)
            raise

    # ==================== 规划 ====================

    def create_plan(self, client: Client, goal: str) -> dict:
        """用 LLM 拆解目标为任务列表"""
        prompt = _PLAN_PROMPT.format(goal=goal)
        try:
            data = _ask_plan_json(client, prompt)
        except Exception as e:
            logger.error(f"规划失败: {e}")
            return {"success": False, "error": str(e)}

        with self._lock:
            self.goal = goal
            self.replan_count = 0
            self.tasks = []
            for i, t in enumerate(data["tasks"]):
                self.tasks.append(Task(
                    id=t.get("id", str(i + 1)),
                    description=t["description"],
                    dependencies=[str(d) for d in t.get("dependencies", [])],
                ))
            self._save()

        logger.info(f"✅ 任务规划完成: {len(self.tasks)} 个任务")
        return {
            "success": True,
            "goal": goal,
            "task_count": len(self.tasks),
            "tasks": [t.to_dict() for t in self.tasks],
        }

    def replan(self, client: Client, failure_reason: str = "") -> dict:
        """连续失败后重新拆解剩余任务，保留已完成任务"""
        with self._lock:
            if not self.goal:
                return {"success": False, "error": "没有当前目标，无法重新规划"}
            if self.replan_count >= MAX_REPLANS:
                return {"success": False, "error": f"已达最大重规划次数({MAX_REPLANS})"}

            done = [t for t in self.tasks if t.status == "done"]
            remaining = [t for t in self.tasks if t.status != "done"]

        done_text = "\n".join(f"- [{t.id}] {t.description}" for t in done) or "（无）"
        remain_text = "\n".join(
            f"- [{t.id}] ({t.status}) {t.description}"
            + (f" → {t.result[:80]}" if t.result else "")
            for t in remaining
        ) or "（无）"

        prompt = f"""你是软件项目规划专家。之前的任务拆解在执行中遇到问题，请重新拆解**未完成**的任务。

总目标：{self.goal}

已完成的任务（不要重复规划）：
{done_text}

剩余/失败的任务：
{remain_text}

最近失败信息：{failure_reason[:300] or '无'}

要求：
1. 只规划剩余未完成的工作，不重复已完成任务
2. 针对失败原因调整：拆更细 / 换实现方式 / 调整顺序
3. 每个任务具体可验证，不超过 10 个
4. 禁止调用任何工具，只输出 JSON

输出格式：
{{"tasks": [
  {{"id": "1", "description": "...", "dependencies": []}}
]}}"""

        try:
            data = _ask_plan_json(client, prompt)
        except Exception as e:
            logger.error(f"重新规划失败: {e}")
            return {"success": False, "error": str(e)}

        with self._lock:
            # 新任务 id 从已完成任务最大数字 id 之后继续
            max_id = 0
            for t in done:
                try:
                    max_id = max(max_id, int(t.id))
                except (ValueError, TypeError):
                    pass
            new_tasks = []
            for i, rt in enumerate(data["tasks"]):
                new_tasks.append(Task(
                    id=str(max_id + i + 1),
                    description=rt["description"],
                    dependencies=[str(d) for d in rt.get("dependencies", [])],
                ))
            # 依赖只保留已存在 id（已完成 + 新任务）
            valid_ids = {t.id for t in done} | {t.id for t in new_tasks}
            for t in new_tasks:
                t.dependencies = [d for d in t.dependencies if d in valid_ids]
            self.tasks = done + new_tasks
            self.replan_count += 1
            self._save()

        logger.info(f"🧠 重新规划完成 (第{self.replan_count}/{MAX_REPLANS}次): 新增 {len(new_tasks)} 个任务")
        return {
            "success": True,
            "replan_count": self.replan_count,
            "new_task_count": len(new_tasks),
            "tasks": [t.to_dict() for t in self.tasks],
        }

    # ==================== 任务导航 ====================

    def get_next_task(self) -> Optional[Task]:
        """取下一个依赖已满足的 pending 任务"""
        with self._lock:
            done_ids = {t.id for t in self.tasks if t.status == "done"}
            for t in self.tasks:
                if t.status == "pending" and all(d in done_ids for d in t.dependencies):
                    return t
        return None

    def get_blocked_pending(self) -> List[Task]:
        """依赖已失败/跳过的 pending 任务（无法执行，应跳过）"""
        with self._lock:
            bad = {t.id for t in self.tasks if t.status in ("failed", "skipped")}
            return [
                t for t in self.tasks
                if t.status == "pending" and any(d in bad for d in t.dependencies)
            ]

    def mark_task(self, task_id: str, status: str, result: str = ""):
        with self._lock:
            for t in self.tasks:
                if t.id == str(task_id):
                    t.status = status
                    if result:
                        t.result = result[:500]
                    self._save()
                    return
            logger.warning(f"⚠️ 未找到任务: {task_id}")

    def get_progress(self) -> dict:
        with self._lock:
            total = len(self.tasks)
            done = sum(1 for t in self.tasks if t.status == "done")
            failed = sum(1 for t in self.tasks if t.status == "failed")
            skipped = sum(1 for t in self.tasks if t.status == "skipped")
            in_progress = sum(1 for t in self.tasks if t.status == "in_progress")
            pending = sum(1 for t in self.tasks if t.status == "pending")
            current = next((t for t in self.tasks if t.status == "in_progress"), None)
            return {
                "goal": self.goal,
                "total": total,
                "done": done,
                "failed": failed,
                "skipped": skipped,
                "pending": pending,
                "in_progress": in_progress,
                "current": current.to_dict() if current else None,
                "progress_pct": round((done + skipped) / total * 100, 1) if total else 0,
                "replan_count": self.replan_count,
                "tasks": [t.to_dict() for t in self.tasks],
            }

    def resume(self, retry_failed: bool = True) -> dict:
        """断点续跑：in_progress -> pending；可选 failed -> pending"""
        with self._lock:
            resumed = 0
            for t in self.tasks:
                if t.status == "in_progress":
                    t.status = "pending"
                    resumed += 1
                elif t.status == "failed" and retry_failed:
                    t.status = "pending"
                    t.result = ""
                    resumed += 1
            self._save()
        pending = sum(1 for t in self.tasks if t.status == "pending")
        logger.info(f"⏯️ 断点续跑准备: 恢复 {resumed} 个任务, 待执行 {pending} 个")
        return {"success": True, "resumed": resumed, "pending": pending}

    def reset(self):
        with self._lock:
            self.goal = ""
            self.replan_count = 0
            self.tasks = []
            self._save()
        logger.info("🔄 任务计划已重置")


# ==================== 顺序执行器 ====================

class Pipeline:
    """顺序执行器：永不阻塞 GUI，逐个执行任务，连续失败自动重新拆解"""

    def __init__(
        self,
        client: Client,
        data_file: str = "hermes_tasks.json",
        max_rounds: int = 100,
        parallel: bool = True,
        max_workers: int = 4,
        replan_threshold: int = REPLAN_THRESHOLD,
    ):
        self.client = client
        self.planner = TaskPlanner(data_file)
        self.max_rounds = max_rounds
        self.parallel = parallel
        self.max_workers = max_workers
        self.replan_threshold = replan_threshold

        self._running = False
        self._stop_requested = False
        self._thread: Optional[threading.Thread] = None
        self._consecutive_failures = 0
        self._lock = threading.Lock()
        self._mode = "idle"  # idle | running | completed | failed | stopped
        self._logs: List[str] = []
        self.current_task: Optional[str] = None

    # ==================== 状态 ====================

    def _log(self, msg: str, level: str = "info"):
        line = f"[{datetime.now().strftime('%H:%M:%S')}] {msg}"
        with self._lock:
            self._logs.append(line)
            if len(self._logs) > 100:
                self._logs = self._logs[-80:]
        getattr(logger, level)(f"[Pipeline] {msg}")

    def _status_snapshot(self) -> dict:
        with self._lock:
            return {
                "mode": self._mode,
                "running": self._running,
                "current": self.current_task,
                "logs": list(self._logs[-30:]),
                "consecutive_failures": self._consecutive_failures,
            }

    def get_status(self) -> dict:
        s = self._status_snapshot()
        s["plan"] = self.planner.get_progress()
        return s

    # ==================== 控制 ====================

    def plan(self, goal: str) -> dict:
        """只拆解任务（不执行），供 GUI 预览"""
        return self.planner.create_plan(self.client, goal)

    def start(self, goal: Optional[str] = None) -> dict:
        """启动流水线。goal 传入则先重新规划，否则接着现有计划跑（断点续跑）"""
        with self._lock:
            if self._running:
                return {"success": False, "message": "流水线已在运行"}

        if goal:
            plan_res = self.plan(goal)
            if not plan_res.get("success"):
                return plan_res
        elif not self.planner.tasks:
            return {"success": False, "message": "无任务计划，请先提供目标"}

        with self._lock:
            self._running = True
            self._stop_requested = False
            self._mode = "running"
            self._consecutive_failures = 0
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        return {
            "success": True,
            "message": "流水线已启动",
            "plan": self.planner.get_progress(),
        }

    def stop(self) -> dict:
        with self._lock:
            if not self._running:
                return {"success": False, "message": "流水线未在运行"}
            self._stop_requested = True
            self._mode = "stopped"
            self._log("⏸️ 正在停止（当前任务结束后生效）")
        return {"success": True, "message": "已请求停止"}

    def wait(self, poll_interval: float = 1.0, timeout: float = None):
        """阻塞等待流水线结束"""
        start = time.time()
        while self._running:
            if timeout and time.time() - start > timeout:
                break
            time.sleep(poll_interval)

    # ==================== 主循环 ====================

    def _run_loop(self):
        agent = Agent(
            self.client,
            max_rounds=self.max_rounds,
            parallel=self.parallel,
            max_workers=self.max_workers,
        )
        goal = self.planner.goal

        try:
            while self._running:
                if self._stop_requested:
                    break

                task = self.planner.get_next_task()
                if not task:
                    # 处理依赖已失败/跳过的任务
                    blocked = self.planner.get_blocked_pending()
                    if blocked:
                        for t in blocked:
                            self.planner.mark_task(t.id, "skipped", "依赖任务失败，跳过")
                            self._log(f"⏭️ 跳过任务 {t.id}: {t.description}（依赖失败）")
                        continue
                    # 没有可执行任务 → 结束
                    with self._lock:
                        self._mode = "completed"
                    self._log("✅ 流水线完成")
                    break

                self.planner.mark_task(task.id, "in_progress")
                with self._lock:
                    self.current_task = task.description
                self._log(f"📋 任务 {task.id}/{self.planner.get_progress()['total']}: {task.description}")

                ok, reply = self._execute_task(agent, task, goal)
                if ok:
                    verified, vinfo = task.verify_completion()
                    if verified:
                        self.planner.mark_task(task.id, "done", reply)
                        with self._lock:
                            self._consecutive_failures = 0
                        self._log(f"✅ 任务 {task.id} 完成")
                    else:
                        self.planner.mark_task(task.id, "failed", f"验证失败: {vinfo}")
                        with self._lock:
                            self._consecutive_failures += 1
                        self._log(f"⚠️ 任务 {task.id} 验证未通过: {vinfo}")
                else:
                    self.planner.mark_task(task.id, "failed", reply)
                    with self._lock:
                        self._consecutive_failures += 1
                    self._log(f"❌ 任务 {task.id} 失败: {reply[:100]}")

                    # 连续失败 → 重新拆解剩余任务
                    if self._consecutive_failures >= self.replan_threshold:
                        res = self.planner.replan(self.client, failure_reason=reply[:300])
                        if res.get("success"):
                            with self._lock:
                                self._consecutive_failures = 0
                            self._log(f"🧠 已重新拆解为 {res['new_task_count']} 个新任务")
                        else:
                            self._log(f"⚠️ 重新规划失败: {res.get('error')}")

                with self._lock:
                    self.current_task = None
                time.sleep(0.5)
        except Exception as e:
            with self._lock:
                self._mode = "failed"
            self._log(f"❌ 流水线异常: {e}", "error")
        finally:
            with self._lock:
                self._running = False
                self.current_task = None

    def _execute_task(self, agent: Agent, task: Task, goal: str) -> tuple:
        """执行单个任务。返回 (成功?, 回复文本)"""
        prompt = f"【任务 {task.id}】{task.description}\n\n总目标：{goal}\n请只完成这个任务，完成后用一两句话总结结果。"
        try:
            reply = agent.chat(prompt)
        except Exception as e:
            logger.error(f"任务 {task.id} 执行异常: {e}")
            return False, f"执行异常: {e}"

        if not reply:
            return False, "无回复"
        if reply.startswith("API 调用失败"):
            return False, reply
        if reply.startswith("(达到最大执行轮数)"):
            return False, "达到最大执行轮数，任务未完成"
        if "检测到重复工具调用" in reply:
            return False, reply
        return True, reply