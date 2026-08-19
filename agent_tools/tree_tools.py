# -*- coding: utf-8 -*-
"""目录树工具 - 以树形结构列出目录内容"""

import os


def _tree_list(args: dict) -> str:
    """
    以树形结构列出目录内容
    """
    path = args.get("path", ".")
    max_depth = args.get("max_depth", 3)
    show_hidden = args.get("show_hidden", False)
    show_size = args.get("show_size", True)
    
    if not os.path.exists(path):
        return f"错误: 路径不存在 - {path}"
    
    if not os.path.isdir(path):
        return f"错误: 路径不是目录 - {path}"
    
    lines = []
    lines.append(f"📁 {os.path.basename(path) or path}")
    
    def _walk_dir(current_path: str, prefix: str, depth: int):
        if depth > max_depth:
            return
        
        try:
            items = list(os.listdir(current_path))
        except PermissionError:
            lines.append(f"{prefix}🚫 权限不足")
            return
        
        # 过滤隐藏文件
        if not show_hidden:
            items = [item for item in items if not item.startswith('.')]
        
        # 排序：目录优先，然后文件
        dirs = []
        files = []
        for item in items:
            full = os.path.join(current_path, item)
            if os.path.isdir(full):
                dirs.append(item)
            else:
                files.append(item)
        dirs.sort()
        files.sort()
        sorted_items = dirs + files
        
        for i, item in enumerate(sorted_items):
            is_last = (i == len(sorted_items) - 1)
            connector = "└── " if is_last else "├── "
            full_path = os.path.join(current_path, item)
            
            if os.path.isdir(full_path):
                if depth + 1 <= max_depth:
                    try:
                        sub_items = os.listdir(full_path)
                        if not show_hidden:
                            sub_items = [x for x in sub_items if not x.startswith('.')]
                        has_children = len(sub_items) > 0
                    except PermissionError:
                        has_children = False
                else:
                    has_children = True
                
                suffix = "/"
                if depth + 1 > max_depth and has_children:
                    suffix = "/ ..."
                lines.append(f"{prefix}{connector}📁 {item}{suffix}")
                
                if depth + 1 <= max_depth:
                    next_prefix = prefix + ("    " if is_last else "│   ")
                    _walk_dir(full_path, next_prefix, depth + 1)
            else:
                # 文件
                size_str = ""
                if show_size:
                    try:
                        size = os.path.getsize(full_path)
                        if size < 1024:
                            size_str = f" ({size}B)"
                        elif size < 1024 * 1024:
                            size_str = f" ({size/1024:.1f}KB)"
                        else:
                            size_str = f" ({size/1024/1024:.1f}MB)"
                    except Exception:
                        pass
                lines.append(f"{prefix}{connector}📄 {item}{size_str}")
    
    _walk_dir(path, "", 0)
    return "\n".join(lines)  # 修复：使用换行符连接，而不是空格


def register_tools():
    try:
        import tools
    except ImportError:
        print("⚠️ 无法导入 tools 模块")
        return 0
    
    tools.register(
        name="tree_list",
        description="以树形结构列出目录内容，支持深度控制和显示隐藏文件",
        parameters={
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "目录路径，默认为当前目录"},
                "max_depth": {"type": "integer", "description": "最大显示深度，默认3"},
                "show_hidden": {"type": "boolean", "description": "是否显示隐藏文件，默认false"},
                "show_size": {"type": "boolean", "description": "是否显示文件大小，默认true"}
            },
            "required": []
        },
        func=_tree_list
    )
    
    print("✅ 已注册 tree_list")
    return 1


# 自动注册
if __name__ != '__main__':
    register_tools()