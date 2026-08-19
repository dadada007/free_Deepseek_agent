# -*- coding: utf-8 -*-
"""
HTTP 文件服务器工具

启动一个简单的 HTTP 文件服务器，方便在局域网内共享文件。
基于 Python 内置的 http.server 模块。
"""

import os
import sys
import threading
import webbrowser
import socket
from http.server import HTTPServer, SimpleHTTPRequestHandler

# 导入全局注册函数
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tools import register


# ==================== 工具实现函数 ====================

# 用于存储正在运行的服务器实例
_server_instance = None


class QuietHTTPHandler(SimpleHTTPRequestHandler):
    """静默版 HTTP 处理器，减少控制台输出"""

    def log_message(self, format, *args):
        # 只记录关键信息，不输出每个请求
        if args and args[0] == 'GET':
            pass  # 忽略 GET 请求日志
        else:
            super().log_message(format, *args)


def find_free_port(start_port=8000, max_attempts=10) -> int:
    """查找可用的端口"""
    port = start_port
    for _ in range(max_attempts):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('', port))
                return port
        except OSError:
            port += 1
    return -1


def get_local_ip() -> str:
    """获取本机局域网 IP"""
    try:
        # 连接外部地址获取本机 IP
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(('8.8.8.8', 80))
            return s.getsockname()[0]
    except Exception:
        return '127.0.0.1'


def start_http_server(args: dict) -> str:
    """
    启动 HTTP 文件服务器

    参数:
        path: 服务器根目录（默认当前目录）
        port: 端口号（默认 8000）
        bind: 绑定地址（默认 0.0.0.0，允许局域网访问）
        open_browser: 是否自动打开浏览器（默认 True）
        quiet: 是否静默模式（默认 True）
    """
    global _server_instance

    # 获取参数
    path = args.get('path', '').strip() or os.getcwd()
    port = args.get('port', 8000)
    bind = args.get('bind', '0.0.0.0')
    open_browser = args.get('open_browser', True)
    quiet = args.get('quiet', True)

    # 参数校验
    if not os.path.exists(path):
        return f"❌ 错误: 目录不存在 '{path}'"

    if not os.path.isdir(path):
        return f"❌ 错误: 路径不是目录 '{path}'"

    # 检查端口是否被占用
    try:
        port = int(port)
        if port < 1 or port > 65535:
            return f"❌ 错误: 端口必须在 1-65535 之间，当前: {port}"
    except ValueError:
        return f"❌ 错误: 端口必须是整数，当前: {port}"

    # 检查端口是否可用
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((bind, port))
    except OSError:
        # 端口被占用，尝试查找可用端口
        new_port = find_free_port(port + 1)
        if new_port == -1:
            return f"❌ 错误: 端口 {port} 被占用，且无法找到可用端口"
        port = new_port

    # 如果已有服务器在运行，先停止
    if _server_instance is not None:
        try:
            _server_instance.shutdown()
            _server_instance = None
        except Exception:
            pass

    # 切换到目标目录
    original_cwd = os.getcwd()
    try:
        os.chdir(path)
    except Exception as e:
        return f"❌ 错误: 无法切换到目录 '{path}': {e}"

    # 创建服务器
    handler_class = QuietHTTPHandler if quiet else SimpleHTTPRequestHandler

    try:
        server = HTTPServer((bind, port), handler_class)
        _server_instance = server
    except Exception as e:
        os.chdir(original_cwd)
        return f"❌ 错误: 无法启动服务器: {e}"

    # 获取访问地址
    local_ip = get_local_ip()
    urls = []
    if bind in ('0.0.0.0', '0.0.0.0'):
        urls.append(f"http://{local_ip}:{port}")
        urls.append(f"http://127.0.0.1:{port}")
    elif bind in ('127.0.0.1', 'localhost'):
        urls.append(f"http://127.0.0.1:{port}")
    else:
        urls.append(f"http://{bind}:{port}")

    # 启动服务器线程（非阻塞）
    def run_server():
        try:
            server.serve_forever()
        except Exception:
            pass
        finally:
            # 恢复工作目录
            try:
                os.chdir(original_cwd)
            except Exception:
                pass

    thread = threading.Thread(target=run_server, daemon=True)
    thread.start()

    # 自动打开浏览器
    if open_browser:
        try:
            webbrowser.open(urls[0])
        except Exception:
            pass

    # 构建返回信息
    lines = [
        f"✅ HTTP 文件服务器已启动",
        "=" * 50,
        f"📂 根目录: {path}",
        f"🌐 绑定地址: {bind}:{port}",
        "",
        "🔗 访问地址:",
    ]
    for url in urls:
        lines.append(f"   {url}")

    lines.extend([
        "",
        f"📊 服务状态: 运行中 (PID: {os.getpid()})",
        "💡 提示: 按 Ctrl+C 停止服务器，或调用 stop_http_server 工具",
    ])

    return "\n".join(lines)


def stop_http_server(args: dict) -> str:
    """
    停止正在运行的 HTTP 文件服务器
    """
    global _server_instance

    if _server_instance is None:
        return "ℹ️ 没有正在运行的 HTTP 服务器"

    try:
        _server_instance.shutdown()
        _server_instance = None
        return "✅ HTTP 服务器已停止"
    except Exception as e:
        return f"❌ 停止服务器失败: {e}"


def http_server_status(args: dict) -> str:
    """
    查看 HTTP 服务器状态
    """
    global _server_instance

    if _server_instance is None:
        return "ℹ️ 当前没有运行的 HTTP 服务器"

    try:
        server = _server_instance
        # 获取服务器地址
        host, port = server.server_address
        return f"✅ HTTP 服务器运行中\n🌐 地址: {host}:{port}"
    except Exception:
        return "⚠️ 服务器状态未知，可能已停止"


# ==================== 工具注册 ====================

def register_tools() -> int:
    """
    注册此模块中的所有工具。
    热加载器会自动调用此函数。
    返回注册的工具数量。
    """

    # 注册 http_server
    register(
        name="http_server",
        description="启动本地 HTTP 文件服务器，在指定目录共享文件。支持局域网访问，可指定端口。当用户需要共享文件、启动临时 Web 服务、或做前端预览时调用。",
        parameters={
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "服务器根目录路径，默认为当前工作目录。使用正斜杠或双反斜杠。",
                    "default": ""
                },
                "port": {
                    "type": "integer",
                    "description": "服务端口号，默认为 8000。如果端口被占用会自动寻找下一个可用端口。",
                    "default": 8000,
                    "minimum": 1,
                    "maximum": 65535
                },
                "bind": {
                    "type": "string",
                    "description": "绑定地址，默认为 0.0.0.0（允许局域网访问）。设置为 127.0.0.1 则仅本地访问。",
                    "default": "0.0.0.0",
                    "enum": ["0.0.0.0", "127.0.0.1", "localhost"]
                },
                "open_browser": {
                    "type": "boolean",
                    "description": "是否自动打开浏览器访问服务器，默认为 True",
                    "default": True
                },
                "quiet": {
                    "type": "boolean",
                    "description": "是否静默模式（减少日志输出），默认为 True",
                    "default": True
                }
            },
            "required": []
        },
        func=start_http_server
    )

    # 注册 stop_http_server
    register(
        name="stop_http_server",
        description="停止正在运行的 HTTP 文件服务器。当用户需要关闭之前启动的服务器时调用。",
        parameters={
            "type": "object",
            "properties": {},
            "required": []
        },
        func=stop_http_server
    )

    # 注册 http_server_status
    register(
        name="http_server_status",
        description="查看 HTTP 文件服务器的运行状态。当用户询问服务器是否在运行、地址是什么时调用。",
        parameters={
            "type": "object",
            "properties": {},
            "required": []
        },
        func=http_server_status
    )

    return 3  # 注册了 3 个工具


# ==================== 本地测试 ====================

if __name__ == "__main__":
    # 注册工具
    count = register_tools()
    print(f"✅ 已注册 {count} 个工具")

    # 测试启动服务器（当前目录，端口 8080）
    print("\n🧪 测试启动服务器...")
    result = start_http_server({
        "path": os.getcwd(),
        "port": 8080,
        "open_browser": True,
        "quiet": True
    })
    print(result)

    # 提示如何停止
    print("\n💡 按 Enter 停止服务器...")
    input()
    print(stop_http_server({}))