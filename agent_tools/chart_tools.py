# -*- coding: utf-8 -*-
"""
数据可视化工具集 - 支持生成图表、报表、仪表盘
"""

import os
import json
from datetime import datetime


def _import_matplotlib():
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        import matplotlib.font_manager as fm
        return plt, fm
    except ImportError:
        return None


def _ensure_dir(path):
    dirname = os.path.dirname(path)
    if dirname and not os.path.exists(dirname):
        os.makedirs(dirname, exist_ok=True)


def _line_chart(args: dict) -> str:
    try:
        path = args.get('path', 'line_chart.png')
        title = args.get('title', '折线图')
        x_data = args.get('x', [])
        y_data = args.get('y', [])
        x_label = args.get('x_label', '')
        y_label = args.get('y_label', '')
        color = args.get('color', 'blue')
        marker = args.get('marker', 'o')
        grid = args.get('grid', True)
        if not x_data or not y_data:
            return "❌ 请提供 x 和 y 数据"
        if len(x_data) != len(y_data):
            return "❌ x 和 y 数据长度不一致"
        plt_module = _import_matplotlib()
        if not plt_module:
            return "❌ 请安装 matplotlib: pip install matplotlib"
        plt, fm = plt_module
        _ensure_dir(path)
        plt.figure(figsize=(10, 6))
        plt.plot(x_data, y_data, color=color, marker=marker, linewidth=2)
        plt.title(title, fontsize=16)
        if x_label:
            plt.xlabel(x_label, fontsize=12)
        if y_label:
            plt.ylabel(y_label, fontsize=12)
        if grid:
            plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig(path, dpi=150, bbox_inches='tight')
        plt.close()
        return json.dumps({'success': True, '输出': path, '标题': title, '数据点': len(x_data)}, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"❌ 生成折线图失败: {e}"


def _bar_chart(args: dict) -> str:
    try:
        path = args.get('path', 'bar_chart.png')
        title = args.get('title', '柱状图')
        x_data = args.get('x', [])
        y_data = args.get('y', [])
        color = args.get('color', 'skyblue')
        if not x_data or not y_data:
            return "❌ 请提供 x 和 y 数据"
        plt_module = _import_matplotlib()
        if not plt_module:
            return "❌ 请安装 matplotlib: pip install matplotlib"
        plt, fm = plt_module
        _ensure_dir(path)
        plt.figure(figsize=(10, 6))
        bars = plt.bar(x_data, y_data, color=color, width=0.6)
        plt.title(title, fontsize=16)
        for bar in bars:
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2., height + 0.1, f'{height}', ha='center', va='bottom', fontsize=10)
        plt.tight_layout()
        plt.savefig(path, dpi=150, bbox_inches='tight')
        plt.close()
        return json.dumps({'success': True, '输出': path, '标题': title}, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"❌ 生成柱状图失败: {e}"


def _pie_chart(args: dict) -> str:
    try:
        path = args.get('path', 'pie_chart.png')
        title = args.get('title', '饼图')
        labels = args.get('labels', [])
        values = args.get('values', [])
        show_percent = args.get('show_percent', True)
        if not labels or not values:
            return "❌ 请提供 labels 和 values 数据"
        plt_module = _import_matplotlib()
        if not plt_module:
            return "❌ 请安装 matplotlib: pip install matplotlib"
        plt, fm = plt_module
        _ensure_dir(path)
        plt.figure(figsize=(8, 8))
        autopct = '%1.1f%%' if show_percent else None
        plt.pie(values, labels=labels, autopct=autopct, startangle=90, shadow=True)
        plt.title(title, fontsize=16)
        plt.axis('equal')
        plt.tight_layout()
        plt.savefig(path, dpi=150, bbox_inches='tight')
        plt.close()
        return json.dumps({'success': True, '输出': path, '标题': title}, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"❌ 生成饼图失败: {e}"


def _scatter_plot(args: dict) -> str:
    try:
        path = args.get('path', 'scatter_plot.png')
        title = args.get('title', '散点图')
        x_data = args.get('x', [])
        y_data = args.get('y', [])
        color = args.get('color', 'blue')
        alpha = args.get('alpha', 0.6)
        if not x_data or not y_data:
            return "❌ 请提供 x 和 y 数据"
        plt_module = _import_matplotlib()
        if not plt_module:
            return "❌ 请安装 matplotlib: pip install matplotlib"
        plt, fm = plt_module
        _ensure_dir(path)
        plt.figure(figsize=(10, 6))
        plt.scatter(x_data, y_data, c=color, alpha=alpha)
        plt.title(title, fontsize=16)
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig(path, dpi=150, bbox_inches='tight')
        plt.close()
        return json.dumps({'success': True, '输出': path, '标题': title}, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"❌ 生成散点图失败: {e}"


def register_tools():
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import tools

    tools.register(
        name="line_chart",
        description="生成折线图。参数: path(输出路径), title(标题), x(X轴数据), y(Y轴数据)",
        parameters={"type": "object", "properties": {
            "path": {"type": "string"}, "title": {"type": "string"},
            "x": {"type": "array"}, "y": {"type": "array"},
            "x_label": {"type": "string"}, "y_label": {"type": "string"}
        }, "required": ["x", "y"]},
        func=_line_chart,
    )
    tools.register(
        name="bar_chart",
        description="生成柱状图。参数: path(输出路径), title(标题), x(类别), y(数值)",
        parameters={"type": "object", "properties": {
            "path": {"type": "string"}, "title": {"type": "string"},
            "x": {"type": "array"}, "y": {"type": "array"}
        }, "required": ["x", "y"]},
        func=_bar_chart,
    )
    tools.register(
        name="pie_chart",
        description="生成饼图。参数: path(输出路径), title(标题), labels(标签), values(数值)",
        parameters={"type": "object", "properties": {
            "path": {"type": "string"}, "title": {"type": "string"},
            "labels": {"type": "array"}, "values": {"type": "array"}
        }, "required": ["labels", "values"]},
        func=_pie_chart,
    )
    tools.register(
        name="scatter_plot",
        description="生成散点图。参数: path(输出路径), title(标题), x(X轴), y(Y轴)",
        parameters={"type": "object", "properties": {
            "path": {"type": "string"}, "title": {"type": "string"},
            "x": {"type": "array"}, "y": {"type": "array"}
        }, "required": ["x", "y"]},
        func=_scatter_plot,
    )
    return 4


def unregister_tools():
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import tools
    for name in ["line_chart", "bar_chart", "pie_chart", "scatter_plot"]:
        tools.TOOLS.pop(name, None)
