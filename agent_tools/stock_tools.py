# -*- coding: utf-8 -*-
"""
股票交易工具集 - 支持A股行情、技术分析、模拟交易
"""

import os
import json
import time
from datetime import datetime, timedelta


def _import_akshare():
    try:
        import akshare as ak
        return ak
    except ImportError:
        return None


def _import_pandas():
    try:
        import pandas as pd
        return pd
    except ImportError:
        return None


def _import_numpy():
    try:
        import numpy as np
        return np
    except ImportError:
        return None


class SimulatedAccount:
    def __init__(self, initial_cash=100000):
        self.cash = initial_cash
        self.positions = {}
        self.trades = []

    def buy(self, symbol, price, shares):
        cost = price * shares
        if cost > self.cash:
            return {"success": False, "message": f"余额不足，需要 {cost:.2f}，可用 {self.cash:.2f}"}
        if symbol in self.positions:
            old = self.positions[symbol]
            total_cost = old['avg_cost'] * old['shares'] + cost
            old['shares'] += shares
            old['avg_cost'] = total_cost / old['shares']
        else:
            self.positions[symbol] = {'shares': shares, 'avg_cost': price}
        self.cash -= cost
        self.trades.append({'time': datetime.now().isoformat(), 'symbol': symbol, 'action': 'buy', 'price': price, 'shares': shares})
        return {"success": True, "message": f"买入 {symbol} {shares}股 @ {price:.2f}"}

    def sell(self, symbol, price, shares=None):
        if symbol not in self.positions:
            return {"success": False, "message": f"未持有 {symbol}"}
        current = self.positions[symbol]
        sell_shares = shares if shares else current['shares']
        if sell_shares > current['shares']:
            return {"success": False, "message": f"持仓不足"}
        revenue = price * sell_shares
        self.cash += revenue
        current['shares'] -= sell_shares
        if current['shares'] == 0:
            del self.positions[symbol]
        self.trades.append({'time': datetime.now().isoformat(), 'symbol': symbol, 'action': 'sell', 'price': price, 'shares': sell_shares})
        return {"success": True, "message": f"卖出 {symbol} {sell_shares}股 @ {price:.2f}"}

    def get_portfolio(self, current_prices=None):
        total_value = self.cash
        holdings = []
        for symbol, pos in self.positions.items():
            price = (current_prices or {}).get(symbol, pos['avg_cost'])
            value = price * pos['shares']
            total_value += value
            holdings.append({'symbol': symbol, 'shares': pos['shares'], 'avg_cost': pos['avg_cost'], 'current_price': price, 'value': value})
        return {'cash': self.cash, 'total_value': total_value, 'holdings': holdings, 'trade_count': len(self.trades)}


_sim_account = None

def get_sim_account(initial_cash=100000):
    global _sim_account
    if _sim_account is None:
        _sim_account = SimulatedAccount(initial_cash)
    return _sim_account


def _get_stock_quote(args: dict) -> str:
    try:
        symbol = args.get('symbol', '')
        if not symbol:
            return "❌ 请提供股票代码"
        ak = _import_akshare()
        if not ak:
            return "❌ 请安装 akshare: pip install akshare"
        df = ak.stock_zh_a_spot_em()
        row = df[df['代码'] == symbol]
        if row.empty:
            return f"❌ 未找到股票代码: {symbol}"
        row = row.iloc[0]
        result = {
            '代码': row.get('代码', symbol), '名称': row.get('名称', ''),
            '最新价': row.get('最新价', 0), '涨跌幅': row.get('涨跌幅', 0),
            '成交量': row.get('成交量', 0), '成交额': row.get('成交额', 0),
        }
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"❌ 获取行情失败: {e}"


def _get_stock_history(args: dict) -> str:
    try:
        symbol = args.get('symbol', '')
        count = args.get('count', 100)
        if not symbol:
            return "❌ 请提供股票代码"
        ak = _import_akshare()
        pd = _import_pandas()
        if not ak or not pd:
            return "❌ 请安装 akshare 和 pandas"
        end_date = datetime.now().strftime('%Y%m%d')
        start_date = (datetime.now() - timedelta(days=count * 2)).strftime('%Y%m%d')
        df = ak.stock_zh_a_hist(symbol, 'daily', start_date, end_date, adjust='')
        if df.empty:
            return f"❌ 未获取到数据"
        df = df.tail(count)
        result = []
        for _, row in df.iterrows():
            result.append({'日期': str(row.get('日期', '')), '开盘': float(row.get('开盘', 0)), '收盘': float(row.get('收盘', 0)), '最高': float(row.get('最高', 0)), '最低': float(row.get('最低', 0))})
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"❌ 获取历史数据失败: {e}"


def _simulate_buy(args: dict) -> str:
    try:
        symbol = args.get('symbol', '')
        price = args.get('price', 0)
        shares = args.get('shares', 0)
        if not symbol or price <= 0 or shares <= 0:
            return "❌ 请提供有效的 symbol, price, shares"
        account = get_sim_account()
        result = account.buy(symbol, price, shares)
        if result['success']:
            return f"✅ {result['message']}\n账户余额: {account.cash:.2f}"
        return f"❌ {result['message']}"
    except Exception as e:
        return f"❌ 模拟买入失败: {e}"


def _simulate_sell(args: dict) -> str:
    try:
        symbol = args.get('symbol', '')
        price = args.get('price', 0)
        shares = args.get('shares', 0)
        if not symbol or price <= 0:
            return "❌ 请提供有效的 symbol, price"
        account = get_sim_account()
        result = account.sell(symbol, price, shares if shares > 0 else None)
        if result['success']:
            return f"✅ {result['message']}\n账户余额: {account.cash:.2f}"
        return f"❌ {result['message']}"
    except Exception as e:
        return f"❌ 模拟卖出失败: {e}"


def _view_portfolio(args: dict) -> str:
    try:
        account = get_sim_account()
        portfolio = account.get_portfolio()
        output = f"📊 模拟账户\n总资产: {portfolio['total_value']:.2f}\n现金: {portfolio['cash']:.2f}\n交易次数: {portfolio['trade_count']}\n\n"
        if portfolio['holdings']:
            for h in portfolio['holdings']:
                output += f"  {h['symbol']}: {h['shares']}股 | 成本 {h['avg_cost']:.2f} | 现价 {h['current_price']:.2f}\n"
        else:
            output += "📭 暂无持仓\n"
        return output
    except Exception as e:
        return f"❌ 查看持仓失败: {e}"


def register_tools():
    """注册工具到 Hermes"""
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import tools

    tools.register(name="get_stock_quote", description="获取A股实时行情。参数: symbol", parameters={"type": "object", "properties": {"symbol": {"type": "string"}}, "required": ["symbol"]}, func=_get_stock_quote)
    tools.register(name="get_stock_history", description="获取股票历史K线。参数: symbol, count", parameters={"type": "object", "properties": {"symbol": {"type": "string"}, "count": {"type": "integer"}}, "required": ["symbol"]}, func=_get_stock_history)
    tools.register(name="simulate_buy", description="模拟买入。参数: symbol, price, shares", parameters={"type": "object", "properties": {"symbol": {"type": "string"}, "price": {"type": "number"}, "shares": {"type": "integer"}}, "required": ["symbol", "price", "shares"]}, func=_simulate_buy)
    tools.register(name="simulate_sell", description="模拟卖出。参数: symbol, price, shares", parameters={"type": "object", "properties": {"symbol": {"type": "string"}, "price": {"type": "number"}, "shares": {"type": "integer"}}, "required": ["symbol", "price"]}, func=_simulate_sell)
    tools.register(name="view_portfolio", description="查看模拟账户持仓", parameters={"type": "object", "properties": {}}, func=_view_portfolio)
    return 5


def unregister_tools():
    """卸载工具"""
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import tools
    for name in ["get_stock_quote", "get_stock_history", "simulate_buy", "simulate_sell", "view_portfolio"]:
        tools.TOOLS.pop(name, None)
