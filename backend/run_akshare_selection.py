"""
使用akshare进行选股（修复列名问题）
"""
import sys
sys.path.insert(0, 'app/services')

from datetime import date, datetime, timedelta
import sqlite3
import numpy as np
import pandas as pd
import time

try:
    import akshare as ak
    HAS_AKSHARE = True
    print("成功导入akshare库")
except ImportError:
    HAS_AKSHARE = False
    print("警告：未安装akshare库")

INDUSTRY_STOCK_POOL = {
    '新能源': ['300750', '002594', '603606', '601012', '600438'],
    '新材料': ['600516', '600111', '000831', '600206', '300224'],
    '半导体': ['600703', '600584', '603986', '600460', '688981'],
    '人工智能': ['603019', '603986', '600588', '600410', '603229'],
    '生物医药': ['600276', '600867', '603259', '600196', '600521'],
    '高端制造': ['600031', '601138', '600895', '603997', '603015'],
}

STOCK_NAME_MAPPING = {
    '300750': '宁德时代', '002594': '比亚迪', '603606': '东方电缆', '601012': '隆基绿能',
    '600438': '通威股份', '600516': '方大炭素', '600111': '北方稀土', '000831': '五矿稀土',
    '600206': '有研新材', '300224': '正海磁材', '600703': '三安光电', '600584': '长电科技',
    '603986': '兆易创新', '600460': '士兰微', '688981': '中芯国际', '603019': '中科曙光',
    '600588': '用友网络', '600410': '华胜天成', '603229': '奥翔药业', '600276': '恒瑞医药',
    '600867': '通化东宝', '603259': '药明康德', '600196': '复星医药', '600521': '华海药业',
    '600031': '三一重工', '601138': '工业富联', '600895': '张江高科', '603997': '继峰股份',
    '603015': '弘讯科技',
}

def get_akshare_kline(stock_code, count=120):
    """从akshare获取K线数据"""
    if not HAS_AKSHARE:
        return None
    
    try:
        end_date = datetime.now().strftime('%Y%m%d')
        start_date = (datetime.now() - timedelta(days=300)).strftime('%Y%m%d')
        
        df = ak.stock_zh_a_hist(
            symbol=stock_code,
            period="daily",
            start_date=start_date,
            end_date=end_date,
            adjust="qfq"
        )
        
        if df is not None and len(df) >= 20:
            df = df.tail(count)
            return df
        return None
    except Exception as e:
        print(f"获取{stock_code}数据失败: {e}")
        return None

def calculate_indicators(kline_data):
    """计算技术指标"""
    if kline_data is None or len(kline_data) < 20:
        return None
    
    try:
        if '收盘' in kline_data.columns:
            close = kline_data['收盘'].values
            volume = kline_data['成交量'].values
        elif 'close' in kline_data.columns:
            close = kline_data['close'].values
            volume = kline_data['volume'].values
        else:
            print(f"列名: {kline_data.columns.tolist()}")
            return None
        
        indicators = {}
        
        ma5 = np.mean(close[-5:])
        ma10 = np.mean(close[-10:])
        ma20 = np.mean(close[-20:])
        ma60 = np.mean(close[-60:]) if len(close) >= 60 else ma20
        
        indicators['ma5'] = round(ma5, 2)
        indicators['ma10'] = round(ma10, 2)
        indicators['ma20'] = round(ma20, 2)
        indicators['ma60'] = round(ma60, 2)
        
        ema12_series = pd.Series(close).ewm(span=12, adjust=False).mean().values
        ema26_series = pd.Series(close).ewm(span=26, adjust=False).mean().values
        diff = ema12_series - ema26_series
        dea = pd.Series(diff).ewm(span=9, adjust=False).mean().values
        macd = (diff - dea) * 2
        
        indicators['diff'] = round(diff[-1], 4)
        indicators['dea'] = round(dea[-1], 4)
        indicators['macd'] = round(macd[-1], 4)
        indicators['diff_gt_dea_and_zero'] = diff[-1] > dea[-1] and diff[-1] > 0
        
        delta = np.diff(close[-14:])
        gain = delta[delta > 0]
        loss = -delta[delta < 0]
        avg_gain = np.mean(gain) if len(gain) > 0 else 0
        avg_loss = np.mean(loss) if len(loss) > 0 else 0
        
        if avg_loss == 0:
            rsi = 100 if avg_gain > 0 else 50
        else:
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
        
        indicators['rsi'] = round(rsi, 2)
        
        ma5_volume = np.mean(volume[-5:])
        indicators['volume'] = int(volume[-1])
        indicators['ma5_volume'] = int(ma5_volume)
        indicators['volume_above_ma5'] = volume[-1] > ma5_volume
        
        std_dev = np.std(close[-20:])
        indicators['bb_upper'] = round(ma20 + 2 * std_dev, 2)
        indicators['bb_middle'] = round(ma20, 2)
        indicators['bb_lower'] = round(ma20 - 2 * std_dev, 2)
        
        obv = np.zeros(len(close))
        obv[0] = volume[0]
        for i in range(1, len(close)):
            if close[i] > close[i-1]:
                obv[i] = obv[i-1] + volume[i]
            elif close[i] < close[i-1]:
                obv[i] = obv[i-1] - volume[i]
            else:
                obv[i] = obv[i-1]
        
        maobv = np.mean(obv[-20:])
        indicators['obv'] = int(obv[-1])
        indicators['maobv'] = int(maobv)
        indicators['obv_above_maobv'] = obv[-1] > maobv
        
        return indicators
    except Exception as e:
        print(f"计算指标失败: {e}")
        return None

def check_conditions(indicators, close_price):
    """检查技术条件"""
    result = {
        'ma_condition': False,
        'volume_condition': False,
        'macd_condition': False,
        'bollinger_condition': False,
        'obv_condition': False,
        'passed_count': 0
    }
    
    if indicators['ma20'] > 0 and close_price >= indicators['ma20'] * 0.98:
        result['ma_condition'] = True
        result['passed_count'] += 1
    
    if indicators['volume_above_ma5']:
        result['volume_condition'] = True
        result['passed_count'] += 1
    
    if indicators['diff_gt_dea_and_zero']:
        result['macd_condition'] = True
        result['passed_count'] += 1
    
    if indicators['bb_upper'] > indicators['bb_middle'] > indicators['bb_lower'] > 0:
        if indicators['bb_middle'] <= close_price <= indicators['bb_upper']:
            result['bollinger_condition'] = True
            result['passed_count'] += 1
    
    if indicators['obv_above_maobv']:
        result['obv_condition'] = True
        result['passed_count'] += 1
    
    return result

def calculate_score(conditions):
    """计算评分"""
    score = 0
    if conditions['ma_condition']:
        score += 25
    if conditions['volume_condition']:
        score += 25
    if conditions['macd_condition']:
        score += 20
    if conditions['bollinger_condition']:
        score += 15
    if conditions['obv_condition']:
        score += 15
    return min(score, 100)

def get_rating(score):
    """获取评级"""
    if score >= 90:
        return '强烈推荐'
    elif score >= 70:
        return '推荐'
    elif score >= 50:
        return '中性'
    elif score >= 30:
        return '观望'
    else:
        return '不推荐'

def save_to_database(selected_stocks):
    """保存选股结果到数据库"""
    try:
        conn = sqlite3.connect('database/trading_system.db')
        cursor = conn.cursor()
        
        today = date.today().isoformat()
        
        for stock in selected_stocks:
            cursor.execute('''
            INSERT OR REPLACE INTO score_record 
            (stock_code, stock_name, score_date, total_score, rating,
            ma_score, macd_score, rsi_score, bollinger_score, volume_score, obv_score,
            ma5, ma10, ma20, ma60, diff, dea, macd, rsi,
            bb_upper, bb_middle, bb_lower, close_price, volume,
            technical_reason)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                stock['stock_code'],
                stock['stock_name'],
                today,
                stock['score'],
                stock['rating'],
                25 if stock['conditions']['ma_condition'] else 0,
                20 if stock['conditions']['macd_condition'] else 0,
                int(stock['indicators']['rsi'] * 0.15),
                15 if stock['conditions']['bollinger_condition'] else 0,
                25 if stock['conditions']['volume_condition'] else 0,
                15 if stock['conditions']['obv_condition'] else 0,
                stock['indicators']['ma5'],
                stock['indicators']['ma10'],
                stock['indicators']['ma20'],
                stock['indicators']['ma60'],
                stock['indicators']['diff'],
                stock['indicators']['dea'],
                stock['indicators']['macd'],
                stock['indicators']['rsi'],
                stock['indicators']['bb_upper'],
                stock['indicators']['bb_middle'],
                stock['indicators']['bb_lower'],
                stock['close_price'],
                stock['indicators']['volume'],
                f"{stock['industry']}行业，技术指标符合选股条件"
            ))
        
        conn.commit()
        conn.close()
        print("选股结果已保存到数据库")
        return True
    except Exception as e:
        print(f"保存选股结果失败: {e}")
        return False

def run_selection(limit=5):
    """执行选股"""
    print("=" * 60)
    print("使用akshare进行选股")
    print("=" * 60)
    
    stock_pool = []
    for industry, codes in INDUSTRY_STOCK_POOL.items():
        for code in codes:
            stock_pool.append({
                'code': code,
                'name': STOCK_NAME_MAPPING.get(code, f'股票{code}'),
                'industry': industry
            })
    
    seen = set()
    unique_pool = []
    for item in stock_pool:
        if item['code'] not in seen:
            seen.add(item['code'])
            unique_pool.append(item)
    
    print(f"股票池共{len(unique_pool)}只股票")
    
    selected_stocks = []
    
    for i, stock_info in enumerate(unique_pool):
        stock_code = stock_info['code']
        stock_name = stock_info['name']
        stock_industry = stock_info['industry']
        
        print(f"[{i+1}/{len(unique_pool)}] 正在分析 {stock_name}({stock_code})...", end=" ")
        
        kline = get_akshare_kline(stock_code, 120)
        if kline is None or len(kline) < 20:
            print("跳过：数据不足")
            continue
        
        indicators = calculate_indicators(kline)
        if indicators is None:
            print("跳过：无法计算指标")
            continue
        
        if '收盘' in kline.columns:
            close_price = float(kline['收盘'].iloc[-1])
        else:
            close_price = float(kline['close'].iloc[-1])
        
        conditions = check_conditions(indicators, close_price)
        
        if conditions['passed_count'] >= 2:
            score = calculate_score(conditions)
            
            selected_stocks.append({
                'stock_code': stock_code,
                'stock_name': stock_name,
                'close_price': close_price,
                'industry': stock_industry,
                'score': score,
                'rating': get_rating(score),
                'conditions': conditions,
                'indicators': indicators
            })
            
            print(f"通过！评分: {score}, 条件: {conditions['passed_count']}/5")
        else:
            print(f"未通过：条件 {conditions['passed_count']}/5")
        
        time.sleep(0.3)
    
    selected_stocks.sort(key=lambda x: x['score'], reverse=True)
    result = selected_stocks[:limit]
    
    print(f"\n筛选完成，共{len(result)}只股票符合条件:")
    for i, stock in enumerate(result, 1):
        print(f"{i}. {stock['stock_name']}({stock['stock_code']}) - 价格: {stock['close_price']}, 评分: {stock['score']}, 评级: {stock['rating']}")
    
    if result:
        save_to_database(result)
    
    return result

if __name__ == "__main__":
    result = run_selection(limit=5)
    
    if result:
        print("\n" + "=" * 60)
        print("选股完成!")
        print("=" * 60)
    else:
        print("\n未找到符合条件的股票")
