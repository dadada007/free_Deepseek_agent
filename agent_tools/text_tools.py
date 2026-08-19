# -*- coding: utf-8 -*-
"""
文本处理工具集 - 支持转换、统计、加密、格式化
"""

import os
import json
import re
import hashlib
import base64


def _import_jieba():
    try:
        import jieba
        return jieba
    except ImportError:
        return None


def _text_stats(args: dict) -> str:
    try:
        text = args.get('text', '')
        if not text:
            return "❌ 请提供文本内容"
        result = {
            '总字符数': len(text),
            '总字数（中文）': len(re.findall(r'[\u4e00-\u9fff]', text)),
            '总词数（英文）': len(re.findall(r'[a-zA-Z]+', text)),
            '行数': text.count('\n') + 1 if text else 0,
        }
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"❌ 统计失败: {e}"


def _encrypt_text(args: dict) -> str:
    try:
        text = args.get('text', '')
        method = args.get('method', 'md5')
        if not text:
            return "❌ 请提供文本内容"
        result = {'原文': text[:50], '方法': method}
        if method == 'md5':
            result['加密结果'] = hashlib.md5(text.encode()).hexdigest()
        elif method == 'sha1':
            result['加密结果'] = hashlib.sha1(text.encode()).hexdigest()
        elif method == 'sha256':
            result['加密结果'] = hashlib.sha256(text.encode()).hexdigest()
        elif method == 'base64':
            result['加密结果'] = base64.b64encode(text.encode()).decode()
        else:
            return f"❌ 不支持的方法: {method}"
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"❌ 加密失败: {e}"


def _convert_text(args: dict) -> str:
    try:
        text = args.get('text', '')
        operation = args.get('operation', 'upper')
        if not text:
            return "❌ 请提供文本内容"
        result = {'原文': text[:50], '操作': operation}
        if operation == 'upper':
            result['结果'] = text.upper()
        elif operation == 'lower':
            result['结果'] = text.lower()
        elif operation == 'capitalize':
            result['结果'] = text.capitalize()
        elif operation == 'reverse':
            result['结果'] = text[::-1]
        elif operation == 'strip':
            result['结果'] = text.strip()
        elif operation == 'remove_spaces':
            result['结果'] = text.replace(' ', '')
        else:
            return f"❌ 不支持的操作: {operation}"
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"❌ 转换失败: {e}"


def _extract_keywords(args: dict) -> str:
    try:
        text = args.get('text', '')
        top_n = args.get('top', 10)
        if not text:
            return "❌ 请提供文本内容"
        jieba = _import_jieba()
        if not jieba:
            return "❌ 请安装 jieba: pip install jieba"
        keywords = jieba.analyse.extract_tags(text, topK=top_n)
        return json.dumps({'成功': True, '关键词': keywords}, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"❌ 提取关键词失败: {e}"


def _markdown_to_html(args: dict) -> str:
    try:
        text = args.get('text', '')
        output = args.get('output', '')
        if not text:
            return "❌ 请提供Markdown内容"
        try:
            import markdown
        except ImportError:
            return "❌ 请安装 markdown: pip install markdown"
        html = markdown.markdown(text)
        if output:
            with open(output, 'w', encoding='utf-8') as f:
                f.write(f'<!DOCTYPE html><html><body>{html}</body></html>')
            result = {'输出': output, '大小': os.path.getsize(output)}
        else:
            result = {'HTML': html}
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"❌ 转换失败: {e}"


def register_tools():
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import tools
    tools.register(name="text_stats", description="统计文本信息。参数: text", parameters={"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]}, func=_text_stats)
    tools.register(name="encrypt_text", description="文本加密。参数: text, method(md5/sha1/sha256/base64)", parameters={"type": "object", "properties": {"text": {"type": "string"}, "method": {"type": "string"}}, "required": ["text"]}, func=_encrypt_text)
    tools.register(name="convert_text", description="文本转换。参数: text, operation(upper/lower/reverse等)", parameters={"type": "object", "properties": {"text": {"type": "string"}, "operation": {"type": "string"}}, "required": ["text"]}, func=_convert_text)
    tools.register(name="extract_keywords", description="提取关键词。参数: text, top", parameters={"type": "object", "properties": {"text": {"type": "string"}, "top": {"type": "integer"}}, "required": ["text"]}, func=_extract_keywords)
    tools.register(name="markdown_to_html", description="Markdown转HTML。参数: text, output", parameters={"type": "object", "properties": {"text": {"type": "string"}, "output": {"type": "string"}}, "required": ["text"]}, func=_markdown_to_html)
    return 5


def unregister_tools():
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import tools
    for name in ["text_stats", "encrypt_text", "convert_text", "extract_keywords", "markdown_to_html"]:
        tools.TOOLS.pop(name, None)
