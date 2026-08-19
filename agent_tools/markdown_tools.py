# -*- coding: utf-8 -*-
"""
Markdown处理工具集 - 支持转HTML、提取标题、生成目录
"""

import os
import json
import re


def _import_markdown():
    try:
        import markdown
        return markdown
    except ImportError:
        return None


def _md_to_html(args: dict) -> str:
    try:
        text = args.get('text', '')
        output = args.get('output', '')
        extensions = args.get('extensions', ['extra', 'codehilite'])
        if not text:
            return "❌ 请提供Markdown内容"
        md = _import_markdown()
        if not md:
            return "❌ 请安装 markdown: pip install markdown"
        html = md.markdown(text, extensions=extensions)
        if output:
            with open(output, 'w', encoding='utf-8') as f:
                f.write(f'<!DOCTYPE html><html><head><meta charset="utf-8"><title>Markdown</title></head><body>{html}</body></html>')
            result = {'成功': True, '输出': output, '大小': os.path.getsize(output)}
        else:
            result = {'成功': True, 'HTML': html}
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"❌ 转换失败: {e}"


def _extract_headers(args: dict) -> str:
    try:
        text = args.get('text', '')
        if not text:
            return "❌ 请提供Markdown内容"
        headers = []
        for line in text.split('\n'):
            match = re.match(r'^(#{1,6})\s+(.+)$', line)
            if match:
                level = len(match.group(1))
                title = match.group(2).strip()
                headers.append({'级别': level, '标题': title})
        return json.dumps({'成功': True, '标题数量': len(headers), '标题列表': headers}, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"❌ 提取标题失败: {e}"


def _generate_toc(args: dict) -> str:
    try:
        text = args.get('text', '')
        indent = args.get('indent', 2)
        if not text:
            return "❌ 请提供Markdown内容"
        headers = []
        for line in text.split('\n'):
            match = re.match(r'^(#{1,6})\s+(.+)$', line)
            if match:
                level = len(match.group(1))
                title = match.group(2).strip()
                headers.append((level, title))
        toc_lines = []
        for level, title in headers:
            prefix = ' ' * (level - 1) * indent
            anchor = re.sub(r'[^\w\-]', '-', title.lower())
            toc_lines.append(f"{prefix}- [{title}](#{anchor})")
        toc = '\n'.join(toc_lines)
        return json.dumps({'成功': True, '目录': toc, '标题数量': len(headers)}, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"❌ 生成目录失败: {e}"


def register_tools():
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import tools
    tools.register(name="md_to_html", description="Markdown转HTML。参数: text, output(可选)", parameters={"type": "object", "properties": {"text": {"type": "string"}, "output": {"type": "string"}}, "required": ["text"]}, func=_md_to_html)
    tools.register(name="extract_headers", description="提取Markdown标题。参数: text", parameters={"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]}, func=_extract_headers)
    tools.register(name="generate_toc", description="生成Markdown目录。参数: text, indent", parameters={"type": "object", "properties": {"text": {"type": "string"}, "indent": {"type": "integer"}}, "required": ["text"]}, func=_generate_toc)
    return 3


def unregister_tools():
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import tools
    for name in ["md_to_html", "extract_headers", "generate_toc"]:
        tools.TOOLS.pop(name, None)
