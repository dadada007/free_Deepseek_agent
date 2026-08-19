# -*- coding: utf-8 -*-
"""工具索引 - 从 TOOLS 注册表自动生成

提供：
- 按分类列出工具
- 按关键词搜索工具
- 生成 OpenAPI 格式文档
"""

import json
from typing import Dict, List, Optional
from tools import TOOLS

# 工具分类映射（手工维护分类，但工具列表自动从 TOOLS 读取）
# 分类名 -> 工具名列表
CATEGORIES = {
    "文件操作": [
        "read_file", "write_file", "append_file", "delete_file",
        "rename_file", "move", "file_info", "edit_file"
    ],
    "目录与压缩": [
        "zip_files", "unzip_files", "tar_files", "untar_files",
        "list_archive_content", "sync_dirs"
    ],
    "系统与进程": [
        "system_info", "sys_info_detail", "process_list",
        "kill_process", "check_port", "disk_analysis", "uptime"
    ],
    "终端与后台": [
        "run_background", "task_output", "kill_task"
    ],
    "Git版本控制": [
        "git_run",  # 这个需要扩展
    ],
    "搜索与查找": [
        "search_files", "find_text", "grep"
    ],
    "文本与字符串": [
        "replace_text", "extract_text", "split_text", "join_text",
        "to_upper", "to_lower", "trim", "reverse",
        "length", "substring", "format", "regex_match"
    ],
    "日期与时间": [
        "get_time", "format_time", "parse_time"
    ],
    "网络与下载": [
        "download_url", "get_headers", "check_url",
        "fetch_json", "fetch_text", "fetch_binary"
    ],
    "图片处理": [
        "resize_image", "crop_image", "rotate_image",
        "convert_image", "get_image_info"
    ],
    "图表生成": [
        "generate_chart", "generate_bar_chart", "generate_pie_chart", "generate_line_chart"
    ],
    "文档生成": [
        "generate_pdf", "generate_word", "generate_markdown", "generate_html"
    ],
    "格式转换": [
        "json_to_yaml", "yaml_to_json", "csv_to_json",
        "json_to_csv", "xml_to_json", "json_to_xml"
    ],
    "CSV与数据": [
        "read_csv", "write_csv", "query_csv"
    ],
    "YAML": [
        "read_yaml", "write_yaml"
    ],
    "Markdown": [
        "read_markdown", "write_markdown", "generate_toc"
    ],
    "HTML与XML": [
        "parse_html", "parse_xml", "extract_tags",
        "sanitize_html", "format_xml"
    ],
    "二维码与条形码": [
        "generate_qr", "read_qr", "generate_barcode", "read_barcode"
    ],
    "任务规划": [
        "plan_task", "plan_next", "list_plans",
        "complete_task", "cancel_task", "replan"
    ],
    "待办事项": [
        "todo_add", "todo_list", "todo_complete", "todo_start"
    ],
    "定时任务": [
        "schedule_task", "list_schedules", "run_task",
        "pause_task", "resume_task"
    ],
    "环境变量": [
        "get_env", "set_env", "list_env"
    ],
    "随机生成": [
        "random_string", "random_int", "random_float",
        "random_uuid", "random_date"
    ],
    "验证": [
        "validate_email", "validate_url", "validate_json", "validate_regex"
    ],
    "邮件": [
        "send_mail", "send_html_mail", "send_with_attachment",
        "read_mail", "list_mail"
    ],
    "配置与日志": [
        "read_config", "write_config", "list_configs",
        "log_info", "log_error", "log_debug", "log_warning"
    ],
    "调试": [
        "debug_var", "debug_stack", "debug_trace", "debug_breakpoint"
    ],
    "记忆管理": [
        "store_memory", "retrieve_memory", "list_memories",
        "delete_memory", "clear_memories"
    ],
    "记忆系统RAG": [
        "rag_search", "rag_add", "rag_delete", "rag_index", "rag_stats"
    ],
    "股票模拟": [
        "stock_price", "stock_history", "stock_buy", "stock_sell", "stock_portfolio"
    ],
    "其他": [
        "calc", "echo", "sleep", "wait",
        "notify", "alert", "clipboard_get",
        "clipboard_set", "open_url", "open_folder", "play_sound"
    ],
}


def _get_tool_info(tool_name: str) -> Optional[Dict]:
    """获取单个工具的完整信息"""
    return TOOLS.get(tool_name)


def list_categories() -> str:
    """列出所有工具分类及每个分类的工具数量"""
    lines = ["Hermes 工具分类:", "-" * 40]
    for cat, tools in sorted(CATEGORIES.items()):
        # 过滤出实际存在的工具
        existing = [t for t in tools if t in TOOLS]
        lines.append(f"{cat:20} ({len(existing)} 个)")
    lines.append("")
    lines.append(f"共 {len(CATEGORIES)} 个分类")
    return "\n".join(lines)


def list_tools() -> str:
    """列出所有工具（按分类分组）"""
    lines = ["Hermes 全部工具:", "=" * 50]
    for cat, tools in sorted(CATEGORIES.items()):
        existing = [t for t in tools if t in TOOLS]
        if not existing:
            continue
        lines.append(f"\n【{cat}】({len(existing)} 个):")
        lines.append("-" * 40)
        for name in existing:
            info = TOOLS.get(name)
            if info:
                # 提取参数名
                params = info.get("parameters", {}).get("properties", {})
                param_names = list(params.keys())
                required = info.get("parameters", {}).get("required", [])
                param_str = ", ".join(param_names)
                required_str = ", ".join(required)
                desc = info.get("description", "")[:50]
                lines.append(f"  {name}: {desc}")
                lines.append(f"    参数: {param_str}")
                if required:
                    lines.append(f"    必填: {required_str}")
    lines.append("")
    lines.append(f"共 {len(TOOLS)} 个工具")
    return "\n".join(lines)


def category_tools(category: str) -> str:
    """按分类查询工具"""
    cat = category.strip()
    if cat not in CATEGORIES:
        # 尝试模糊匹配
        matches = [c for c in CATEGORIES if cat in c or c in cat]
        if matches:
            return f"未找到分类 '{cat}'，您是不是要找：{', '.join(matches)}"
        return f"未找到分类 '{cat}'，可用分类：{', '.join(sorted(CATEGORIES.keys()))}"

    tools = [t for t in CATEGORIES[cat] if t in TOOLS]
    if not tools:
        return f"分类 '{cat}' 下暂无已注册工具"

    lines = [f"【{cat}】({len(tools)} 个):", "-" * 40]
    for name in tools:
        info = TOOLS.get(name)
        if info:
            params = info.get("parameters", {}).get("properties", {})
            param_names = list(params.keys())
            required = info.get("parameters", {}).get("required", [])
            desc = info.get("description", "")[:50]
            lines.append(f"  {name}: {desc}")
            lines.append(f"    参数: {', '.join(param_names)}")
            if required:
                lines.append(f"    必填: {', '.join(required)}")
    return "\n".join(lines)


def search_tools(keyword: str) -> str:
    """按关键词搜索工具（名称或描述中包含关键词）"""
    keyword_lower = keyword.strip().lower()
    if not keyword_lower:
        return "请提供搜索关键词"

    results = []
    for name, info in TOOLS.items():
        desc = info.get("description", "").lower()
        if keyword_lower in name.lower() or keyword_lower in desc:
            results.append((name, info))

    if not results:
        return f"未找到包含 '{keyword}' 的工具"

    lines = [f"搜索 '{keyword}' 结果 ({len(results)} 个):", "-" * 50]
    for name, info in results:
        # 尝试找分类
        category = "未分类"
        for cat, tools in CATEGORIES.items():
            if name in tools:
                category = cat
                break
        desc = info.get("description", "")[:40]
        params = info.get("parameters", {}).get("properties", {})
        required = info.get("parameters", {}).get("required", [])
        lines.append(f"[{category}] {name}: {desc}")
        if required:
            lines.append(f"  必填: {', '.join(required)}")
    return "\n".join(lines)


def export_schemas() -> str:
    """导出所有工具的 OpenAI 格式 schema（JSON）"""
    schemas = []
    for name, info in TOOLS.items():
        schemas.append({
            "type": "function",
            "function": {
                "name": name,
                "description": info.get("description", ""),
                "parameters": info.get("parameters", {})
            }
        })
    return json.dumps(schemas, ensure_ascii=False, indent=2)


def tool_help(tool_name: str) -> str:
    """获取某个工具的详细帮助"""
    if tool_name not in TOOLS:
        return f"工具 '{tool_name}' 不存在"

    info = TOOLS[tool_name]
    params = info.get("parameters", {}).get("properties", {})
    required = info.get("parameters", {}).get("required", [])

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

    return "\n".join(lines)


# 这个模块的对外接口（供 tools.py 注册时调用）
# 注意：这些函数不需要注册为工具，它们是工具索引的查询接口
# 但要暴露给 AI 使用，需要在 tools.py 中注册

def get_tool_names() -> List[str]:
    """获取所有已注册的工具名"""
    return list(TOOLS.keys())


def get_category_for_tool(tool_name: str) -> Optional[str]:
    """获取工具所属的分类"""
    for cat, tools in CATEGORIES.items():
        if tool_name in tools:
            return cat
    return None


# 自动生成工具列表（用于调试）
if __name__ == "__main__":
    print(list_categories())
    print("\n" + "=" * 60 + "\n")
    print(list_tools())
