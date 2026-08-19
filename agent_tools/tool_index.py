# -*- coding: utf-8 -*-
"""工具索引查询模块 - 完全自动从 tools.TOOLS 读取

无需手动维护任何列表，自动从注册表生成分类、参数等信息。
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools import register, TOOLS


# ============ 工具分类映射（仅此一处需要维护） ============
# 将工具名映射到分类名，如果没有匹配则归入"其他"
# 这个字典是唯一需要手工维护的地方，但比之前少很多
CATEGORY_MAP = {
    # 文件操作
    "read_file": "文件操作",
    "write_file": "文件操作",
    "append_file": "文件操作",
    "delete_file": "文件操作",
    "rename_file": "文件操作",
    "move": "文件操作",
    "file_info": "文件操作",
    "edit_file": "文件操作",
    "search_by_name": "搜索与查找",
    "search_by_content": "搜索与查找",
    "search_by_size": "搜索与查找",
    "glob": "搜索与查找",
    "grep": "搜索与查找",
    
    # 目录与压缩
    "zip_files": "目录与压缩",
    "unzip_files": "目录与压缩",
    "tar_files": "目录与压缩",
    "untar_files": "目录与压缩",
    "list_archive_content": "目录与压缩",
    "sync_dirs": "目录与压缩",
    
    # 系统与进程
    "sys_info_detail": "系统与进程",
    "system_info": "系统与进程",
    "process_list": "系统与进程",
    "kill_process": "系统与进程",
    "disk_analysis": "系统与进程",
    "uptime": "系统与进程",
    "check_port": "系统与进程",
    
    # 终端与后台
    "run_background": "终端与后台",
    "task_output": "终端与后台",
    "kill_task": "终端与后台",
    
    # 环境变量
    "get_env": "环境变量",
    "set_env": "环境变量",
    "delete_env": "环境变量",
    
    # Git版本控制
    "git_status": "Git版本控制",
    "git_log": "Git版本控制",
    "git_diff": "Git版本控制",
    "git_commit": "Git版本控制",
    "git_branch": "Git版本控制",
    "git_merge": "Git版本控制",
    "git_stash": "Git版本控制",
    "git_reset": "Git版本控制",
    "git_push": "Git版本控制",
    "git_pull": "Git版本控制",
    "git_run": "Git版本控制",
    
    # 图片处理
    "image_info": "图片处理",
    "convert_image": "图片处理",
    "resize_image": "图片处理",
    "crop_image": "图片处理",
    "create_gif": "图片处理",
    
    # 二维码与条形码
    "generate_qr": "二维码与条形码",
    "decode_qr": "二维码与条形码",
    "batch_generate_qr": "二维码与条形码",
    "generate_barcode": "二维码与条形码",
    
    # 图表生成
    "line_chart": "图表生成",
    "bar_chart": "图表生成",
    "pie_chart": "图表生成",
    "scatter_plot": "图表生成",
    
    # 文档生成
    "generate_ppt": "文档生成",
    "generate_pdf": "文档生成",
    "generate_word": "文档生成",
    "generate_excel": "文档生成",
    
    # 邮件
    "set_email_config": "邮件",
    "send_email": "邮件",
    "read_emails": "邮件",
    "batch_send_email": "邮件",
    "get_email_config": "邮件",
    
    # CSV与数据
    "read_csv": "CSV与数据",
    "write_csv": "CSV与数据",
    "csv_to_json": "CSV与数据",
    
    # 配置与日志
    "read_ini": "配置与日志",
    "write_ini": "配置与日志",
    "set_ini_value": "配置与日志",
    "write_log": "配置与日志",
    "read_log": "配置与日志",
    "analyze_log": "配置与日志",
    "clear_log": "配置与日志",
    
    # 文本与字符串
    "hash_text": "文本与字符串",
    "hash_file": "文本与字符串",
    "verify_hash": "文本与字符串",
    "encrypt_text": "文本与字符串",
    "convert_text": "文本与字符串",
    "extract_keywords": "文本与字符串",
    "text_stats": "文本与字符串",
    "regex_match": "文本与字符串",
    "regex_replace": "文本与字符串",
    "diff_text": "文本与字符串",
    "sort_list": "文本与字符串",
    "sort_dict": "文本与字符串",
    
    # Markdown
    "md_to_html": "Markdown",
    "extract_headers": "Markdown",
    "generate_toc": "Markdown",
    
    # HTML与XML
    "extract_text": "HTML与XML",
    "extract_links": "HTML与XML",
    "parse_table": "HTML与XML",
    "parse_xml": "HTML与XML",
    "create_xml": "HTML与XML",
    
    # YAML
    "read_yaml": "YAML",
    "write_yaml": "YAML",
    
    # 网络与下载
    "http_request": "网络与下载",
    "download_file": "网络与下载",
    "batch_download": "网络与下载",
    "fetch_url": "网络与下载",
    "web_screenshot": "网络与下载",
    "parse_rss": "网络与下载",
    
    # 记忆系统RAG
    "rag_index": "记忆系统RAG",
    "rag_search": "记忆系统RAG",
    "rag_status": "记忆系统RAG",
    "rag_drop": "记忆系统RAG",
    "rag_clear": "记忆系统RAG",
    
    # 记忆管理
    "memory_save": "记忆管理",
    "memory_search": "记忆管理",
    "memory_summary": "记忆管理",
    "memory_forget": "记忆管理",
    "memory_status": "记忆管理",
    
    # 任务规划
    "plan_create": "任务规划",
    "plan_status": "任务规划",
    "plan_mark": "任务规划",
    "plan_next": "任务规划",
    "plan_reset": "任务规划",
    "plan_remove": "任务规划",
    
    # 定时任务
    "create_task": "定时任务",
    "list_tasks": "定时任务",
    "run_task": "定时任务",
    "delete_task": "定时任务",
    "toggle_task": "定时任务",
    
    # 股票模拟
    "get_stock_quote": "股票模拟",
    "get_stock_history": "股票模拟",
    "simulate_buy": "股票模拟",
    "simulate_sell": "股票模拟",
    "view_portfolio": "股票模拟",
    
    # 待办事项
    "todo_add": "待办事项",
    "todo_start": "待办事项",
    "todo_complete": "待办事项",
    "todo_list": "待办事项",
    
    # 随机生成
    "random_number": "随机生成",
    "random_string": "随机生成",
    "random_date": "随机生成",
    "generate_password": "随机生成",
    "check_password_strength": "随机生成",
    
    # 格式转换
    "hex_to_rgb": "格式转换",
    "rgb_to_hex": "格式转换",
    "convert_length": "格式转换",
    "convert_temp": "格式转换",
    "convert_currency": "格式转换",
    "format_code": "格式转换",
    
    # 验证
    "validate_email": "验证",
    "validate_phone": "验证",
    "validate_url": "验证",
    "validate_ip": "验证",
    
    # 日期与时间
    "now_time": "日期与时间",
    "date_calc": "日期与时间",
    "date_diff": "日期与时间",
    
    # 调试
    "debug_run_code": "调试",
    "debug_analyze": "调试",
    "debug_check_file": "调试",
    "debug_explain_error": "调试",
    
    # 其他
    "to_pinyin": "其他",
    "summarize_text": "其他",
    "calculate": "其他",
    "get_file_permission": "其他",
    "show_progress": "其他",
    "watch_directory": "其他",
    "parse_email": "其他",
    "extract_bookmarks": "其他",
    "audio_info": "其他",
    "video_info": "其他",
    "backup_db": "其他",
    
    # 工具索引查询（自引用）
    "list_tools": "工具索引",
    "search_tools": "工具索引",
    "category_tools": "工具索引",
    "list_categories": "工具索引",
}


def _get_tools_by_category() -> dict:
    """自动从 TOOLS 生成分类 -> 工具列表的映射"""
    categories = {}
    for tool_name in TOOLS.keys():
        category = CATEGORY_MAP.get(tool_name, "其他")
        if category not in categories:
            categories[category] = []
        categories[category].append(tool_name)
    return categories


def _get_tool_params(tool_name: str) -> dict:
    """自动从 TOOLS 读取工具参数信息"""
    tool_info = TOOLS.get(tool_name)
    if not tool_info:
        return {"params": {}, "required": []}
    
    params = tool_info.get("parameters", {})
    properties = params.get("properties", {})
    required = params.get("required", [])
    
    return {
        "params": properties,
        "required": required
    }


def list_categories(args: dict = None) -> str:
    """列出所有工具分类及每个分类的工具数量（自动从 TOOLS 生成）"""
    categories = _get_tools_by_category()
    lines = ["Hermes 工具分类:", "-" * 40]
    for i, (cat, tools) in enumerate(sorted(categories.items()), 1):
        lines.append(f"  {i:2d}. {cat} ({len(tools)} 个)")
    total_tools = len(TOOLS)
    lines.append(f"\n共 {len(categories)} 个分类，{total_tools} 个工具")
    return "\n".join(lines)


def list_tools(args: dict = None) -> str:
    """列出所有工具（按分类分组），自动从 TOOLS 读取"""
    categories = _get_tools_by_category()
    lines = ["Hermes 全部工具:", "=" * 50]
    
    for cat in sorted(categories.keys()):
        tools = sorted(categories[cat])
        lines.append(f"\n【{cat}】({len(tools)} 个):")
        lines.append("-" * 40)
        
        for name in tools:
            info = TOOLS.get(name)
            if not info:
                continue
            desc = info.get("description", "无描述")
            params_info = _get_tool_params(name)
            required = params_info.get("required", [])
            param_names = list(params_info.get("params", {}).keys())
            
            param_str = f" [参数: {', '.join(param_names)}]" if param_names else ""
            req_str = f" [必填: {', '.join(required)}]" if required else ""
            lines.append(f"  {name}: {desc}{param_str}{req_str}")
    
    lines.append(f"\n共 {len(TOOLS)} 个工具")
    return "\n".join(lines)


def category_tools(args: dict) -> str:
    """按分类查询工具（自动从 TOOLS 读取）"""
    category = args.get("category", "").strip()
    if not category:
        return "错误: 请提供 category 参数"
    
    categories = _get_tools_by_category()
    
    # 精确匹配
    if category in categories:
        tools = sorted(categories[category])
        return _format_category_tools(category, tools)
    
    # 模糊匹配
    matches = [cat for cat in categories.keys() if category.lower() in cat.lower()]
    if len(matches) == 1:
        tools = sorted(categories[matches[0]])
        return _format_category_tools(matches[0], tools)
    elif len(matches) > 1:
        return f"找到多个匹配分类: {', '.join(matches)}，请指定更精确的分类名"
    
    return f"未找到分类 '{category}'。可用分类: {', '.join(sorted(categories.keys()))}"


def _format_category_tools(category: str, tools: list) -> str:
    """格式化分类工具列表"""
    lines = [f"【{category}】({len(tools)} 个):", "-" * 40]
    for name in tools:
        info = TOOLS.get(name)
        if not info:
            continue
        desc = info.get("description", "无描述")
        params_info = _get_tool_params(name)
        required = params_info.get("required", [])
        param_names = list(params_info.get("params", {}).keys())
        
        param_str = f" [参数: {', '.join(param_names)}]" if param_names else ""
        req_str = f" [必填: {', '.join(required)}]" if required else ""
        lines.append(f"  {name}: {desc}{param_str}{req_str}")
    return "\n".join(lines)


def search_tools(args: dict) -> str:
    """按关键词搜索工具（名称或描述中包含关键词）"""
    keyword = args.get("keyword", "").strip().lower()
    if not keyword:
        return "错误: 请提供 keyword 参数"
    
    results = []
    categories = _get_tools_by_category()
    
    for name, info in TOOLS.items():
        desc = info.get("description", "").lower()
        if keyword in name.lower() or keyword in desc:
            # 找分类
            cat = "未分类"
            for c, tools in categories.items():
                if name in tools:
                    cat = c
                    break
            results.append((cat, name, info))
    
    if not results:
        return f"未找到与 '{keyword}' 相关的工具"
    
    lines = [f"搜索 '{keyword}' 结果 ({len(results)} 个):", "-" * 50]
    for cat, name, info in results:
        desc = info.get("description", "无描述")[:50]
        params_info = _get_tool_params(name)
        required = params_info.get("required", [])
        req_str = f" [必填: {', '.join(required)}]" if required else ""
        lines.append(f"[{cat}] {name}: {desc}{req_str}")
    
    return "\n".join(lines)


def tool_help(args: dict) -> str:
    """获取某个工具的详细帮助"""
    tool_name = args.get("tool", "").strip()
    if not tool_name:
        return "错误: 请提供 tool 参数"
    
    if tool_name not in TOOLS:
        return f"工具 '{tool_name}' 不存在"
    
    info = TOOLS[tool_name]
    params_info = _get_tool_params(tool_name)
    params = params_info.get("params", {})
    required = params_info.get("required", [])
    
    lines = [
        f"工具: {tool_name}",
        "=" * 50,
        f"描述: {info.get('description', '无描述')}",
        "",
        "参数:",
        "-" * 30,
    ]
    
    for name, schema in params.items():
        req = "*必填*" if name in required else "可选"
        desc = schema.get("description", "")
        typ = schema.get("type", "any")
        lines.append(f"  {name} ({typ}) {req}: {desc}")
    
    if not params:
        lines.append("  (无参数)")
    
    return "\n".join(lines)


# ============ 工具注册函数 ============
def register_tools():
    """注册工具索引查询功能到 TOOLS"""
    register(
        name="list_categories",
        description="列出所有工具分类及每个分类的工具数量。当用户问'有哪些分类'或'工具分类'时调用。",
        parameters={"type": "object", "properties": {}, "required": []},
        func=list_categories
    )
    
    register(
        name="list_tools",
        description="列出所有可用工具，按分类组织，包含描述和参数信息。当用户问'有哪些工具'或'全部工具'时调用。",
        parameters={"type": "object", "properties": {}, "required": []},
        func=list_tools
    )
    
    register(
        name="category_tools",
        description="按分类查询工具列表。当用户问'文件操作有哪些工具'或'XX分类的工具'时调用。",
        parameters={
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "description": "分类名称，如 '文件操作'、'图片处理'、'Git版本控制'"
                }
            },
            "required": ["category"]
        },
        func=category_tools
    )
    
    register(
        name="search_tools",
        description="按关键词搜索工具。当用户问'有没有XXX工具'或'搜索工具XXX'时调用。",
        parameters={
            "type": "object",
            "properties": {
                "keyword": {
                    "type": "string",
                    "description": "搜索关键词，如 '图片'、'压缩'、'git'"
                }
            },
            "required": ["keyword"]
        },
        func=search_tools
    )
    
    register(
        name="tool_help",
        description="获取某个工具的详细帮助信息，包括参数说明。当用户问'XX工具怎么用'或'XX工具的参数'时调用。",
        parameters={
            "type": "object",
            "properties": {
                "tool": {
                    "type": "string",
                    "description": "工具名称，如 'read_file'"
                }
            },
            "required": ["tool"]
        },
        func=tool_help
    )


# 自动注册（导入时执行）
register_tools()


# ============ 调试入口 ============
if __name__ == "__main__":
    print("=== 工具索引自动加载测试 ===\n")
    print(list_categories({}))
    print("\n" + "=" * 60 + "\n")
    print(list_tools({}))
    print("\n" + "=" * 60 + "\n")
    print(category_tools({"category": "文件操作"}))
    print("\n" + "=" * 60 + "\n")
    print(search_tools({"keyword": "图片"}))
