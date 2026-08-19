# -*- coding: utf-8 -*-
"""工具注册和执行 - 使用全局 tools.TOOLS"""

import os
import json
import logging
import sys

# 确保可以导入 tools
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

import tools

# ✅ 导入共享缓存
from smart_file_reader_tools import FileContextCache

logger = logging.getLogger(__name__)

# 获取全局缓存实例
_file_cache = FileContextCache()

# 分块配置
CHUNK_THRESHOLD = 20000    # 2万字符才分块
CHUNK_SIZE = 20000         # 每块2万字符


def write_file(args: dict) -> str:
    """写入文件 - 直接写入，不做任何转义处理"""
    file_path = args.get("file_path", "")
    content = args.get("content", "")
    
    if not file_path:
        return "错误: 缺少 file_path 参数"
    
    try:
        os.makedirs(os.path.dirname(file_path) or '.', exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        # ✅ 写入后清除旧缓存，下次读取会重新缓存
        _file_cache.clear()
        return f"✅ 文件已写入: {file_path} ({len(content)} 字符)"
    except Exception as e:
        return f"❌ 写入失败: {e}"


def _generate_summary(content: str, file_path: str) -> str:
    """生成文件摘要 - 扫描全部行"""
    lines = content.splitlines()
    total_lines = len(lines)
    total_chars = len(content)
    non_empty = sum(1 for line in lines if line.strip())
    
    # ✅ 扫描全部行，提取函数/类定义
    headers = []
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        
        # Markdown标题
        if stripped.startswith('#'):
            level = len(stripped) - len(stripped.lstrip('#'))
            title = stripped.lstrip('#').strip()
            if title:
                headers.append(f"{'#' * min(level, 3)} {title}(L{i})")
        
        # Python定义
        elif stripped.startswith('def ') or stripped.startswith('class '):
            name = stripped.split('(', 1)[0].replace('def ', '').replace('class ', '')
            headers.append(f"🔹 {name}()(L{i})")
        
        # JS/TS 函数/类
        elif (stripped.startswith('function ') or 
              stripped.startswith('export function ') or
              stripped.startswith('export class ') or
              stripped.startswith('class ')):
            parts = stripped.split(' ', 2)
            if len(parts) >= 2:
                name = parts[-1].split('(', 1)[0] if '(' in parts[-1] else parts[-1][:30]
                if name and name not in ['{', '=']:
                    headers.append(f"🔹 {name}(L{i})")
        
        # Java 方法
        elif ('public ' in stripped or 'private ' in stripped or 'protected ' in stripped) and '(' in stripped and ')' in stripped:
            match = re.search(r'\b(\w+)\s*\(', stripped)
            if match:
                name = match.group(1)
                if name not in ['if', 'for', 'while', 'switch']:
                    headers.append(f"🔹 {name}()(L{i})")
    
    # 提取语言
    ext = os.path.splitext(file_path)[1].lower()
    lang_map = {
        '.py': 'python', '.js': 'javascript', '.ts': 'typescript',
        '.java': 'java', '.c': 'c', '.cpp': 'cpp', '.go': 'go',
        '.rs': 'rust', '.rb': 'ruby', '.php': 'php', '.html': 'html',
        '.css': 'css', '.json': 'json', '.yaml': 'yaml', '.yml': 'yaml',
        '.md': 'markdown', '.txt': 'text', '.xml': 'xml', '.sql': 'sql',
        '.sh': 'bash', '.bat': 'batch', '.ps1': 'powershell'
    }
    language = lang_map.get(ext, '未知')
    
    summary_lines = [
        f"📊 文件统计: {total_lines} 行, {total_chars} 字符, {non_empty} 非空行, 语言={language}"
    ]
    if headers:
        summary_lines.append(f"  结构概览({len(headers)}):")
        # 显示前30个
        for h in headers[:30]:
            summary_lines.append(f"    {h}")
        if len(headers) > 30:
            summary_lines.append(f"    ... 还有 {len(headers)-30} 个")
    
    return "\n".join(summary_lines)


def read_file(args: dict) -> str:
    """
    读取文件 - 智能分块
    
    参数:
        file_path: 文件路径
        raw: 是否返回原始完整内容（默认 False）
        chunk_index: 指定读取第几块（从1开始），不指定则返回第一块
        chunk_size: 每块大小（字符数），默认 20000
    
    行为:
        - 文件小于阈值（20000字符）时，直接返回完整内容
        - 文件大于阈值时，自动分块，返回摘要 + 当前块内容
    """
    file_path = args.get("file_path", "")
    raw = args.get("raw", False)
    chunk_index = args.get("chunk_index", 1)
    chunk_size = args.get("chunk_size", CHUNK_SIZE)
    
    if not file_path:
        return "错误: 缺少 file_path 参数"
    
    if not os.path.exists(file_path):
        return f"❌ 文件不存在: {file_path}"
    
    # ✅ 尝试从缓存获取
    cache_entry = _file_cache.get(file_path)
    if cache_entry:
        content = cache_entry["content"]
        logger.info(f"📦 使用缓存: {os.path.basename(file_path)}")
    else:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            # 缓存文件内容
            lines = content.splitlines()
            summary = _file_cache.generate_summary(file_path, lines)
            _file_cache.put(file_path, content, lines, summary)
            logger.info(f"📖 首次读取并缓存: {os.path.basename(file_path)}")
        except Exception as e:
            return f"❌ 读取失败: {e}"
    
    total_chars = len(content)
    
    # 如果文件较小 或 用户要求原始内容，直接返回
    if raw or total_chars <= CHUNK_THRESHOLD:
        return content
    
    # 大文件：分块处理
    total_chunks = (total_chars + chunk_size - 1) // chunk_size
    
    # 确保 chunk_index 有效
    if chunk_index < 1:
        chunk_index = 1
    if chunk_index > total_chunks:
        chunk_index = total_chunks
    
    start = (chunk_index - 1) * chunk_size
    end = min(start + chunk_size, total_chars)
    chunk_content = content[start:end]
    
    # 计算行号范围
    lines_before = content[:start].count('\n')
    lines_in_chunk = chunk_content.count('\n')
    start_line = lines_before + 1
    end_line = lines_before + lines_in_chunk + 1
    
    # 生成摘要
    summary = _generate_summary(content, file_path)
    
    # 构建输出
    filename = os.path.basename(file_path)
    result_parts = [
        f"📄 {filename}（{total_chars} 字符, 共 {total_chunks} 块）",
        "",
        "【文件摘要】",
        summary,
        "",
        f"📦 第 {chunk_index}/{total_chunks} 块（行 {start_line}-{end_line}）",
        "=" * 50,
        chunk_content,
        "=" * 50,
    ]
    
    # 提示未读块
    if chunk_index < total_chunks:
        result_parts.append(f"💡 还有 {total_chunks - chunk_index} 块未读，用 read_file(file_path='{file_path}', chunk_index={chunk_index + 1}) 继续")
    else:
        result_parts.append("✅ 已读完最后一块！")
    
    return "\n".join(result_parts)


def append_file(args: dict) -> str:
    """追加内容到文件"""
    file_path = args.get("file_path", "")
    content = args.get("content", "")
    
    if not file_path:
        return "错误: 缺少 file_path 参数"
    
    try:
        os.makedirs(os.path.dirname(file_path) or '.', exist_ok=True)
        with open(file_path, 'a', encoding='utf-8') as f:
            f.write(content)
        # ✅ 追加后清除旧缓存
        _file_cache.clear()
        return f"✅ 已追加: {file_path} ({len(content)} 字符)"
    except Exception as e:
        return f"❌ 追加失败: {e}"


def delete_file(args: dict) -> str:
    """删除文件"""
    path = args.get("path", "")
    if not path:
        return "错误: 缺少 path 参数"
    try:
        if os.path.exists(path):
            os.remove(path)
            _file_cache.clear()  # ✅ 清除缓存
            return f"✅ 已删除: {path}"
        return f"文件不存在: {path}"
    except Exception as e:
        return f"❌ 删除失败: {e}"


def rename_file(args: dict) -> str:
    """重命名文件"""
    old = args.get("old_path", "")
    new = args.get("new_path", "")
    if not old or not new:
        return "错误: 需要 old_path 和 new_path"
    try:
        os.rename(old, new)
        _file_cache.clear()  # ✅ 清除缓存
        return f"✅ 已重命名: {old} → {new}"
    except Exception as e:
        return f"❌ 重命名失败: {e}"


def list_dir(args: dict) -> str:
    """列出目录"""
    path = args.get("path", ".")
    try:
        items = os.listdir(path)
        # 按类型排序：目录在前
        dirs = []
        files = []
        for item in items:
            full_path = os.path.join(path, item)
            if os.path.isdir(full_path):
                dirs.append(f"📁 {item}")
            else:
                files.append(f"📄 {item}")
        return "\n".join(dirs + files)
    except Exception as e:
        return f"错误: {e}"


def get_cwd(args: dict) -> str:
    """获取当前工作目录"""
    return os.getcwd()


# ============================================
# 注册工具到全局 tools.TOOLS
# ============================================

tools.register(
    "write_file",
    "写入文件。content 中的代码直接写，不要转义任何字符。",
    {
        "type": "object",
        "properties": {
            "file_path": {"type": "string", "description": "文件路径"},
            "content": {"type": "string", "description": "文件内容，原样写入"}
        },
        "required": ["file_path", "content"]
    },
    write_file
)

tools.register(
    "read_file",
    "读取文件内容。支持智能分块：小文件直接返回完整内容，大文件自动分块返回摘要+内容块。可通过 chunk_index 参数读取指定块。",
    {
        "type": "object",
        "properties": {
            "file_path": {"type": "string", "description": "文件路径"},
            "raw": {"type": "boolean", "description": "是否返回原始完整内容（跳过智能分块）", "default": False},
            "chunk_index": {"type": "integer", "description": "读取第几块（从1开始），仅大文件有效", "default": 1},
            "chunk_size": {"type": "integer", "description": "每块大小（字符数），默认 20000", "default": 20000}
        },
        "required": ["file_path"]
    },
    read_file
)

tools.register(
    "append_file",
    "追加内容到文件末尾",
    {
        "type": "object",
        "properties": {
            "file_path": {"type": "string", "description": "文件路径"},
            "content": {"type": "string", "description": "要追加的内容"}
        },
        "required": ["file_path", "content"]
    },
    append_file
)

tools.register(
    "delete_file",
    "删除文件",
    {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "文件路径"}
        },
        "required": ["path"]
    },
    delete_file
)

tools.register(
    "rename_file",
    "重命名或移动文件",
    {
        "type": "object",
        "properties": {
            "old_path": {"type": "string", "description": "原路径"},
            "new_path": {"type": "string", "description": "新路径"}
        },
        "required": ["old_path", "new_path"]
    },
    rename_file
)

tools.register(
    "list_dir",
    "列出目录内容，目录和文件分别显示",
    {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "目录路径，默认当前目录"}
        },
        "required": []
    },
    list_dir
)

tools.register(
    "get_cwd",
    "获取当前工作目录",
    {
        "type": "object",
        "properties": {},
        "required": []
    },
    get_cwd
)

logger.info("✅ file_operations_tools 已注册到全局 tools.TOOLS")