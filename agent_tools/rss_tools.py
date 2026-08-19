# -*- coding: utf-8 -*-
"""
RSS阅读工具集 - 解析RSS订阅源
"""

import json
import os


def _parse_rss(args: dict) -> str:
    url = args.get('url', '')
    if not url:
        return "❌ 请提供RSS地址"
    try:
        import feedparser
        feed = feedparser.parse(url)
        items = []
        for entry in feed.entries[:10]:
            items.append({
                '标题': entry.get('title', ''),
                '链接': entry.get('link', ''),
                '摘要': entry.get('summary', '')[:200],
                '发布时间': entry.get('published', '')
            })
        return json.dumps({'成功': True, '订阅源': feed.feed.get('title', ''), '文章数': len(items), '文章': items}, ensure_ascii=False, indent=2)
    except ImportError:
        return "❌ 请安装 feedparser: pip install feedparser"
    except Exception as e:
        return f"❌ 解析失败: {e}"


def register_tools():
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import tools
    tools.register(name="parse_rss", description="解析RSS订阅源。参数: url(RSS地址)", parameters={"type": "object", "properties": {"url": {"type": "string"}}, "required": ["url"]}, func=_parse_rss)
    return 1


def unregister_tools():
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import tools
    for name in ["parse_rss"]:
        tools.TOOLS.pop(name, None)
