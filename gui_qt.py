# -*- coding: utf-8 -*-
"""GUI - PyQt6 图形界面（修复卡死问题）

用法:
    python run.py --qt              # 启动 PyQt6 界面
"""
import sys
import os
import json
import re
import threading
import urllib.request
import uuid
from collections import deque
from datetime import datetime
from typing import Optional, Dict, List, Set, Tuple
from functools import lru_cache

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtCore import Qt, QTimer, QObject, pyqtSignal, QMutex, QMutexLocker
from PyQt6.QtGui import QFont, QColor, QFontDatabase, QTextCharFormat, QSyntaxHighlighter
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTextEdit, QPushButton, QLabel, QFrame, QScrollArea,
    QMessageBox, QSizePolicy, QDialog, QLineEdit, QFormLayout,
)

from agent import Agent
from planner import Pipeline

_SETTINGS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gui_qt_settings.json")
_CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")


FONT_UI = None
FONT_MONO = None


def _ensure_fonts():
    """惰性初始化字体（需要 QApplication 已存在）"""
    global FONT_UI, FONT_MONO
    if FONT_UI is not None:
        return
    try:
        available = set(QFontDatabase.families())
    except Exception:
        available = set()
    FONT_UI = _first_existing(available, "Microsoft YaHei UI", "Segoe UI",
                              "PingFang SC", "Helvetica Neue", "Arial")
    FONT_MONO = _first_existing(available, "Cascadia Code", "Consolas",
                                "JetBrains Mono", "Courier New", "Consolas")


def _first_existing(available, *candidates):
    for c in candidates:
        if c in available:
            return c
    return candidates[-1] if candidates else "Arial"


THEMES = {
    "dark": {
        "name": "深邃黑", "icon": "🌙",
        "bg": "#0f1117", "card": "#1a1d27", "border": "#2a2e3a",
        "fg": "#e6e6e6", "accent": "#6366f1",
        "ok": "#10b981", "err": "#ef4444", "warn": "#f59e0b",
        "text2": "#a1a1aa", "text3": "#71717a",
        "code_bg": "#0d0d0f", "code_border": "#2a2e3a", "code_text": "#e4e4e7",
        "hl_string": "#a5b4fc", "hl_number": "#fbbf24",
        "hl_comment": "#71717a", "hl_keyword": "#f472b6",
    },
    "light": {
        "name": "纯净白", "icon": "☀️",
        "bg": "#fafafa", "card": "#ffffff", "border": "#e4e4e7",
        "fg": "#0a0a0a", "accent": "#6366f1",
        "ok": "#059669", "err": "#dc2626", "warn": "#d97706",
        "text2": "#52525b", "text3": "#a1a1aa",
        "code_bg": "#f4f4f5", "code_border": "#d4d4d8", "code_text": "#1f2937",
        "hl_string": "#4f46e5", "hl_number": "#b45309",
        "hl_comment": "#6b7280", "hl_keyword": "#db2777",
    },
    "midnight": {
        "name": "暗夜蓝", "icon": "🌊",
        "bg": "#0a1428", "card": "#0f1d3a", "border": "#1e3a6b",
        "fg": "#e0f2fe", "accent": "#06b6d4",
        "ok": "#10b981", "err": "#ef4444", "warn": "#f59e0b",
        "text2": "#94a3b8", "text3": "#64748b",
        "code_bg": "#0a1428", "code_border": "#1e3a6b", "code_text": "#e0f2fe",
        "hl_string": "#93c5fd", "hl_number": "#fde68a",
        "hl_comment": "#64748b", "hl_keyword": "#f9a8d4",
    },
}
THEME_ORDER = ["dark", "light", "midnight"]


# ==================== 正则表达式预编译 ====================
_INLINE_PATTERN = re.compile(
    r"(`[^`]+`)|"
    r"(\*\*[^*]+\*\*)|"
    r"(\*[^*]+\*)|"
    r"(\[([^\]]+)\]\(([^)]+)\))"
)

_CODE_BLOCK_RE = re.compile(r'^```(\w*)\s*$')
_HEADER_RE = re.compile(r'^(#{1,3})\s+(.+)$')
_HR_RE = re.compile(r'^---+\s*$')
_LIST_RE = re.compile(r'^(\s*)([-*]|\d+\.)\s+(.+)$')
_STATUS_CODE_RE = re.compile(r'(?:return|exit|status|code)[\s:=]+(\d+)', re.IGNORECASE)
_NUMBER_RE = re.compile(r'\b\d+\.?\d*\b')


def _inline_html(text, c, fs):
    esc = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    out = []
    pos = 0
    for m in _INLINE_PATTERN.finditer(esc):
        if m.start() > pos:
            out.append(esc[pos:m.start()])
        if m.group(1):
            out.append(f'<span style="font-family:{FONT_MONO};'
                       f'background-color:{c["code_bg"]};color:{c["code_text"]};">'
                       f'{m.group(1)[1:-1]}</span>')
        elif m.group(2):
            out.append(f"<b>{m.group(2)[2:-2]}</b>")
        elif m.group(3):
            out.append(f"<i>{m.group(3)[1:-1]}</i>")
        elif m.group(4):
            out.append(f'<a href="{m.group(6)}" style="color:{c["accent"]};'
                       f'text-decoration:none;">{m.group(5)}</a>')
        pos = m.end()
    if pos < len(esc):
        out.append(esc[pos:])
    return "".join(out)


def _parse_markdown(text):
    if not text:
        return []
    blocks = []
    lines = text.split('\n')
    i = 0
    n = len(lines)
    while i < n:
        line = lines[i]
        m = _CODE_BLOCK_RE.match(line)
        if m:
            lang = m.group(1) or "text"
            code_lines = []
            i += 1
            while i < n and not _CODE_BLOCK_RE.match(lines[i]):
                code_lines.append(lines[i])
                i += 1
            blocks.append(("code", '\n'.join(code_lines), {"lang": lang}))
            i += 1
            continue
        m = _HEADER_RE.match(line)
        if m:
            blocks.append((f"h{len(m.group(1))}", m.group(2), {}))
            i += 1
            continue
        if _HR_RE.match(line):
            blocks.append(("hr", "", {}))
            i += 1
            continue
        m = _LIST_RE.match(line)
        if m:
            blocks.append(("li", m.group(3),
                           {"indent": len(m.group(1)), "ordered": "." in m.group(2)}))
            i += 1
            continue
        para = [line]
        i += 1
        while i < n:
            nxt = lines[i]
            if (_CODE_BLOCK_RE.match(nxt) or _HEADER_RE.match(nxt) or
                    _LIST_RE.match(nxt) or _HR_RE.match(nxt) or nxt.strip() == ''):
                break
            para.append(nxt)
            i += 1
        blocks.append(("p", ' '.join(para), {}))
    return blocks


class Signals(QObject):
    """工作线程 -> GUI 线程的信号桥"""
    append_msg = pyqtSignal(str, str)
    tool_call = pyqtSignal(str, object)
    tool_result = pyqtSignal(str, str)
    typing_start = pyqtSignal()
    typing_stop = pyqtSignal()
    set_status = pyqtSignal(str, str)
    send_done = pyqtSignal()
    login_result = pyqtSignal(bool, str)
    inject_result = pyqtSignal(bool, str)


class ImprovedSyntaxHighlighter(QSyntaxHighlighter):
    MAX_LINES = 200
    
    def __init__(self, document, colors):
        super().__init__(document)
        self.colors = colors
        self.keywords = {
            'def', 'class', 'import', 'from', 'return', 'if', 'else',
            'elif', 'for', 'while', 'try', 'except', 'with', 'as',
            'in', 'not', 'and', 'or', 'True', 'False', 'None', 'lambda',
            'pass', 'break', 'continue', 'yield', 'global', 'nonlocal',
            'async', 'await', 'self', 'print', 'raise', 'finally', 'assert',
            'del', 'exec', 'eval', 'is'
        }

    def highlightBlock(self, text):
        if len(text) > 5000 or text.count('\n') > self.MAX_LINES:
            return
        
        c = self.colors
        fmt_key = QTextCharFormat()
        fmt_key.setForeground(QColor(c["hl_keyword"]))
        fmt_key.setFontWeight(QFont.Weight.Bold)

        fmt_num = QTextCharFormat()
        fmt_num.setForeground(QColor(c["hl_number"]))

        fmt_str = QTextCharFormat()
        fmt_str.setForeground(QColor(c["hl_string"]))

        fmt_com = QTextCharFormat()
        fmt_com.setForeground(QColor(c["hl_comment"]))
        fmt_com.setFontItalic(True)

        i = 0
        n = len(text)
        in_string = False
        string_char = None
        in_comment = False
        
        while i < n:
            if not in_string and not in_comment and text[i:i+1] == '#':
                in_comment = True
                start = i
                self.setFormat(start, n - start, fmt_com)
                break
            
            if not in_comment and not in_string and text[i] in ('"', "'"):
                in_string = True
                string_char = text[i]
                start = i
                i += 1
                while i < n:
                    if text[i] == string_char and (i == 0 or text[i-1] != '\\'):
                        self.setFormat(start, i - start + 1, fmt_str)
                        in_string = False
                        string_char = None
                        i += 1
                        break
                    i += 1
                if in_string:
                    self.setFormat(start, n - start, fmt_str)
                    in_string = False
                continue
            
            if in_string:
                i += 1
                continue
            
            if not in_comment:
                if _NUMBER_RE.match(text[i:]):
                    m = _NUMBER_RE.match(text[i:])
                    if m:
                        self.setFormat(i, len(m.group()), fmt_num)
                        i += len(m.group())
                        continue
                
                for kw in self.keywords:
                    if text[i:].startswith(kw) and (i + len(kw) == n or not text[i+len(kw)].isalnum()):
                        self.setFormat(i, len(kw), fmt_key)
                        i += len(kw)
                        break
                else:
                    i += 1
            else:
                i += 1


class CodeBlock(QFrame):
    def __init__(self, code, lang, colors, font_size, on_copy):
        super().__init__()
        self.setObjectName("codeBlock")
        self.setStyleSheet(
            f"QFrame#codeBlock {{ background:{colors['code_border']}; "
            f"border-radius:6px; }}"
        )
        v = QVBoxLayout(self)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(0)

        header = QFrame()
        header.setStyleSheet(
            f"QFrame {{ background:{colors['code_border']}; "
            f"border-top-left-radius:6px; border-top-right-radius:6px; }}"
        )
        h = QHBoxLayout(header)
        h.setContentsMargins(10, 2, 6, 2)
        lang_lbl = QLabel(f"  {lang}  ")
        lang_lbl.setStyleSheet(f"color:{colors['text3']}; background:transparent;")
        lang_lbl.setFont(QFont(FONT_MONO, max(8, font_size - 2)))
        copy_btn = QPushButton("📋 复制")
        copy_btn.setStyleSheet(
            f"QPushButton {{ color:{colors['text3']}; background:transparent; "
            f"border:none; padding:2px 6px; }} "
            f"QPushButton:hover {{ color:{colors['fg']}; }}"
        )
        copy_btn.setFont(QFont(FONT_UI, max(8, font_size - 2)))
        copy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        copy_btn.clicked.connect(lambda: on_copy(code))
        h.addWidget(lang_lbl)
        h.addStretch(1)
        h.addWidget(copy_btn)
        v.addWidget(header)

        body = QTextEdit()
        body.setReadOnly(True)
        body.setPlainText(code)
        body.setStyleSheet(
            f"QTextEdit {{ background:{colors['code_bg']}; color:{colors['code_text']}; "
            f"border:none; border-bottom-left-radius:6px; border-bottom-right-radius:6px; "
            f"padding:8px 10px; }}"
        )
        body.setFont(QFont(FONT_MONO, font_size))
        body.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        body.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        line_count = code.count('\n') + 1
        max_height = min(420, 60 + line_count * int(font_size * 1.6))
        body.setMaximumHeight(max_height)
        
        if line_count <= ImprovedSyntaxHighlighter.MAX_LINES:
            ImprovedSyntaxHighlighter(body.document(), colors)
        v.addWidget(body)


class ToolBlock(QFrame):
    def __init__(self, seq, name, args, colors, font_size):
        super().__init__()
        self.colors = colors
        self.font_size = font_size
        self.seq = seq
        self.name = name
        self.status = "running"
        self.expanded = False
        self.start_time = datetime.now()

        self.setObjectName("toolBlock")
        self.setStyleSheet(
            f"QFrame#toolBlock {{ background:{colors['card']}; "
            f"border:1px solid {colors['border']}; border-radius:6px; }}"
        )

        v = QVBoxLayout(self)
        v.setContentsMargins(8, 4, 8, 4)
        v.setSpacing(4)

        self._header = QPushButton()
        self._header.setObjectName("toolHeader")
        self._header.setStyleSheet(
            f"QPushButton#toolHeader {{ background:transparent; border:none; "
            f"color:{colors['accent']}; text-align:left; padding:4px; }} "
            f"QPushButton#toolHeader:hover {{ background:{colors['border']}; }}"
        )
        self._header.setFont(QFont(FONT_UI, 9, QFont.Weight.Bold))
        self._header.setCursor(Qt.CursorShape.PointingHandCursor)
        self._header.clicked.connect(self._toggle)

        if isinstance(args, str):
            try:
                args_obj = json.loads(args)
                args_str = json.dumps(args_obj, ensure_ascii=False, indent=2)
            except Exception:
                args_str = args
        else:
            args_str = json.dumps(args, ensure_ascii=False, indent=2)
        if len(args_str) > 2000:
            args_str = args_str[:2000] + "\n... (参数过长，已截断)"

        self._body = QTextEdit()
        self._body.setReadOnly(True)
        self._body.setStyleSheet(
            f"QTextEdit {{ background:{colors['bg']}; color:{colors['text2']}; "
            f"border:1px solid {colors['border']}; border-radius:4px; padding:6px; }}"
        )
        self._body.setFont(QFont(FONT_MONO, max(8, font_size - 2)))
        self._body.setPlainText(f"    参数: \n{args_str}\n")
        self._body.setVisible(False)
        self._body.setFixedHeight(1)

        v.addWidget(self._header)
        v.addWidget(self._body)
        self._refresh_header()

    def _refresh_header(self):
        if self.expanded:
            icon = "▾"
        elif self.status == "success":
            icon = "✅"
        elif self.status == "failed":
            icon = "❌"
        else:
            icon = "▶"
        suffix = {"running": "⏳", "success": "✅", "failed": "❌"}[self.status]
        self._header.setText(f"{icon}  [#{self.seq}] {self.name} {suffix}")

    def _toggle(self):
        self.expanded = not self.expanded
        if self.expanded:
            self._body.setFixedHeight(self._body.sizeHint().height())
            self._body.setVisible(True)
        else:
            self._body.setVisible(False)
            self._body.setFixedHeight(1)
        self._refresh_header()

    def append_result(self, result, is_error, elapsed):
        if len(result) > 5000:
            display = result[:5000] + "\n... (结果过长，已截断)"
        else:
            display = result
        self.status = "failed" if is_error else "success"
        status_icon = "❌" if is_error else "✅"
        status_text = "失败" if is_error else "成功"
        status_code = ""
        cm = _STATUS_CODE_RE.search(result)
        if cm:
            status_code = f" (返回码: {cm.group(1)})"
        time_str = f"{elapsed:.3f}s" if elapsed is not None else "未知"
        text = (f"    状态: {status_icon} {status_text}{status_code}  |  耗时: {time_str}\n"
                f"    结果:\n{display}\n")
        self._body.append(text)
        if self.expanded:
            self._body.setFixedHeight(self._body.sizeHint().height())
        self._refresh_header()


class ChatMessage(QFrame):
    def __init__(self, role, text, colors, font_size, on_copy, msg_id=None):
        super().__init__()
        self.colors = colors
        self.msg_id = msg_id or str(uuid.uuid4())
        self.setObjectName("msg")
        self.setStyleSheet("QFrame#msg { background:transparent; }")

        root = QVBoxLayout(self)
        root.setContentsMargins(4, 4, 4, 4)
        root.setSpacing(2)

        top = QHBoxLayout()
        top.setContentsMargins(0, 0, 0, 0)
        top.setSpacing(8)

        avatar = QLabel()
        avatar.setFixedSize(28, 28)
        avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        avatar.setFont(QFont(FONT_UI, 12, QFont.Weight.Bold))

        name = QLabel()
        name.setFont(QFont(FONT_UI, 9, QFont.Weight.Bold))
        ts = QLabel(datetime.now().strftime("%H:%M"))
        ts.setFont(QFont(FONT_UI, 8))
        ts.setStyleSheet(f"color:{colors['text3']}; background:transparent;")

        if role == "user":
            avatar.setText("🧑")
            avatar.setStyleSheet(
                f"background:{colors['accent']}; color:white; border-radius:14px;")
            name.setText("你")
            name.setStyleSheet(f"color:{colors['accent']}; background:transparent;")
            top.addStretch(1)
            top.addWidget(ts)
            top.addWidget(name)
            top.addWidget(avatar)
        else:
            avatar.setText("🦊")
            avatar.setStyleSheet(
                f"background:{colors['ok']}; color:white; border-radius:14px;")
            name.setText("Hermes" if role == "bot" else "工具")
            name.setStyleSheet(f"color:{colors['ok'] if role == 'bot' else colors['warn']};"
                               f"background:transparent;")
            top.addWidget(avatar)
            top.addWidget(name)
            top.addWidget(ts)
            top.addStretch(1)
        root.addLayout(top)

        bubble = QFrame()
        if role == "user":
            bubble.setObjectName("userBubble")
            bubble.setStyleSheet(
                f"QFrame#userBubble {{ background:{colors['accent']}; color:white; "
                f"border-radius:12px; }} "
                f"QLabel {{ color:white; background:transparent; }}")
            bh = QVBoxLayout(bubble)
            bh.setContentsMargins(14, 10, 14, 10)
            bh.setSpacing(4)
            lbl = QLabel(text)
            lbl.setWordWrap(True)
            lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            lbl.setFont(QFont(FONT_UI, font_size))
            bh.addWidget(lbl)
            root.addWidget(bubble)
        elif role == "tool":
            bubble.setObjectName("toolBubble")
            bubble.setStyleSheet(
                f"QFrame#toolBubble {{ background:{colors['bg']}; "
                f"border:1px solid {colors['border']}; border-radius:10px; }} "
                f"QLabel {{ color:{colors['text2']}; background:transparent; }}")
            bh = QVBoxLayout(bubble)
            bh.setContentsMargins(12, 8, 12, 8)
            lbl = QLabel(text)
            lbl.setWordWrap(True)
            lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            lbl.setFont(QFont(FONT_MONO, max(8, font_size - 1)))
            bh.addWidget(lbl)
            root.addWidget(bubble)
        else:
            bubble.setObjectName("botBubble")
            bubble.setStyleSheet(
                f"QFrame#botBubble {{ background:{colors['card']}; "
                f"border:1px solid {colors['border']}; border-radius:12px; }} "
                f"QLabel {{ background:transparent; }}")
            bh = QVBoxLayout(bubble)
            bh.setContentsMargins(14, 10, 14, 10)
            bh.setSpacing(4)
            self._render_markdown(text, bh, font_size, on_copy)
            root.addWidget(bubble)

    def _render_markdown(self, text, v, fs, on_copy):
        blocks = _parse_markdown(text)
        for btype, content, meta in blocks:
            if btype == "code":
                v.addWidget(CodeBlock(content, meta.get("lang", "text"),
                                      self.colors, fs, on_copy))
            elif btype in ("h1", "h2", "h3"):
                level = int(btype[1])
                size = fs + (4 - level) * 2
                lbl = QLabel(content)
                lbl.setWordWrap(True)
                lbl.setStyleSheet(f"color:{self.colors['fg']}; background:transparent;")
                lbl.setFont(QFont(FONT_UI, size, QFont.Weight.Bold))
                v.addWidget(lbl)
            elif btype == "hr":
                line = QFrame()
                line.setFixedHeight(1)
                line.setStyleSheet(f"background:{self.colors['border']};")
                v.addWidget(line)
            elif btype == "li":
                indent = meta.get("indent", 0) // 2
                bullet = f"{'　' * indent}• "
                lbl = QLabel(bullet + _inline_html(content, self.colors, fs))
                lbl.setWordWrap(True)
                lbl.setOpenExternalLinks(True)
                lbl.setTextInteractionFlags(
                    Qt.TextInteractionFlag.TextSelectableByMouse |
                    Qt.TextInteractionFlag.LinksAccessibleByMouse)
                lbl.setStyleSheet(f"color:{self.colors['fg']}; background:transparent;")
                lbl.setFont(QFont(FONT_UI, fs))
                v.addWidget(lbl)
            else:
                lbl = QLabel(_inline_html(content, self.colors, fs))
                lbl.setWordWrap(True)
                lbl.setOpenExternalLinks(True)
                lbl.setTextInteractionFlags(
                    Qt.TextInteractionFlag.TextSelectableByMouse |
                    Qt.TextInteractionFlag.LinksAccessibleByMouse)
                lbl.setStyleSheet(f"color:{self.colors['fg']}; background:transparent;")
                lbl.setFont(QFont(FONT_UI, fs))
                v.addWidget(lbl)


class TypingIndicator(QFrame):
    def __init__(self, colors, font_size):
        super().__init__()
        self.colors = colors
        self._dot = 0
        self.setObjectName("typing")
        self.setStyleSheet("QFrame#typing { background:transparent; }")
        root = QVBoxLayout(self)
        root.setContentsMargins(4, 4, 4, 4)
        root.setSpacing(4)

        top = QHBoxLayout()
        top.setSpacing(8)
        avatar = QLabel("🦊")
        avatar.setFixedSize(28, 28)
        avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        avatar.setFont(QFont(FONT_UI, 12, QFont.Weight.Bold))
        avatar.setStyleSheet(f"background:{colors['ok']}; color:white; border-radius:14px;")
        hl = QLabel("Hermes")
        hl.setStyleSheet(f"color:{colors['ok']}; background:transparent;")
        hl.setFont(QFont(FONT_UI, 9, QFont.Weight.Bold))
        top.addWidget(avatar)
        top.addWidget(hl)
        top.addStretch(1)
        root.addLayout(top)

        bubble = QFrame()
        bubble.setStyleSheet(
            f"background:{colors['card']}; border:1px solid {colors['border']}; "
            f"border-radius:12px;")
        bh = QVBoxLayout(bubble)
        bh.setContentsMargins(14, 10, 14, 10)
        self._lbl = QLabel()
        self._lbl.setStyleSheet(f"color:{colors['text3']}; background:transparent;")
        self._lbl.setFont(QFont(FONT_UI, font_size))
        bh.addWidget(self._lbl)
        root.addWidget(bubble, alignment=Qt.AlignmentFlag.AlignLeft)

        self._timer = QTimer(self)
        self._timer.setInterval(350)
        self._timer.timeout.connect(self._animate)
        self._timer.start()
        self._animate()

    def _animate(self):
        self._dot = (self._dot + 1) % 4
        dots = "  ".join(["●" if i < self._dot else "○" for i in range(3)])
        self._lbl.setText(f"  思考中  {dots}")

    def stop(self):
        self._timer.stop()


class ConfigDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("配置")
        self.setModal(True)
        self.resize(400, 200)
        
        layout = QVBoxLayout(self)
        form = QFormLayout()
        
        config = self._load_config()
        self.base_url = QLineEdit(config.get("base_url", "http://127.0.0.1:8000"))
        self.model = QLineEdit(config.get("model", "deepseek-browser"))
        self.api_key = QLineEdit(config.get("api_key", "sk-admin"))
        self.api_key.setEchoMode(QLineEdit.EchoMode.Password)
        
        form.addRow("API地址:", self.base_url)
        form.addRow("模型:", self.model)
        form.addRow("API Key:", self.api_key)
        layout.addLayout(form)
        
        btn_layout = QHBoxLayout()
        ok_btn = QPushButton("保存")
        ok_btn.clicked.connect(self._save)
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)
    
    def _load_config(self):
        try:
            if os.path.exists(_CONFIG_FILE):
                with open(_CONFIG_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception:
            pass
        return {}
    
    def _save(self):
        config = {
            "base_url": self.base_url.text().strip(),
            "model": self.model.text().strip(),
            "api_key": self.api_key.text().strip()
        }
        try:
            with open(_CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            QMessageBox.information(self, "成功", "配置已保存")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存失败: {e}")


class GUI(QMainWindow):
    MAX_MESSAGES = 300
    TOOLS_REFRESH_INTERVAL = 180000
    SCROLL_DEBOUNCE_MS = 50
    
    def __init__(self, agent: Agent):
        super().__init__()
        self.agent = agent
        self.setWindowTitle("Hermes Agent")
        self.resize(1080, 700)
        self.setMinimumSize(900, 560)

        self.is_sending = False
        self.is_auto_running = False
        self._tool_blocks = []
        self._tool_block_seq = 0
        self._typing_indicator: Optional[TypingIndicator] = None
        self._signals = Signals()
        self._worker_threads = []
        self._message_ids = deque(maxlen=500)
        self._scroll_pending = False
        self._stop_requested = False
        
        # 用简单的计数器替代
        self._op_count = 0

        self._load_settings()
        self._build_ui()
        self._connect_signals()

        self._pipeline = Pipeline(
            client=self.agent.client,
            max_rounds=self.agent.max_rounds,
            parallel=self.agent.parallel,
            max_workers=self.agent.max_workers,
        )
        self._shown_logs = 0

        self._setup_hot_reload()
        self._load_tools_once()

    # ==================== 热加载器 ====================
    
    def _setup_hot_reload(self):
        tools_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "agent_tools")
        if not os.path.exists(tools_dir):
            return
        try:
            from agent_tools.hot_reload import start_hot_reload
            start_hot_reload(watch_dir=tools_dir)
        except Exception:
            pass

    # ==================== 持久化 ====================

    def _load_settings(self):
        defaults = {"theme": "dark", "font_size": 11}
        try:
            if os.path.exists(_SETTINGS_FILE):
                with open(_SETTINGS_FILE, "r", encoding="utf-8") as f:
                    defaults.update(json.load(f))
        except Exception:
            pass
        self.font_size = max(9, min(20, defaults.get("font_size", 11)))
        self.theme = defaults.get("theme", "dark")
        if self.theme not in THEMES:
            self.theme = "dark"
        self.colors = dict(THEMES[self.theme])

    def _save_settings(self):
        try:
            with open(_SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump({"theme": self.theme, "font_size": self.font_size},
                          f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    # ==================== UI 构建 ====================

    def _build_ui(self):
        _ensure_fonts()
        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(240)
        root.addWidget(sidebar)

        sv = QVBoxLayout(sidebar)
        sv.setContentsMargins(14, 16, 14, 12)
        sv.setSpacing(8)

        logo_row = QHBoxLayout()
        logo_row.setSpacing(8)
        logo_badge = QLabel("🦊")
        logo_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_badge.setFixedSize(34, 34)
        logo_badge.setFont(QFont(FONT_UI, 15))
        logo_row.addWidget(logo_badge)
        logo = QLabel("Hermes")
        logo.setFont(QFont(FONT_UI, 16, QFont.Weight.Bold))
        logo_row.addWidget(logo)
        logo_row.addStretch(1)
        sv.addLayout(logo_row)

        self.status_label = QLabel("●  就绪")
        self.status_label.setFont(QFont(FONT_UI, 9))
        sv.addWidget(self.status_label)

        sv.addSpacing(6)

        new_btn = QPushButton("＋  新对话")
        new_btn.setObjectName("primary")
        new_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        new_btn.clicked.connect(self._new_chat)
        new_btn.setMinimumHeight(36)
        sv.addWidget(new_btn)

        config_btn = QPushButton("⚙️  配置")
        config_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        config_btn.clicked.connect(self._show_config)
        config_btn.setMinimumHeight(32)
        sv.addWidget(config_btn)

        login_btn = QPushButton("🔑  登录")
        login_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        login_btn.clicked.connect(self._login)
        login_btn.setMinimumHeight(32)
        sv.addWidget(login_btn)

        inject_btn = QPushButton("💉  注入提示词")
        inject_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        inject_btn.clicked.connect(self._inject_prompt)
        inject_btn.setMinimumHeight(32)
        sv.addWidget(inject_btn)

        sv.addSpacing(10)
        auto_label = QLabel("自动任务")
        auto_label.setFont(QFont(FONT_UI, 10, QFont.Weight.Bold))
        sv.addWidget(auto_label)

        self.goal_entry = QTextEdit()
        self.goal_entry.setPlaceholderText("例如：搭建一个简单的 Flask 博客")
        self.goal_entry.setMaximumHeight(66)
        sv.addWidget(self.goal_entry)

        btns = QHBoxLayout()
        btns.setSpacing(6)
        self._auto_start_btn = QPushButton("开始任务")
        self._auto_start_btn.setObjectName("primary")
        self._auto_start_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._auto_start_btn.clicked.connect(self._start_auto)
        self._auto_stop_btn = QPushButton("停止")
        self._auto_stop_btn.setObjectName("danger")
        self._auto_stop_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._auto_stop_btn.clicked.connect(self._stop_auto)
        btns.addWidget(self._auto_start_btn)
        btns.addWidget(self._auto_stop_btn)
        sv.addLayout(btns)

        sv.addSpacing(10)
        tools_label = QLabel("可用工具")
        tools_label.setFont(QFont(FONT_UI, 10, QFont.Weight.Bold))
        sv.addWidget(tools_label)

        self._tools_scroll = QScrollArea()
        self._tools_scroll.setWidgetResizable(True)
        self._tools_scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._tools_scroll.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self._tools_frame = QWidget()
        self._tools_layout = QVBoxLayout(self._tools_frame)
        self._tools_layout.setContentsMargins(6, 4, 4, 4)
        self._tools_layout.setSpacing(3)
        self._tools_layout.addStretch(1)
        self._tools_scroll.setWidget(self._tools_frame)
        sv.addWidget(self._tools_scroll, stretch=1)

        self._tools_timer = QTimer(self)
        self._tools_timer.setInterval(self.TOOLS_REFRESH_INTERVAL)
        self._tools_timer.timeout.connect(self._refresh_tools_list)
        self._tools_timer.start()

        self.theme_btn = QPushButton()
        self.theme_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.theme_btn.clicked.connect(self._cycle_theme)
        self.theme_btn.setMinimumHeight(32)
        sv.addWidget(self.theme_btn)

        main = QVBoxLayout()
        main.setContentsMargins(0, 0, 0, 0)
        main.setSpacing(0)
        root.addLayout(main, stretch=1)

        self.chat_scroll = QScrollArea()
        self.chat_scroll.setWidgetResizable(True)
        self.chat_scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.chat_container = QWidget()
        self.chat_layout = QVBoxLayout(self.chat_container)
        self.chat_layout.setContentsMargins(10, 10, 10, 10)
        self.chat_layout.addStretch(1)
        self.chat_scroll.setWidget(self.chat_container)
        main.addWidget(self.chat_scroll, stretch=1)

        self._chat_sb = self.chat_scroll.verticalScrollBar()
        self._chat_sb.rangeChanged.connect(self._on_chat_range_changed)

        input_frame = QFrame()
        ih = QHBoxLayout(input_frame)
        ih.setContentsMargins(10, 8, 10, 8)
        
        self.input_text = QTextEdit()
        self.input_text.setMaximumHeight(90)
        self.input_text.installEventFilter(self)
        
        btn_widget = QWidget()
        btn_widget.setFixedWidth(80)
        btn_layout = QVBoxLayout(btn_widget)
        btn_layout.setContentsMargins(0, 0, 0, 0)
        btn_layout.setSpacing(4)
        
        self.send_btn = QPushButton("发送")
        self.send_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.send_btn.setFixedHeight(36)
        self.send_btn.clicked.connect(self._send)
        
        self.stop_btn = QPushButton("⏹ 停止")
        self.stop_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.stop_btn.setFixedHeight(36)
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self._stop_current)
        
        btn_layout.addWidget(self.send_btn)
        btn_layout.addWidget(self.stop_btn)
        
        ih.addWidget(self.input_text, stretch=1)
        ih.addWidget(btn_widget)
        main.addWidget(input_frame)

        self._apply_theme()

    def _load_tools_once(self):
        try:
            import tools
            items = list(tools.TOOLS.items())
        except Exception:
            items = []
        self._render_tools(items)

    def _refresh_tools_list(self):
        try:
            import tools
            items = list(tools.TOOLS.items())
        except Exception:
            items = []
        self._render_tools(items)

    def _render_tools(self, items: List[Tuple[str, dict]]):
        while self._tools_layout.count() > 1:
            item = self._tools_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
        
        if not items:
            item = QFrame(self._tools_frame)
            il = QVBoxLayout(item)
            il.setContentsMargins(8, 8, 8, 8)
            lbl = QLabel("⚠️ 无可用工具\n请检查 agent_tools 目录")
            lbl.setWordWrap(True)
            lbl.setStyleSheet(f"color:{self.colors['text3']}; background:transparent;")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            il.addWidget(lbl)
            self._tools_layout.insertWidget(0, item)
            return
        
        for name, meta in items:
            meta = meta or {}
            item = QFrame(self._tools_frame)
            item.setObjectName("toolItem")
            item.setStyleSheet(
                f"QFrame#toolItem {{ background:transparent; }} "
                f"QFrame#toolItem:hover {{ background:{self.colors['border']}; "
                f"border-radius:6px; }}")
            il = QVBoxLayout(item)
            il.setContentsMargins(8, 3, 8, 3)
            il.setSpacing(0)
            n_lbl = QLabel(name)
            n_lbl.setFont(QFont(FONT_MONO, 9, QFont.Weight.Bold))
            n_lbl.setStyleSheet(f"color:{self.colors['fg']}; background:transparent;")
            il.addWidget(n_lbl)
            desc = (meta.get("description") or "").strip()
            if desc:
                if len(desc) > 60:
                    desc = desc[:60] + "…"
                d_lbl = QLabel(desc)
                d_lbl.setWordWrap(True)
                d_lbl.setStyleSheet(
                    f"color:{self.colors['text3']}; background:transparent; "
                    f"font-size:8pt;")
                il.addWidget(d_lbl)
            self._tools_layout.insertWidget(self._tools_layout.count() - 1, item)

    def eventFilter(self, obj, event):
        if (obj is self.input_text and event.type() == event.Type.KeyPress and
                event.key() == Qt.Key.Key_Return):
            if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                self.input_text.insertPlainText("\n")
            else:
                # 使用 QTimer 延迟发送，避免事件循环阻塞
                QTimer.singleShot(0, self._send)
            return True
        return super().eventFilter(obj, event)

    def _connect_signals(self):
        s = self._signals
        s.append_msg.connect(self._append, Qt.ConnectionType.QueuedConnection)
        s.tool_call.connect(self._open_tool_block, Qt.ConnectionType.QueuedConnection)
        s.tool_result.connect(self._append_tool_result, Qt.ConnectionType.QueuedConnection)
        s.typing_start.connect(self._start_typing, Qt.ConnectionType.QueuedConnection)
        s.typing_stop.connect(self._stop_typing, Qt.ConnectionType.QueuedConnection)
        s.set_status.connect(self._set_status, Qt.ConnectionType.QueuedConnection)
        s.send_done.connect(self._on_done, Qt.ConnectionType.QueuedConnection)
        s.login_result.connect(self._login_result, Qt.ConnectionType.QueuedConnection)
        s.inject_result.connect(self._inject_result, Qt.ConnectionType.QueuedConnection)

    # ==================== 主题 ====================

    def _apply_theme(self):
        c = self.colors
        self.setStyleSheet(f"""
            QMainWindow {{ background:{c['bg']}; }}
            QWidget {{ background:{c['bg']}; color:{c['fg']};
                        font-family:'{FONT_UI}'; font-size:10pt; }}
            QFrame#sidebar {{ background:{c['card']};
                              border-right:1px solid {c['border']}; }}
            QLabel {{ background:transparent; }}
            QPushButton {{ background:transparent; color:{c['fg']};
                           border:1px solid transparent; border-radius:8px;
                           padding:6px 10px; text-align:left; }}
            QPushButton:hover {{ background:{c['border']}; }}
            QPushButton:pressed {{ background:{c['bg']}; }}
            QPushButton:disabled {{ color:{c['text3']}; }}
            QPushButton#primary {{ background:{c['accent']}; color:white;
                                   border:none; font-weight:bold; text-align:center; }}
            QPushButton#primary:hover {{ background:{c['accent']}; }}
            QPushButton#danger {{ background:transparent; color:{c['err']};
                                  border:1px solid {c['border']}; }}
            QPushButton#danger:hover {{ background:rgba(239,68,68,0.1); }}
            QTextEdit {{ background:{c['card']}; color:{c['fg']};
                         border:1px solid {c['border']}; border-radius:8px;
                         padding:6px; }}
            QScrollArea {{ background:transparent; border:none; }}
            QScrollBar:vertical {{ background:transparent; width:10px; }}
            QScrollBar::handle:vertical {{ background:{c['border']};
                                           border-radius:5px; min-height:30px; }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical
                {{ height:0; }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical
                {{ background:transparent; }}
        """)

        self.goal_entry.setStyleSheet(
            f"QTextEdit {{ background:{c['bg']}; color:{c['fg']}; "
            f"border:1px solid {c['border']}; border-radius:8px; padding:6px; "
            f"selection-background-color:{c['accent']}; }}")
        self.input_text.setStyleSheet(
            f"QTextEdit {{ background:{c['card']}; color:{c['fg']}; "
            f"border:1px solid {c['border']}; border-radius:10px; padding:8px; "
            f"selection-background-color:{c['accent']}; }}")

        self.send_btn.setStyleSheet(
            f"QPushButton {{ background:{c['accent']}; color:white; border:none; "
            f"border-radius:10px; font-weight:bold; padding:10px; }} "
            f"QPushButton:hover {{ background:{c['accent']}; }} "
            f"QPushButton:disabled {{ background:{c['border']}; color:{c['text3']}; }}"
        )
        
        self.stop_btn.setStyleSheet(
            f"QPushButton {{ background:#ef4444; color:white; border:none; "
            f"border-radius:10px; font-weight:bold; padding:6px; }} "
            f"QPushButton:hover {{ background:#dc2626; }} "
            f"QPushButton:disabled {{ background:{c['border']}; color:{c['text3']}; }}"
        )

        self._set_status(self.status_label.text().lstrip("●").strip() or "就绪", "ok")

    def _cycle_theme(self):
        idx = THEME_ORDER.index(self.theme)
        self.theme = THEME_ORDER[(idx + 1) % len(THEME_ORDER)]
        self.colors = dict(THEMES[self.theme])
        self._apply_theme()
        self.theme_btn.setText(f"{THEMES[self.theme]['icon']}  {THEMES[self.theme]['name']}")
        self._save_settings()

    # ==================== 消息渲染 ====================

    def _append(self, role: str, text: str):
        if not text:
            return
        
        msg_hash = f"{role}:{text[:50]}"
        if msg_hash in self._message_ids:
            return
        self._message_ids.append(msg_hash)
        
        msg = ChatMessage(role, text, self.colors, self.font_size, self._copy_to_clipboard)
        self._insert_widget(msg)
        self._scroll_bottom()
        self._trim_messages()

    def _insert_widget(self, widget: QWidget):
        if self.chat_layout.count() > 0:
            item = self.chat_layout.itemAt(self.chat_layout.count() - 1)
            if item and item.layout() is None and item.widget() is None:
                self.chat_layout.removeItem(item)
        
        self.chat_layout.addWidget(widget)
        self.chat_layout.addStretch(1)

    def _trim_messages(self):
        """限制消息数量，防止长时间对话导致 Widget 堆积"""
        count = 0
        widgets_to_remove = []
        
        # 遍历所有 widget（不包括最后的 stretch）
        for i in range(self.chat_layout.count() - 1):
            item = self.chat_layout.itemAt(i)
            if item and item.widget():
                count += 1
                if count > self.MAX_MESSAGES:
                    widgets_to_remove.append(item)
        
        # 删除多余的 widget
        for item in widgets_to_remove:
            w = item.widget()
            if w:
                # 如果是从 ToolBlock，从列表中移除
                if isinstance(w, ToolBlock):
                    try:
                        self._tool_blocks.remove(w)  # 从列表移除
                    except ValueError:
                        pass  # 如果已经不在列表中，忽略
                self.chat_layout.removeItem(item)
                w.deleteLater()

    def _scroll_bottom(self):
        if not self._scroll_pending:
            self._scroll_pending = True
            QTimer.singleShot(self.SCROLL_DEBOUNCE_MS, self._force_scroll_bottom)

    def _force_scroll_bottom(self):
        self._scroll_pending = False
        self._chat_sb.setValue(self._chat_sb.maximum())

    def _on_chat_range_changed(self, _min, _max):
        if self._chat_sb.maximum() - self._chat_sb.value() < 120:
            self._chat_sb.setValue(self._chat_sb.maximum())

    def _copy_to_clipboard(self, text):
        try:
            QApplication.clipboard().setText(text)
        except Exception:
            pass
        self.status_label.setText("已复制")
        QTimer.singleShot(1500, lambda: self.status_label.setText("就绪"))

    def _set_status(self, text: str, color: Optional[str] = None):
        self.status_label.setText(f"●  {text}")
        c = self.colors.get(color, self.colors["ok"])
        self.status_label.setStyleSheet(
            f"color:{c}; background:transparent; font-weight:bold; font-size:9pt;")

    # ==================== 打字指示器 ====================

    def _start_typing(self):
        if self._typing_indicator is None:
            self._typing_indicator = TypingIndicator(self.colors, self.font_size)
            self._insert_widget(self._typing_indicator)
            self._scroll_bottom()

    def _stop_typing(self):
        if self._typing_indicator is not None:
            self._typing_indicator.stop()
            for i in range(self.chat_layout.count() - 1):
                item = self.chat_layout.itemAt(i)
                if item and item.widget() == self._typing_indicator:
                    self.chat_layout.removeItem(item)
                    break
            self._typing_indicator.deleteLater()
            self._typing_indicator = None

    # ==================== 工具块 ====================

    def _open_tool_block(self, name: str, args) -> None:
        self._tool_block_seq += 1
        block = ToolBlock(self._tool_block_seq, name, args,
                          self.colors, self.font_size)
        self._tool_blocks.append(block)  # 使用列表，不用字典
        self._insert_widget(block)
        self._scroll_bottom()

    def _append_tool_result(self, name: str, result: str) -> None:
        # 使用列表查找（不用 tool_id）
        block = None
        for b in self._tool_blocks:
            if b.name == name and b.status == "running":
                block = b
                break
        
        if block is None:
            self._append("tool", f"[{name}] 结果: {result[:200]}...")
            return

        is_error = any(kw in result for kw in
                       ["错误", "失败", "Error", "error", "FAILED", "异常", "exception"])
        elapsed = (datetime.now() - block.start_time).total_seconds()
        block.append_result(result, is_error, elapsed)
        self._scroll_bottom()

    # ==================== 操作计数器 ====================

    def _increment_operations(self):
        self._op_count += 1
        self.stop_btn.setEnabled(True)

    def _decrement_operations(self):
        self._op_count = max(0, self._op_count - 1)
        self.stop_btn.setEnabled(self._op_count > 0)

    

    # ==================== 停止 ====================

    def _stop_current(self):
        """停止当前正在进行的操作"""
        # 直接执行，不需要锁
        if self._op_count == 0:
            return
        
        self._stop_requested = True
        
        if hasattr(self.agent, 'request_stop'):
            self.agent.request_stop()
            self._set_status("正在停止...", "err")
        
        if self._pipeline._running:
            self._pipeline.stop()
            self._set_status("正在停止任务...", "err")
        
        self._append("bot", "⏹ 正在停止当前操作...")

    # ==================== 发送 ====================

    def _send(self) -> None:
        text = self.input_text.toPlainText().strip()
        if not text or self.is_sending:
            return
        self.input_text.clear()
        self._append("user", text)

        self.is_sending = True
        self.send_btn.setEnabled(False)
        self.send_btn.setText("■")
        self.stop_btn.setEnabled(True)
        self._set_status("思考中...", "warn")
        self._signals.typing_start.emit()

        def _run():
            def on_tool_call(name, args):
                self._signals.tool_call.emit(name, args)

            def on_tool_result(name, result):
                self._signals.tool_result.emit(name, result)

            def on_thinking():
                self._signals.set_status.emit("思考中...", "warn")

            self.agent.on_tool_call = on_tool_call
            self.agent.on_tool_result = on_tool_result
            self.agent.on_thinking = on_thinking

            try:
                reply = self.agent.chat(text)
                self._signals.typing_stop.emit()
                self._signals.append_msg.emit("bot", reply)
                tracker = getattr(self.agent, "token_tracker", None)
                if tracker and tracker.call_count:
                    self._signals.append_msg.emit("tool", tracker.get_summary())
            except StopIteration:
                self._signals.typing_stop.emit()
                self._signals.append_msg.emit("bot", "⏹ 已停止")
            except (ConnectionError, urllib.error.URLError, TimeoutError) as e:
                self._signals.typing_stop.emit()
                self._signals.append_msg.emit("bot",
                    f"网络错误，无法连接 API 服务:\n{e}\n\n请确认后端服务已启动（8000/8001）")
            except Exception as e:
                self._signals.typing_stop.emit()
                self._signals.append_msg.emit("bot", f"错误: {e}")
            finally:
                self._signals.send_done.emit()

        t = threading.Thread(target=_run, daemon=True)
        self._worker_threads.append(t)
        t.start()

    def _on_done(self):
        self.is_sending = False
        self._stop_typing()
        self.send_btn.setEnabled(True)
        self.send_btn.setText("发送")
        self._decrement_operations()  # 已经调用了
        self._stop_requested = False
        self._set_status("就绪", "ok")

    def _new_chat(self):
        self.agent.reset()
        if hasattr(self.agent, 'token_tracker'):
            self.agent.token_tracker.reset()
        
        while self.chat_layout.count():
            item = self.chat_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
        
        self.chat_layout.addStretch(1)
        self._tool_blocks.clear()  # 列表用 clear()
        self._tool_block_seq = 0
        self._message_ids.clear()
        self._append("bot", "已开启新对话")

    # ==================== 配置 ====================

    def _show_config(self):
        dialog = ConfigDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self._reload_config()

    def _reload_config(self):
        try:
            if os.path.exists(_CONFIG_FILE):
                with open(_CONFIG_FILE, "r", encoding="utf-8") as f:
                    config = json.load(f)
                
                from client import Client
                new_client = Client(
                    base_url=config.get("base_url", "http://127.0.0.1:8000"),
                    model=config.get("model", "deepseek-browser"),
                    api_key=config.get("api_key", "sk-admin"),
                    agent_name=self.agent.client.agent_name
                )
                self.agent.client = new_client
                self._pipeline.client = new_client
                QMessageBox.information(self, "成功", "配置已重新加载")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"重新加载配置失败: {e}")

    # ==================== 登录 / 注入 ====================

    def _login(self):
        self._increment_operations()
        
        def _run():
            try:
                result = self.agent.client.login()
                msg = result.get("message", str(result))
                self._signals.login_result.emit(True, str(msg))
            except Exception as e:
                self._signals.login_result.emit(False, str(e))
            finally:
                self._decrement_operations()
        
        t = threading.Thread(target=_run, daemon=True)
        self._worker_threads.append(t)
        t.start()

    def _login_result(self, ok, msg):
        if ok:
            QMessageBox.information(self, "登录", msg)
        else:
            QMessageBox.critical(self, "错误", msg)

    def _inject_prompt(self):
        config = self._load_config_from_file()
        base = config.get("base_url", getattr(self.agent.client, "base_url", "http://127.0.0.1:8000"))
        
        self._increment_operations()

        def _run():
            try:
                try:
                    req = urllib.request.Request(f"{base}/status")
                    with urllib.request.urlopen(req, timeout=5) as resp:
                        status = json.loads(resp.read().decode("utf-8"))
                    if not status.get("logged_in"):
                        self._signals.inject_result.emit(False, "DeepSeek 未登录，请先点击[登录]")
                        return
                except Exception:
                    self._signals.inject_result.emit(False, "12.py (DeepSeek API) 未启动\n\n请先启动: python 12.py")
                    return

                req = urllib.request.Request(f"{base}/inject")
                with urllib.request.urlopen(req, timeout=60) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                if data.get("success"):
                    self._signals.inject_result.emit(
                        True, f"✅ 已注入提示词\n工具数: {data.get('tool_count', '?')}\n"
                              f"长度: {data.get('prompt_length', '?')} 字符")
                else:
                    self._signals.inject_result.emit(False, data.get("error", "未知错误"))
            except Exception as e:
                self._signals.inject_result.emit(False, f"注入失败:\n{e}")
            finally:
                self._decrement_operations()
        
        t = threading.Thread(target=_run, daemon=True)
        self._worker_threads.append(t)
        t.start()

    def _load_config_from_file(self):
        try:
            if os.path.exists(_CONFIG_FILE):
                with open(_CONFIG_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception:
            pass
        return {}

    def _inject_result(self, ok, msg):
        if ok:
            QMessageBox.information(self, "注入提示词", msg)
        else:
            QMessageBox.warning(self, "提示", msg)

    # ==================== 自动任务 ====================

    def _start_auto(self):
        goal = self.goal_entry.toPlainText().strip()
        if not goal:
            QMessageBox.warning(self, "提示", "请先输入目标")
            return
        if self._pipeline._running:
            QMessageBox.information(self, "提示", "自动任务已在运行")
            return

        self._append("user", f"[自动任务] {goal}")
        self.goal_entry.clear()
        self._auto_start_btn.setEnabled(False)
        self._auto_start_btn.setText("规划中...")
        self.send_btn.setEnabled(False)
        self.is_auto_running = True
        self._increment_operations()
        self._set_status("规划中...", "warn")
        
        with self._pipeline._lock:
            self._pipeline._logs = []
        self._shown_logs = 0

        def _run():
            try:
                res = self._pipeline.start(goal)
            except Exception as e:
                self._signals.append_msg.emit("bot", f"自动任务启动失败: {e}")
                self._signals.send_done.emit()
                return
            if not res.get("success"):
                detail = res.get("message") or res.get("error") or "未知原因"
                self._signals.append_msg.emit("bot", f"启动失败: {detail}")
                self._signals.send_done.emit()
                return
            self._auto_start_btn.setText("运行中...")
            QTimer.singleShot(100, self._poll_auto)

        t = threading.Thread(target=_run, daemon=True)
        self._worker_threads.append(t)
        t.start()

    def _poll_auto(self):
        if not self._pipeline._running:
            self._auto_done()
            return
        
        st = self._pipeline.get_status()
        logs = st["logs"]
        if len(logs) > self._shown_logs:
            for line in logs[self._shown_logs:]:
                self._append("tool", line)
            self._shown_logs = len(logs)

        plan = st["plan"]
        if plan["total"]:
            pct = f"{plan['done'] + plan['skipped']}/{plan['total']}（{plan['progress_pct']}%）"
            self._set_status(f"{st['mode']} {pct}", "warn")
        
        if self._pipeline._running:
            interval = 200 if plan.get('done', 0) < plan.get('total', 0) else 500
            QTimer.singleShot(interval, self._poll_auto)
        else:
            self._auto_done()

    def _stop_auto(self):
        if self._pipeline._running:
            self._pipeline.stop()
            self._set_status("停止中...", "err")
            self._append("bot", "⏹ 正在停止自动任务...")

    def _auto_done(self):
        if self._pipeline._running:
            return
        
        st = self._pipeline.get_status()
        logs = st["logs"]
        if len(logs) > self._shown_logs:
            for line in logs[self._shown_logs:]:
                self._append("tool", line)
            self._shown_logs = len(logs)
        
        self._set_status(st["mode"], "ok")
        self._append("bot", f"自动任务结束（{st['mode']}）")
        
        self._auto_start_btn.setEnabled(True)
        self._auto_start_btn.setText("开始任务")
        self.send_btn.setEnabled(True)
        self.is_auto_running = False
        self._decrement_operations()
        self._set_status("就绪", "ok")

    # ==================== 关闭 ====================

    def closeEvent(self, event):
        self._pipeline.stop()
        
        try:
            from agent_tools.hot_reload import stop_hot_reload
            stop_hot_reload()
        except Exception:
            pass
        
        for t in self._worker_threads:
            if t.is_alive():
                t.join(timeout=3)
        
        self._save_settings()
        super().closeEvent(event)

    def run(self):
        self._append("bot", "你好！我是 Hermes，有什么可以帮你的？")
        self.show()


def main():
    from client import Client
    
    config = {}
    try:
        if os.path.exists(_CONFIG_FILE):
            with open(_CONFIG_FILE, "r", encoding="utf-8") as f:
                config = json.load(f)
    except Exception:
        pass
    
    _agent_name = os.environ.get("HERMES_AGENT") or "hermes"
    client = Client(
        base_url=config.get("base_url", "http://127.0.0.1:8000"),
        model=config.get("model", "deepseek-browser"),
        api_key=config.get("api_key", "sk-admin"),
        agent_name=_agent_name
    )
    agent = Agent(client=client, max_rounds=100, parallel=True, max_workers=4)
    
    app = QApplication(sys.argv)
    app.setApplicationName("Hermes Agent")
    _ensure_fonts()
    
    gui = GUI(agent)
    gui.run()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()