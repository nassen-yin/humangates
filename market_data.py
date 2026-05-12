#!/usr/bin/env python3
"""
郑商所主要期权品种的期货实时行情获取工具
Usage: python3 market_data.py futures <品种名>
品种名: PTA, 郑醇, 白糖, 菜油, 棉花
"""

import urllib.request
import json
import sys
import time

# ZCE品种对应的合约代码
CONTRACTS = {
    'PTA': 'TAM',
    '郑醇': 'MAM',
    '白糖': 'SRM',
    '菜油': 'OIM',
    '棉花': 'CFM',
}

VARIETY_NAMES = {
    'TAM': 'PTA',
    'MAM': '郑醇(甲醇)',
    'SRM': '白糖',
    'OIM': '菜油',
    'CFM': '棉花',
}

def fetch_all_zce_data():
    """Fetch all ZCE futures data with pagination"""
    all_items = []
    page = 1
    while True:
        url = f'https://push2.eastmoney.com/api/qt/clist/get?pn={page}&pz=100&po=1&np=1&fltt=2&invt=2&fid=f3&fs=m:115&fields=f2,f3,f4,f5,f6,f7,f12,f14,f15,f16,f17,f18'
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'
        })
        try:
            resp = urllib.request.urlopen(req, timeout=10)
            data = json.loads(resp.read().decode('utf-8'))
            if not data.get('data') or not data['data'].get('diff'):
                break
            items = data['data']['diff']
            if not items:
                break
            all_items.extend(items)
            page += 1
            if len(items) < 100:
                break
        except Exception as e:
            print(f"获取数据出错: {e}", file=sys.stderr)
            break
    return all_items


def format_number(val):
    """Format number with commas"""
    if val is None or val == '-':
        return '-'
    try:
        return f'{int(val):,}'
    except (ValueError, TypeError):
        return str(val)


def query_single(name):
    """Query a single variety"""
    code = CONTRACTS.get(name)
    if not code:
        print(f"未知品种: {name}")
        print(f"可用品种: {', '.join(CONTRACTS.keys())}")
        return
    
    items = fetch_all_zce_data()
    found = None
    for item in items:
        if item['f12'] == code:
            found = item
            break
    
    if not found:
        print(f"未找到 {name} ({code}) 的行情数据")
        return
    
    print(f"\n{'='*70}")
    print(f"  {name} ({found['f14']}) 期货实时行情")
    print(f"{'='*70}")
    print(f"  最新价:    {found.get('f2', '-')}")
    print(f"  涨跌幅:    {found.get('f3', '-')}%")
    print(f"  涨跌额:    {found.get('f4', '-')}")
    print(f"  成交量:    {format_number(found.get('f5', '-'))} 手")
    print(f"  成交额:    {format_number(found.get('f6', '-'))} 元")
    print(f"  昨收价:    {found.get('f15', '-')}")
    print(f"  今开价:    {found.get('f16', '-')}")
    print(f"  最高价:    {found.get('f17', '-')}")
    print(f"  最低价:    {found.get('f18', '-')}")
    print(f"{'='*70}")


def query_all():
    """Query all configured varieties"""
    items = fetch_all_zce_data()
    
    # Build lookup dict
    lookup = {}
    for item in items:
        lookup[item['f12']] = item
    
    print(f'\n{"郑商所(ZCE)主要品种期货实时行情":^90}')
    print(f'{"="*100}')
    header = f'{"品种":14s} {"合约":8s} {"最新价":>10s} {"涨跌幅":>10s} {"涨跌额":>10s} {"成交量(手)":>12s} {"成交额(元)":>18s} {"昨收":>10s}'
    print(header)
    print(f'{"-"*100}')
    
    for ch_name, code in CONTRACTS.items():
        item = lookup.get(code)
        if item:
            price = str(item.get('f2', '-'))
            pct = f"{item.get('f3', '-')}%"
            change = str(item.get('f4', '-'))
            volume = format_number(item.get('f5', '-'))
            turnover = format_number(item.get('f6', '-'))
            prev_close = str(item.get('f15', '-'))
            print(f'{ch_name:14s} {code:8s} {price:>10s} {pct:>10s} {change:>10s} {volume:>12s} {turnover:>18s} {prev_close:>10s}')
        else:
            print(f'{ch_name:14s} {code:8s} {"暂无数据":>10s}')
    
    print(f'{"="*100}')
    print(f'数据来源: 东方财富 East Money API')


def main():
    if len(sys.argv) < 2:
        print("用法: python3 market_data.py futures [品种名]")
        print("品种名: PTA, 郑醇, 白糖, 菜油, 棉花")
        print("不指定品种则显示全部")
        return
    
    cmd = sys.argv[1]
    if cmd == 'futures':
        if len(sys.argv) >= 3:
            query_single(sys.argv[2])
        else:
            query_all()
    else:
        print(f"未知命令: {cmd}")
        print("用法: python3 market_data.py futures [品种名]")


if __name__ == '__main__':
    main()
