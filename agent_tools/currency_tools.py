# -*- coding: utf-8 -*-
"""
货币转换工具集 - 汇率转换
"""

import json
import os


def _convert_currency(args: dict) -> str:
    amount = args.get('amount', 1)
    from_cur = args.get('from', 'USD')
    to_cur = args.get('to', 'CNY')
    try:
        import requests
        url = f"https://api.exchangerate-api.com/v4/latest/{from_cur}"
        resp = requests.get(url, timeout=10)
        rates = resp.json().get('rates', {})
        if to_cur not in rates:
            return "❌ 不支持的货币"
        result = amount * rates[to_cur]
        return json.dumps({'成功': True, '金额': amount, '从': from_cur, '到': to_cur, '结果': round(result, 2)}, ensure_ascii=False, indent=2)
    except ImportError:
        return "❌ 请安装 requests: pip install requests"
    except Exception as e:
        return f"❌ 转换失败: {e}"


def register_tools():
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import tools
    tools.register(
        name="convert_currency",
        description="货币汇率转换。参数: amount(金额), from(源货币), to(目标货币)",
        parameters={"type": "object", "properties": {
            "amount": {"type": "number", "description": "金额"},
            "from": {"type": "string", "description": "源货币代码如USD"},
            "to": {"type": "string", "description": "目标货币代码如CNY"}
        }, "required": ["amount", "from", "to"]},
        func=_convert_currency,
    )
    return 1


def unregister_tools():
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import tools
    for name in ["convert_currency"]:
        tools.TOOLS.pop(name, None)
