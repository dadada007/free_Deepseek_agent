# -*- coding: utf-8 -*-
"""工具注册中心 - 统一解析 arguments + JSON 转义"""
import json
import logging
from typing import Dict, Any, Callable, Optional
import ast
logger = logging.getLogger(__name__)

# 工具注册表
TOOLS: Dict[str, dict] = {}


def register(name: str, description: str, parameters: dict, func: Callable):
    """注册工具"""
    TOOLS[name] = {
        "name": name,
        "description": description,
        "parameters": parameters,
        "func": func,
    }


def get_schemas() -> list:
    """获取所有工具的 OpenAI 格式 schema"""
    schemas = []
    for tool in TOOLS.values():
        schemas.append({
            "type": "function",
            "function": {
                "name": tool["name"],
                "description": tool["description"],
                "parameters": tool["parameters"],
            }
        })
    return schemas


def _resolve_name(name: str) -> Optional[str]:
    """大小写不敏感解析工具名"""
    if name in TOOLS:
        return name
    target = (name or "").strip().lower()
    if not target:
        return None
    for key in TOOLS:
        if key.lower() == target:
            return key
    return None


def _parse_arguments(args) -> dict:
    """
    统一解析 arguments
    支持：dict、JSON 字符串、原始字符串
    同时处理所有字符串参数的 JSON 转义
    """
    # 1. 如果是字符串，用 json.loads() 解析
    if isinstance(args, str):
        try:
            args = ast.literal_eval(f'"args"')
        except (ValueError, SyntaxError):
            logger.warning(f"arguments 字符串解析失败，返回空 dict")
            return {}
    
    # 2. 如果不是 dict，返回空
    if not isinstance(args, dict):
        return {}
    
    # 3. 统一处理所有字符串参数的 JSON 转义
    for key, value in args.items():
        if isinstance(value, str) and value:
            try:
                # 将 JSON 转义转换为真正字符
                args[key] = ast.literal_eval(f'"{value}"')
                
            except (ValueError, SyntaxError):
                # 如果包含未转义的双引号，尝试直接替换
                try:
                    fixed = value.replace('\\"', '"').replace('\\\\', '\\')
                    args[key] = ast.literal_eval(f'"{fixed}"')
                except (ValueError, SyntaxError):
                    # 实在不行，保持原样
                    pass
    
    return args


def execute(name: str, args) -> str:
    """执行工具（大小写不敏感）"""
    resolved = _resolve_name(name)
    if resolved is None:
        return f"错误: 未知工具 '{name}'"
    
    # 统一解析 arguments
    parsed_args = _parse_arguments(args)
    
    try:
        result = TOOLS[resolved]["func"](parsed_args)
        return str(result)
    except Exception as e:
        logger.error(f"工具执行失败: {resolved} - {e}")
        return f"错误: {e}"


def build_system_prompt() -> str:
    """从已注册工具生成系统提示词"""
    base = """【系统指令】请严格遵守以下规则：
⚠️ 最高优先级规则（违反将导致系统异常）
重要：一次只能调用一个工具；写入后发现出现语法问题，就精准修复，不要重写全部。
1. 
当需要调用工具时，必须且只能输出"目的：+ JSON数组"格式。禁止在JSON前后添加任何自然语言、解释、问候或总结。
2. 
当不需要调用工具时，正常用自然语言回复，禁止输出JSON。
3. 
禁止编造工具调用结果。必须等待真实工具返回后再处理。
🔁 强制思维链（每次响应前必须在内部执行，不输出给用户）
步骤1：判断用户请求是否需要调用工具？
步骤2：如果需要 → 走工具协议；如果不需要 → 走自然语言回复。
步骤3：如果需要工具，判断调用哪个工具、填什么参数。
步骤4：按正确格式输出。
📐 标准输出格式示例（必须严格模仿）
【示例1：单工具调用】
用户："读取 C:/temp/config.ini 的内容"
模型输出：
目的：读取配置文件内容以便查看当前设置。
```json
[{"name": "read_file", "arguments": {"file_path": "C:/temp/config.ini"}}]
【示例3：执行终端命令】
用户："查看当前目录下所有 py 文件"
模型输出：
目的：列出当前目录下的所有 Python 文件。
```json
[{"name": "execute_command", "arguments": {"command": "dir *.py"}}]
【示例4：不需要工具时】
用户："你好，你是谁？"
模型输出：
我是 Hermes，一个本地运行的软件工程 AI 助手，可以在 Windows 环境下帮你读写文件、执行命令、管理代码等。有什么可以帮你的？
【❌ 错误示例（绝对禁止模仿）】
❌ 好的，我来帮你读取文件。目的：读取文件。 [{"name":"read_file",...}] 有什么需要再找我。
→ 错误原因：JSON前后加了多余文字
❌ 目的：读取文件。{"name": "read_file", "arguments": {"file_path": "C:/temp/a.py"}}
→ 错误原因：JSON 必须用数组格式 [] 包裹，不能是裸对象
❌ [{"name": "read_file", "arguments": {"file_path": "C: emp.py"}}]
→ 错误原因：Windows 路径用了单反斜杠，     会被解析为制表符
Windows 路径写法（极其重要，反复强调）
所有路径参数必须使用以下两种格式之一：
● 
正确格式A：{"file_path": "C:/temp/a.py"}  ← 正斜杠（推荐）
● 
正确格式B：{"file_path": "C: emp.py"} ← 双反斜杠
● 
❌ 绝对禁止：{"file_path": "C:    emp.py"} ← 单反斜杠（    → 制表符，路径损坏）
适用此规则的所有参数名（不限于）：
file_path, path, command, output, source, archive, old_path, new_path, input_path, output_dir, backup_dir, repo_path, directory, dst, src, config, data
content 参数换行规则
write_file、append_file、generate_word、generate_pdf 的 content 参数：
● 
✅ 正确：用 
 表示换行（JSON 标准转义）
● 
❌ 禁止：[[newline]]、、{newline}、
 等非标准占位符
● 
代码缩进必须用空格，确保语法正确
工具调用失败处理
● 
如果工具返回失败信息，禁止盲目重试
● 
必须立即向用户反馈错误原因和失败信息
● 
请求用户提供正确的参数或指导
● 
示例："工具调用失败：文件 'C:/temp/not_exist.py' 不存在，请确认路径是否正确。

回复风格
● 
简洁、专业、中文

 ## 工具查询（重要）
    - 不要凭记忆猜测工具名，先用以下工具查询：
      - `list_categories` — 查看所有工具分类
      - `list_tools` — 查看全部工具（按分类）
      - `search_tools` — 按关键词搜索工具（如 "图片"、"压缩"）
      - `category_tools` — 按分类查询工具（如 "文件操作"）
"""
    lines = [base]
   
    return "\n".join(lines)