#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hermes Agent - Python 图形界面版 (PyQt6)
"""
import sys
import os
import logging
import argparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from client import Client
from agent import Agent


def main():
    parser = argparse.ArgumentParser(description="Hermes Agent - PyQt6 图形界面")
    parser.add_argument("--url", default="http://127.0.0.1:8003", help="API 服务器地址")
    parser.add_argument("--model", default="deepseek-browser", help="模型名称")
    parser.add_argument("--max-rounds", type=int, default=100, help="最大执行轮数")
    parser.add_argument("--no-parallel", dest="parallel", action="store_false", help="关闭并行动作")
    parser.add_argument("--max-workers", type=int, default=4, help="并行最大线程数")
    parser.add_argument("--debug", action="store_true", help="调试模式")
    parser.add_argument("--agent-name", default=None, help="Agent 身份名")
    parser.add_argument("--speak", action="store_true", help="启用语音朗读")
    parser.add_argument("--speak-rate", type=int, default=150, help="语音朗读语速")
    
    args = parser.parse_args()

    agent_name = args.agent_name or os.environ.get("HERMES_AGENT") or "hermes"

    logging.basicConfig(level=logging.DEBUG if args.debug else logging.INFO,
                        format="%(asctime)s [%(levelname)s] %(message)s")

    if args.speak:
        try:
            import pyttsx3
        except ImportError:
            logging.warning("⚠️ pyttsx3 未安装，语音功能不可用")
            args.speak = False

    client = Client(
        base_url=args.url,
        model=args.model,
        api_key="sk-admin",
        agent_name=agent_name
    )

    agent = Agent(
        client=client,
        max_rounds=args.max_rounds,
        parallel=args.parallel,
        max_workers=args.max_workers,
    )

    # 直接从 gui_qt 导入 GUI 并启动
    try:
        from gui_qt import GUI
        from PyQt6.QtWidgets import QApplication
        from gui_qt import _ensure_fonts
        
        app = QApplication(sys.argv)
        app.setApplicationName("Hermes Agent")
        _ensure_fonts()
        
        gui = GUI(agent)
        gui._append("bot", "你好！我是 Hermes，有什么可以帮你的？")
        gui.show()
        sys.exit(app.exec())
        
    except ImportError as e:
        logging.error(f"GUI 启动失败: {e}")
        logging.error("请确保已安装 PyQt6: pip install PyQt6")
        sys.exit(1)


if __name__ == "__main__":
    main()
