# -*- coding: utf-8 -*-
"""
HTML处理工具集 - 支持提取文本、链接、表格解析
"""

import json
import re
import os


def _import_bs4():
    try:
        from bs4 import BeautifulSoup
        return BeautifulSoup
    except ImportError:
        return None


def _extract_text(args: dict) -> str:
    try:
        html = args.get('html', '')
        if not html:
            return "❌ 请提供HTML内容"
        bs4 = _import_bs4()
        if bs4:
            soup = bs4(html, 'html.parser')
            text = soup.get_text(separator='\n', strip=True)
        else:
            text = re.sub(r'<[^>]+>', '', html)
            text = re.sub(r'\s+', ' ', text).strip()
        return json.dumps({'成功': True, '文本长度': len(text), '文本': text[:1000]}, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"❌ 提取文本失败: {e}"


def _extract_links(args: dict) -> str:
    try:
        html = args.get('html', '')
        if not html:
            return "❌ 请提供HTML内容"
        bs4 = _import_bs4()
        links = []
        if bs4:
            soup = bs4(html, 'html.parser')
            for a in soup.find_all('a', href=True):
                links.append({'文本': a.get_text(strip=True)[:100], '链接': a['href']})
        else:
            for match in re.finditer(r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>([^<]*)</a>', html, re.IGNORECASE):
                links.append({'文本': match.group(2).strip()[:100], '链接': match.group(1)})
        return json.dumps({'成功': True, '链接数量': len(links), '链接列表': links[:100]}, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"❌ 提取链接失败: {e}"


def _parse_table(args: dict) -> str:
    try:
        html = args.get('html', '')
        if not html:
            return "❌ 请提供HTML内容"
        bs4 = _import_bs4()
        if not bs4:
            return "❌ 请安装 beautifulsoup4: pip install beautifulsoup4"
        soup = bs4(html, 'html.parser')
        tables = []
        for table in soup.find_all('table'):
            rows = []
            for tr in table.find_all('tr'):
                row = []
                for td in tr.find_all(['td', 'th']):
                    row.append(td.get_text(strip=True))
                if row:
                    rows.append(row)
            if rows:
                tables.append(rows)
        return json.dumps({'成功': True, '表格数量': len(tables), '表格数据': tables[:10]}, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"❌ 解析表格失败: {e}"


def register_tools():
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import tools
    tools.register(name="extract_text", description="从HTML提取纯文本。参数: html", parameters={"type": "object", "properties": {"html": {"type": "string"}}, "required": ["html"]}, func=_extract_text)
    tools.register(name="extract_links", description="从HTML提取链接。参数: html", parameters={"type": "object", "properties": {"html": {"type": "string"}}, "required": ["html"]}, func=_extract_links)
    tools.register(name="parse_table", description="从HTML解析表格。参数: html", parameters={"type": "object", "properties": {"html": {"type": "string"}}, "required": ["html"]}, func=_parse_table)
    return 3


def unregister_tools():
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import tools
    for name in ["extract_text", "extract_links", "parse_table"]:
        tools.TOOLS.pop(name, None)
