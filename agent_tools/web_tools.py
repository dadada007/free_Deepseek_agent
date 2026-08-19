# -*- coding: utf-8 -*-
"""
网络爬虫工具集 - 支持网页抓取、内容提取、链接分析
"""

import re
import json
import os


def _import_requests():
    try:
        import requests
        return requests
    except ImportError:
        return None


def _import_bs4():
    try:
        from bs4 import BeautifulSoup
        return BeautifulSoup
    except ImportError:
        return None


def _extract_title(html):
    match = re.search(r'<title>(.*?)</title>', html, re.IGNORECASE)
    return match.group(1).strip() if match else '未找到标题'


def _fetch_url(args: dict) -> str:
    try:
        url = args.get('url', '')
        timeout = args.get('timeout', 10)
        if not url:
            return "❌ 请提供 URL 地址"
        requests = _import_requests()
        if not requests:
            return "❌ 请安装 requests: pip install requests"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        resp = requests.get(url, timeout=timeout, headers=headers)
        resp.encoding = resp.apparent_encoding or 'utf-8'
        result = {
            'url': url, 'status_code': resp.status_code,
            'content_length': len(resp.text),
            'title': _extract_title(resp.text),
            'content_preview': resp.text[:2000] + '...' if len(resp.text) > 2000 else resp.text
        }
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"❌ 抓取失败: {e}"


def _extract_links(args: dict) -> str:
    try:
        url = args.get('url', '')
        max_links = args.get('max_links', 50)
        if not url:
            return "❌ 请提供 URL 地址"
        requests = _import_requests()
        if not requests:
            return "❌ 请安装 requests: pip install requests"
        bs4 = _import_bs4()
        if not bs4:
            return "❌ 请安装 beautifulsoup4: pip install beautifulsoup4"
        headers = {'User-Agent': 'Mozilla/5.0'}
        resp = requests.get(url, timeout=10, headers=headers)
        soup = bs4(resp.text, 'html.parser')
        links = []
        for a in soup.find_all('a', href=True):
            href = a.get('href', '')
            text = a.get_text(strip=True)[:100]
            links.append({'text': text if text else '无文本', 'url': href})
            if len(links) >= max_links:
                break
        return json.dumps({'url': url, 'total_links': len(links), 'links': links}, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"❌ 提取链接失败: {e}"


def _search_web(args: dict) -> str:
    try:
        url = args.get('url', '')
        keyword = args.get('keyword', '')
        if not url or not keyword:
            return "❌ 请提供 URL 和关键词"
        requests = _import_requests()
        if not requests:
            return "❌ 请安装 requests"
        headers = {'User-Agent': 'Mozilla/5.0'}
        resp = requests.get(url, timeout=10, headers=headers)
        resp.encoding = 'utf-8'
        matches = []
        lines = resp.text.split('\n')
        for i, line in enumerate(lines):
            if keyword.lower() in line.lower():
                matches.append({'line': i + 1, 'content': line.strip()[:200]})
                if len(matches) >= 20:
                    break
        return json.dumps({'url': url, 'keyword': keyword, 'matches': matches, 'total_matches': len(matches)}, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"❌ 搜索失败: {e}"


def _web_screenshot(args: dict) -> str:
    try:
        url = args.get('url', '')
        output = args.get('output', 'screenshot.png')
        if not url:
            return "❌ 请提供 URL 地址"
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
        except ImportError:
            return "❌ 请安装 selenium: pip install selenium"
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        driver = webdriver.Chrome(options=options)
        driver.get(url)
        driver.save_screenshot(output)
        driver.quit()
        return f"✅ 截图已保存: {output}"
    except Exception as e:
        return f"❌ 截图失败: {e}"


def register_tools():
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import tools
    tools.register(name="fetch_url", description="抓取网页内容。参数: url, timeout, render", parameters={"type": "object", "properties": {"url": {"type": "string"}, "timeout": {"type": "integer"}}, "required": ["url"]}, func=_fetch_url)
    tools.register(name="extract_links", description="提取页面链接。参数: url, max_links", parameters={"type": "object", "properties": {"url": {"type": "string"}, "max_links": {"type": "integer"}}, "required": ["url"]}, func=_extract_links)
    tools.register(name="search_web", description="搜索网页内容。参数: url, keyword", parameters={"type": "object", "properties": {"url": {"type": "string"}, "keyword": {"type": "string"}}, "required": ["url", "keyword"]}, func=_search_web)
    tools.register(name="web_screenshot", description="获取网页截图。参数: url, output", parameters={"type": "object", "properties": {"url": {"type": "string"}, "output": {"type": "string"}}, "required": ["url"]}, func=_web_screenshot)
    return 4


def unregister_tools():
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import tools
    for name in ["fetch_url", "extract_links", "search_web", "web_screenshot"]:
        tools.TOOLS.pop(name, None)
