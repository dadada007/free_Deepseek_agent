#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通用 OpenAI 兼容 API 网关 完美版 v5.0
======================================
核心设计理念：简洁、健壮、高性能

特性：
- 非流式获取 + 本地模拟流式（稳定可靠）
- 智能重试与连接池管理
- 完整的工具调用支持
- 批量请求聚合
- 7级 session_id 派生
- 完整的 OpenAI 兼容性
"""

import asyncio
import json
import logging
import os
import sys
import time
import uuid
import hashlib
from typing import Any, Dict, List, Optional, Tuple
from contextlib import asynccontextmanager
from dataclasses import dataclass, field

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse, Response
import httpx
import uvicorn

# ============ 日志配置 ============
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("gateway-perfect")

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

# ============ Hermes 工具模块 ============
_HERMES_PATH = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "hermes"))
if _HERMES_PATH not in sys.path:
    sys.path.insert(0, _HERMES_PATH)

try:
    import tools
except ImportError:
    _ALT_PATH = os.path.dirname(os.path.abspath(__file__))
    if _ALT_PATH not in sys.path:
        sys.path.insert(0, _ALT_PATH)
    try:
        import tools
    except ImportError:
        logger.warning("⚠️ 无法导入 tools 模块，/inject 将使用硬编码提示词")
        tools = None

# ============ 集中配置 ============
class Config:
    """统一配置管理"""
    HOST = os.environ.get("API_HOST", "0.0.0.0")
    PORT = int(os.environ.get("API_PORT", sys.argv[1] if len(sys.argv) > 1 else "8003"))
    UPSTREAM_URL = os.environ.get("UPSTREAM_URL", "http://127.0.0.1:8002").rstrip("/")
    UPSTREAM_MODEL = os.environ.get("UPSTREAM_MODEL", "deepseek-browser")
    UPSTREAM_API_KEY = os.environ.get("UPSTREAM_API_KEY", "sk-admin")

    # 超时配置
    REQUEST_TIMEOUT = float(os.environ.get("REQUEST_TIMEOUT", "300"))
    STREAM_READ_TIMEOUT = float(os.environ.get("STREAM_READ_TIMEOUT", "120"))
    CONNECT_TIMEOUT = float(os.environ.get("CONNECT_TIMEOUT", "10.0"))
    POOL_TIMEOUT = float(os.environ.get("POOL_TIMEOUT", "5.0"))

    # 重试配置
    RETRIES = int(os.environ.get("RETRIES", "2"))
    RETRY_DELAY = float(os.environ.get("RETRY_DELAY", "0.5"))
    MAX_REQUEST_SIZE = int(os.environ.get("MAX_REQUEST_SIZE", str(10 * 1024 * 1024)))

    # 限流
    RATE_LIMIT_PER_MINUTE = int(os.environ.get("RATE_LIMIT_PER_MINUTE", "0"))

    # 连接池
    MAX_CONNECTIONS = int(os.environ.get("MAX_CONNECTIONS", "100"))
    MAX_KEEPALIVE = int(os.environ.get("MAX_KEEPALIVE", "20"))
    KEEPALIVE_EXPIRY = int(os.environ.get("KEEPALIVE_EXPIRY", "30"))

    # 模型映射
    MODEL_MAPPING: Dict[str, str] = {}
    _mm = os.environ.get("MODEL_MAPPING", "")
    if _mm.strip():
        try:
            MODEL_MAPPING = json.loads(_mm)
        except Exception as e:
            logger.warning(f"MODEL_MAPPING 解析失败: {e}")
    ADVERTISE_MODELS = [m.strip() for m in os.environ.get("ADVERTISE_MODELS", "").split(",") if m.strip()]
    ACCEPT_ALL_MODELS = os.environ.get("ACCEPT_ALL_MODELS", "true").lower() == "true"

    # 鉴权
    _API_KEYS = [
        k.strip() for k in
        (os.environ.get("HERMES_API_KEY", "") + "," + os.environ.get("API_KEYS", ""))
        .split(",")
        if k.strip()
    ]
    PUBLIC_PATHS = {"/", "/health", "/docs", "/redoc", "/openapi.json", "/favicon.ico"}

    # 批量聚合
    BATCH_ENABLED = os.environ.get("BATCH_ENABLED", "false").lower() == "true"
    BATCH_INITIAL_WAIT = float(os.environ.get("BATCH_INITIAL_WAIT", "3.0"))
    BATCH_EXTEND_WAIT = float(os.environ.get("BATCH_EXTEND_WAIT", "2.0"))
    BATCH_MAX_WAIT = float(os.environ.get("BATCH_MAX_WAIT", "4.0"))
    BATCH_MAX_MESSAGES = int(os.environ.get("BATCH_MAX_MESSAGES", "50"))


config = Config()

# ============ 限流器 ============
class RateLimiter:
    """简单高效的限流器"""
    def __init__(self, max_requests: int, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests: Dict[str, List[float]] = {}
        self._lock = asyncio.Lock()

    async def is_allowed(self, key: str) -> bool:
        if self.max_requests <= 0:
            return True
        async with self._lock:
            now = time.time()
            records = self._requests.get(key, [])
            # 清理过期记录
            records = [t for t in records if now - t < self.window_seconds]
            if len(records) >= self.max_requests:
                return False
            records.append(now)
            self._requests[key] = records
            return True


rate_limiter = RateLimiter(config.RATE_LIMIT_PER_MINUTE)

# ============ 工具函数 ============
def _estimate_tokens(text: str) -> int:
    """估算 token 数量"""
    if not text:
        return 0
    chinese = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
    return int(chinese / 1.5 + (len(text) - chinese) / 4)


def _openai_error(message: str, type_: str = "api_error", status: int = 500, code: str = None) -> JSONResponse:
    return JSONResponse(
        content={"error": {"message": message, "type": type_, "param": None, "code": code}},
        status_code=status,
    )


def _extract_token(request: Request) -> str:
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        return auth[7:].strip()
    if auth.strip():
        return auth.strip()
    return (
        request.headers.get("x-api-key", "")
        or request.headers.get("api-key", "")
        or request.query_params.get("api_key", "")
    )


def _extract_client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _normalize_content(content: Any) -> str:
    """归一化消息内容，支持 vision 数组"""
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts, has_image = [], False
        for p in content:
            if not isinstance(p, dict):
                continue
            if p.get("type") == "text" and p.get("text"):
                parts.append(str(p["text"]))
            elif p.get("type") in ("image_url", "image"):
                has_image = True
                try:
                    img = p.get("image_url", {})
                    u = img.get("url") if isinstance(img, dict) else None
                except Exception:
                    u = None
                parts.append(f"[图片: {u}]" if u else "[图片]")
        text = "\n".join(x for x in parts if x).strip()
        return text if text else ("[图片]" if has_image else "")
    return str(content)


def _normalize_messages(messages: List[dict]) -> List[dict]:
    """归一化消息列表"""
    out = []
    for m in messages or []:
        if not isinstance(m, dict):
            continue
        m = dict(m)
        role = (m.get("role") or "user").lower().strip()
        if role == "developer":
            role = "system"
        elif role == "function":
            role = "tool"
        m["role"] = role
        m["content"] = _normalize_content(m.get("content"))
        if m.get("content") or role in ("assistant", "tool") or m.get("tool_calls"):
            out.append(m)
    return out


def _normalize_tools(body: dict) -> dict:
    """归一化工具/函数定义"""
    body = dict(body)
    if not body.get("tools") and body.get("functions"):
        body["tools"] = [
            {"type": "function", "function": f} for f in body.pop("functions") if isinstance(f, dict)
        ]
    if not body.get("tool_choice") and body.get("function_call"):
        body["tool_choice"] = body.pop("function_call")
    return body


def _resolve_model(requested: Optional[str]) -> str:
    if not requested:
        return config.UPSTREAM_MODEL
    return config.MODEL_MAPPING.get(requested, requested)


def _apply_model(obj: dict, model: str) -> dict:
    if model and isinstance(obj, dict):
        obj["model"] = model
    return obj


def _first_user_text(messages: List[dict]) -> str:
    for m in messages or []:
        if isinstance(m, dict) and m.get("role") in ("user", "tool"):
            c = m.get("content")
            if isinstance(c, str) and c.strip():
                return c.strip()
    return ""


def _generate_session_id(request: Request, body: dict, messages: List[dict]) -> str:
    """7级 session_id 派生"""
    if body.get("session_id"):
        return str(body["session_id"])
    if body.get("user"):
        stable = hashlib.md5(str(body["user"]).encode("utf-8")).hexdigest()[:16]
        return f"user-{stable}"
    user_id = request.headers.get("X-User-ID") or request.headers.get("x-user-id")
    if user_id:
        stable = hashlib.md5(str(user_id).encode("utf-8")).hexdigest()[:16]
        return f"user-{stable}"
    conv = request.headers.get("X-Conversation") or request.headers.get("x-conversation")
    if conv:
        return f"conv-{hashlib.md5(conv.encode("utf-8")).hexdigest()[:16]}"
    auth = request.headers.get("Authorization", "")
    first_user = _first_user_text(messages)
    if auth and first_user:
        stable = hashlib.md5(f"{auth}|{first_user[:80]}".encode("utf-8")).hexdigest()[:16]
        return f"auth-{stable}"
    if first_user:
        stable = hashlib.md5(first_user[:100].encode("utf-8")).hexdigest()[:16]
        return f"fp-{stable}"
    return f"req-{uuid.uuid4().hex[:12]}"


def _sse(data: Any) -> str:
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"


def _chunk_with(src: dict, delta: dict, finish: Optional[str] = None) -> dict:
    """构建 SSE chunk"""
    out = dict(src)
    choices = []
    for c in src.get("choices") or []:
        choice = dict(c)
        choice["delta"] = delta
        if finish is not None:
            choice["finish_reason"] = finish
        choices.append(choice)
    out["choices"] = choices
    return out


def _split_tool_calls(obj: dict) -> List[dict]:
    """拆分 tool_calls 为增量格式"""
    choices = obj.get("choices")
    if not choices:
        return [obj]
    delta = choices[0].get("delta") or {}
    tcs = delta.get("tool_calls")
    if not tcs:
        return [obj]
    if any(isinstance(tc, dict) and tc.get("index") is not None for tc in tcs):
        return [obj]
    
    out = []
    for idx, tc in enumerate(tcs):
        if not isinstance(tc, dict):
            continue
        fn = tc.get("function") or {}
        call_id = tc.get("id") or f"call_{uuid.uuid4().hex[:8]}"
        out.append(_chunk_with(obj, {
            "role": "assistant",
            "content": None,
            "tool_calls": [{
                "index": idx,
                "id": call_id,
                "type": "function",
                "function": {"name": fn.get("name") or "", "arguments": ""},
            }],
        }))
        args = fn.get("arguments")
        if args:
            out.append(_chunk_with(obj, {
                "tool_calls": [{"index": idx, "function": {"arguments": args}}],
            }))
    return out or [obj]


def _smart_chunks(text: str, chunk_size: int = 8) -> List[str]:
    """智能切分文本"""
    if not text:
        return []
    chunks = []
    i = 0
    n = len(text)
    while i < n:
        if i + chunk_size >= n:
            chunks.append(text[i:])
            break
        break_at = i + chunk_size
        for j in range(min(i + chunk_size + 4, n - 1), i + chunk_size - 4, -1):
            if j <= i:
                break
            if text[j] in " \t\n，。！？；：,.!?;:：":
                break_at = j + 1
                break
        chunks.append(text[i:break_at])
        i = break_at
    return chunks


def _usage_state(text: str, args: str, body: dict) -> dict:
    """计算 usage"""
    prompt_text = "".join((m.get("content") or "") for m in (body.get("messages") or []))
    usage = {
        "prompt_tokens": _estimate_tokens(prompt_text),
        "completion_tokens": _estimate_tokens(text) + _estimate_tokens(args),
    }
    usage["total_tokens"] = usage["prompt_tokens"] + usage["completion_tokens"]
    return usage

# ============ HTTP 客户端管理 ============
class HTTPClientManager:
    """高性能 HTTP 客户端管理器"""
    def __init__(self):
        self._client: Optional[httpx.AsyncClient] = None
        self._lock = asyncio.Lock()

    async def get_client(self) -> httpx.AsyncClient:
        async with self._lock:
            if self._client is None or self._client.is_closed:
                self._client = httpx.AsyncClient(
                    timeout=httpx.Timeout(
                        config.REQUEST_TIMEOUT,
                        read=config.STREAM_READ_TIMEOUT,
                        connect=config.CONNECT_TIMEOUT,
                        pool=config.POOL_TIMEOUT,
                    ),
                    limits=httpx.Limits(
                        max_connections=config.MAX_CONNECTIONS,
                        max_keepalive_connections=config.MAX_KEEPALIVE,
                        keepalive_expiry=config.KEEPALIVE_EXPIRY,
                    ),
                    follow_redirects=True,
                    headers={"User-Agent": "OpenAI-Gateway/5.0"},
                )
                logger.debug("HTTP 客户端已创建")
            return self._client

    async def close(self):
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None


client_manager = HTTPClientManager()


def _build_headers(request: Request = None, body: dict = None) -> Dict[str, str]:
    """构建请求头"""
    headers = {}
    if request:
        for name in ("Authorization", "X-API-Key", "api-key", "x-api-key", "X-User-ID", "x-user-id", "X-Conversation"):
            if v := request.headers.get(name):
                headers[name] = v
    if body:
        hdrs = body.get("_headers")
        if isinstance(hdrs, dict):
            for name in ("Authorization", "X-API-Key", "api-key", "x-api-key", "X-User-ID", "x-user-id", "X-Conversation"):
                if hdrs.get(name):
                    headers[name] = hdrs[name]
    if not headers.get("Authorization"):
        if config._API_KEYS:
            headers["Authorization"] = f"Bearer {config._API_KEYS[0]}"
        elif config.UPSTREAM_API_KEY:
            headers["Authorization"] = f"Bearer {config.UPSTREAM_API_KEY}"
    return headers


async def _upstream_request(
    method: str,
    path: str,
    json_body: dict = None,
    params: dict = None,
    headers: dict = None,
) -> httpx.Response:
    """发请求到上游，带智能重试"""
    client = await client_manager.get_client()
    url = f"{config.UPSTREAM_URL}{path}"
    last_err: Exception = None
    
    # 流式请求不重试（由上层处理）
    max_retries = 0 if (json_body and json_body.get("stream")) else config.RETRIES
    
    for attempt in range(max_retries + 1):
        try:
            resp = await client.request(
                method, url,
                json=json_body,
                params=params,
                headers=headers or {},
            )
            
            # 可重试的错误
            if resp.status_code >= 500 and attempt < max_retries:
                delay = config.RETRY_DELAY * (attempt + 1)
                logger.warning(f"上游 {resp.status_code} 错误，{delay}s 后重试 (尝试 {attempt + 1}/{max_retries})")
                await asyncio.sleep(delay)
                continue
            
            return resp
            
        except (httpx.ConnectError, httpx.ConnectTimeout, httpx.TimeoutException) as e:
            last_err = e
            if attempt < max_retries:
                delay = config.RETRY_DELAY * (attempt + 1) * 2
                logger.warning(f"连接失败: {e}，{delay}s 后重试 (尝试 {attempt + 1}/{max_retries})")
                await asyncio.sleep(delay)
                continue
            break
        except Exception as e:
            last_err = e
            if attempt < max_retries:
                await asyncio.sleep(config.RETRY_DELAY * (attempt + 1))
                continue
            break
    
    error_msg = f"上游服务不可用: {str(last_err) if last_err else '连接失败'}"
    logger.error(error_msg)
    body = {"error": {"message": error_msg, "type": "api_error", "param": None, "code": "upstream_unavailable"}}
    return httpx.Response(status_code=502, content=json.dumps(body).encode("utf-8"))

# ============ 批量聚合 ============
@dataclass
class PendingBatch:
    client_id: str
    session_id: str
    messages: List[Dict[str, Any]] = field(default_factory=list)
    responses: List[asyncio.Future] = field(default_factory=list)
    request_bodies: List[Dict[str, Any]] = field(default_factory=list)
    first_request_time: float = field(default_factory=time.time)
    last_request_time: float = field(default_factory=time.time)
    is_processing: bool = False
    task: Optional[asyncio.Task] = None

    def add_request(self, body: Dict[str, Any], response_future: asyncio.Future):
        for m in body.get("messages") or []:
            if isinstance(m, dict) and m.get("content"):
                self.messages.append(dict(m))
        self.request_bodies.append(body)
        self.responses.append(response_future)
        self.last_request_time = time.time()

    def should_send(self, current_time: float) -> bool:
        elapsed = current_time - self.first_request_time
        if elapsed >= config.BATCH_MAX_WAIT:
            return True
        if len(self.messages) >= config.BATCH_MAX_MESSAGES:
            return True
        if current_time - self.last_request_time >= config.BATCH_EXTEND_WAIT and elapsed >= config.BATCH_INITIAL_WAIT:
            return True
        return False


class BatchAggregator:
    """批量请求聚合器"""
    def __init__(self):
        self._pending_batches: Dict[str, PendingBatch] = {}
        self._lock = asyncio.Lock()

    def _get_client_id(self, request: Request, session_id: str) -> str:
        token = _extract_token(request)
        client_ip = request.client.host if request.client else "unknown"
        if token:
            return f"sess:{session_id}:key:{token[:16]}:{client_ip}"
        return f"sess:{session_id}:ip:{client_ip}"

    def _should_batch(self, body: dict) -> bool:
        if not config.BATCH_ENABLED:
            return False
        if body.get("stream"):
            return False
        if body.get("disable_batch"):
            return False
        if body.get("tools") or body.get("functions") or body.get("tool_choice"):
            return False
        return len(body.get("messages") or []) <= 2

    async def process_request(self, request: Request, body: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if not self._should_batch(body):
            return None
        
        session_id = body.get("session_id")
        if not session_id:
            messages = _normalize_messages(body.get("messages"))
            session_id = _generate_session_id(request, body, messages)
        
        client_id = self._get_client_id(request, session_id)
        response_future = asyncio.get_event_loop().create_future()

        start_task = False
        async with self._lock:
            batch = self._pending_batches.get(client_id)
            if batch is None:
                batch = PendingBatch(client_id=client_id, session_id=session_id)
                self._pending_batches[client_id] = batch
                start_task = True
            batch.add_request(body, response_future)

        if start_task:
            batch.task = asyncio.create_task(self._process_batch(client_id))

        try:
            return await asyncio.wait_for(response_future, timeout=config.BATCH_MAX_WAIT + 5)
        except asyncio.TimeoutError:
            logger.warning(f"批量请求超时: {client_id}")
            return {"error": {"message": "batch aggregation timeout", "type": "api_error"}}

    async def _process_batch(self, client_id: str):
        try:
            while True:
                await asyncio.sleep(0.1)
                async with self._lock:
                    batch = self._pending_batches.get(client_id)
                    if batch is None:
                        return
                    if batch.should_send(time.time()):
                        batch.is_processing = True
                        self._pending_batches.pop(client_id, None)
                        bodies = batch.request_bodies.copy()
                        futures = batch.responses.copy()
                        break

            result = await self._execute_batch(bodies)
            for fut in futures:
                if not fut.done():
                    fut.set_result(result)
        except asyncio.CancelledError:
            raise
        except Exception as e:
            logger.error(f"批量处理异常: {e}", exc_info=True)
            async with self._lock:
                batch = self._pending_batches.pop(client_id, None)
                if batch:
                    for fut in batch.responses:
                        if not fut.done():
                            fut.set_result({"error": {"message": str(e), "type": "api_error"}})

    async def _execute_batch(self, bodies: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not bodies:
            return {"error": {"message": "没有有效的消息", "type": "api_error"}}
        
        base = bodies[0]
        merged_messages = []
        for body in bodies:
            for m in (body.get("messages") or []):
                if isinstance(m, dict) and m.get("content"):
                    merged_messages.append(dict(m))

        payload = {
            "model": _resolve_model(base.get("model") or config.UPSTREAM_MODEL),
            "messages": merged_messages,
            "stream": False,
        }
        for k in ("temperature", "max_tokens", "top_p", "stop"):
            if base.get(k) is not None:
                payload[k] = base[k]
        if base.get("session_id"):
            payload["session_id"] = base["session_id"]
        if base.get("user"):
            payload["user"] = base["user"]

        try:
            resp = await _upstream_request(
                "POST", "/v1/chat/completions",
                json_body=payload,
                headers=_build_headers(body=base)
            )
            data = resp.json() if resp.status_code < 400 else {}
            if resp.status_code >= 400:
                err = data.get("error", {}) if isinstance(data, dict) else {}
                return {"error": {"message": err.get("message", f"上游错误 {resp.status_code}"), "type": "api_error"}}
            return self._format_response(data, base.get("model") or config.UPSTREAM_MODEL, merged_messages, len(bodies))
        except Exception as e:
            logger.error(f"执行批量请求失败: {e}")
            return {"error": {"message": str(e), "type": "api_error"}}

    def _format_response(self, data: Dict[str, Any], model: str, messages: List[dict], count: int) -> Dict[str, Any]:
        data = dict(data)
        if not data.get("choices"):
            text = str(data.get("content") or data.get("answer") or data.get("reply") or "")
            data["choices"] = [{"index": 0, "message": {"role": "assistant", "content": text},
                                "finish_reason": "stop", "logprobs": None}]
        for c in data.get("choices") or []:
            if not isinstance(c, dict):
                continue
            msg = c.get("message")
            if not isinstance(msg, dict):
                msg = {"content": str(msg) if msg else ""}
                c["message"] = msg
            msg.setdefault("role", "assistant")
            msg.setdefault("content", "")
            if c.get("finish_reason") is None:
                c["finish_reason"] = "tool_calls" if msg.get("tool_calls") else "stop"
            c.setdefault("logprobs", None)
        data["model"] = model
        if "usage" not in data or not isinstance(data.get("usage"), dict):
            prompt_text = "".join((m.get("content") or "") for m in messages)
            completion_text = (data.get("choices") or [{}])[0].get("message", {}).get("content") or ""
            data["usage"] = {
                "prompt_tokens": _estimate_tokens(prompt_text),
                "completion_tokens": _estimate_tokens(completion_text),
                "total_tokens": _estimate_tokens(prompt_text + completion_text),
            }
        data["batch_info"] = {"merged_count": count, "total_messages": len(messages)}
        return data


batch_aggregator = BatchAggregator()

# ============ FastAPI ============
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"🚀 启动通用 OpenAI 兼容网关 完美版 v5.0")
    logger.info(f"   上游: {config.UPSTREAM_URL}  模型: {config.UPSTREAM_MODEL}")
    logger.info(f"   鉴权: {'开启' if config._API_KEYS else '关闭'}")
    logger.info(f"   重试: {config.RETRIES} 次  批量聚合: {'开启' if config.BATCH_ENABLED else '关闭'}")
    
    # 健康检查
    try:
        client = await client_manager.get_client()
        resp = await client.get(f"{config.UPSTREAM_URL}/health", timeout=5.0)
        if resp.status_code == 200:
            logger.info("✅ 上游服务健康检查通过")
        else:
            logger.warning(f"⚠️ 上游服务健康检查返回 {resp.status_code}")
    except Exception as e:
        logger.warning(f"⚠️ 上游服务健康检查失败: {e}")
    
    yield
    await client_manager.close()
    logger.info("🛑 网关已关闭")


app = FastAPI(
    title="Universal OpenAI Compatible API Gateway Perfect",
    version="5.0.0",
    description="完美版 OpenAI 兼容网关",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============ 中间件 ============
@app.middleware("http")
async def auth_and_logging_middleware(request: Request, call_next):
    start_time = time.time()

    # 鉴权
    if config._API_KEYS and request.url.path not in config.PUBLIC_PATHS:
        token = _extract_token(request)
        if not token or token not in config._API_KEYS:
            logger.warning(f"鉴权失败: {_extract_client_ip(request)} {request.url.path}")
            return JSONResponse(
                content={"error": {"message": "Invalid API key", "type": "invalid_request_error",
                                   "param": None, "code": "invalid_api_key"}},
                status_code=401,
            )

    # 限流
    if request.url.path not in config.PUBLIC_PATHS:
        if not await rate_limiter.is_allowed(_extract_client_ip(request)):
            logger.warning(f"限流触发: {_extract_client_ip(request)}")
            return JSONResponse(
                content={"error": {"message": "Rate limit exceeded", "type": "rate_limit_error",
                                   "param": None, "code": "rate_limit_exceeded"}},
                status_code=429,
            )

    try:
        response = await call_next(request)
    except Exception as e:
        logger.exception(f"未处理异常: {e}")
        response = _openai_error("Internal server error", "api_error", 500)

    duration = time.time() - start_time
    if response is not None:
        logger.info(f"{request.method} {request.url.path} - {response.status_code} - {duration:.2f}s")
    return response

# ============ 信息端点 ============
def _all_models() -> List[str]:
    models = {config.UPSTREAM_MODEL}
    models.update(config.ADVERTISE_MODELS)
    models.update(config.MODEL_MAPPING.keys())
    models.update(config.MODEL_MAPPING.values())
    return sorted(models)


@app.get("/")
async def root():
    return {
        "service": "Universal OpenAI Compatible API Gateway Perfect",
        "version": "5.0.0",
        "upstream": config.UPSTREAM_URL,
        "status": "running",
        "openai_compatible": True,
        "features": {
            "tool_calls": True,
            "streaming": True,
            "batch_aggregation": config.BATCH_ENABLED,
            "session_management": "7-level",
        },
        "models": _all_models(),
        "endpoints": [
            "POST /v1/chat/completions",
            "GET  /v1/models",
            "GET  /status", "GET  /health",
            "POST /login", "POST /reset",
            "GET  /sessions", "GET  /screenshot", "GET  /inject",
        ],
    }


@app.get("/status")
async def status():
    data = {
        "logged_in": False,
        "active_sessions": 0,
        "model": config.UPSTREAM_MODEL,
        "upstream": config.UPSTREAM_URL,
        "upstream_ok": False,
        "api_keys_configured": bool(config._API_KEYS),
        "pending_batches": len(batch_aggregator._pending_batches),
    }
    try:
        resp = await client_manager.get_client().get(f"{config.UPSTREAM_URL}/status", timeout=8)
        if resp.status_code == 200:
            up = resp.json()
            up.pop("api_keys_configured", None)
            data.update(up)
            data["upstream_ok"] = True
    except Exception as e:
        data["upstream_error"] = str(e)
    return data


@app.get("/health")
async def health():
    st = await status()
    return {"status": "ok" if st.get("upstream_ok") else "degraded", **st}

# ============ 模型端点 ============
@app.get("/v1/models")
async def list_models():
    data = [{"id": m, "object": "model", "created": 1700000000, "owned_by": "deepseek-browser"}
            for m in _all_models()]
    try:
        resp = await client_manager.get_client().get(f"{config.UPSTREAM_URL}/v1/models", timeout=8)
        if resp.status_code == 200:
            seen = {d["id"] for d in data}
            for item in (resp.json().get("data") or []):
                if isinstance(item, dict) and item.get("id") not in seen:
                    data.append(item)
                    seen.add(item["id"])
    except Exception:
        pass
    return {"object": "list", "data": data}


@app.get("/v1/models/{model_id}")
async def get_model(model_id: str):
    known = _all_models()
    if model_id in known or config.ACCEPT_ALL_MODELS:
        return {"id": model_id, "object": "model", "created": 1700000000,
                "owned_by": "deepseek-browser", "mapped_to": _resolve_model(model_id)}
    return _openai_error(f"Model '{model_id}' not found", "invalid_request_error", 404, "model_not_found")

# ============ 聊天核心 ============
async def _read_body(request: Request) -> Optional[dict]:
    try:
        return await request.json()
    except Exception:
        return None


def _build_payload(body: dict, messages: List[dict]) -> dict:
    """构建上游请求 payload"""
    payload = _normalize_tools(body)
    payload["messages"] = messages
    payload["model"] = _resolve_model(body.get("model") or config.UPSTREAM_MODEL)
    payload["session_id"] = body.get("session_id")
    if body.get("user"):
        payload["user"] = body["user"]
    if body.get("new_conversation"):
        payload["new_conversation"] = True
    if body.get("tools"):
        payload["tools"] = body["tools"]
    if body.get("tool_choice"):
        payload["tool_choice"] = body["tool_choice"]
    for k in ("temperature", "top_p", "max_tokens", "stop"):
        if body.get(k) is not None:
            payload[k] = body[k]
    payload.pop("_headers", None)
    payload.pop("functions", None)
    payload.pop("function_call", None)
    return payload


@app.post("/v1/chat/completions")
@app.post("/chat/completions")
async def chat_completions(request: Request):
    body = await _read_body(request)
    if body is None:
        return _openai_error("Invalid JSON in request body", "invalid_request_error", 400)
    if not isinstance(body, dict):
        return _openai_error("Request body must be a JSON object", "invalid_request_error", 400)

    # 请求大小检查
    try:
        if len(json.dumps(body)) > config.MAX_REQUEST_SIZE:
            return _openai_error(
                f"Request too large. Maximum size is {config.MAX_REQUEST_SIZE} bytes",
                "invalid_request_error", 413, "request_too_large")
    except Exception:
        pass

    body["_headers"] = _build_headers(request, body)

    messages = _normalize_messages(body.get("messages"))
    if not messages:
        prompt = body.get("prompt") or body.get("input") or body.get("message") or ""
        if isinstance(prompt, list):
            prompt = _normalize_content(prompt)
        messages = [{"role": "user", "content": str(prompt)}]

    session_id = _generate_session_id(request, body, messages)
    body["session_id"] = session_id
    requested = body.get("model") or config.UPSTREAM_MODEL

    # 非流式：尝试批量聚合
    if not body.get("stream"):
        try:
            batched = await batch_aggregator.process_request(request, body)
            if batched is not None:
                if "error" in batched:
                    err = batched["error"]
                    return _openai_error(err.get("message", "Unknown error"), "api_error", 400)
                batched.setdefault("session_id", session_id)
                return JSONResponse(content=batched)
        except Exception as e:
            logger.warning(f"批量聚合降级: {e}")

    # 流式：使用本地模拟流式（稳定可靠）
    if body.get("stream"):
        return StreamingResponse(
            _stream_chat(body, requested),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    # 非流式（未聚合）
    resp = await _upstream_request(
        "POST", "/v1/chat/completions",
        json_body=_build_payload(body, messages),
        headers=_build_headers(body=body)
    )
    try:
        data = resp.json()
    except Exception:
        return _openai_error(f"Invalid JSON from upstream: {resp.text[:200]}", "api_error", 502)

    if resp.status_code >= 400:
        if isinstance(data, dict) and isinstance(data.get("error"), dict):
            return JSONResponse(content={"error": data["error"]}, status_code=resp.status_code)
        return _openai_error(str(data)[:300], "api_error", resp.status_code)

    if not isinstance(data, dict):
        return _openai_error("Invalid upstream response", "api_error", 502)

    data = _apply_model(data, requested)
    data["session_id"] = session_id

    # 归一化响应
    if not data.get("choices"):
        text = str(data.get("content") or data.get("answer") or data.get("reply") or "")
        data["choices"] = [{"index": 0, "message": {"role": "assistant", "content": text},
                            "finish_reason": "stop", "logprobs": None}]
    for c in data.get("choices") or []:
        if not isinstance(c, dict):
            continue
        msg = c.get("message")
        if not isinstance(msg, dict):
            msg = {"content": str(msg) if msg else ""}
            c["message"] = msg
        msg.setdefault("role", "assistant")
        msg.setdefault("content", "")
        if c.get("finish_reason") is None:
            c["finish_reason"] = "tool_calls" if msg.get("tool_calls") else "stop"
        c.setdefault("logprobs", None)

    if "usage" not in data or not isinstance(data.get("usage"), dict):
        prompt_text = "".join((m.get("content") or "") for m in messages)
        completion_text = (data.get("choices") or [{}])[0].get("message", {}).get("content") or ""
        data["usage"] = {
            "prompt_tokens": _estimate_tokens(prompt_text),
            "completion_tokens": _estimate_tokens(completion_text),
            "total_tokens": _estimate_tokens(prompt_text + completion_text),
        }

    return JSONResponse(content=data)

# ============ 流式处理（完美版：非流式获取 + 本地模拟） ============
async def _stream_chat(body: dict, requested: str):
    """稳定可靠的流式响应：获取完整结果后本地模拟 SSE"""
    include_usage = False
    so = body.get("stream_options")
    if isinstance(so, dict) and so.get("include_usage"):
        include_usage = True

    payload = _build_payload(body, _normalize_messages(body.get("messages")))
    payload["stream"] = False  # 关键：不使用上游流式
    payload.pop("stream_options", None)

    logger.info(f"📡 流式请求: 非流式获取 + 本地模拟 (model={requested})")

    try:
        resp = await _upstream_request(
            "POST", "/v1/chat/completions",
            json_body=payload,
            headers=_build_headers(body=body),
        )
        if resp.status_code >= 400:
            try:
                err = resp.json()
            except Exception:
                err = {"message": f"Upstream error {resp.status_code}"}
            yield _sse({"error": err.get("error", err), "session_id": body.get("session_id")})
            yield "data: [DONE]\n\n"
            return
        data = resp.json()
    except Exception as e:
        logger.error(f"流式请求上游失败: {e}")
        yield _sse({"error": {"message": str(e), "type": "api_error"}, "session_id": body.get("session_id")})
        yield "data: [DONE]\n\n"
        return

    choices = data.get("choices") or []
    message = choices[0].get("message", {}) if choices else {}
    content = message.get("content") or ""
    tool_calls = message.get("tool_calls") or []
    session_id = data.get("session_id", body.get("session_id"))

    resp_id = data.get("id", f"chatcmpl-{uuid.uuid4().hex[:24]}")
    created = data.get("created", int(time.time()))

    chunk_base = {
        "id": resp_id,
        "object": "chat.completion.chunk",
        "created": created,
        "model": requested,
        "session_id": session_id,
    }

    collected_text = ""
    collected_args = ""

    # 发送角色块
    yield _sse(_chunk_with(chunk_base, {"role": "assistant", "content": ""}))

    if tool_calls:
        # 拆分成增量格式发送
        for idx, tc in enumerate(tool_calls):
            call_id = tc.get("id", f"call_{uuid.uuid4().hex[:8]}")
            fn = tc.get("function", {})
            fn_name = fn.get("name", "")
            fn_args = fn.get("arguments", "")

            # 发送 id + name
            yield _sse(_chunk_with(chunk_base, {
                "tool_calls": [{
                    "index": idx, "id": call_id, "type": "function",
                    "function": {"name": fn_name, "arguments": ""},
                }]
            }))

            # 发送 arguments（智能切分）
            if fn_args:
                for piece in _smart_chunks(fn_args, chunk_size=40):
                    yield _sse(_chunk_with(chunk_base, {
                        "tool_calls": [{"index": idx, "function": {"arguments": piece}}]
                    }))
                    collected_args += piece
                    await asyncio.sleep(0.01)

        # 结束
        yield _sse(_chunk_with(chunk_base, {}, finish="tool_calls"))
    else:
        # 普通文本流式：智能切分
        for piece in _smart_chunks(str(content), chunk_size=6):
            yield _sse(_chunk_with(chunk_base, {"content": piece}))
            collected_text += piece
            await asyncio.sleep(0.01)

        yield _sse(_chunk_with(chunk_base, {}, finish="stop"))

    # include_usage
    if include_usage:
        usage = _usage_state(collected_text, collected_args, body)
        yield _sse({**chunk_base, "choices": [], "usage": usage})

    yield "data: [DONE]\n\n"

# ============ 管理端点 ============
@app.post("/login")
@app.post("/v1/login")
async def login(request: Request):
    try:
        resp = await _upstream_request("POST", "/login", headers=_build_headers(request))
        return JSONResponse(content=resp.json(), status_code=resp.status_code)
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.post("/reset")
async def reset(request: Request):
    body = await _read_body(request) or {}
    params = {"session_id": body.get("session_id") or request.query_params.get("session_id")}
    params = {k: v for k, v in params.items() if v}
    try:
        resp = await _upstream_request("POST", "/reset", params=params or None, headers=_build_headers(request))
        return JSONResponse(content=resp.json(), status_code=resp.status_code)
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.get("/sessions")
@app.get("/v1/sessions")
async def list_sessions(request: Request):
    try:
        resp = await _upstream_request("GET", "/sessions", headers=_build_headers(request))
        return JSONResponse(content=resp.json(), status_code=resp.status_code)
    except Exception as e:
        return {"sessions": [], "total": 0, "error": str(e)}


@app.delete("/v1/sessions/{session_id}")
@app.post("/v1/sessions/{session_id}/clear")
async def delete_session(session_id: str, request: Request):
    try:
        resp = await _upstream_request(
            "POST", "/session/clear", params={"session_id": session_id}, headers=_build_headers(request))
        return JSONResponse(content=resp.json(), status_code=resp.status_code)
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.get("/screenshot")
@app.get("/v1/screenshot")
async def screenshot(request: Request):
    try:
        resp = await _upstream_request("GET", "/screenshot", headers=_build_headers(request))
        return Response(
            content=resp.content,
            media_type=resp.headers.get("content-type", "image/png"),
            headers={"Cache-Control": "no-cache"}
        )
    except Exception as e:
        return _openai_error(str(e), "api_error", 500)


@app.get("/inject")
async def inject(request: Request):
    session_id = request.query_params.get("session_id")

    # 尝试使用 tools 模块
    prompt = None
    if tools is not None:
        try:
            prompt = tools.build_system_prompt()
        except Exception as e:
            logger.warning(f"使用 tools.build_system_prompt() 失败: {e}")

    if prompt is None:
        prompt = (
            "【系统指令】你是一个本地运行的软件工程 AI 助手 Hermes。\n"
            "需要操作文件、执行命令时，请输出 JSON 数组格式的工具调用，例如：\n"
            '[{"name": "write_file", "arguments": {"file_path": "a.py", "content": "..."}}]\n'
            "工具结果会以\"工具结果\"形式返回给你。\n"
            "可用工具：read_file, write_file, list_dir, terminal, web_fetch, "
            "delete_file, rename_file, append_file, edit_file, run_background, "
            "task_output, kill_task, glob, grep, calculate, get_time, "
            "todo_add, todo_start, todo_complete, todo_list"
        )

    try:
        params = {"session_id": session_id, "prompt": prompt} if session_id else {"prompt": prompt}
        params = {k: v for k, v in params.items() if v}

        resp = await _upstream_request("GET", "/inject", params=params or None, headers=_build_headers(request))

        result = resp.json() if resp.status_code == 200 else {}
        if resp.status_code == 200:
            tool_count = len(tools.TOOLS) if tools is not None and hasattr(tools, "TOOLS") else 0
            result.update({
                "prompt_length": len(prompt),
                "tool_count": tool_count,
                "using_tools_module": tools is not None,
            })

        return JSONResponse(content=result, status_code=resp.status_code)

    except Exception as e:
        logger.error(f"/inject 转发失败: {e}")
        return JSONResponse(
            content={
                "success": False,
                "error": str(e),
                "prompt_length": len(prompt),
                "fallback": tools is None
            },
            status_code=500
        )

# ============ 错误处理 ============
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"message": str(exc.detail), "type": "http_error", "param": None, "code": None}}
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception(f"未处理异常: {exc}")
    return _openai_error("Internal server error", "api_error", 500)

# ============ 启动 ============
if __name__ == "__main__":
    print("=" * 60)
    print("🌐 通用 OpenAI 兼容 API 网关 完美版 v5.0")
    print("=" * 60)
    print(f"📌 http://{config.HOST}:{config.PORT}")
    print(f"🔗 上游后端: {config.UPSTREAM_URL}")
    print(f"🔑 鉴权: {'开启' if config._API_KEYS else '关闭'}")
    print(f"🔄 重试: {config.RETRIES} 次")
    print(f"📦 批量聚合: {'开启' if config.BATCH_ENABLED else '关闭'}")
    print("=" * 60)
    uvicorn.run(app, host=config.HOST, port=config.PORT, log_level="info")