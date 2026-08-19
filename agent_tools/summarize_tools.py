# -*- coding: utf-8 -*-
"""
文本摘要工具集 - 支持文本摘要、关键词提取
"""

import json
import re
from collections import Counter
import os


def _summarize_text(args: dict) -> str:
    text = args.get('text', '')
    if not text:
        return "❌ 请提供文本"
    sentences = re.split(r'[。！？.!?]', text)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 10]
    summary = sentences[:3] if len(sentences) >= 3 else sentences
    words = re.findall(r'[\u4e00-\u9fff]+', text)
    if words:
        keywords = [w for w, c in Counter(words).most_common(5)]
    else:
        keywords = []
    return json.dumps({'成功': True, '摘要': '。'.join(summary), '关键词': keywords}, ensure_ascii=False, indent=2)


def register_tools():
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import tools
    tools.register(name="summarize_text", description="文本摘要。参数: text(文本内容)", parameters={"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]}, func=_summarize_text)
    return 1


def unregister_tools():
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import tools
    for name in ["summarize_text"]:
        tools.TOOLS.pop(name, None)
