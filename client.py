# -*- coding: utf-8 -*-
"""API 客户端 - 连接 g.py DeepSeek Browser 服务"""
import json
import logging
import requests
from typing import Optional, List, Dict

from parser import extract_tool_calls

logger = logging.getLogger(__name__)


class ChatResult:
    """一次回复的结果"""
    def __init__(self, content: str = None, tool_calls: List[dict] = None):
        self.content = content
        self.tool_calls = tool_calls or []

    def has_tools(self) -> bool:
        return bool(self.tool_calls)


class Client:
    """OpenAI 兼容 API 客户端"""

    def __init__(
        self,
        base_url: str = "http://127.0.0.1:8003",
        model: str = "deepseek-browser",
        session_id: str = None,
        api_key: str = "sk-admin",
        agent_name: str = None,
    ):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.session_id = session_id
        self.api_key = api_key or ""
        self.agent_name = agent_name or ""
        self.session = requests.Session()
        self._current_response = None
        self.session.headers["Content-Type"] = "application/json"
        if api_key:
            self.session.headers["Authorization"] = f"Bearer {api_key}"

    @property
    def chat_url(self) -> str:
        return f"{self.base_url}/v1/chat/completions"

    def chat(self, messages: List[Dict], tools: List[Dict] = None, stream: bool = False,
             new_conversation: bool = False) -> ChatResult:
        """发送对话请求"""
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": stream,
        }
        if self.agent_name:
            payload["user"] = self.agent_name
        if tools:
            payload["tools"] = tools
        if self.session_id:
            payload["session_id"] = self.session_id
        if new_conversation:
            payload["new_conversation"] = True

        try:
            if stream:
                return self._chat_stream(payload)
            else:
                return self._chat_sync(payload)
        except Exception as e:
            logger.error(f"API 调用失败: {e}")
            raise

    def reset_conversation(self):
        self.session_id = None

    def _chat_sync(self, payload: dict) -> ChatResult:
        self._current_response = self.session.post(self.chat_url, json=payload, timeout=300)
        resp = self._current_response
        resp.raise_for_status()
        data = resp.json()

        sid = data.get("session_id")
        if sid and self.session_id != sid:
            self.session_id = sid
            payload["session_id"] = sid

        choice = data["choices"][0]
        msg = choice["message"]

        content = msg.get("content", "")
        tool_calls = msg.get("tool_calls", [])

        if not tool_calls and content:
            # parser.py 负责清理中文 + 提取工具调用
            tool_calls = extract_tool_calls(content)
            if tool_calls:
                content = None

        return ChatResult(content=content, tool_calls=tool_calls)

    def cancel_request(self):
        if self._current_response:
            try:
                self._current_response.close()
            except:
                pass

    def _chat_stream(self, payload: dict) -> ChatResult:
        resp = self.session.post(self.chat_url, json=payload, stream=True, timeout=300)
        resp.raise_for_status()

        content_parts = []
        tool_calls = {}

        for line in resp.iter_lines():
            if not line:
                continue
            line = line.decode("utf-8", errors="replace")
            if not line.startswith("data:"):
                continue
            data_str = line[5:].strip()
            if data_str == "[DONE]":
                break

            try:
                chunk = json.loads(data_str)
            except json.JSONDecodeError:
                continue

            sid = chunk.get("session_id")
            if sid and self.session_id != sid:
                self.session_id = sid

            choice = chunk.get("choices", [{}])[0]
            delta = choice.get("delta", {})

            if delta.get("content"):
                content_parts.append(delta["content"])

            if delta.get("tool_calls"):
                for tc in delta["tool_calls"]:
                    idx = tc.get("index", 0)
                    if idx not in tool_calls:
                        tool_calls[idx] = {"id": "", "name": "", "arguments": ""}
                    if tc.get("id"):
                        tool_calls[idx]["id"] = tc["id"]
                    fn = tc.get("function", {})
                    if fn.get("name"):
                        tool_calls[idx]["name"] = fn["name"]
                    if fn.get("arguments"):
                        tool_calls[idx]["arguments"] += fn["arguments"]

        content = "".join(content_parts) if content_parts else None
        calls = [tool_calls[i] for i in sorted(tool_calls) if tool_calls[i]["name"]]

        return ChatResult(content=content, tool_calls=calls)

    def reset(self) -> dict:
        try:
            resp = self.session.post(f"{self.base_url}/reset", json={}, timeout=10)
            return resp.json()
        except Exception as e:
            return {"success": False, "error": str(e)}

    def status(self) -> dict:
        try:
            resp = self.session.get(f"{self.base_url}/status", timeout=5)
            return resp.json()
        except Exception as e:
            return {"logged_in": False, "error": str(e)}

    def login(self) -> dict:
        try:
            resp = self.session.post(f"{self.base_url}/login", timeout=10)
            return resp.json()
        except Exception as e:
            return {"success": False, "error": str(e)}