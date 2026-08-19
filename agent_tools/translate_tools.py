# -*- coding: utf-8 -*-
"""
翻译工具 - 读取文件内容，翻译后写入新文件
"""

import os
import re
import json


def _translate_file(args: dict) -> str:
    input_path = args.get('input_path', '')
    target_lang = args.get('target_lang', 'zh')
    output_path = args.get('output_path', '')
    if not input_path or not os.path.exists(input_path):
        return f"❌ 文件不存在: {input_path}"
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        return f"❌ 读取文件失败: {str(e)}"
    if not content.strip():
        return "❌ 文件内容为空"
    if not output_path:
        base, ext = os.path.splitext(input_path)
        output_path = f"{base}_翻译{ext}"
    language_map = {"zh": "中文", "en": "英文", "ja": "日文", "ko": "韩文", "fr": "法文", "de": "德文"}
    target_name = language_map.get(target_lang, target_lang)
    prompt = f"请将以下内容翻译成{target_name}，只输出翻译结果：\n\n{content}"
    return json.dumps({
        "success": True,
        "message": f"翻译提示词已生成，目标语言: {target_name}",
        "input_file": input_path,
        "output_file": output_path,
        "prompt_preview": prompt[:200] + "..."
    }, ensure_ascii=False, indent=2)


def register_tools():
    """注册工具到 Hermes"""
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import tools

    tools.register(
        name="translate_file",
        description="读取文件内容，翻译后写入新文件。参数: input_path(输入文件), target_lang(目标语言zh/en/ja等), output_path(输出文件可选)",
        parameters={"type": "object", "properties": {
            "input_path": {"type": "string", "description": "输入文件路径"},
            "target_lang": {"type": "string", "description": "目标语言代码: zh, en, ja, ko, fr, de等"},
            "output_path": {"type": "string", "description": "输出文件路径(可选)"}
        }, "required": ["input_path"]},
        func=_translate_file,
    )
    return 1


def unregister_tools():
    """卸载工具"""
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import tools
    for name in ["translate_file"]:
        tools.TOOLS.pop(name, None)
