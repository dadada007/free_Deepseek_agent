#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hermes Agent - Python 图形界面版 (PyQt6)
连接 12.py DeepSeek Browser API

用法:
    python run.py                            # 启动 GUI
    python run.py --url http://127.0.0.1:8001
    python run.py --no-parallel              # 关闭并行动作（严格串行）
    python run.py --debug                    # 调试模式
    python run.py --speak                    # 启用语音朗读
    python run.py --speak-rate 180           # 设置语速
"""
import sys
import os
import logging
import argparse

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 显式导入所有核心模块
import tools
import agent
import client
import memory
import memory_db
import parser
import planner
import speech

from client import Client
from agent import Agent


def main():
    parser = argparse.ArgumentParser(description="Hermes Agent - PyQt6 图形界面")
    parser.add_argument("--url", default="http://127.0.0.1:8003", help="API 服务器地址")
    parser.add_argument("--model", default="deepseek-browser", help="模型名称")
    parser.add_argument("--max-rounds", type=int, default=100, help="最大执行轮数（0=无限制）")
    parser.add_argument("--parallel", action="store_true", default=True, help="并行执行多个工具调用（默认开启）")
    parser.add_argument("--no-parallel", dest="parallel", action="store_false", help="关闭并行动作")
    parser.add_argument("--max-workers", type=int, default=4, help="并行最大线程数")
    parser.add_argument("--debug", action="store_true", help="调试模式")
    parser.add_argument("--agent-name", default=None,
                        help="Agent 身份名（用于会话隔离与复用；默认取进程环境 HERMES_AGENT 或 'hermes'）")
    
    # 语音参数
    parser.add_argument("--speak", action="store_true", help="启用语音朗读")
    parser.add_argument("--speak-rate", type=int, default=150, help="语音朗读语速（默认150）")
    parser.add_argument("--speak-volume", type=float, default=0.9, help="语音朗读音量（默认0.9）")
    
    args = parser.parse_args()

    agent_name = args.agent_name or os.environ.get("HERMES_AGENT") or "hermes"

    # 配置日志
    level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
    )

    # 如果启用语音，检查依赖
    if args.speak:
        logging.info(f"🔊 语音朗读已启用 (语速: {args.speak_rate}, 音量: {args.speak_volume})")
        try:
            import pyttsx3
            logging.info("✅ pyttsx3 已加载")
        except ImportError:
            logging.warning("⚠️ pyttsx3 未安装，语音功能不可用")
            logging.warning("请运行: pip install pyttsx3")
            args.speak = False

    # 创建客户端
    client = Client(
        base_url=args.url,
        model=args.model,
        api_key="sk-admin",
        agent_name=agent_name
    )

    # 创建 Agent（传递语音参数）
    agent = Agent(
        client=client,
        max_rounds=args.max_rounds,
        parallel=args.parallel,
        max_workers=args.max_workers,
        
    )

    # 启动 GUI（完全不变）
    try:
        from PyQt6.QtWidgets import QApplication
        from gui_qt.gui import GUI as QtGUI
        from gui_qt.theme import ensure_fonts
        
        app = QApplication(sys.argv)
        app.setApplicationName("Hermes Agent")
        ensure_fonts()
        
        gui = QtGUI(agent)  # GUI 完全不变
        gui.run()
        sys.exit(app.exec())
        
    except ImportError as e:
        logging.error(f"界面启动失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()