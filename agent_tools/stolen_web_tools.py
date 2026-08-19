"""
从 D:/miss/agent_tools/tools.py 偷来的 Web 工具
包含 browse_url 函数及其依赖
"""
import subprocess
import os
import re

# ==================== 偷来的编码处理工具 ====================

def _try_decode_bytes(byte_data: bytes, fallback_encoding: str = 'utf-8') -> str:
    """尝试用多种编码解码字节数据（偷自 tools.py）"""
    encodings = ['utf-8', 'gbk', 'gb2312', 'gb18030', fallback_encoding, 'latin-1']
    
    for encoding in encodings:
        try:
            return byte_data.decode(encoding)
        except (UnicodeDecodeError, LookupError):
            continue
    
    return byte_data.decode('utf-8', errors='replace')


def _decode_subprocess_output(stdout_bytes: bytes, stderr_bytes: bytes) -> str:
    """智能解码子进程输出，过滤不可打印字符（偷自 tools.py）"""
    stdout_text = _try_decode_bytes(stdout_bytes) if stdout_bytes else ""
    stderr_text = _try_decode_bytes(stderr_bytes) if stderr_bytes else ""

    output = stdout_text if stdout_text else stderr_text

    if output:
        output = output.replace('\x00', '')
        output = ''.join(char for char in output if char >= ' ' or char in '\n	')

    return output


# ==================== 偷来的核心工具函数 ====================

def browse_url(params: str) -> str:
    """获取指定网页的纯文本内容（使用 curl）—— 偷自 tools.py"""
    try:
        url = params.strip()
        if not url:
            return "错误：未提供 URL 地址"
        
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        result = subprocess.run(
            ['curl', '-s', '-L', '-A', 'Mozilla/5.0', url],
            capture_output=True,
            timeout=15
        )
        
        output = _decode_subprocess_output(result.stdout, result.stderr)
        
        if not output:
            return "网页无内容（可能无法访问或需要 JavaScript 渲染）"
        
        return output
        
    except subprocess.TimeoutExpired:
        return "请求超时（15秒），请检查网络或 URL 是否正确"
    except Exception as e:
        return f"浏览失败: {e}"


def analyze_call_graph(params: str) -> str:
    """分析函数调用关系图（偷自 tools.py）"""
    import ast
    
    parts = params.split('[fg_]')
    directory = parts[0].strip() if parts else "."
    target_func = parts[1].strip() if len(parts) > 1 and parts[1].strip() else None
    extensions_str = parts[2].strip() if len(parts) > 2 and parts[2].strip() else ".py,.js,.ts,.java,.go,.rs,.cpp,.cs"
    
    if not os.path.exists(directory):
        return f"❌ 目录不存在: {directory}"
    if not os.path.isdir(directory):
        return f"❌ 不是目录: {directory}"
    
    extensions = [ext.strip().lower() for ext in extensions_str.split(',') if ext.strip()]
    if not extensions:
        extensions = ['.py', '.js', '.ts', '.java', '.go', '.rs', '.cpp', '.cs']
    
    exclude_dirs = {'.git', '__pycache__', 'node_modules', 'dist', 'build', '.venv', 'venv', '.idea', '.vscode'}
    
    results = {}
    total_files = 0
    
    for root, dirs, files in os.walk(directory):
        dirs[:] = [d for d in dirs if d not in exclude_dirs and not d.startswith('.')]
        for file in files:
            file_path = os.path.join(root, file)
            ext = os.path.splitext(file)[1].lower()
            if ext not in extensions:
                continue
            total_files += 1
            try:
                if os.path.getsize(file_path) > 1 * 1024 * 1024:
                    continue
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                calls = _extract_calls(content, file_path, target_func)
                if calls:
                    rel_path = os.path.relpath(file_path, directory)
                    results[rel_path] = calls
            except Exception:
                continue
    
    if not results:
        return f"🔍 未找到调用关系（扫描 {total_files} 个文件）"
    
    total_calls = sum(len(c) for c in results.values())
    output_lines = [
        f"🔗 调用关系图",
        f"📂 目录: {directory}",
        f"📁 分析文件: {len(results)} 个（扫描 {total_files} 个）",
        f"📞 调用数: {total_calls}",
        f"",
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        f"",
    ]
    
    for file_path, calls in sorted(results.items()):
        output_lines.append(f"📁 {file_path}")
        for call in calls:
            caller = call.get('caller', 'unknown')
            callee = call.get('callee', 'unknown')
            line = call.get('line', '?')
            output_lines.append(f"  ├── 📞 {caller} → {callee} (行 {line})")
        output_lines.append("")
    
    return "\n".join(output_lines)


def _extract_calls(content: str, file_path: str, target_func: str = None) -> list:
    """提取函数调用关系（偷自 tools.py）"""
    import ast
    calls = []
    ext = os.path.splitext(file_path)[1].lower()
    
    if ext == '.py':
        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name):
                        func_name = node.func.id
                        if target_func and func_name != target_func:
                            continue
                        calls.append({
                            'caller': _get_enclosing_function(tree, node),
                            'callee': func_name,
                            'line': node.lineno
                        })
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        calls.append({
                            'caller': 'import',
                            'callee': alias.name,
                            'line': node.lineno
                        })
                elif isinstance(node, ast.ImportFrom):
                    for alias in node.names:
                        calls.append({
                            'caller': f'from {node.module}',
                            'callee': alias.name,
                            'line': node.lineno
                        })
        except Exception:
            pass
    
    return calls


def _get_enclosing_function(tree, node) -> str:
    """获取包含节点的函数名（偷自 tools.py）"""
    import ast
    for n in ast.walk(tree):
        if isinstance(n, ast.FunctionDef):
            for child in ast.walk(n):
                if child is node:
                    return n.name
    return '<module>'


# ==================== 工具注册函数 ====================

def register_tools(registry):
    """
    注册偷来的工具到 Hermes 系统
    
    Args:
        registry: 工具注册器（如 tool_registry 或 fs_register 的注册接口）
    """
    # 方式1：使用装饰器风格注册
    # 注意：这里需要适配 Hermes 的注册方式
    # 如果 registry 有 register 方法，使用它
    
    if hasattr(registry, 'register'):
        # 注册 browse_url
        registry.register(
            name="browse_url",
            description="获取指定网页的纯文本内容（使用 curl）—— 偷自 miss/agent_tools",
            parameters={"format": "URL地址"},
            category="network"
        )(browse_url)
        
        # 注册 analyze_call_graph
        registry.register(
            name="analyze_call_graph",
            description="分析指定文件的函数调用关系，生成调用树。帮助理解代码执行流程和函数间的依赖关系。支持 Python/JS/TS/Java/Go/Rust/C++。—— 偷自 miss/agent_tools",
            parameters={"format": "目录路径[fg_]函数名（可选）[fg_]文件扩展名（可选）"},
            category="file"
        )(analyze_call_graph)
        
        print("✅ 已注册偷来的工具: browse_url, analyze_call_graph")
    else:
        # 方式2：直接暴露函数供外部手动注册
        print("⚠️ 注册器不支持 register 方法，请手动注册以下函数：")
        print(f"  - browse_url: {browse_url.__doc__}")
        print(f"  - analyze_call_graph: {analyze_call_graph.__doc__}")


# 导出函数供外部直接使用
__all__ = ['browse_url', 'analyze_call_graph', 'register_tools']
