import requests
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Referer': 'https://quote.eastmoney.com/'
}

def get_stock_detail(code):
    """获取单个股票详细信息"""
    try:
        if code.startswith('SH') or code.startswith('SZ'):
            market = 1 if code.startswith('SH') else 0
            pure_code = code[2:]
        else:
            return None

        url = 'https://push2delay.eastmoney.com/api/qt/stock/get'
        params = {
            'secid': f'{market}.{pure_code}',
            'fields': 'f43,f44,f45,f46,f47,f48,f50,f51,f52,f55,f56,f57,f58,f60,f116,f117,f162,f163,f167,f168,f169,f170'
        }

        r = requests.get(url, params=params, headers=headers, timeout=10)
        if r.status_code == 200:
            data = r.json()
            if data.get('data'):
                d = data['data']
                price = d.get('f43', 0) / 100 if d.get('f43') else 0
                price_high_52w = d.get('f168', 0) / 100 if d.get('f168') else 0
                price_low_52w = d.get('f169', 0) / 100 if d.get('f169') else 0
                pe_ttm = d.get('f116', 0) / 100 if d.get('f116') else 0
                pb = d.get('f167', 0) / 100 if d.get('f167') else 0

                return {
                    'code': code,
                    'name': d.get('f58', ''),
                    'price': price,
                    'change_pct': d.get('f170', 0) / 100 if d.get('f170') else 0,
                    'volume': d.get('f47', 0),
                    'pe_ttm': pe_ttm if 0 < pe_ttm < 10000 else 0,
                    'pb': pb if 0 < pb < 1000 else 0,
                    'price_high_52w': price_high_52w,
                    'price_low_52w': price_low_52w,
                }
    except Exception as e:
        pass
    return None

def get_hot_stocks():
    """获取东方财富人气榜单"""
    url = 'https://emappdata.eastmoney.com/stockrank/getAllCurrentList'
    params = {
        'appId': 'appId01',
        'globalId': '786e4c21-70dc-435a-93bb-38',
        'pageSize': 100,
        'pageNo': 1,
        'sortFields': 'SZ000858,SZ002594,SH600036,SZ300750',
        'direction': 'descending',
        'market': 'CN',
        'marketType': 0
    }

    r = requests.post(url, json=params, headers=headers, timeout=15)
    if r.status_code == 200:
        data = r.json()
        if data.get('data'):
            return [s['sc'] for s in data['data']]
    return []

def calculate_potential_score(stock):
    """计算股票潜力评分（基于估值、位置、流动性）"""
    score = 0
    reasons = []

    # 估值评分（权重40%）
    if stock['pe_ttm'] > 0:
        if stock['pe_ttm'] < 15:
            score += 40
            reasons.append(f'低PE({stock["pe_ttm"]:.1f})')
        elif stock['pe_ttm'] < 25:
            score += 35 - ((stock['pe_ttm'] - 15) / 10) * 10
            reasons.append(f'适中PE({stock["pe_ttm"]:.1f})')
        elif stock['pe_ttm'] < 40:
            score += 25 - ((stock['pe_ttm'] - 25) / 15) * 10
            reasons.append(f'偏高PE({stock["pe_ttm"]:.1f})')
        else:
            score += 10
            reasons.append(f'高PE({stock["pe_ttm"]:.1f})')
    else:
        score += 5
        reasons.append('亏损(无PE)')

    # 市净率评分（权重20%）
    if stock['pb'] > 0:
        if stock['pb'] < 2:
            score += 20
            reasons.append(f'低PB({stock["pb"]:.2f})')
        elif stock['pb'] < 4:
            score += 15 - ((stock['pb'] - 2) / 2) * 5
            reasons.append(f'适中PB({stock["pb"]:.2f})')
        elif stock['pb'] < 6:
            score += 10 - ((stock['pb'] - 4) / 2) * 5
        else:
            score += 5
    else:
        score += 10

    # 52周位置评分（权重25%）
    if stock['price'] > 0 and stock['price_high_52w'] > 0 and stock['price_low_52w'] > 0:
        position = (stock['price'] - stock['price_low_52w']) / (stock['price_high_52w'] - stock['price_low_52w'])
        if position < 0.3:
            score += 25
            reasons.append('52周低位')
        elif position < 0.5:
            score += 20
            reasons.append('52周中低位')
        elif position < 0.7:
            score += 10
            reasons.append('52周中部')
        else:
            score += 0
            reasons.append('52周高位')

    # 流动性评分（权重15%）
    volume = stock['volume']
    if volume > 100000000:
        score += 15
    elif volume > 50000000:
        score += 10
    elif volume > 10000000:
        score += 5

    return {
        'score': min(score, 100),
        'reasons': reasons
    }

def main():
    print('=' * 70)
    print('有潜力股票筛选工具 v3')
    print('策略：人气榜单 + 低估值 + 52周低位 + 高流动性')
    print('=' * 70)

    # 获取人气榜单
    print('\n[1/3] 获取东方财富人气榜单...')
    hot_codes = get_hot_stocks()
    print(f'获取到 {len(hot_codes)} 只人气股票')

    # 获取详细信息
    print(f'\n[2/3] 获取 {len(hot_codes)} 只股票的详细信息...')
    stock_infos = []
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(get_stock_detail, code): code for code in hot_codes}
        for i, future in enumerate(as_completed(futures), 1):
            result = future.result()
            if result and result['price'] > 0:
                stock_infos.append(result)

    print(f'成功获取 {len(stock_infos)} 只股票的详细信息')

    # 计算潜力评分
    print('\n[3/3] 计算潜力评分...')
    scored_stocks = []
    for stock in stock_infos:
        potential = calculate_potential_score(stock)
        scored_stocks.append({
            **stock,
            'potential_score': potential['score'],
            'potential_reasons': potential['reasons']
        })

    # 按潜力评分排序
    scored_stocks.sort(key=lambda x: x['potential_score'], reverse=True)

    # 输出结果
    print('\n' + '=' * 70)
    print('有潜力股票排行榜（人气榜单二次筛选 - 价值投资策略）')
    print('=' * 70)
    print(f"{'排名':<5} {'代码':<10} {'名称':<10} {'现价':<10} {'涨幅':<10} {'PE(TTM)':<10} {'PB':<8} {'潜力分':<8} {'选股理由'}")
    print('-' * 70)

    for i, stock in enumerate(scored_stocks[:50], 1):
        reasons = ','.join(stock['potential_reasons'][:3]) if stock['potential_reasons'] else '-'
        pe_str = f"{stock['pe_ttm']:.1f}" if stock['pe_ttm'] > 0 else '亏损'
        print(f"{i:<5} {stock['code']:<10} {stock['name']:<10} {stock['price']:<10.2f} {stock['change_pct']:>+8.2f}% {pe_str:<10} {stock['pb']:<8.2f} {stock['potential_score']:<8.1f} {reasons}")

    # 保存到文件
    with open('potential_stocks_result.txt', 'w', encoding='utf-8') as f:
        f.write('有潜力股票排行榜\n')
        f.write(f'扫描时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n')
        f.write('策略：人气榜单 + 低估值 + 52周低位 + 高流动性\n')
        f.write('=' * 70 + '\n')
        f.write(f"{'排名':<5} {'代码':<10} {'名称':<10} {'现价':<10} {'涨幅':<10} {'PE(TTM)':<10} {'PB':<8} {'潜力分':<8} {'选股理由'}\n")
        f.write('-' * 70 + '\n')
        for i, stock in enumerate(scored_stocks[:50], 1):
            reasons = ','.join(stock['potential_reasons'][:3]) if stock['potential_reasons'] else '-'
            pe_str = f"{stock['pe_ttm']:.1f}" if stock['pe_ttm'] > 0 else '亏损'
            f.write(f"{i:<5} {stock['code']:<10} {stock['name']:<10} {stock['price']:<10.2f} {stock['change_pct']:>+8.2f}% {pe_str:<10} {stock['pb']:<8.2f} {stock['potential_score']:<8.1f} {reasons}\n")

    print('\n结果已保存到 potential_stocks_result.txt')

if __name__ == '__main__':
    main()
