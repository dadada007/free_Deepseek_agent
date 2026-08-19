# -*- coding: utf-8 -*-
"""
CSV处理工具集 - 支持读取、写入、转换
"""

import os
import json
import csv


def _read_csv(args: dict) -> str:
    try:
        path = args.get('path', '')
        limit = args.get('limit', 100)
        encoding = args.get('encoding', 'utf-8')
        if not path:
            return "❌ 请提供CSV文件路径"
        if not os.path.exists(path):
            return f"❌ 文件不存在: {path}"
        rows = []
        with open(path, 'r', encoding=encoding) as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames
            for i, row in enumerate(reader):
                if i >= limit:
                    break
                rows.append(row)
        return json.dumps({'成功': True, '文件': path, '列名': headers, '总行数': len(rows), '数据': rows}, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"❌ 读取CSV失败: {e}"


def _write_csv(args: dict) -> str:
    try:
        path = args.get('path', 'output.csv')
        headers = args.get('headers', [])
        rows = args.get('data', [])
        encoding = args.get('encoding', 'utf-8')
        if not headers:
            return "❌ 请提供列名"
        if not rows:
            return "❌ 请提供数据"
        with open(path, 'w', newline='', encoding=encoding) as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            writer.writerows(rows)
        return json.dumps({'成功': True, '输出': path, '行数': len(rows), '列数': len(headers)}, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"❌ 写入CSV失败: {e}"


def _csv_to_json(args: dict) -> str:
    try:
        path = args.get('path', '')
        output = args.get('output', '')
        encoding = args.get('encoding', 'utf-8')
        if not path:
            return "❌ 请提供CSV文件路径"
        if not os.path.exists(path):
            return f"❌ 文件不存在: {path}"
        rows = []
        with open(path, 'r', encoding=encoding) as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        if output:
            with open(output, 'w', encoding='utf-8') as f:
                json.dump(rows, f, ensure_ascii=False, indent=2)
            result = {'成功': True, '输出': output, '行数': len(rows)}
        else:
            result = {'成功': True, '数据': rows}
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"❌ 转换失败: {e}"


def register_tools():
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import tools
    tools.register(
        name="read_csv",
        description="读取CSV文件。参数: path(文件路径), limit(行数限制), encoding(编码)",
        parameters={"type": "object", "properties": {
            "path": {"type": "string"}, "limit": {"type": "integer"}, "encoding": {"type": "string"}
        }, "required": ["path"]},
        func=_read_csv,
    )
    tools.register(
        name="write_csv",
        description="写入CSV文件。参数: path(路径), headers(列名), data(数据行)",
        parameters={"type": "object", "properties": {
            "path": {"type": "string"}, "headers": {"type": "array"}, "data": {"type": "array"}
        }, "required": ["headers", "data"]},
        func=_write_csv,
    )
    tools.register(
        name="csv_to_json",
        description="CSV转JSON。参数: path(CSV路径), output(输出路径)",
        parameters={"type": "object", "properties": {
            "path": {"type": "string"}, "output": {"type": "string"}
        }, "required": ["path"]},
        func=_csv_to_json,
    )
    return 3


def unregister_tools():
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import tools
    for name in ["read_csv", "write_csv", "csv_to_json"]:
        tools.TOOLS.pop(name, None)
