# -*- coding: utf-8 -*-
"""
工具调用解析器 - 只提取 name 和 arguments 原始字符串
不解析任何 JSON，只做括号匹配提取
"""
import re
import logging

logger = logging.getLogger(__name__)


def extract_tool_calls(text: str) -> list:
    """
    从 AI 回复中提取工具调用
    1. 清理中文（提取最外层 [] 内容）
    2. 提取 name 原始字符串
    3. 提取 arguments 原始字符串
    4. 返回 name 和 arguments 原始字符串，不做任何解析
    """
    if not text:
        return []
    
    # 1. 找到最外层 [ 的位置
    start = text.find('[')
    if start == -1:
        return []
    
    # 2. 括号匹配找到对应的 ]（清理中文）
    bracket_count = 0
    in_string = False
    escape_next = False
    end = len(text)
    
    for i in range(start, len(text)):
        char = text[i]
        
        if escape_next:
            escape_next = False
            continue
        
        if char == '\\':
            escape_next = True
            continue
        
        if char == '"' and not escape_next:
            in_string = not in_string
            continue
        
        if not in_string:
            if char == '[':
                bracket_count += 1
            elif char == ']':
                bracket_count -= 1
                if bracket_count == 0:
                    end = i + 1
                    break
    
    # 3. 截取纯 JSON 结构（包含所有内容）
    json_str = text[start:end]
    
    # 4. 提取 name（用正则）
    name_match = re.search(r'"name":\s*"([^"]+)"', json_str)
    if not name_match:
        logger.warning("未找到 name 字段")
        return []
    name = name_match.group(1)
    
    # 5. 提取 arguments 原始字符串（用括号匹配，不解析）
    args_start = json_str.find('"arguments"')
    if args_start == -1:
        logger.warning("未找到 arguments 字段")
        return []
    
    # 找到 "arguments": 后面的 {
    colon_pos = json_str.find(':', args_start)
    if colon_pos == -1:
        return []
    
    brace_pos = json_str.find('{', colon_pos)
    if brace_pos == -1:
        return []
    
    # 括号匹配提取完整的 arguments
    args_bracket_count = 0
    args_in_string = False
    args_escape_next = False
    args_end = len(json_str)
    
    for i in range(brace_pos, len(json_str)):
        char = json_str[i]
        
        if args_escape_next:
            args_escape_next = False
            continue
        
        if char == '\\':
            args_escape_next = True
            continue
        
        if char == '"' and not args_escape_next:
            args_in_string = not args_in_string
            continue
        
        if not args_in_string:
            if char == '{':
                args_bracket_count += 1
            elif char == '}':
                args_bracket_count -= 1
                if args_bracket_count == 0:
                    args_end = i + 1
                    break
    
    # 6. 提取 arguments 原始字符串
    args_str = json_str[brace_pos:args_end]
    
    logger.debug(f"提取到工具: {name}")
    logger.debug(f"arguments 长度: {len(args_str)}")
    
    # 7. 返回 name 和 arguments 原始字符串
    return [{
        "id": "call_0",
        "type": "function",
        "function": {
            "name": name,
            "arguments": args_str  # 原始字符串，不做任何解析
        }
    }]