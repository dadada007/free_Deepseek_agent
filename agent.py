# -*- coding: utf-8 -*-
"""Agent 核心循环 - 简化版"""
import json
import logging
import concurrent.futures
import threading
from typing import List, Dict, Optional, Callable

from client import Client
import tools
import memory


logger = logging.getLogger(__name__)

MAX_TOOL_RESULT_CHARS = 50000


def _inject_memories_into_prompt(system_prompt: str, user_message: str) -> str:
    """将相关记忆注入到系统提示中"""
    try:
        mems = memory.auto_load_memory(user_message, limit=5)
        if not mems:
            return system_prompt
        mem_text = memory.format_memories_for_context(mems)
        if mem_text:
            return system_prompt + "\n\n" + mem_text
    except Exception as e:
        logger.warning(f"记忆加载失败: {e}")
    return system_prompt


class Agent:
    """Agent - 支持并行工具调用，集成记忆系统"""

    def __init__(
        self,
        client: Client,
        max_rounds: int = 100,
        parallel: bool = True,
        max_workers: int = 4,
        on_tool_call: Callable = None,
        on_tool_result: Callable = None,
        on_thinking: Callable = None,
        
    ):
        self.client = client
        self.max_rounds = max_rounds
        self.parallel = parallel
        self.max_workers = max_workers
        self.history: List[Dict] = []
        self.on_tool_call = on_tool_call
        self.on_tool_result = on_tool_result
        self.on_thinking = on_thinking
        self._stop_requested = False
        self._stop_lock = threading.Lock()
        
        # ====================
        
        # 启动记忆服务
        try:
            memory.get_service()
            logger.info("🧠 记忆服务已启动")
        except Exception as e:
            logger.warning(f"记忆服务启动失败: {e}")

    def request_stop(self):
        with self._stop_lock:
            self._stop_requested = True

    def reset_stop(self):
        with self._stop_lock:
            self._stop_requested = False

    def should_stop(self) -> bool:
        with self._stop_lock:
            return self._stop_requested

    def chat(self, user_message: str) -> str:
        self.reset_stop()
        self.history.append({"role": "user", "content": user_message})

        # 记录用户消息到记忆系统
        try:
            memory.record_turn("user", user_message, source="hermes")
        except Exception as e:
            logger.warning(f"记录用户记忆失败: {e}")

        # 构建系统提示（注入相关记忆）
        base_prompt = tools.build_system_prompt()
        enhanced_prompt = _inject_memories_into_prompt(base_prompt, user_message)
        messages = [{"role": "system", "content": enhanced_prompt}]
        messages.extend(self.history)

        last_tool_calls = []
        assistant_reply = ""

        for round_num in range(self.max_rounds):
            logger.info(f"轮次 {round_num + 1}/{self.max_rounds}")

            if self.on_thinking:
                self.on_thinking()

            try:
                result = self.client.chat(
                    messages=messages,
                    tools=tools.get_schemas(),
                    stream=False,
                )
            except Exception as e:
                error_msg = f"API 调用失败: {e}"
                logger.error(error_msg)
                self.history.append({"role": "assistant", "content": error_msg})
                return error_msg

            # 重复工具调用检测
            if result.has_tools():
                tc = result.tool_calls[0]["function"]
                key = (tc["name"], str(tc.get("arguments", {})))
                last_tool_calls.append(str(key))
                if len(last_tool_calls) >= 3 and len(set(last_tool_calls[-2:])) == 1:
                    logger.warning(f"⛔ 检测到重复工具调用: {tc['name']}，强制中断")
                    dup_msg = f"(检测到重复工具调用: {tc['name']} 连续 2 次相同，已自动停止)"
                    self.history.append({"role": "assistant", "content": dup_msg})
                    return dup_msg

            # 没有工具调用 -> 最终答案
            if not result.has_tools():
                content = result.content or "(无回复)"
                self.history.append({"role": "assistant", "content": content})
                assistant_reply = content
                # 记录助手回复到记忆系统
                try:
                    memory.record_turn("assistant", content, source="hermes")
                except Exception as e:
                    logger.warning(f"记录助手记忆失败: {e}")
                
                
                return content

            # 有工具调用 -> 执行
            tool_calls = result.tool_calls
            logger.info(f"本轮收到 {len(tool_calls)} 个工具调用")
            
            if self.should_stop():
                raise StopIteration("用户请求停止")
            
            if len(tool_calls) <= 1:
                results = [self._execute_one(tool_calls[0])]
            elif self.parallel:
                results = self._execute_parallel(tool_calls)
            else:
                results = [self._execute_one(tc) for tc in tool_calls]

            # 构建工具结果消息
            if len(results) == 1:
                result_msg = f"📦 工具结果:\n{results[0]['result']}"
            else:
                parts = [f"[{r['name']}] {r['result']}" for r in results]
                result_msg = f"📦 工具结果 ({len(results)} 个并行):\n\n" + "\n\n".join(parts)

            # 加入消息历史
            call_list = [{"name": r["name"], "arguments": r["args"]} for r in results]
            assistant_text = json.dumps(call_list, ensure_ascii=False)

            messages.append({"role": "assistant", "content": assistant_text})
            messages.append({"role": "tool", "content": result_msg})

            self.history.append({"role": "assistant", "content": assistant_text})
            self.history.append({"role": "tool", "content": result_msg})

        return "(达到最大执行轮数)"

    def _execute_one(self, tc: dict) -> dict:
        """执行单个工具调用"""
        name = tc["function"]["name"]
        
        # 直接取 arguments（已经是 dict）
        args = tc["function"].get("arguments", {})
        
        # 如果是字符串，尝试解析（兼容旧版本）
        if isinstance(args, str):
            try:
                args = json.loads(args)
            except:
                args = {}

        logger.info(f"工具调用: {name}({args})")
        if self.on_tool_call:
            self.on_tool_call(name, args)

        # tools.execute() 内部会统一处理 JSON 转义
        raw = tools.execute(name, args)
        
        # 截断过长输出
        if len(raw) > MAX_TOOL_RESULT_CHARS:
            raw = raw[:MAX_TOOL_RESULT_CHARS] + f"\n... (截断，原长度 {len(raw)})"

        logger.info(f"工具结果: {raw[:200]}")
        if self.on_tool_result:
            self.on_tool_result(name, raw)

        return {"name": name, "args": args, "result": raw}

    def _execute_parallel(self, tool_calls: List[dict]) -> List[dict]:
        """并行执行多个工具调用"""
        workers = max(1, min(self.max_workers, len(tool_calls)))
        logger.info(f"并行执行 {len(tool_calls)} 个工具 (workers={workers})")

        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as ex:
            return list(ex.map(self._execute_one, tool_calls))

    def reset(self):
        self.history = []
        try:
            self.client.reset_conversation()
        except Exception:
            pass