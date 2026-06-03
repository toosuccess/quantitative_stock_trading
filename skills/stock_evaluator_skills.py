"""
评价技能
职责：对stock_basic_info中的股票打分，输出到score_record表
"""

import akshare as ak
import pymysql
from pymysql.cursors import DictCursor
import os
import sys
import json
import numpy as np
import pandas as pd
from datetime import datetime, date, timedelta
import urllib3
import warnings

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
warnings.filterwarnings('ignore')

PROXY_HOST = os.environ.get('PROXY_HOST', '127.0.0.1')
PROXY_PORT = os.environ.get('PROXY_PORT', '7897')
PROXY_ENABLED = os.environ.get('PROXY_ENABLED', 'false').lower() == 'true'

if PROXY_ENABLED:
    os.environ['HTTP_PROXY'] = f'http://{PROXY_HOST}:{PROXY_PORT}'
    os.environ['HTTPS_PROXY'] = f'http://{PROXY_HOST}:{PROXY_PORT}'
    os.environ['NO_PROXY'] = 'localhost,127.0.0.1'
else:
    os.environ['HTTP_PROXY'] = ''
    os.environ['HTTPS_PROXY'] = ''
    os.environ['http_proxy'] = ''
    os.environ['https_proxy'] = ''

BACKEND_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'backend')
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app.database_config import MYSQL_CONFIG

POLICY_ORIENTED_INDUSTRIES = {
    '新能源': {'industry_type': '战略性新兴产业', 'growth_potential': '高'},
    '新材料': {'industry_type': '战略性新兴产业', 'growth_potential': '高'},
    '6G': {'industry_type': '未来产业', 'growth_potential': '极高'},
    '核聚变': {'industry_type': '未来产业', 'growth_potential': '极高'},
    '消费升级': {'industry_type': '民生消费', 'growth_potential': '中高'},
    '半导体': {'industry_type': '战略性新兴产业', 'growth_potential': '高'},
    '人工智能': {'industry_type': '未来产业', 'growth_potential': '极高'},
    '生物医药': {'industry_type': '战略性新兴产业', 'growth_potential': '高'},
    '高端制造': {'industry_type': '战略性新兴产业', 'growth_potential': '高'},
    '数字经济': {'industry_type': '未来产业', 'growth_potential': '极高'}
}


class StockEvaluatorSkills:
    """评价技能类"""
    
    def __init__(self, db_path=None):
        self.db_path = db_path
        self.conn = None
    
    def connect(self):
        """连接数据库"""
        self.conn = pymysql.connect(**MYSQL_CONFIG, cursorclass=DictCursor)
        return self.conn
    
    def disconnect(self):
        """断开数据库连接"""
        if self.conn:
            self.conn.close()
            self.conn = None
    
    def _get_stock_name_from_api(self, stock_code):
        """从API获取股票名称（优先akshare，备用东方财富）"""
        pure_code = stock_code.replace('sh', '').replace('sz', '').replace('bj', '')

        try:
            import akshare as ak
            df = ak.stock_individual_info_em(symbol=pure_code)
            if df is not None and len(df) > 0:
                name_row = df[df['item'] == '股票简称']
                if len(name_row) > 0:
                    return name_row['value'].values[0]
        except Exception as e:
            print(f"akshare获取股票{pure_code}名称失败: {e}")

        try:
            import requests
            market = 1 if pure_code.startswith('6') else 0
            url = 'https://push2delay.eastmoney.com/api/qt/stock/get'
            params = {
                'secid': f'{market}.{pure_code}',
                'fields': 'f58'
            }
            r = requests.get(url, params=params, timeout=10)
            if r.status_code == 200:
                data = r.json()
                if data.get('data') and data['data'].get('f58'):
                    return data['data']['f58']
        except Exception as e:
            print(f"东方财富获取股票{pure_code}名称失败: {e}")

        return None
    
    def get_stock_price_data(self, stock_code):
        """获取股票价格数据（使用akshare K线接口，备用东方财富接口）"""
        pure_code = stock_code.replace('sh', '').replace('sz', '').replace('bj', '')

        is_bj_stock = pure_code.startswith('83') or pure_code.startswith('87') or pure_code.startswith('92')

        if is_bj_stock:
            return self._get_bj_stock_price(pure_code)

        try:
            import akshare as ak
            prefix = 'sh' if pure_code.startswith('6') else 'sz'
            symbol = f"{prefix}{pure_code}"

            df = ak.stock_zh_a_daily(symbol=symbol, adjust="qfq")

            if df is not None and len(df) >= 60:
                return self._process_akshare_data(df)
        except Exception as e:
            print(f"akshare获取{stock_code}失败，尝试东方财富接口: {e}")

        return self._get_em_stock_kline(pure_code)

    def _get_bj_stock_price(self, pure_code):
        """获取北交所股票价格（使用东方财富实时接口）"""
        import requests
        url = 'https://push2delay.eastmoney.com/api/qt/stock/get'
        params = {
            'secid': f'0.{pure_code}',
            'fields': 'f43,f44,f45,f46,f47,f48,f50,f51,f52,f55,f56,f57,f58,f60'
        }
        r = requests.get(url, params=params, timeout=15)
        data = r.json()

        if not data.get('data'):
            return None

        d = data['data']
        current_close = d.get('f43', 0) / 100 if d.get('f43') else 0

        if current_close == 0:
            return None

        return {
            'close': current_close,
            'high': d.get('f44', 0) / 100 if d.get('f44') else current_close,
            'low': d.get('f45', 0) / 100 if d.get('f45') else current_close,
            'volume': d.get('f47', 0) if d.get('f47') else 0,
            'MA5': current_close,
            'MA10': current_close,
            'MA20': current_close,
            'MA60': current_close,
            'MA180': current_close,
            'MA250': current_close,
            'MA5_Volume': d.get('f47', 0) if d.get('f47') else 0,
            'MA60_Volume': d.get('f47', 0) if d.get('f47') else 0,
            'Turnover_Rate': 0.1,
            'DIFF': 0,
            'DEA': 0,
            'MACD': 0,
            'RSI': 50,
            'OBV': 0,
            'MAOBV': 0,
            'BB_Upper': current_close * 1.02,
            'BB_Middle': current_close,
            'BB_Lower': current_close * 0.98
        }

    def _get_em_stock_kline(self, pure_code):
        """使用东方财富K线接口获取股票数据"""
        import requests
        import numpy as np
        import pandas as pd

        secid = f'1.{pure_code}' if pure_code.startswith('6') else f'0.{pure_code}'
        url = 'https://push2his.eastmoney.com/api/qt/stock/kline/get'
        params = {
            'secid': secid,
            'fields1': 'f1,f2,f3,f4,f5,f6',
            'fields2': 'f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61',
            'klt': '101',
            'fqt': '1',
            'lmt': '250',
            'end': '20500101'
        }

        r = requests.get(url, params=params, timeout=15)
        data = r.json()

        if not data.get('data') or not data['data'].get('klines'):
            print(f"东方财富K线接口获取{pure_code}失败")
            return None

        klines = data['data']['klines']

        close_prices = []
        highs = []
        lows = []
        volumes = []

        for kline in klines:
            parts = kline.split(',')
            close_prices.append(float(parts[2]))
            highs.append(float(parts[3]))
            lows.append(float(parts[4]))
            volumes.append(float(parts[5]))

        close = np.array(close_prices)
        high = np.array(highs)
        low = np.array(lows)
        volume = np.array(volumes)

        current_close = float(close[-1])
        current_volume = float(volume[-1])

        ma20 = np.mean(close[-20:]) if len(close) >= 20 else current_close
        ma20_prev = np.mean(close[-21:-1]) if len(close) >= 21 else ma20
        ma60 = np.mean(close[-60:]) if len(close) >= 60 else ma20
        ma180 = np.mean(close[-180:]) if len(close) >= 180 else ma60
        ma250 = np.mean(close[-250:]) if len(close) >= 250 else ma180

        ema12 = pd.Series(close).ewm(span=12).mean().values
        ema26 = pd.Series(close).ewm(span=26).mean().values
        diff = ema12 - ema26
        dea = pd.Series(diff).ewm(span=9).mean().values
        macd = 2 * (diff - dea)

        delta = np.diff(close)
        gain = delta[delta > 0]
        loss = -delta[delta < 0]
        avg_gain = np.mean(gain) if len(gain) > 0 else 0
        avg_loss = np.mean(loss) if len(loss) > 0 else 0
        rsi = 100 - (100 / (1 + avg_gain / avg_loss)) if avg_loss != 0 else 50

        obv = [0]
        for i in range(1, len(close)):
            if close[i] > close[i-1]:
                obv.append(obv[-1] + volume[i])
            elif close[i] < close[i-1]:
                obv.append(obv[-1] - volume[i])
            else:
                obv.append(obv[-1])
        obv = np.array(obv)
        maobv = np.mean(obv[-30:]) if len(obv) >= 30 else np.mean(obv)

        bb_middle = np.mean(close[-20:]) if len(close) >= 20 else current_close
        bb_std = np.std(close[-20:]) if len(close) >= 20 else 0
        bb_upper = bb_middle + 2 * bb_std
        bb_lower = bb_middle - 2 * bb_std

        ma5_volume = np.mean(volume[-5:]) if len(volume) >= 5 else current_volume
        ma60_volume = np.mean(volume[-60:]) if len(volume) >= 60 else ma5_volume

        turnover_rate = 0.02

        print(f"✅ 东方财富获取 {pure_code} 价格数据成功: close={current_close}, volume={current_volume}")

        return {
            'close': current_close,
            'volume': current_volume,
            'MA5': np.mean(close[-5:]) if len(close) >= 5 else current_close,
            'MA10': np.mean(close[-10:]) if len(close) >= 10 else current_close,
            'MA20': ma20,
            'MA20_prev': ma20_prev,
            'MA60': ma60,
            'MA180': ma180,
            'MA250': ma250,
            'DIFF': diff[-1],
            'DEA': dea[-1],
            'MACD': macd[-1],
            'RSI': rsi,
            'OBV': obv[-1],
            'MAOBV': maobv,
            'BB_Upper': bb_upper,
            'BB_Middle': bb_middle,
            'BB_Lower': bb_lower,
            'MA5_Volume': ma5_volume,
            'MA60_Volume': ma60_volume,
            'Turnover_Rate': turnover_rate
        }

    def _process_akshare_data(self, df):
        """处理akshare获取的数据"""
        import numpy as np
        import pandas as pd

        df = df.tail(250)

        close = df['close'].values
        high = df['high'].values
        low = df['low'].values
        volume = df['volume'].values

        current_close = float(close[-1])
        current_volume = float(volume[-1])

        ma20 = np.mean(close[-20:]) if len(close) >= 20 else current_close
        ma20_prev = np.mean(close[-21:-1]) if len(close) >= 21 else ma20
        ma60 = np.mean(close[-60:]) if len(close) >= 60 else ma20
        ma180 = np.mean(close[-180:]) if len(close) >= 180 else ma60
        ma250 = np.mean(close[-250:]) if len(close) >= 250 else ma180

        ema12 = pd.Series(close).ewm(span=12).mean().values
        ema26 = pd.Series(close).ewm(span=26).mean().values
        diff = ema12 - ema26
        dea = pd.Series(diff).ewm(span=9).mean().values
        macd = 2 * (diff - dea)

        delta = np.diff(close)
        gain = delta[delta > 0]
        loss = -delta[delta < 0]
        avg_gain = np.mean(gain) if len(gain) > 0 else 0
        avg_loss = np.mean(loss) if len(loss) > 0 else 0
        rsi = 100 - (100 / (1 + avg_gain / avg_loss)) if avg_loss != 0 else 50

        obv = [0]
        for i in range(1, len(close)):
            if close[i] > close[i-1]:
                obv.append(obv[-1] + volume[i])
            elif close[i] < close[i-1]:
                obv.append(obv[-1] - volume[i])
            else:
                obv.append(obv[-1])
        obv = np.array(obv)
        maobv = np.mean(obv[-30:]) if len(obv) >= 30 else np.mean(obv)

        bb_middle = np.mean(close[-20:]) if len(close) >= 20 else current_close
        bb_std = np.std(close[-20:]) if len(close) >= 20 else 0
        bb_upper = bb_middle + 2 * bb_std
        bb_lower = bb_middle - 2 * bb_std

        ma5_volume = np.mean(volume[-5:]) if len(volume) >= 5 else current_volume
        ma60_volume = np.mean(volume[-60:]) if len(volume) >= 60 else ma5_volume

        turnover_rate = 0.02

        return {
            'close': current_close,
            'volume': current_volume,
            'MA5': np.mean(close[-5:]) if len(close) >= 5 else current_close,
            'MA10': np.mean(close[-10:]) if len(close) >= 10 else current_close,
            'MA20': ma20,
            'MA20_prev': ma20_prev,
            'MA60': ma60,
            'MA180': ma180,
            'MA250': ma250,
            'DIFF': diff[-1],
            'DEA': dea[-1],
            'MACD': macd[-1],
            'RSI': rsi,
            'OBV': obv[-1],
            'MAOBV': maobv,
            'BB_Upper': bb_upper,
            'BB_Middle': bb_middle,
            'BB_Lower': bb_lower,
            'MA5_Volume': ma5_volume,
            'MA60_Volume': ma60_volume,
            'Turnover_Rate': turnover_rate
        }
    
    def calculate_technical_score(self, stock_code):
        """计算技术面得分"""
        import numpy as np
        price_data = self.get_stock_price_data(stock_code)
        
        if not price_data:
            return 0, {}, None
        
        ma_score = 0
        volume_score = 0
        macd_score = 0
        obv_score = 0
        bollinger_score = 0
        
        ma_condition = {}
        volume_condition = {}
        trend_condition = {}
        fund_condition = {}
        bollinger_condition = {}
        
        if price_data['close'] > price_data['MA20']:
            ma20_up = price_data['MA20'] > price_data.get('MA20_prev', price_data['MA20'])
            ma20_above_ma60 = price_data['MA20'] > price_data['MA60']
            ma_condition['price_above_ma20'] = True
            ma_condition['ma20_up'] = ma20_up
            ma_condition['ma20_above_ma60'] = ma20_above_ma60
            if ma20_up and ma20_above_ma60:
                ma_score = 25
        else:
            ma_condition['price_above_ma20'] = False
            ma_condition['ma20_up'] = False
            ma_condition['ma20_above_ma60'] = False
        
        volume_above_ma5 = price_data['volume'] > price_data['MA5_Volume']
        volume_above_ma60 = price_data['volume'] > price_data['MA60_Volume']
        turnover_rate_range = 0.05 <= price_data['Turnover_Rate'] <= 0.20
        
        volume_condition['volume_above_ma5'] = volume_above_ma5
        volume_condition['volume_above_ma60'] = volume_above_ma60
        volume_condition['turnover_rate_range'] = turnover_rate_range
        
        if volume_above_ma5 and volume_above_ma60 and turnover_rate_range:
            volume_score = 25
        
        diff_gt_dea = price_data['DIFF'] > price_data['DEA']
        macd_above_zero = price_data['MACD'] > 0
        trend_condition['diff_gt_dea_and_zero'] = diff_gt_dea and macd_above_zero
        trend_condition['macd_golden_cross'] = diff_gt_dea
        trend_condition['macd_above_zero'] = macd_above_zero
        trend_condition['dmi_condition'] = True
        
        if diff_gt_dea and macd_above_zero:
            macd_score = 20
        
        obv_above_maobv = price_data['OBV'] > price_data['MAOBV']
        fund_condition['obv_above_maobv'] = obv_above_maobv
        fund_condition['obv_up'] = obv_above_maobv
        
        if obv_above_maobv:
            obv_score = 15
        
        price_above_middle = price_data['close'] > price_data['BB_Middle']
        not_overbought = price_data['close'] < price_data['BB_Upper'] * 1.05
        
        bollinger_condition['price_above_middle_band'] = price_above_middle
        bollinger_condition['not_overbought'] = not_overbought
        
        if price_above_middle and not_overbought:
            bollinger_score = 15
        
        total_score = ma_score + volume_score + macd_score + obv_score + bollinger_score
        
        indicators = {
            'ma_condition': ma_condition,
            'volume_condition': volume_condition,
            'trend_condition': trend_condition,
            'fund_condition': fund_condition,
            'bollinger_condition': bollinger_condition
        }
        
        return total_score, indicators, price_data
    
    def get_fundamental_data(self, stock_code):
        """获取基本面数据 - 新5大类评分体系"""
        pure_code = stock_code.replace('sh', '').replace('sz', '').replace('bj', '')
        result = {
            'pe': 0, 'pb': 0, 'roe': 0,
            'net_profit_growth': 0, 'revenue_growth': 0, 'debt_ratio': 0,
            'gross_margin': 0, 'operating_margin': 0,
            'current_ratio': 0, 'asset_turnover': 0, 'cash_flow_ratio': 0
        }

        if not self.conn:
            self.connect()

        cursor = self.conn.cursor()

        cursor.execute('''
            SELECT pe, pb, roe, net_profit_growth, revenue_growth, debt_ratio,
                   gross_margin, operating_margin, current_ratio, asset_turnover, cash_flow_ratio, update_time
            FROM fundamental_data_cache
            WHERE stock_code = %s
        ''', (pure_code,))
        cache_data = cursor.fetchone()

        if cache_data:
            try:
                from datetime import datetime, timedelta
                cache_time = datetime.strptime(cache_data.get('update_time', ''), '%Y-%m-%d %H:%M:%S')
                now = datetime.now()
                days_diff = (now - cache_time).days

                if days_diff <= 7:
                    result = {
                        'pe': cache_data.get('pe') or 0, 'pb': cache_data.get('pb') or 0, 'roe': cache_data.get('roe') or 0,
                        'net_profit_growth': cache_data.get('net_profit_growth') or 0, 'revenue_growth': cache_data.get('revenue_growth') or 0,
                        'debt_ratio': cache_data.get('debt_ratio') or 0, 'gross_margin': cache_data.get('gross_margin') or 0,
                        'operating_margin': cache_data.get('operating_margin') or 0, 'current_ratio': cache_data.get('current_ratio') or 0,
                        'asset_turnover': cache_data.get('asset_turnover') or 0, 'cash_flow_ratio': cache_data.get('cash_flow_ratio') or 0
                    }
                    print(f"✅ 使用缓存的基本面数据: {pure_code}")
                    return result
            except Exception as e:
                print(f"缓存数据解析失败: {e}")

        try:
            import requests
            secid = f"1.{pure_code}" if pure_code.startswith('6') else f"0.{pure_code}"
            url = 'https://push2delay.eastmoney.com/api/qt/stock/get'
            params = {'secid': secid, 'fields': 'f9,f23,f162,f167,f173,f105'}
            r = requests.get(url, params=params, timeout=15)
            if r.status_code == 200:
                data = r.json()
                if data.get('data'):
                    d = data['data']
                    if d.get('f162'): result['pe'] = d['f162'] / 100
                    if d.get('f167'): result['pb'] = d['f167'] / 100
                    if d.get('f173'): result['roe'] = d['f173']
        except Exception as e:
            print(f"获取个股信息失败: {e}")

        if result['pe'] == 0 or result['pb'] == 0 or result['gross_margin'] == 0 or result['operating_margin'] == 0:
            try:
                # 尝试从财务分析指标获取
                df = ak.stock_financial_analysis_indicator(symbol=pure_code)
                if df is not None and len(df) > 0:
                    latest = df.iloc[0]
                    if result['pe'] == 0 and latest.get('市盈率') and float(latest.get('市盈率', 0)) > 0:
                        result['pe'] = float(latest.get('市盈率', 0))
                    if result['pb'] == 0 and latest.get('市净率') and float(latest.get('市净率', 0)) > 0:
                        result['pb'] = float(latest.get('市净率', 0))
                    if result['roe'] == 0 and latest.get('净资产收益率') and float(latest.get('净资产收益率', 0)) != 0:
                        result['roe'] = float(latest.get('净资产收益率', 0))
                    if latest.get('销售毛利率') and float(latest.get('销售毛利率', 0)) != 0:
                        result['gross_margin'] = float(latest.get('销售毛利率', 0))
                    if latest.get('销售净利率') and float(latest.get('销售净利率', 0)) != 0:
                        result['operating_margin'] = float(latest.get('销售净利率', 0))
            except Exception as e:
                print(f"方法1获取财务指标失败: {e}")
        
        # 尝试从利润表计算毛利率和净利率
        if result['gross_margin'] == 0 or result['operating_margin'] == 0:
            try:
                income_df = ak.stock_financial_report_sina(stock=pure_code, symbol="利润表")
                if income_df is not None and len(income_df) > 0:
                    latest = income_df.iloc[0]
                    # 计算毛利率：(营业收入 - 营业成本) / 营业收入 * 100
                    operating_revenue = latest.get('营业收入', 0)
                    operating_cost = latest.get('营业成本', 0)
                    if operating_revenue and operating_cost and float(operating_revenue) > 0:
                        gross_profit = float(operating_revenue) - float(operating_cost)
                        result['gross_margin'] = (gross_profit / float(operating_revenue)) * 100
                    
                    # 计算净利率：净利润 / 营业收入 * 100
                    net_profit = latest.get('净利润', 0)
                    if operating_revenue and net_profit and float(operating_revenue) > 0:
                        result['operating_margin'] = (float(net_profit) / float(operating_revenue)) * 100
            except Exception as e:
                pass

        if result['debt_ratio'] == 0 or result['current_ratio'] == 0:
            try:
                balance_df = ak.stock_financial_report_sina(stock=pure_code, symbol="资产负债表")
                if balance_df is not None and len(balance_df) > 0:
                    latest = balance_df.iloc[0]
                    total_assets = latest.get('资产总计', 0)
                    total_liab = latest.get('负债合计', 0)
                    current_assets = latest.get('流动资产合计', 0)
                    current_liab = latest.get('流动负债合计', 0)
                    if total_assets and total_liab and float(total_assets) > 0:
                        result['debt_ratio'] = float(total_liab) / float(total_assets) * 100
                    if current_assets and current_liab and float(current_liab) > 0:
                        result['current_ratio'] = float(current_assets) / float(current_liab)
            except Exception as e:
                pass

        if result['net_profit_growth'] == 0 or result['revenue_growth'] == 0:
            try:
                income_df = ak.stock_financial_report_sina(stock=pure_code, symbol="利润表")
                if income_df is not None and len(income_df) >= 4:
                    # 寻找年度数据（报告日为12月31日）
                    annual_data = income_df[income_df['报告日'].astype(str).str.endswith('1231')]
                    if len(annual_data) >= 2:
                        # 最新年度和去年年度数据（年度同比）
                        current = annual_data.iloc[0]
                        prev = annual_data.iloc[1]
                        if result['net_profit_growth'] == 0:
                            current_np = current.get('净利润', 0)
                            prev_np = prev.get('净利润', 0)
                            if current_np and prev_np and float(prev_np) != 0:
                                result['net_profit_growth'] = (float(current_np) - float(prev_np)) / float(prev_np) * 100
                        if result['revenue_growth'] == 0:
                            current_rev = current.get('营业收入', 0)
                            prev_rev = prev.get('营业收入', 0)
                            if current_rev and prev_rev and float(prev_rev) != 0:
                                result['revenue_growth'] = (float(current_rev) - float(prev_rev)) / float(prev_rev) * 100
                    else:
                        # 如果没有足够的年度数据，使用最新的季度数据（季度同比）
                        current = income_df.iloc[0]
                        # 寻找去年同期数据（大约4个季度前）
                        if len(income_df) >= 4:
                            prev = income_df.iloc[3]
                            if result['net_profit_growth'] == 0:
                                current_np = current.get('净利润', 0)
                                prev_np = prev.get('净利润', 0)
                                if current_np and prev_np and float(prev_np) != 0:
                                    result['net_profit_growth'] = (float(current_np) - float(prev_np)) / float(prev_np) * 100
                            if result['revenue_growth'] == 0:
                                current_rev = current.get('营业收入', 0)
                                prev_rev = prev.get('营业收入', 0)
                                if current_rev and prev_rev and float(prev_rev) != 0:
                                    result['revenue_growth'] = (float(current_rev) - float(prev_rev)) / float(prev_rev) * 100
            except Exception as e:
                pass

        if result['asset_turnover'] == 0 or result['cash_flow_ratio'] == 0:
            try:
                # 资产周转率：营业收入 / 平均资产总额
                income_df = ak.stock_financial_report_sina(stock=pure_code, symbol="利润表")
                balance_df = ak.stock_financial_report_sina(stock=pure_code, symbol="资产负债表")
                cash_df = ak.stock_financial_report_sina(stock=pure_code, symbol="现金流量表")
                
                if income_df is not None and balance_df is not None and len(income_df) > 0 and len(balance_df) > 0:
                    latest_income = income_df.iloc[0]
                    latest_balance = balance_df.iloc[0]
                    
                    # 计算资产周转率
                    operating_revenue = latest_income.get('营业收入', 0)
                    total_assets = latest_balance.get('资产总计', 0)
                    if operating_revenue and total_assets and float(total_assets) > 0:
                        result['asset_turnover'] = float(operating_revenue) / float(total_assets) * 100
                
                # 现金流动比率：经营活动现金流量净额 / 净利润
                if cash_df is not None and income_df is not None and len(cash_df) > 0 and len(income_df) > 0:
                    latest_cash = cash_df.iloc[0]
                    latest_income = income_df.iloc[0]
                    operating_cf = latest_cash.get('经营活动产生的现金流量净额', 0)
                    net_profit = latest_income.get('净利润', 0)
                    if operating_cf and net_profit and float(net_profit) != 0:
                        result['cash_flow_ratio'] = float(operating_cf) / abs(float(net_profit))
            except Exception as e:
                pass

        is_valid = result['pe'] > 0 or result['pb'] > 0 or result['roe'] != 0

        if is_valid:
            try:
                cursor.execute('''
                    INSERT INTO fundamental_data_cache
                    (stock_code, pe, pb, roe, net_profit_growth, revenue_growth, debt_ratio,
                     gross_margin, operating_margin, current_ratio, asset_turnover, cash_flow_ratio, update_time)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
                    ON DUPLICATE KEY UPDATE
                    pe=VALUES(pe), pb=VALUES(pb), roe=VALUES(roe),
                    net_profit_growth=VALUES(net_profit_growth), revenue_growth=VALUES(revenue_growth),
                    debt_ratio=VALUES(debt_ratio), gross_margin=VALUES(gross_margin),
                    operating_margin=VALUES(operating_margin), current_ratio=VALUES(current_ratio),
                    asset_turnover=VALUES(asset_turnover), cash_flow_ratio=VALUES(cash_flow_ratio),
                    update_time=NOW()
                ''', (pure_code, result['pe'], result['pb'], result['roe'],
                      result['net_profit_growth'], result['revenue_growth'], result['debt_ratio'],
                      result['gross_margin'], result['operating_margin'], result['current_ratio'],
                      result['asset_turnover'], result['cash_flow_ratio']))
                self.conn.commit()
                print(f"✅ 已缓存基本面数据: {pure_code}")
            except Exception as e:
                print(f"保存缓存失败: {e}")
        elif cache_data:
            print(f"⚠️ API数据无效，使用缓存数据: {pure_code}")
            result = {
                'pe': cache_data.get('pe') or 0, 'pb': cache_data.get('pb') or 0, 'roe': cache_data.get('roe') or 0,
                'net_profit_growth': cache_data.get('net_profit_growth') or 0, 'revenue_growth': cache_data.get('revenue_growth') or 0,
                'debt_ratio': cache_data.get('debt_ratio') or 0, 'gross_margin': cache_data.get('gross_margin') or 0,
                'operating_margin': cache_data.get('operating_margin') or 0, 'current_ratio': cache_data.get('current_ratio') or 0,
                'asset_turnover': cache_data.get('asset_turnover') or 0, 'cash_flow_ratio': cache_data.get('cash_flow_ratio') or 0
            }

        return result
    
    def calculate_fundamental_score(self, stock_code):
        """计算基本面得分 - 新5大类评分体系
        盈利能力（30%）+ 成长能力（25%）+ 估值（20%）+ 财务健康（15%）+ 现金流&运营（10%）
        """
        data = self.get_fundamental_data(stock_code)

        score = 0
        details = {}

        # ========== 1. 盈利能力（30分）==========
        # ROE（净资产收益率）- 20分
        roe_score = 0
        roe_detail = ""
        if data['roe'] >= 20:
            roe_score = 20
            roe_detail = f"ROE={data['roe']:.2f}%,优秀"
        elif data['roe'] >= 15:
            roe_score = 16
            roe_detail = f"ROE={data['roe']:.2f}%,良好"
        elif data['roe'] >= 10:
            roe_score = 12
            roe_detail = f"ROE={data['roe']:.2f}%,一般"
        elif data['roe'] >= 5:
            roe_score = 6
            roe_detail = f"ROE={data['roe']:.2f}%,偏低"
        else:
            roe_detail = f"ROE={data['roe']:.2f}%,较差"
        score += roe_score
        details['roe'] = {'score': roe_score, 'value': data['roe'], 'detail': roe_detail}

        # 净利率 - 10分
        nm_score = 0
        nm_detail = ""
        if data['operating_margin'] >= 20:
            nm_score = 10
            nm_detail = f"净利率={data['operating_margin']:.2f}%,优秀"
        elif data['operating_margin'] >= 10:
            nm_score = 8
            nm_detail = f"净利率={data['operating_margin']:.2f}%,良好"
        elif data['operating_margin'] >= 5:
            nm_score = 5
            nm_detail = f"净利率={data['operating_margin']:.2f}%,一般"
        elif data['operating_margin'] > 0:
            nm_score = 2
            nm_detail = f"净利率={data['operating_margin']:.2f}%,偏低"
        else:
            nm_score = 0
            nm_detail = f"净利率={data['operating_margin']:.2f}%,亏损"
        score += nm_score
        details['net_margin'] = {'score': nm_score, 'value': data['operating_margin'], 'detail': nm_detail}

        # ========== 2. 成长能力（25分）==========
        # 净利润增长率 - 15分
        npg_score = 0
        npg_detail = ""
        if data['net_profit_growth'] >= 50:
            npg_score = 15
            npg_detail = f"净利润增长{data['net_profit_growth']:.1f}%,强劲"
        elif data['net_profit_growth'] >= 20:
            npg_score = 12
            npg_detail = f"净利润增长{data['net_profit_growth']:.1f}%,良好"
        elif data['net_profit_growth'] >= 10:
            npg_score = 8
            npg_detail = f"净利润增长{data['net_profit_growth']:.1f}%,平稳"
        elif data['net_profit_growth'] >= 0:
            npg_score = 4
            npg_detail = f"净利润增长{data['net_profit_growth']:.1f}%,放缓"
        else:
            npg_score = 0
            npg_detail = f"净利润增长{data['net_profit_growth']:.1f}%,下滑"
        score += npg_score
        details['net_profit_growth'] = {'score': npg_score, 'value': data['net_profit_growth'], 'detail': npg_detail}

        # 营收增长率 - 10分
        rg_score = 0
        rg_detail = ""
        if data['revenue_growth'] >= 30:
            rg_score = 10
            rg_detail = f"营收增长{data['revenue_growth']:.1f}%,高速"
        elif data['revenue_growth'] >= 15:
            rg_score = 8
            rg_detail = f"营收增长{data['revenue_growth']:.1f}%,良好"
        elif data['revenue_growth'] >= 5:
            rg_score = 5
            rg_detail = f"营收增长{data['revenue_growth']:.1f}%,平稳"
        elif data['revenue_growth'] >= 0:
            rg_score = 2
            rg_detail = f"营收增长{data['revenue_growth']:.1f}%,放缓"
        else:
            rg_score = 0
            rg_detail = f"营收增长{data['revenue_growth']:.1f}%,下滑"
        score += rg_score
        details['revenue_growth'] = {'score': rg_score, 'value': data['revenue_growth'], 'detail': rg_detail}

        # ========== 3. 估值（20分）==========
        # PE（市盈率）- 12分
        pe_score = 0
        pe_detail = ""
        if 0 < data['pe'] <= 15:
            pe_score = 12
            pe_detail = f"PE={data['pe']:.2f},低估"
        elif 15 < data['pe'] <= 25:
            pe_score = 10
            pe_detail = f"PE={data['pe']:.2f},合理"
        elif 25 < data['pe'] <= 40:
            pe_score = 6
            pe_detail = f"PE={data['pe']:.2f},偏高"
        elif data['pe'] > 40:
            pe_score = 2
            pe_detail = f"PE={data['pe']:.2f},高估"
        else:
            pe_detail = f"PE={data['pe']:.2f},无效"
        score += pe_score
        details['pe'] = {'score': pe_score, 'value': data['pe'], 'detail': pe_detail}

        # PB（市净率）- 8分
        pb_score = 0
        pb_detail = ""
        if 0 < data['pb'] <= 2:
            pb_score = 8
            pb_detail = f"PB={data['pb']:.2f},低估"
        elif 2 < data['pb'] <= 4:
            pb_score = 6
            pb_detail = f"PB={data['pb']:.2f},合理"
        elif 4 < data['pb'] <= 6:
            pb_score = 3
            pb_detail = f"PB={data['pb']:.2f},偏高"
        elif data['pb'] > 6:
            pb_score = 1
            pb_detail = f"PB={data['pb']:.2f},高估"
        else:
            pb_detail = f"PB={data['pb']:.2f},无效"
        score += pb_score
        details['pb'] = {'score': pb_score, 'value': data['pb'], 'detail': pb_detail}

        # ========== 4. 财务健康（15分）==========
        # 负债率 - 10分
        dr_score = 0
        dr_detail = ""
        if data['debt_ratio'] <= 30:
            dr_score = 10
            dr_detail = f"负债率{data['debt_ratio']:.1f}%,优秀"
        elif data['debt_ratio'] <= 50:
            dr_score = 8
            dr_detail = f"负债率{data['debt_ratio']:.1f}%,良好"
        elif data['debt_ratio'] <= 70:
            dr_score = 5
            dr_detail = f"负债率{data['debt_ratio']:.1f}%,适中"
        else:
            dr_score = 0
            dr_detail = f"负债率{data['debt_ratio']:.1f}%,过高"
        score += dr_score
        details['debt_ratio'] = {'score': dr_score, 'value': data['debt_ratio'], 'detail': dr_detail}

        # 流动比率 - 5分
        cr_score = 0
        cr_detail = ""
        if data['current_ratio'] >= 2:
            cr_score = 5
            cr_detail = f"流动比率={data['current_ratio']:.2f},优秀"
        elif data['current_ratio'] >= 1.5:
            cr_score = 4
            cr_detail = f"流动比率={data['current_ratio']:.2f},良好"
        elif data['current_ratio'] >= 1:
            cr_score = 3
            cr_detail = f"流动比率={data['current_ratio']:.2f},合格"
        elif data['current_ratio'] > 0:
            cr_score = 1
            cr_detail = f"流动比率={data['current_ratio']:.2f},不足"
        else:
            cr_detail = f"流动比率={data['current_ratio']:.2f},无效"
        score += cr_score
        details['current_ratio'] = {'score': cr_score, 'value': data['current_ratio'], 'detail': cr_detail}

        # ========== 5. 现金流&运营（10分）==========
        # 资产周转率 - 5分
        at_score = 0
        at_detail = ""
        if data['asset_turnover'] >= 30:
            at_score = 5
            at_detail = f"资产周转={data['asset_turnover']:.1f}%,优秀"
        elif data['asset_turnover'] >= 20:
            at_score = 4
            at_detail = f"资产周转={data['asset_turnover']:.1f}%,良好"
        elif data['asset_turnover'] >= 10:
            at_score = 3
            at_detail = f"资产周转={data['asset_turnover']:.1f}%,一般"
        elif data['asset_turnover'] > 0:
            at_score = 1
            at_detail = f"资产周转={data['asset_turnover']:.1f}%,偏低"
        else:
            at_detail = f"资产周转={data['asset_turnover']:.1f}%,无效"
        score += at_score
        details['asset_turnover'] = {'score': at_score, 'value': data['asset_turnover'], 'detail': at_detail}

        # 现金流动比率 - 5分
        cf_score = 0
        cf_detail = ""
        if data['cash_flow_ratio'] >= 1.5:
            cf_score = 5
            cf_detail = f"现金流比率={data['cash_flow_ratio']:.2f},优秀"
        elif data['cash_flow_ratio'] >= 1:
            cf_score = 4
            cf_detail = f"现金流比率={data['cash_flow_ratio']:.2f},良好"
        elif data['cash_flow_ratio'] >= 0.5:
            cf_score = 3
            cf_detail = f"现金流比率={data['cash_flow_ratio']:.2f},一般"
        elif data['cash_flow_ratio'] > 0:
            cf_score = 1
            cf_detail = f"现金流比率={data['cash_flow_ratio']:.2f},不足"
        else:
            cf_score = 0
            cf_detail = f"现金流比率={data['cash_flow_ratio']:.2f},异常"
        score += cf_score
        details['cash_flow_ratio'] = {'score': cf_score, 'value': data['cash_flow_ratio'], 'detail': cf_detail}

        return score, details
    
    def calculate_news_score(self, stock_code):
        """计算消息面得分（只对最近三天新闻加减分）"""
        pure_code = stock_code.replace('sh', '').replace('sz', '').replace('bj', '')
        score = 0
        events = []
        
        three_days_ago = (datetime.now() - timedelta(days=3)).strftime('%Y-%m-%d')
        today = datetime.now().strftime('%Y-%m-%d')
        
        try:
            df = ak.stock_news_em(symbol=pure_code)
            if df is not None and len(df) > 0:
                positive_keywords = ['利好', '增长', '盈利', '中标', '合作', '突破', '创新']
                negative_keywords = ['利空', '亏损', '下滑', '风险', '诉讼', '处罚', '减持']
                
                for _, row in df.head(5).iterrows():
                    title = str(row.get('新闻标题', ''))
                    news_time = str(row.get('发布时间', ''))[:10] if row.get('发布时间') else today
                    news_url = str(row.get('新闻链接', ''))
                    news_source = str(row.get('文章来源', ''))
                    news_content = str(row.get('新闻内容', ''))[:100] if row.get('新闻内容') else ''
                    
                    is_recent = (news_time >= three_days_ago and news_time <= today)
                    
                    event_type = '中性'
                    score_impact = 0
                    
                    for kw in positive_keywords:
                        if kw in title:
                            event_type = '利好'
                            if is_recent:
                                score_impact = 5
                                score += 5
                            break
                    
                    for kw in negative_keywords:
                        if kw in title:
                            event_type = '利空'
                            if is_recent:
                                score_impact = -5
                                score -= 5
                            break
                    
                    events.append({
                        'date': news_time, 
                        'type': event_type,
                        'title': title[:50], 
                        'score_impact': score_impact, 
                        'is_recent': is_recent,
                        'url': news_url,
                        'source': news_source,
                        'summary': news_content
                    })
                    
        except Exception as e:
            print(f"获取{stock_code}新闻数据失败: {e}")
        
        return score, events
    
    def calculate_policy_score(self, stock_code, industry):
        """计算政策面得分"""
        score = 3
        policies = []
        
        if industry in POLICY_ORIENTED_INDUSTRIES:
            industry_info = POLICY_ORIENTED_INDUSTRIES[industry]
            industry_type = industry_info.get('industry_type', '')
            policy_support = industry_info.get('policy_support', '')
            
            if industry_type == '未来产业':
                score = 10
            elif industry_type == '战略性新兴产业':
                score = 8
            elif industry_type == '民生消费':
                score = 5
            
            policies.append({
                'date': datetime.now().strftime('%Y-%m-%d'),
                'level': '国家政策',
                'title': f'{industry}产业政策支持',
                'content': policy_support,
                'score_impact': score,
                'url': '',
                'source': '十五五规划'
            })
        
        return score, policies
    
    def calculate_deduction_score(self, stock_code):
        """计算减项扣分"""
        return 0, []
    
    def calculate_composite_score(self, technical_score, fundamental_score, news_score, policy_score, deduction_score):
        """计算综合评分
        技术面60% + 基本面40% + 消息面加减分 + 政策面加减分 - 减项扣分
        """
        return technical_score * 0.6 + fundamental_score * 0.4 + news_score + policy_score - deduction_score
    
    def get_rating(self, total_score):
        """根据得分获取评级"""
        if total_score >= 90: return "强烈推荐"
        elif total_score >= 70: return "推荐"
        elif total_score >= 50: return "中性"
        elif total_score >= 30: return "观望"
        else: return "不推荐"
    
    def save_score_record(self, stock_code, stock_name, industry, scores, price_data, indicators):
        """保存评分记录到score_record表"""
        if not self.conn:
            self.connect()
        
        cursor = self.conn.cursor()
        score_date = date.today().strftime('%Y-%m-%d')
        
        try:
            cursor.execute('''
                INSERT INTO score_record 
                (stock_code, stock_name, score_date, 
                fundamental_score, fundamental_reason,
                technical_score, technical_reason,
                ma_score, macd_score, rsi_score, bollinger_score, volume_score, obv_score,
                total_score, composite_score, rating,
                news_score, policy_score, deduction_score,
                close_price, volume, turnover_rate,
                create_time, update_time,
                technical_detail, fundamental_detail, news_detail, policy_detail, deduction_detail,
                summary, is_leader)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ''', (
                stock_code, stock_name, score_date,
                scores['fundamental_score'], f"基本面得分{scores['fundamental_score']}分",
                scores['technical_score'], f"技术面得分{scores['technical_score']}分",
                scores.get('ma_score', 0), scores.get('macd_score', 0), 0,
                scores.get('bollinger_score', 0), scores.get('volume_score', 0), scores.get('obv_score', 0),
                scores['composite_score'], scores['composite_score'], scores['rating'],
                scores['news_score'], scores['policy_score'], scores['deduction_score'],
                price_data.get('close', 0) if price_data else 0,
                price_data.get('volume', 0) if price_data else 0,
                price_data.get('Turnover_Rate', 0) if price_data else 0,
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                json.dumps({
                    'ma': {'score': scores.get('ma_score', 0), 'detail': f"股价站稳20日均线: {'是' if indicators.get('ma_condition', {}).get('price_above_ma20') else '否'}\n20日均线向上: {'是' if indicators.get('ma_condition', {}).get('ma20_up') else '否'}\n20日均线在60日均线上: {'是' if indicators.get('ma_condition', {}).get('ma20_above_ma60') else '否'}"},
                    'volume': {'score': scores.get('volume_score', 0), 'detail': f"成交量放大: {'是' if scores.get('volume_score', 0) > 0 else '否'}"},
                    'trend': {'score': scores.get('macd_score', 0), 'detail': f"MACD金叉: {'是' if scores.get('macd_score', 0) > 0 else '否'}"},
                    'fund': {'score': scores.get('obv_score', 0), 'detail': f"OBV>MAOBV: {'是' if scores.get('obv_score', 0) > 0 else '否'}"},
                    'bollinger': {'score': scores.get('bollinger_score', 0), 'detail': f"布林带中轨上方: {'是' if scores.get('bollinger_score', 0) > 0 else '否'}"}
                }, ensure_ascii=False),
                json.dumps(scores.get('fundamental_detail', {}), ensure_ascii=False),
                json.dumps({'events': scores.get('news_events', [])}, ensure_ascii=False),
                json.dumps({'policies': scores.get('policy_policies', [])}, ensure_ascii=False),
                json.dumps({}, ensure_ascii=False),
                scores.get('summary', ''), 0
            ))
            
            self.conn.commit()

            last_id = cursor.lastrowid
            print(f"✅ 已保存评分记录 ID={last_id}: {stock_name}({stock_code}) - {scores['composite_score']:.0f}分 - {scores['rating']}")
            return True

        except Exception as e:
            self.conn.rollback()
            print(f"❌ 保存评分记录失败 {stock_code}: {e}")
            import traceback
            traceback.print_exc()
            raise Exception(f"保存评分记录到数据库失败: {stock_name}({stock_code}) - {str(e)}")
    
    def evaluate_stock(self, stock_code, stock_name=None, industry=None):
        """评价单只股票"""
        if not self.conn:
            self.connect()
        
        cursor = self.conn.cursor()
        
        # 去除股票代码前缀，统一格式（stock_basic_info 表中存储的是不带前缀的代码）
        pure_code = stock_code.lower().replace('sh', '').replace('sz', '').replace('bj', '')
        
        # 使用多种格式查询 stock_basic_info 表，确保能匹配到
        # 支持：纯代码(601816)、带前缀(sh601816)、大写(SH601816)
        # 同时匹配数据库中可能存在的各种格式
        cursor.execute('''
            SELECT stock_name, industry FROM stock_basic_info 
            WHERE LOWER(stock_code) IN (%s, %s, %s, %s, %s)
        ''', (pure_code, stock_code.lower(), f'sh{pure_code}', f'sz{pure_code}', pure_code.upper()))
        result = cursor.fetchone()
        
        if result:
            db_stock_name = result.get('stock_name')
            db_industry = result.get('industry')
            # 优先使用数据库中的中文名称
            stock_name = db_stock_name if db_stock_name else (stock_name or stock_code)
            industry = db_industry if db_industry else (industry or '未知')
        else:
            # 股票不在 stock_basic_info 表中
            # 尝试从 API 获取股票名称
            if not stock_name:
                stock_name = self._get_stock_name_from_api(pure_code)
            
            if stock_name:
                # 添加到 stock_basic_info 表（使用纯代码，不带前缀）
                exchange = 'SH' if pure_code.startswith('6') else 'SZ'
                if pure_code.startswith('68'):
                    exchange = 'SH'  # 科创板
                elif pure_code.startswith('30'):
                    exchange = 'SZ'  # 创业板
                cursor.execute('''
                    INSERT INTO stock_basic_info (stock_code, stock_name, exchange, status, create_time, update_time)
                    VALUES (%s, %s, %s, 'normal', NOW(), NOW())
                    ON DUPLICATE KEY UPDATE stock_name=VALUES(stock_name), exchange=VALUES(exchange)
                ''', (pure_code, stock_name, exchange))
                self.conn.commit()
            else:
                stock_name = stock_code
            
            industry = industry or '未知'
        
        print(f"\n正在评价：{stock_name}({pure_code})")
        
        technical_score, indicators, price_data = self.calculate_technical_score(stock_code)
        fundamental_score, fundamental_detail = self.calculate_fundamental_score(stock_code)
        news_score, news_events = self.calculate_news_score(stock_code)
        policy_score, policy_policies = self.calculate_policy_score(stock_code, industry)
        deduction_score, deduction_items = self.calculate_deduction_score(stock_code)
        
        composite_score = self.calculate_composite_score(
            technical_score, fundamental_score, news_score, policy_score, deduction_score
        )
        
        rating = self.get_rating(composite_score)
        
        scores = {
            'technical_score': technical_score,
            'fundamental_score': fundamental_score,
            'news_score': news_score,
            'policy_score': policy_score,
            'deduction_score': deduction_score,
            'composite_score': composite_score,
            'rating': rating,
            'ma_score': 25 if indicators.get('ma_condition', {}).get('price_above_ma20') and indicators.get('ma_condition', {}).get('ma20_up') and indicators.get('ma_condition', {}).get('ma20_above_ma60') else 0,
            'macd_score': 20 if indicators.get('trend_condition', {}).get('diff_gt_dea_and_zero') else 0,
            'bollinger_score': 15 if indicators.get('bollinger_condition', {}).get('price_above_middle_band') and indicators.get('bollinger_condition', {}).get('not_overbought') else 0,
            'volume_score': 25 if indicators.get('volume_condition', {}).get('volume_above_ma5') and indicators.get('volume_condition', {}).get('volume_above_ma60') else 0,
            'obv_score': 15 if indicators.get('fund_condition', {}).get('obv_above_maobv') else 0,
            'fundamental_detail': fundamental_detail,
            'news_events': news_events,
            'news_detail': {'events': news_events},
            'policy_policies': policy_policies,
            'policy_detail': {'policies': policy_policies},
            'summary': f"技术面{technical_score}分,基本面{fundamental_score}分,政策面{policy_score}分"
        }
        
        # 保存评分记录时使用不带前缀的股票代码，确保格式统一
        self.save_score_record(pure_code, stock_name, industry, scores, price_data, indicators)
        
        return scores
    
    def evaluate_all(self):
        """评价stock_basic_info中所有股票"""
        if not self.conn:
            self.connect()
        
        cursor = self.conn.cursor()
        cursor.execute('SELECT stock_code, stock_name, industry FROM stock_basic_info WHERE status = "normal"')
        stocks = cursor.fetchall()
        
        print("=" * 60)
        print(f"开始评价股票池，股票数量: {len(stocks)}")
        print("=" * 60)
        
        results = []
        for stock_code, stock_name, industry in stocks:
            result = self.evaluate_stock(stock_code, stock_name, industry)
            results.append(result)
        
        print("\n" + "=" * 60)
        print(f"评价完成，共评价 {len(results)} 只股票")
        print("=" * 60)
        
        return results


def run_stock_evaluation(stock_code=None, stock_name=None, industry=None):
    """运行股票评价（供外部调用）"""
    evaluator = StockEvaluatorSkills()
    evaluator.connect()
    
    if stock_code:
        result = evaluator.evaluate_stock(stock_code, stock_name, industry)
    else:
        result = evaluator.evaluate_all()
    
    evaluator.disconnect()
    return result


if __name__ == '__main__':
    run_stock_evaluation()
