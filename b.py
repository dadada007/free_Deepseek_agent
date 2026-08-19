#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DeepSeek Browser API - OpenAI 兼容代理 终极版 v10.4 (简化稳定性修复)
================================================================
修复内容：
- 移除复杂的恢复逻辑
- 直接使用现有页面
- 只发送新消息
- 超时不重建页面
"""
import os
import sys
import json
import asyncio
import logging
import uuid
import time
import re
import hashlib
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
from contextlib import asynccontextmanager
from dataclasses import dataclass, field

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("deepseek-ultimate")

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
except Exception as e:
    logger.warning(f"⚠️ 无法导入 hermes/tools 模块: {e}")
    tools = None


def _build_hermes_prompt() -> Optional[str]:
    if tools is None:
        return None
    try:
        return tools.build_system_prompt()
    except Exception as e:
        logger.warning(f"tools.build_system_prompt() 失败: {e}")
        return None


# ============ 配置 ============
HOST = os.environ.get("API_HOST", "0.0.0.0")
PORT = int(os.environ.get("API_PORT", sys.argv[1] if len(sys.argv) > 1 else "8002"))

_DATA_DIR = Path(os.environ.get("HERMES_DIR", os.path.dirname(os.path.abspath(__file__)))) / "data"
_DATA_DIR.mkdir(exist_ok=True)
DATA_DIR = _DATA_DIR
STORAGE_FILE = DATA_DIR / "storage.json"
DEEPSEEK_URL = "https://chat.deepseek.com/"

MAX_SESSIONS = int(os.environ.get("MAX_SESSIONS", "100"))
SESSION_TIMEOUT = int(os.environ.get("SESSION_TIMEOUT", "86400"))  # 24小时
MAX_CONCURRENT = int(os.environ.get("MAX_CONCURRENT", "4"))
REPLY_TIMEOUT = int(os.environ.get("REPLY_TIMEOUT", "300"))
LOGIN_TIMEOUT = int(os.environ.get("LOGIN_TIMEOUT", "300"))
MAX_REQUEST_SIZE = int(os.environ.get("MAX_REQUEST_SIZE", str(10 * 1024 * 1024)))
HEARTBEAT_INTERVAL = int(os.environ.get("HEARTBEAT_INTERVAL", "120"))  # 2分钟

_API_KEYS = [
    k.strip() for k in
    (os.environ.get("HERMES_API_KEY", "") + "," + os.environ.get("API_KEYS", ""))
    .split(",")
    if k.strip()
]

_PUBLIC_PATHS = {"/", "/health", "/docs", "/redoc", "/openapi.json", "/favicon.ico", "/diagnose"}


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


def _require_auth(request: Request):
    if not _API_KEYS:
        return
    token = _extract_token(request)
    if not token or token not in _API_KEYS:
        raise HTTPException(status_code=401, detail="Invalid API key")


# ============ 会话管理器 ============

@dataclass
class ChatSession:
    session_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    page: Any = None
    sent_message_ids: List[str] = field(default_factory=list)  # 已发送消息ID
    last_activity: float = field(default_factory=time.time)
    created: float = field(default_factory=time.time)
    lock: Any = None
    message_count: int = 0

    def __post_init__(self):
        if self.lock is None:
            self.lock = asyncio.Lock()


class SessionManager:
    def __init__(self, max_sessions: int = MAX_SESSIONS, session_timeout: int = SESSION_TIMEOUT):
        self.sessions: Dict[str, ChatSession] = {}
        self.max_sessions = max_sessions
        self.session_timeout = session_timeout
        self._lock = asyncio.Lock()
        self._heartbeat_task: Optional[asyncio.Task] = None

    async def get_or_create(self, session_id: Optional[str] = None) -> Tuple[ChatSession, bool]:
        async with self._lock:
            await self._cleanup_expired()
            if session_id and session_id in self.sessions:
                s = self.sessions[session_id]
                s.last_activity = time.time()
                logger.debug(f"复用会话: {session_id}")
                return s, False
            if len(self.sessions) >= self.max_sessions:
                oldest = min(self.sessions.items(), key=lambda x: x[1].last_activity)
                await self._close_session(oldest[1])
                del self.sessions[oldest[0]]
                logger.warning(f"会话数达上限，驱逐最旧会话: {oldest[0]}")
            s = ChatSession(session_id=session_id or uuid.uuid4().hex[:12])
            self.sessions[s.session_id] = s
            logger.info(f"创建新会话: {s.session_id}")
            return s, True

    async def remove(self, session_id: str):
        async with self._lock:
            s = self.sessions.pop(session_id, None)
            if s:
                await self._close_session(s)
                logger.info(f"移除会话: {session_id}")

    async def _close_session(self, s: ChatSession):
        if s.page and not s.page.is_closed():
            try:
                await s.page.close()
            except Exception as e:
                logger.warning(f"关闭会话页面失败: {e}")
        s.page = None

    async def close_all(self):
        async with self._lock:
            if self._heartbeat_task:
                self._heartbeat_task.cancel()
                try:
                    await self._heartbeat_task
                except Exception:
                    pass
            for s in list(self.sessions.values()):
                await self._close_session(s)
            self.sessions.clear()

    async def _cleanup_expired(self):
        now = time.time()
        expired = [
            sid for sid, s in self.sessions.items()
            if now - s.last_activity > self.session_timeout
        ]
        for sid in expired:
            logger.info(f"清理过期会话: {sid}")
            await self._close_session(self.sessions[sid])
            del self.sessions[sid]

    async def start_heartbeat(self, browser):
        """启动心跳任务 - 只做轻量检查"""
        if self._heartbeat_task and not self._heartbeat_task.done():
            return
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop(browser))
        logger.info("❤️ 心跳任务已启动")

    async def _heartbeat_loop(self, browser):
        """定期检查会话 - 只检查页面是否还活着，不重建"""
        while True:
            try:
                await asyncio.sleep(HEARTBEAT_INTERVAL)
                now = time.time()
                async with self._lock:
                    for sid, session in list(self.sessions.items()):
                        # 只检查活跃会话
                        if now - session.last_activity > 3600:
                            continue
                        try:
                            if session.page:
                                if session.page.is_closed():
                                    logger.warning(f"会话 {sid} 页面已关闭")
                                    session.page = None
                                else:
                                    # 简单检查
                                    await asyncio.wait_for(
                                        session.page.evaluate("1 + 1"),
                                        timeout=3.0
                                    )
                        except asyncio.TimeoutError:
                            logger.warning(f"会话 {sid} 心跳超时，可能页面卡死")
                        except Exception as e:
                            logger.debug(f"会话 {sid} 心跳检查失败: {e}")
            except asyncio.CancelledError:
                logger.info("心跳任务已取消")
                break
            except Exception as e:
                logger.error(f"心跳任务异常: {e}")


# ============ 浏览器客户端 ============

class DeepSeekBrowser:
    def __init__(self):
        self._pw = None
        self._browser = None
        self._context = None
        self._lock = asyncio.Lock()
        self._concurrency = asyncio.Semaphore(MAX_CONCURRENT)
        self._is_closing = False
        self._reconnect_attempts = 0
        self._max_reconnect_attempts = 5

    async def _ensure(self, force_reconnect: bool = False):
        """确保浏览器连接可用"""
        if self._is_closing:
            raise RuntimeError("浏览器正在关闭")
        
        if self._browser and self._browser.is_connected() and not force_reconnect:
            return
        
        if force_reconnect or self._browser is None or not self._browser.is_connected():
            self._reconnect_attempts += 1
            if self._reconnect_attempts > self._max_reconnect_attempts:
                logger.error(f"浏览器重连次数超过限制 ({self._max_reconnect_attempts})")
                self._reconnect_attempts = 0
                raise RuntimeError("浏览器重连失败次数过多")
            
            logger.info(f"🔄 重新连接浏览器 (尝试 {self._reconnect_attempts}/{self._max_reconnect_attempts})")
            
            await self._cleanup_browser()
            
            try:
                from playwright.async_api import async_playwright
                self._pw = await async_playwright().start()
                self._browser = await self._pw.chromium.launch(
                    headless=False,
                    args=[
                        "--window-size=1280,800",
                        "--disable-blink-features=AutomationControlled",
                        "--no-sandbox",
                        "--disable-dev-shm-usage"
                    ]
                )
                storage = str(STORAGE_FILE) if STORAGE_FILE.exists() else None
                self._context = await self._browser.new_context(
                    viewport={"width": 1280, "height": 800},
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    storage_state=storage,
                    locale="zh-CN",
                )
                if storage:
                    logger.info("✅ 已加载登录态")
                self._reconnect_attempts = 0
            except Exception as e:
                logger.error(f"浏览器启动失败: {e}")
                raise

    async def _cleanup_browser(self):
        """清理浏览器资源"""
        try:
            if self._context:
                await self._context.close()
        except Exception:
            pass
        try:
            if self._browser:
                await self._browser.close()
        except Exception:
            pass
        try:
            if self._pw:
                await self._pw.stop()
        except Exception:
            pass
        self._context = None
        self._browser = None
        self._pw = None

    async def open_homepage(self):
        await self._ensure()
        if self._context and self._context.pages:
            alive = [p for p in self._context.pages if not p.is_closed()]
            if alive:
                return
        try:
            page = await self._context.new_page()
            await page.goto(DEEPSEEK_URL, wait_until="domcontentloaded", timeout=30000)
            logger.info("📌 已打开 DeepSeek 页面")
        except Exception as e:
            logger.error(f"打开 DeepSeek 页面失败: {e}")
            await self._ensure(force_reconnect=True)
            page = await self._context.new_page()
            await page.goto(DEEPSEEK_URL, wait_until="domcontentloaded", timeout=30000)

    async def _save(self):
        if self._context and not self._is_closing:
            try:
                await self._context.storage_state(path=str(STORAGE_FILE))
            except Exception as e:
                logger.warning(f"保存登录态失败: {e}")

    async def is_page_healthy(self, page=None) -> bool:
        if page is None:
            if not self._context:
                return False
            pages = self._context.pages
            alive = [x for x in pages if not x.is_closed()]
            page = alive[0] if alive else None
        
        if page is None:
            return False
        
        try:
            if page.is_closed():
                return False
            url = page.url
            if not url or "about:blank" in url:
                return False
            textarea = await page.query_selector("textarea")
            if textarea is None:
                return False
            if "sign_in" in url:
                return False
            return True
        except Exception:
            return False

    async def get_or_create_page(self, session: ChatSession) -> Any:
        """获取或创建页面 - 不重建现有页面"""
        # 如果页面存在且未关闭，直接使用
        if session.page and not session.page.is_closed():
            try:
                # 简单检查页面是否可用
                await session.page.evaluate("1 + 1")
                return session.page
            except Exception as e:
                logger.warning(f"页面不可用: {e}")
                # 页面不可用，需要创建新页面
                session.page = None
        
        # 需要创建新页面
        logger.info(f"🔄 为会话 {session.session_id} 创建新页面")
        try:
            await self._ensure()
            
            if session.page and not session.page.is_closed():
                try:
                    await session.page.close()
                except Exception:
                    pass
            
            new_page = await self._context.new_page()
            await new_page.goto(DEEPSEEK_URL, wait_until="domcontentloaded", timeout=30000)
            await self._ensure_fresh(new_page)
            
            session.page = new_page
            # 页面是新的，重置已发送消息列表
            session.sent_message_ids = []
            session.message_count = 0
            
            logger.info(f"✅ 会话 {session.session_id} 新页面创建成功")
            return new_page
        except Exception as e:
            logger.error(f"创建新页面失败: {e}")
            raise

    async def check_login(self, page=None) -> bool:
        if self._is_closing:
            return False
        try:
            await self._ensure()
        except Exception:
            return False
        
        p = page
        if p is None:
            if not self._context:
                return False
            pages = self._context.pages
            alive = [x for x in pages if not x.is_closed()]
            if not alive:
                return False
            p = alive[0]
        
        try:
            if "sign_in" in p.url:
                return False
            inp = await p.query_selector("textarea")
            return inp is not None
        except Exception:
            return False

    async def new_session_page(self) -> Any:
        await self._ensure()
        page = await self._context.new_page()
        await page.goto(DEEPSEEK_URL, wait_until="domcontentloaded", timeout=30000)
        await self._ensure_fresh(page)
        return page

    async def _ensure_fresh(self, page):
        try:
            await page.wait_for_load_state("networkidle", timeout=8000)
        except Exception:
            pass
        try:
            btn = await page.query_selector('button:has-text("新对话")')
            if btn:
                await btn.click()
                await asyncio.sleep(1.2)
        except Exception as e:
            logger.debug(f"新建对话跳过: {e}")

    async def new_conversation(self, page):
        try:
            btn = await page.query_selector('button:has-text("新对话")')
            if btn:
                await btn.click()
                await asyncio.sleep(1.5)
                return True
        except Exception as e:
            logger.warning(f"新建对话失败: {e}")
        return False

    async def login(self, timeout: int = LOGIN_TIMEOUT) -> Dict[str, Any]:
        await self._ensure()
        page = await self._context.new_page()
        try:
            await page.goto("https://chat.deepseek.com/sign_in", wait_until="domcontentloaded")
        except Exception as e:
            await page.close()
            return {"success": False, "error": f"打开登录页失败: {e}"}
        start = asyncio.get_event_loop().time()
        while asyncio.get_event_loop().time() - start < timeout:
            try:
                if await page.query_selector("textarea") and "sign_in" not in page.url:
                    await self._save()
                    await page.close()
                    return {"success": True, "message": "登录成功"}
            except Exception:
                pass
            await asyncio.sleep(2)
        try:
            await page.close()
        except Exception:
            pass
        return {"success": False, "message": f"登录超时({timeout}s)"}

    STOP_BTN_SELECTORS = (
        'button:has-text("停止生成")',
        'button:has-text("停止")',
        'button:has-text("Stop generating")',
        'button[aria-label*="停止"]',
        'button[title*="停止"]',
        'button[aria-label*="stop"]',
        'button[title*="stop"]',
    )

    async def _is_generating(self, page) -> bool:
        for sel in self.STOP_BTN_SELECTORS:
            try:
                if await page.query_selector(sel):
                    return True
            except Exception:
                continue
        return False

    async def _send_message(self, page, text: str):
        try:
            textarea = await page.wait_for_selector("textarea", timeout=10000)
        except Exception:
            raise RuntimeError("找不到输入框，可能需要重新登录")
        await textarea.click()
        await asyncio.sleep(0.3)
        await textarea.fill("")
        await asyncio.sleep(0.2)
        try:
            await textarea.fill(text)
        except Exception:
            chunk_size = 2000
            for i in range(0, len(text), chunk_size):
                chunk = text[i:i + chunk_size]
                await textarea.type(chunk, delay=0)
                await asyncio.sleep(0.1)
        await asyncio.sleep(0.5)
        try:
            send_btn = await page.query_selector('button[type="submit"]')
            if send_btn:
                await send_btn.click()
            else:
                await textarea.press("Enter")
        except Exception:
            await textarea.press("Enter")
        await asyncio.sleep(1)

    async def _wait_for_reply(self, page, timeout: int) -> str:
        last_text = ""
        stable_count = 0
        start_time = asyncio.get_event_loop().time()
        MIN_CONTENT_LENGTH = 30
        no_response_count = 0

        while asyncio.get_event_loop().time() - start_time < timeout:
            await asyncio.sleep(0.8)
            try:
                generating = await self._is_generating(page)
                if generating:
                    stable_count = 0
                    no_response_count = 0
                    continue
            except Exception:
                pass

            try:
                selectors = [
                    '.ds-markdown',
                    '[class*="message"] [class*="content"]',
                    '.markdown',
                    '[data-testid="message-content"]'
                ]
                messages = None
                for selector in selectors:
                    try:
                        messages = await page.query_selector_all(selector)
                        if messages and len(messages) > 0:
                            break
                    except Exception:
                        continue
                if not messages:
                    no_response_count += 1
                    if no_response_count > 20:
                        logger.warning("⚠️ 长时间无响应，可能页面异常")
                        return "超时：未收到回复"
                    continue
                try:
                    text = await messages[-1].inner_text()
                except Exception:
                    text = await messages[-1].text_content()
                if not text or not text.strip():
                    no_response_count += 1
                    continue
                current = text.strip()
                if current == last_text:
                    stable_count += 1
                    if stable_count >= 12 and len(current) >= MIN_CONTENT_LENGTH:
                        return last_text
                    if stable_count >= 30:
                        logger.warning("⚠️ 超时保护返回")
                        return last_text
                else:
                    stable_count = 0
                    last_text = current
                    no_response_count = 0
            except Exception as e:
                logger.debug(f"获取消息失败: {e}")

        return last_text or "超时：未收到回复"

    async def screenshot(self, page=None) -> bytes:
        await self._ensure()
        if page is None:
            pages = self._context.pages if self._context else []
            alive = [x for x in pages if not x.is_closed()]
            page = alive[0] if alive else await self.new_session_page()
        return await page.screenshot(full_page=True)

    async def close(self):
        self._is_closing = True
        try:
            if self._context:
                await self._save()
                await self._context.close()
        except Exception as e:
            logger.warning(f"关闭 context 失败: {e}")
        try:
            if self._browser:
                await self._browser.close()
        except Exception as e:
            logger.warning(f"关闭 browser 失败: {e}")
        try:
            if self._pw:
                await self._pw.stop()
        except Exception as e:
            logger.warning(f"关闭 playwright 失败: {e}")


# ============ JSON 修复与解析 ============

def _repair_multiline_json(s: str) -> str:
    out, in_str, esc = [], False, False
    for ch in s:
        if in_str:
            if esc:
                out.append(ch); esc = False; continue
            if ch == '\\':
                esc = True; out.append(ch); continue
            if ch == '"':
                in_str = False; out.append(ch); continue
            if ch == '\n':
                out.append('\n')
            elif ch == '\r':
                out.append('\r')
            elif ch == '\t':
                out.append('\t')
            else:
                out.append(ch)
        else:
            if ch == '"': in_str = True
            out.append(ch)
    return ''.join(out)


def _repair_value_quotes(s: str) -> str:
    out, in_str, is_value, esc, last_nonspace = [], False, False, False, None
    i, n = 0, len(s)
    while i < n:
        ch = s[i]
        if esc:
            out.append(ch); esc = False; last_nonspace = ch; i += 1; continue
        if ch == '\\':
            out.append(ch); esc = True; last_nonspace = ch; i += 1; continue
        if ch == '"':
            if not in_str:
                in_str = True; is_value = (last_nonspace == ':')
                out.append(ch); i += 1; continue
            if is_value:
                j = i + 1
                while j < n and s[j] in ' \t\r\n':
                    j += 1
                if j < n and s[j] in ',}]':
                    in_str = False; out.append(ch)
                else:
                    out.append('\\"')
                last_nonspace = ch
            else:
                in_str = False; out.append(ch); last_nonspace = ch
            i += 1; continue
        if ch not in ' \t\r\n':
            last_nonspace = ch
        out.append(ch)
        i += 1
    return ''.join(out)


def _find_string_spans(s: str) -> list:
    spans = []
    i, n = 0, len(s)
    while i < n:
        if s[i] != '"':
            i += 1
            continue
        j, esc = i + 1, False
        while j < n:
            c = s[j]
            if esc:
                esc = False
            elif c == '\\':
                esc = True
            elif c == '"':
                spans.append((i, j + 1))
                i = j + 1
                break
            j += 1
        else:
            break
    return spans


def _repair_windows_paths(s: str) -> str:
    spans = _find_string_spans(s)
    if not spans:
        return s
    out = list(s)
    for start, end in reversed(spans):
        inner = s[start + 1:end - 1]
        if not re.search(r'(?i)[a-z]:\\', inner):
            continue
        parts = []
        i, n = 0, len(inner)
        while i < n:
            c = inner[i]
            if c == '\\':
                nxt = inner[i + 1] if i + 1 < n else ''
                if nxt == '\\':
                    parts.append('\\\\')
                    i += 2
                    continue
                parts.append('\\\\')
                i += 1
                continue
            if c == '"':
                parts.append('\\"')
                i += 1
                continue
            parts.append(c)
            i += 1
        rebuilt = ''.join(parts)
        if rebuilt != inner:
            out[start + 1:end - 1] = list(rebuilt)
    return ''.join(out)


def _try_load_json(s: str):
    candidates = []
    pw = _repair_windows_paths(s)
    if pw != s:
        candidates.append(pw)
    candidates.append(s)
    r1 = _repair_multiline_json(s)
    if r1 != s:
        candidates.append(r1)
    r2 = _repair_value_quotes(r1)
    if r2 != r1:
        candidates.append(r2)
    pat = re.compile(r'(?<!\\)\\(?!["\\/bfnrtu])')
    r3a = pat.sub(r'\\\\', r1)
    if r3a != r1:
        candidates.append(r3a)
    r3b = pat.sub(r'\\\\', r2)
    if r3b != r2:
        candidates.append(r3b)
    r4 = _repair_value_quotes(pat.sub(r'\\\\', r1))
    if r4 not in candidates:
        candidates.append(r4)
    for cand in candidates:
        try:
            return json.loads(cand)
        except (json.JSONDecodeError, ValueError):
            continue
    return None


def _extract_balanced(text: str, start: int):
    depth, in_str, esc = 0, False, False
    for j in range(start, len(text)):
        ch = text[j]
        if in_str:
            if esc: esc = False
            elif ch == '\\': esc = True
            elif ch == '"': in_str = False
            continue
        if ch == '"': in_str = True
        elif ch in '{[': depth += 1
        elif ch in '}]':
            depth -= 1
            if depth == 0:
                return text[start:j + 1]
    return None


def _extract_call(item, schema_map: Dict[str, dict], out: List[tuple]):
    if not isinstance(item, dict):
        return
    fn = item.get('function') if isinstance(item.get('function'), dict) else item
    name = str(fn.get('name') or fn.get('tool') or '').strip()
    if not name:
        return
    args = fn.get('arguments')
    if args is None:
        args = fn.get('parameters') or fn.get('params')
    if args is None:
        args = fn.get('arguments_str')

    if isinstance(args, str):
        parsed = _try_load_json(args)
        if isinstance(parsed, dict):
            args = parsed
        else:
            sm = schema_map.get(name.lower())
            if sm and len(sm.get("required", [])) == 1:
                args = {sm["required"][0]: args}
            else:
                return
    if not isinstance(args, dict):
        return
    out.append((name, args))


def _parse_tool_calls(text: str, schema_map: Dict[str, dict]) -> List[dict]:
    if not text:
        return []
    out: List[tuple] = []
    seen = set()
    i = 0
    n = len(text)
    while i < n:
        ch = text[i]
        if ch not in '{[':
            i += 1
            continue
        snippet = _extract_balanced(text, i)
        if snippet is None:
            i += 1
            continue
        data = _try_load_json(snippet)
        if data is not None:
            items = data if isinstance(data, list) else [data]
            for it in items:
                _extract_call(it, schema_map, out)
        i += len(snippet)

    tool_calls = []
    for name, args in out:
        key = f"{name.lower()}|{json.dumps(args, sort_keys=True, ensure_ascii=False)}"
        if key in seen:
            continue
        seen.add(key)
        tool_calls.append({
            "id": f"call_{uuid.uuid4().hex[:8]}",
            "type": "function",
            "function": {
                "name": name,
                "arguments": json.dumps(args, ensure_ascii=False)
            }
        })
    return tool_calls


# ============ 请求模型 ============

class FunctionDef(BaseModel):
    name: str
    description: Optional[str] = None
    parameters: Optional[Any] = None


class ToolDef(BaseModel):
    type: str = "function"
    function: FunctionDef


class ChatMessage(BaseModel):
    role: str
    content: Optional[Any] = None
    name: Optional[str] = None
    tool_calls: Optional[Any] = None
    tool_call_id: Optional[str] = None


class ChatCompletionRequest(BaseModel):
    model: str = "deepseek-browser"
    messages: List[ChatMessage]
    tools: Optional[List[ToolDef]] = None
    tool_choice: Optional[Any] = None
    stream: bool = False
    stream_options: Optional[Any] = None
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    max_tokens: Optional[int] = None
    stop: Optional[Any] = None
    session_id: Optional[str] = None
    new_conversation: bool = False
    user: Optional[str] = None


def _normalize_content(content: Any) -> str:
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
                    url = p.get("image_url", {})
                    u = url.get("url") if isinstance(url, dict) else None
                except Exception:
                    u = None
                parts.append(f"[图片: {u}]" if u else "[图片]")
        text = "\n".join(x for x in parts if x).strip()
        return text if text else ("[图片]" if has_image else "")
    return str(content)


def _build_tool_schemas(tools: Optional[List[ToolDef]]) -> Dict[str, dict]:
    sm = {}
    for t in tools or []:
        fn = t.function
        params = fn.parameters if isinstance(fn.parameters, dict) else {}
        props = params.get("properties", {}) if isinstance(params, dict) else {}
        required = params.get("required", []) if isinstance(params, dict) else []
        sm[fn.name.lower()] = {
            "name": fn.name,
            "description": fn.description or "",
            "required": [str(r) for r in required],
            "properties": {str(k): v for k, v in props.items()},
        }
    return sm


def _build_tools_instruction(schema_map: Dict[str, dict], tool_choice: Any) -> str:
    if not schema_map:
        return ""
    lines = ["【可用工具】当需要调用工具时，只输出一个 ```JSON：",
             '[{"name": "工具名", "arguments": {"参数名": "值"}}]', ""]

    if isinstance(tool_choice, str):
        tc = tool_choice.lower()
        if tc == "none":
            lines.append("【重要】本次禁止调用任何工具，直接用文字回答。")
        elif tc == "required":
            lines.append("【重要】你必须至少调用一次工具来完成回答。")
    elif isinstance(tool_choice, dict):
        fn = tool_choice.get("function")
        if isinstance(fn, dict) and fn.get("name"):
            lines.append(f"【重要】本次只能调用工具：{fn['name']}，且必须先输出它的调用。")
    lines.append("【工具结果】每次调用后你会收到\"工具结果\"，请据此继续，直到任务完成。。如果写代码，字符串里的\\n，用os.linesep")
    return "\n".join(lines)


def _render_turn(role: str, content: str) -> str:
    content = content or ""
    if role == "system":
        return f"【系统指令】请严格遵守以下规则：\n{content}"
    if role == "tool":
        return f"（工具调用结果）\n{content}\n\n请根据结果继续。"
    return content


def _turn_hash(role: str, content: str) -> str:
    return hashlib.md5(f"{role}|{content}".encode("utf-8")).hexdigest()


def _estimate_tokens(text: str) -> int:
    if not text:
        return 0
    chinese = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
    return int(chinese / 1.5 + (len(text) - chinese) / 4)


def _derive_session_key(req: ChatCompletionRequest, system_text: str, turns: List[tuple], request: Request = None) -> str:
    if request is not None:
        conv = request.headers.get("X-Conversation") or request.headers.get("x-conversation")
        if conv:
            return f"conv-{hashlib.md5(conv.encode('utf-8')).hexdigest()[:16]}"
    if req.session_id:
        return req.session_id
    if req.user:
        return f"user-{hashlib.md5(str(req.user).encode('utf-8')).hexdigest()[:16]}"
    first_user = next((c for r, c in turns if r == "user"), "")
    if first_user:
        stable = hashlib.md5(f"{req.user or ''}|{first_user[:100]}".encode("utf-8")).hexdigest()[:16]
        return f"fp-{stable}"
    return None


# ============ 聊天处理 ============

def _build_turns(req: ChatCompletionRequest, schema_map: Dict[str, dict], tools_instruction: str) -> Tuple[str, List[tuple]]:
    system_parts = []
    turns: List[tuple] = []
    for m in req.messages:
        if m.role == "system" and m.content:
            system_parts.append(_normalize_content(m.content))
        elif m.role == "user":
            c = _normalize_content(m.content)
            if c:
                turns.append(("user", c))
        elif m.role == "tool":
            c = _normalize_content(m.content)
            if c:
                turns.append(("tool", c))
        elif m.role == "assistant":
            pass
    system_text = "\n\n".join(system_parts)
    if tools_instruction:
        system_text = (system_text + "\n\n" + tools_instruction) if system_text else tools_instruction
    return system_text, turns


async def _run_completion(session: ChatSession, req: ChatCompletionRequest,
                          system_text: str, turns: List[tuple],
                          schema_map: Dict[str, dict], timeout: int = REPLY_TIMEOUT) -> Dict[str, Any]:
    browser: DeepSeekBrowser = await get_browser()
    async with session.lock:
        # 获取页面（如果页面不存在才创建）
        try:
            page = await browser.get_or_create_page(session)
        except Exception as e:
            logger.error(f"获取页面失败: {e}")
            return {"error": f"无法获取会话页面: {e}"}

        # 检查登录状态
        try:
            if not await browser.check_login(page):
                return {"error": "未登录，请先调用 /login"}
        except Exception as e:
            logger.error(f"检查登录状态失败: {e}")
            return {"error": "未登录，请先调用 /login"}

        if not turns:
            return {"error": "没有有效的用户消息"}

        # 计算消息哈希
        current_ids = [_turn_hash(role, content) for role, content in turns]
        sent_ids = set(session.sent_message_ids)
        
        # 找出新消息
        new_messages = []
        for i, (role, content) in enumerate(turns):
            if current_ids[i] not in sent_ids:
                new_messages.append((role, content, current_ids[i]))

        # 如果是新会话或重置，发送所有消息
        if req.new_conversation or len(session.sent_message_ids) == 0:
            try:
                await browser.new_conversation(page)
                logger.info(f"🔄 新对话: {session.session_id}")
            except Exception as e:
                logger.warning(f"新建对话失败: {e}")
            
            send_turns = []
            if system_text:
                send_turns.append(("system", system_text))
            send_turns.extend(turns)
            
            session.sent_message_ids = []
            
            for role, content in send_turns:
                rendered = _render_turn(role, content)
                await browser._send_message(page, rendered)
                if role != "system":
                    session.sent_message_ids.append(_turn_hash(role, content))
            
            logger.info(f"发送 {len(send_turns)} 条消息 (新会话)")
        
        elif new_messages:
            # 只发送新消息
            logger.info(f"📤 发送 {len(new_messages)} 条新消息")
            
            for role, content, msg_id in new_messages:
                rendered = _render_turn(role, content)
                await browser._send_message(page, rendered)
                session.sent_message_ids.append(msg_id)
                session.message_count += 1
        
        else:
            # 没有新消息，但可能工具结果需要发送
            if turns and turns[-1][0] == "tool":
                role, content = turns[-1]
                rendered = _render_turn(role, content)
                await browser._send_message(page, rendered)
                session.sent_message_ids.append(_turn_hash(role, content))
            else:
                # 确实没有新消息，但用户可能想继续对话
                logger.info(f"ℹ️ 没有新消息，会话状态: {len(session.sent_message_ids)} 条已发送")
                # 如果有系统提示，发送它
                if system_text:
                    rendered = _render_turn("system", system_text)
                    await browser._send_message(page, rendered)

        # 等待回复
        reply = await browser._wait_for_reply(page, timeout)
        session.last_activity = time.time()

        if "未收到回复" in reply or reply.startswith("超时"):
            return {"error": reply}

        tool_calls = _parse_tool_calls(reply, schema_map) if schema_map else []

        usage = {
            "prompt_tokens": _estimate_tokens((system_text or "") + "".join(c for _, c in turns)),
            "completion_tokens": _estimate_tokens(reply),
            "total_tokens": 0
        }
        usage["total_tokens"] = usage["prompt_tokens"] + usage["completion_tokens"]

        return {
            "content": None if tool_calls else reply,
            "tool_calls": tool_calls,
            "session_id": session.session_id,
            "usage": usage,
            "reply": reply,
        }


# ============ FastAPI ============

session_manager = SessionManager()
_browser: Optional[DeepSeekBrowser] = None
_browser_lock = asyncio.Lock()


async def get_browser() -> DeepSeekBrowser:
    global _browser
    async with _browser_lock:
        if _browser is None:
            _browser = DeepSeekBrowser()
        return _browser


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 启动 DeepSeek Browser API 终极版 (v10.4 简化稳定性修复)...")
    browser = None
    try:
        browser = await get_browser()
        await browser._ensure()
        await browser.open_homepage()
        await session_manager.start_heartbeat(browser)
        logger.info("✅ 服务启动完成")
    except Exception as e:
        logger.error(f"启动失败: {e}")
    yield
    logger.info("🛑 关闭...")
    await session_manager.close_all()
    if browser:
        await browser.close()


app = FastAPI(
    title="DeepSeek Browser API Ultimate",
    version="10.4.0",
    description="OpenAI 兼容代理（浏览器后端）简化稳定性修复版",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    if _API_KEYS and request.url.path not in _PUBLIC_PATHS:
        token = _extract_token(request)
        if not token or token not in _API_KEYS:
            return JSONResponse(
                content={"error": {"message": "Invalid API key", "type": "invalid_request_error",
                                   "param": None, "code": "invalid_api_key"}},
                status_code=401,
            )
    return await call_next(request)


# ============ 路由 ============

@app.get("/")
async def root():
    return {
        "service": "DeepSeek Browser API Ultimate",
        "version": "10.4.0",
        "status": "running",
        "openai_compatible": True,
        "endpoints": [
            "POST /v1/chat/completions",
            "GET  /v1/models",
            "GET  /v1/models/{model_id}",
            "GET  /status",
            "GET  /health",
            "GET  /diagnose",
            "GET  /sessions",
            "POST /login",
            "POST /reset",
            "POST /session/clear",
            "GET  /inject",
            "GET  /screenshot",
        ],
    }


@app.get("/status")
async def status():
    browser = await get_browser()
    try:
        logged_in = await browser.check_login()
    except Exception:
        logged_in = False
    return {
        "service": "deepseek-browser-ultimate",
        "version": "10.4.0",
        "logged_in": logged_in,
        "active_sessions": len(session_manager.sessions),
        "api_keys_configured": bool(_API_KEYS),
        "model": "deepseek-browser",
        "max_sessions": MAX_SESSIONS,
        "max_concurrent": MAX_CONCURRENT,
        "heartbeat_interval": HEARTBEAT_INTERVAL,
        "session_timeout": SESSION_TIMEOUT,
    }


@app.get("/health")
async def health():
    browser = await get_browser()
    try:
        healthy = await browser.is_page_healthy()
        logged_in = await browser.check_login() if healthy else False
    except Exception:
        healthy = False
        logged_in = False
    return {
        "status": "ok" if (healthy and logged_in) else "degraded",
        "healthy": healthy,
        "logged_in": logged_in,
        "sessions": len(session_manager.sessions),
    }


@app.get("/diagnose")
async def diagnose():
    browser = await get_browser()
    result = {
        "browser": {
            "initialized": browser._browser is not None,
            "connected": browser._browser.is_connected() if browser._browser else False,
            "context_exists": browser._context is not None,
            "is_closing": browser._is_closing,
        },
        "pages": [],
        "sessions": [],
        "logged_in": False,
    }
    
    if browser._context:
        try:
            pages = browser._context.pages
            for i, page in enumerate(pages):
                try:
                    is_closed = page.is_closed()
                    url = page.url if not is_closed else "closed"
                    result["pages"].append({
                        "index": i,
                        "url": url[:100] if url else "unknown",
                        "is_closed": is_closed,
                    })
                except Exception as e:
                    result["pages"].append({"index": i, "error": str(e)})
        except Exception as e:
            result["pages_error"] = str(e)
    
    for sid, session in session_manager.sessions.items():
        result["sessions"].append({
            "id": sid,
            "has_page": session.page is not None and not session.page.is_closed() if session.page else False,
            "sent_messages": len(session.sent_message_ids),
            "message_count": session.message_count,
            "last_activity": session.last_activity,
            "age_seconds": int(time.time() - session.created),
        })
    
    try:
        result["logged_in"] = await browser.check_login()
    except Exception as e:
        result["logged_in_error"] = str(e)
    
    return result


@app.get("/v1/models")
async def list_models():
    return {
        "object": "list",
        "data": [{
            "id": "deepseek-browser",
            "object": "model",
            "created": 1700000000,
            "owned_by": "deepseek-browser",
        }]
    }


@app.get("/v1/models/{model_id}")
async def get_model(model_id: str):
    if model_id != "deepseek-browser" and not model_id.startswith("deepseek"):
        raise HTTPException(status_code=404, detail="Model not found")
    return {
        "id": model_id,
        "object": "model",
        "created": 1700000000,
        "owned_by": "deepseek-browser",
    }


@app.post("/login")
async def login():
    browser = await get_browser()
    try:
        return await browser.login()
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.post("/v1/chat/completions")
async def chat_completions(req: ChatCompletionRequest, request: Request):
    _require_auth(request)
    browser = await get_browser()

    schema_map = _build_tool_schemas(req.tools)
    tools_instruction = _build_tools_instruction(schema_map, req.tool_choice)
    system_text, turns = _build_turns(req, schema_map, tools_instruction)

    session_key = _derive_session_key(req, system_text, turns, request)

    if req.new_conversation and req.session_id:
        await session_manager.remove(session_key)
        logger.info(f"重置会话: {session_key}")

    session, _ = await session_manager.get_or_create(session_key)
    logger.info(f"使用会话: {session.session_id}, 已发送 {len(session.sent_message_ids)} 条消息")

    try:
        async with browser._concurrency:
            result = await _run_completion(session, req, system_text, turns, schema_map)
    except Exception as e:
        logger.error(f"聊天请求失败: {e}", exc_info=True)
        return JSONResponse(
            {"error": {"message": str(e), "type": "api_error"}},
            status_code=500
        )

    if "error" in result:
        code = 401 if "未登录" in result["error"] else 500
        return JSONResponse(
            {"error": {"message": result["error"], "type": "api_error"}},
            status_code=code
        )

    resp_id = f"chatcmpl-{uuid.uuid4().hex[:24]}"
    created = int(time.time())
    tool_calls = result.get("tool_calls") or []
    content = result.get("content")

    assistant_message: Dict[str, Any] = {"role": "assistant"}
    if tool_calls:
        assistant_message["content"] = None
        assistant_message["tool_calls"] = tool_calls
        finish_reason = "tool_calls"
    else:
        assistant_message["content"] = content or ""
        finish_reason = "stop"

    base = {
        "id": resp_id,
        "object": "chat.completion",
        "created": created,
        "model": req.model,
        "choices": [{
            "index": 0,
            "message": assistant_message,
            "finish_reason": finish_reason,
            "logprobs": None,
        }],
        "usage": result.get("usage", {}),
        "session_id": session.session_id,
    }

    if req.stream:
        include_usage = False
        so = req.stream_options
        if isinstance(so, dict) and so.get("include_usage"):
            include_usage = True

        async def generate():
            try:
                yield _sse_chunk(base, {"role": "assistant", "content": ""})
                if tool_calls:
                    for idx, tc in enumerate(tool_calls):
                        fn = tc.get("function") or {}
                        call_id = tc.get("id") or f"call_{uuid.uuid4().hex[:8]}"
                        yield _sse_chunk(base, {
                            "content": None,
                            "tool_calls": [{
                                "index": idx,
                                "id": call_id,
                                "type": "function",
                                "function": {"name": fn.get("name") or "", "arguments": ""},
                            }],
                        })
                        args = fn.get("arguments")
                        if args:
                            step = 50
                            for i in range(0, len(args), step):
                                yield _sse_chunk(base, {
                                    "tool_calls": [{"index": idx, "function": {"arguments": args[i:i + step]}}],
                                })
                                await asyncio.sleep(0.01)
                    yield _sse_chunk(base, {}, finish="tool_calls")
                else:
                    text = content or ""
                    for char in text:
                        yield _sse_chunk(base, {"content": char})
                        await asyncio.sleep(0.01)
                    yield _sse_chunk(base, {}, finish="stop")
                if include_usage:
                    yield _sse_chunk(base, {}, usage=result.get("usage", {}))
                yield "data: [DONE]\n\n"
            except Exception as e:
                logger.error(f"流式响应错误: {e}")
                yield f"data: {json.dumps({'error': {'message': str(e), 'type': 'api_error'}})}\n\n"

        return StreamingResponse(generate(), media_type="text/event-stream")

    return base


def _sse_chunk(base: dict, delta: dict, finish: Optional[str] = None, usage: Any = None) -> str:
    chunk = {
        "id": base["id"],
        "object": "chat.completion.chunk",
        "created": base["created"],
        "model": base["model"],
        "session_id": base.get("session_id"),
        "choices": [{
            "index": 0,
            "delta": delta,
            "finish_reason": finish,
        }],
    }
    if usage is not None:
        chunk["usage"] = usage
        chunk["choices"] = []
    return f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"


@app.post("/reset")
async def reset(session_id: Optional[str] = None, request: Request = None):
    _require_auth(request)
    browser = await get_browser()
    if session_id:
        session, _ = await session_manager.get_or_create(session_id)
        session.sent_message_ids = []
        session.message_count = 0
        if session.page and not session.page.is_closed():
            try:
                await browser.new_conversation(session.page)
                logger.info(f"重置对话: {session_id}")
            except Exception:
                pass
    else:
        for s in session_manager.sessions.values():
            s.sent_message_ids = []
            s.message_count = 0
    return {"success": True, "message": "对话已重置"}


@app.post("/session/clear")
async def clear_session(session_id: str, request: Request = None):
    _require_auth(request)
    await session_manager.remove(session_id)
    return {"success": True, "message": f"会话 {session_id} 已清除"}


@app.get("/sessions")
async def list_sessions(request: Request = None):
    _require_auth(request)
    sessions_info = []
    for sid, sess in session_manager.sessions.items():
        sessions_info.append({
            "session_id": sid,
            "has_page": sess.page is not None and not sess.page.is_closed(),
            "sent_messages": len(sess.sent_message_ids),
            "message_count": sess.message_count,
            "last_activity": sess.last_activity,
            "created": sess.created,
        })
    return {"sessions": sessions_info, "total": len(sessions_info)}


@app.get("/inject")
async def inject_prompt(session_id: Optional[str] = None, prompt: Optional[str] = None, request: Request = None):
    _require_auth(request)
    browser = await get_browser()
    session, _ = await session_manager.get_or_create(session_id)
    if prompt is None:
        prompt = _build_hermes_prompt()
    if prompt is None:
        prompt = (
            "【系统指令】你是一个本地运行的软件工程 AI 助手。"
            "需要操作文件、执行命令时，请输出 JSON 数组格式的工具调用，例如：\n"
            '[{"name": "write_file", "arguments": {"file_path": "a.py", "content": "..."}}]\n'
            "工具结果会以\"工具结果\"形式返回给你。"
        )
    try:
        page = await browser.get_or_create_page(session)
        await browser.new_conversation(page)
        await browser._send_message(page, f"【系统指令】请严格遵守以下规则：\n{prompt}")
        session.sent_message_ids = [_turn_hash("system", prompt)]
        await asyncio.sleep(2)
        return JSONResponse({
            "success": True,
            "message": "提示词已注入",
            "session_id": session.session_id,
            "prompt_length": len(prompt),
            "tool_count": len(tools.TOOLS) if tools is not None and hasattr(tools, "TOOLS") else 0,
            "using_tools_module": tools is not None,
        })
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)


@app.get("/screenshot")
async def screenshot(request: Request = None):
    from fastapi.responses import Response
    _require_auth(request)
    browser = await get_browser()
    try:
        png = await browser.screenshot()
        return Response(content=png, media_type="image/png")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"message": str(exc.detail), "type": "http_error", "param": None, "code": None}}
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"error": {"message": "Internal server error", "type": "api_error", "param": None, "code": None}}
    )


if __name__ == "__main__":
    print("=" * 60)
    print("🟢 DeepSeek Browser API 终极版 v10.4 (简化稳定性修复)")
    print("=" * 60)
    print(f"📌 http://{HOST}:{PORT}")
    print(f"🔑 鉴权: {'开启' if _API_KEYS else '关闭（默认安全）'}")
    print(f"❤️ 心跳间隔: {HEARTBEAT_INTERVAL}s")
    print(f"⏰ 会话超时: {SESSION_TIMEOUT}s ({SESSION_TIMEOUT//3600}小时)")
    print("=" * 60)
    uvicorn.run(app, host=HOST, port=PORT, log_level="info")
