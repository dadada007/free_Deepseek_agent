# -*- coding: utf-8 -*-
"""
桌面通知工具 - 在 Windows 右下角弹出系统通知
"""

import os
import sys
import time

# 导入全局注册函数
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tools import register


def _get_notification_backend():
    """
    延迟加载通知库，返回 (backend_name, notify_func)
    优先使用 plyer，其次 win10toast
    """
    try:
        from plyer import notification
        return ('plyer', notification)
    except ImportError:
        pass
    
    try:
        from win10toast import ToastNotifier
        return ('win10toast', ToastNotifier)
    except ImportError:
        pass
    
    return ('fallback', None)


def _notify_plyer(notification, title: str, message: str, duration: int, icon_path: str = None) -> str:
    """使用 plyer 发送通知"""
    try:
        kwargs = {
            'title': title,
            'message': message,
            'app_name': 'Hermes',
            'timeout': duration,
        }
        if icon_path and os.path.exists(icon_path):
            kwargs['app_icon'] = icon_path
        
        notification.notify(**kwargs)
        return f"✅ 通知已发送 (plyer): {title}"
    except Exception as e:
        return f"❌ plyer 通知失败: {e}"


def _notify_win10toast(ToastNotifier, title: str, message: str, duration: int, icon_path: str = None) -> str:
    """使用 win10toast 发送通知"""
    try:
        toaster = ToastNotifier()
        toaster.show_toast(
            title=title,
            msg=message,
            duration=duration,
            icon_path=icon_path if icon_path and os.path.exists(icon_path) else None,
            threaded=True
        )
        while toaster.notification_active():
            time.sleep(0.1)
        return f"✅ 通知已发送 (win10toast): {title}"
    except Exception as e:
        return f"❌ win10toast 通知失败: {e}"


def _notify_fallback(title: str, message: str) -> str:
    """备用方案：控制台输出 + 系统提示音"""
    try:
        import winsound
        winsound.MessageBeep(winsound.MB_ICONINFORMATION)
    except:
        pass
    
    print(f"{'='*50}")
    print(f"🔔 桌面通知 (模拟)")
    print(f"标题: {title}")
    print(f"内容: {message}")
    print(f"{'='*50}")
    return f"✅ 通知已模拟 (控制台输出): {title}"


def notify_desktop(args: dict) -> str:
    """
    发送 Windows 桌面系统通知（右下角弹窗）
    """
    title = args.get('title', '').strip()
    message = args.get('message', '').strip()
    duration = args.get('duration', 5)
    icon_path = args.get('icon_path', '').strip()
    
    if not title:
        return "❌ 错误: 请提供 title 参数（通知标题）"
    if not message:
        return "❌ 错误: 请提供 message 参数（通知内容）"
    
    try:
        duration = int(duration)
        if duration < 1:
            duration = 3
        elif duration > 60:
            duration = 60
    except:
        duration = 5
    
    if icon_path:
        icon_path = icon_path.replace('\\', '/')  # 只替换反斜杠
        if not os.path.exists(icon_path):
            icon_path = None
    else:
        icon_path = None
    
    # 运行时检测后端
    backend, module = _get_notification_backend()
    
    if backend == 'plyer':
        result = _notify_plyer(module, title, message, duration, icon_path)
    elif backend == 'win10toast':
        result = _notify_win10toast(module, title, message, duration, icon_path)
    else:
        result = _notify_fallback(title, message)
    
    return result


def send_alert(args: dict) -> str:
    """发送紧急警报通知"""
    title = args.get('title', '⚠️ 警报')
    message = args.get('message', '')
    duration = args.get('duration', 10)
    
    if not message:
        return "❌ 错误: 请提供 message 参数"
    
    if not title.startswith('⚠️') and not title.startswith('❗'):
        title = f"⚠️ {title}"
    
    return notify_desktop({
        'title': title,
        'message': message,
        'duration': duration
    })


def notify_quick(args: dict) -> str:
    """快捷通知：仅需 message"""
    message = args.get('message', '').strip()
    if not message:
        return "❌ 错误: 请提供 message 参数"
    
    title = "Hermes 通知"
    if len(message) > 30:
        title = "📌 新通知"
    
    return notify_desktop({
        'title': title,
        'message': message,
        'duration': args.get('duration', 5)
    })


# ==================== 工具注册 ====================

def register_tools() -> int:
    count = 0
    
    register(
        name="notify_desktop",
        description="发送 Windows 桌面系统通知（右下角弹窗）。适用于任务完成提醒、定时提醒、错误告警等场景。",
        parameters={
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "通知标题（必填）",
                },
                "message": {
                    "type": "string",
                    "description": "通知正文内容（必填）",
                },
                "duration": {
                    "type": "integer",
                    "description": "显示持续时间（秒），默认 5",
                    "default": 5,
                },
                "icon_path": {
                    "type": "string",
                    "description": "图标文件路径（可选），支持 .ico 格式",
                },
            },
            "required": ["title", "message"]
        },
        func=notify_desktop
    )
    count += 1
    
    register(
        name="send_alert",
        description="发送紧急警报通知，标题自动添加 ⚠️ 前缀，默认持续 10 秒。",
        parameters={
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "警报标题（可选）",
                    "default": "⚠️ 警报"
                },
                "message": {
                    "type": "string",
                    "description": "警报内容（必填）",
                },
                "duration": {
                    "type": "integer",
                    "description": "显示持续时间（秒），默认 10",
                    "default": 10,
                }
            },
            "required": ["message"]
        },
        func=send_alert
    )
    count += 1
    
    register(
        name="notify_quick",
        description="快捷通知：只需提供 message，自动生成标题。",
        parameters={
            "type": "object",
            "properties": {
                "message": {
                    "type": "string",
                    "description": "通知内容（必填）",
                },
                "duration": {
                    "type": "integer",
                    "description": "显示持续时间（秒），默认 5",
                    "default": 5,
                },
            },
            "required": ["message"]
        },
        func=notify_quick
    )
    count += 1
    
    return count


if __name__ == "__main__":
    register_tools()
    print("✅ notify_tools 已加载")
    
    result = notify_desktop({
        "title": "自测",
        "message": "Hermes 桌面通知 (延迟加载版)",
        "duration": 3
    })
    print(result)
