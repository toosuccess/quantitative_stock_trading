"""
股票复审技能
职责：对评价得分为强烈推荐、推荐、中性的股票进行深度技术面复审
核心指标：MACD + 20日均线 + 布林线 + DMI + K线风控
评分规则：大项中任一小项不达标，整个大项0分（一票否决制）
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


class StockReviewSkills:
    """复审技能类 - 供Trae AI调用"""
    
    def __init__(self):
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
    
    def get_review_candidates(self):
        """获取待复审股票列表（评分≥30分的股票，包含强烈推荐、推荐、中性、观望）"""
        if not self.conn:
            self.connect()
        
        cursor = self.conn.cursor(pymysql.cursors.DictCursor)
        
        cursor.execute('''
            SELECT sr.stock_code, sr.stock_name, sr.rating, sr.composite_score
            FROM score_record sr
            INNER JOIN (
                SELECT stock_code, MAX(id) as max_id
                FROM score_record
                GROUP BY stock_code
            ) latest ON sr.id = latest.max_id
            WHERE sr.composite_score >= 30
            ORDER BY sr.composite_score DESC
        ''')
        score_stocks = cursor.fetchall()
        
        candidates = []
        for stock in score_stocks:
            sr_code = stock['stock_code']
            sr_name = stock['stock_name']
            
            pure_code = sr_code.replace('sh', '').replace('sz', '').replace('bj', '')
            sh_code = f'sh{pure_code}'
            sz_code = f'sz{pure_code}'
            bj_code = f'bj{pure_code}'
            
            cursor.execute('''
                SELECT stock_code, stock_name, industry 
                FROM stock_basic_info 
                WHERE stock_code IN (%s, %s, %s, %s, %s)
                LIMIT 1
            ''', (sr_code, pure_code, sh_code, sz_code, bj_code))
            sbi_info = cursor.fetchone()
            
            if sbi_info:
                candidates.append({
                    'stock_code': sbi_info['stock_code'],
                    'stock_name': sbi_info['stock_name'],
                    'industry': sbi_info['industry'] or '',
                    'rating': stock['rating'],
                    'composite_score': stock['composite_score']
                })
            else:
                print(f"⚠️ 奇怪！{sr_code}({sr_name}) 在score_record表有，但stock_basic_info没找到！")
        
        return candidates
    
    def get_stock_price_data(self, stock_code):
        """获取股票K线数据"""
        pure_code = stock_code.replace('sh', '').replace('sz', '').replace('bj', '')
        
        is_bj_stock = pure_code.startswith('83') or pure_code.startswith('87') or pure_code.startswith('92')
        
        if is_bj_stock:
            return self._get_bj_stock_price(pure_code)
        
        try:
            prefix = 'sh' if pure_code.startswith('6') else 'sz'
            symbol = f"{prefix}{pure_code}"
            df = ak.stock_zh_a_daily(symbol=symbol, adjust="qfq")
            
            if df is not None and len(df) >= 60:
                return self._process_kline_data(df)
        except Exception as e:
            print(f"akshare获取{stock_code}失败，尝试东方财富接口: {e}")
        
        return self._get_em_stock_kline(pure_code)
    
    def _get_bj_stock_price(self, pure_code):
        """获取北交所股票价格"""
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
            'open': current_close,
            'high': d.get('f44', 0) / 100 if d.get('f44') else current_close,
            'low': d.get('f45', 0) / 100 if d.get('f45') else current_close,
            'volume': d.get('f47', 0) if d.get('f47') else 0,
            'prev_close': current_close,
            'MA5': current_close, 'MA10': current_close, 'MA20': current_close,
            'MA60': current_close, 'MA180': current_close, 'MA250': current_close,
            'DIFF': 0, 'DEA': 0, 'MACD': 0,
            'BB_Upper': current_close * 1.02, 'BB_Middle': current_close, 'BB_Lower': current_close * 0.98,
            'DI_PLUS': 50, 'DI_MINUS': 50, 'ADX': 20
        }
    
    def _get_em_stock_kline(self, pure_code):
        """使用东方财富K线接口获取数据"""
        import requests
        
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
        
        opens = []
        closes = []
        highs = []
        lows = []
        volumes = []
        
        for kline in klines:
            parts = kline.split(',')
            opens.append(float(parts[1]))
            closes.append(float(parts[2]))
            highs.append(float(parts[3]))
            lows.append(float(parts[4]))
            volumes.append(float(parts[5]))
        
        close = np.array(closes)
        high = np.array(highs)
        low = np.array(lows)
        volume = np.array(volumes)
        open_arr = np.array(opens)
        
        current_close = float(close[-1])
        current_open = float(open_arr[-1])
        current_high = float(high[-1])
        current_low = float(low[-1])
        current_volume = float(volume[-1])
        prev_close = float(close[-2]) if len(close) >= 2 else current_close
        
        ma5 = np.mean(close[-5:]) if len(close) >= 5 else current_close
        ma10 = np.mean(close[-10:]) if len(close) >= 10 else current_close
        ma20 = np.mean(close[-20:]) if len(close) >= 20 else current_close
        ma60 = np.mean(close[-60:]) if len(close) >= 60 else ma20
        ma180 = np.mean(close[-180:]) if len(close) >= 180 else ma60
        ma250 = np.mean(close[-250:]) if len(close) >= 250 else ma180
        
        ema12 = pd.Series(close).ewm(span=12).mean().values
        ema26 = pd.Series(close).ewm(span=26).mean().values
        diff = ema12 - ema26
        dea = pd.Series(diff).ewm(span=9).mean().values
        macd_hist = 2 * (diff - dea)
        
        bb_middle = np.mean(close[-20:]) if len(close) >= 20 else current_close
        bb_std = np.std(close[-20:]) if len(close) >= 20 else 0
        bb_upper = bb_middle + 2 * bb_std
        bb_lower = bb_middle - 2 * bb_std
        
        dmi_result = self._calculate_dmi(high, low, close)
        
        avg_volume_5 = np.mean(volume[-5:]) if len(volume) >= 5 else current_volume
        avg_volume_20 = np.mean(volume[-20:]) if len(volume) >= 20 else current_volume
        
        deviation = (current_close - ma20) / ma20 * 100 if ma20 > 0 else 0
        
        return {
            'close': current_close,
            'open': current_open,
            'high': current_high,
            'low': current_low,
            'volume': current_volume,
            'prev_close': prev_close,
            'MA5': ma5, 'MA10': ma10, 'MA20': ma20,
            'MA60': ma60, 'MA180': ma180, 'MA250': ma250,
            'DIFF': diff[-1], 'DEA': dea[-1], 'MACD': macd_hist[-1],
            'DIFF_series': diff[-20:] if len(diff) >= 20 else diff,
            'DEA_series': dea[-20:] if len(dea) >= 20 else dea,
            'MACD_series': macd_hist[-20:] if len(macd_hist) >= 20 else macd_hist,
            'close_series': close[-20:] if len(close) >= 20 else close,
            'BB_Upper': bb_upper, 'BB_Middle': bb_middle, 'BB_Lower': bb_lower,
            'DI_PLUS': dmi_result['di_plus'], 'DI_MINUS': dmi_result['di_minus'],
            'ADX': dmi_result['adx'],
            'avg_volume_5': avg_volume_5, 'avg_volume_20': avg_volume_20,
            'deviation': deviation
        }
    
    def _process_kline_data(self, df):
        """处理akshare K线数据"""
        df = df.tail(250)
        
        close = df['close'].values
        high = df['high'].values
        low = df['low'].values
        open_arr = df['open'].values
        volume = df['volume'].values
        
        current_close = float(close[-1])
        current_open = float(open_arr[-1])
        current_high = float(high[-1])
        current_low = float(low[-1])
        current_volume = float(volume[-1])
        prev_close = float(close[-2]) if len(close) >= 2 else current_close
        
        ma5 = np.mean(close[-5:]) if len(close) >= 5 else current_close
        ma10 = np.mean(close[-10:]) if len(close) >= 10 else current_close
        ma20 = np.mean(close[-20:]) if len(close) >= 20 else current_close
        ma60 = np.mean(close[-60:]) if len(close) >= 60 else ma20
        ma180 = np.mean(close[-180:]) if len(close) >= 180 else ma60
        ma250 = np.mean(close[-250:]) if len(close) >= 250 else ma180
        
        ema12 = pd.Series(close).ewm(span=12).mean().values
        ema26 = pd.Series(close).ewm(span=26).mean().values
        diff = ema12 - ema26
        dea = pd.Series(diff).ewm(span=9).mean().values
        macd_hist = 2 * (diff - dea)
        
        bb_middle = np.mean(close[-20:]) if len(close) >= 20 else current_close
        bb_std = np.std(close[-20:]) if len(close) >= 20 else 0
        bb_upper = bb_middle + 2 * bb_std
        bb_lower = bb_middle - 2 * bb_std
        
        dmi_result = self._calculate_dmi(high, low, close)
        
        avg_volume_5 = np.mean(volume[-5:]) if len(volume) >= 5 else current_volume
        avg_volume_20 = np.mean(volume[-20:]) if len(volume) >= 20 else current_volume
        
        deviation = (current_close - ma20) / ma20 * 100 if ma20 > 0 else 0
        
        return {
            'close': current_close,
            'open': current_open,
            'high': current_high,
            'low': current_low,
            'volume': current_volume,
            'prev_close': prev_close,
            'MA5': ma5, 'MA10': ma10, 'MA20': ma20,
            'MA60': ma60, 'MA180': ma180, 'MA250': ma250,
            'DIFF': diff[-1], 'DEA': dea[-1], 'MACD': macd_hist[-1],
            'DIFF_series': diff[-20:] if len(diff) >= 20 else diff,
            'DEA_series': dea[-20:] if len(dea) >= 20 else dea,
            'MACD_series': macd_hist[-20:] if len(macd_hist) >= 20 else macd_hist,
            'close_series': close[-20:] if len(close) >= 20 else close,
            'BB_Upper': bb_upper, 'BB_Middle': bb_middle, 'BB_Lower': bb_lower,
            'DI_PLUS': dmi_result['di_plus'], 'DI_MINUS': dmi_result['di_minus'],
            'ADX': dmi_result['adx'],
            'avg_volume_5': avg_volume_5, 'avg_volume_20': avg_volume_20,
            'deviation': deviation
        }
    
    def _calculate_dmi(self, high_prices, low_prices, close_prices, period=14):
        """计算DMI指标（DI+, DI-, ADX）- 使用标准Wilder平滑法"""
        high = np.array(high_prices)
        low = np.array(low_prices)
        close = np.array(close_prices)
        
        tr_list = []
        plus_dm = []
        minus_dm = []
        
        for i in range(1, len(close)):
            tr = max(high[i] - low[i], abs(high[i] - close[i-1]), abs(low[i] - close[i-1]))
            tr_list.append(tr)
            
            up_move = high[i] - high[i-1]
            down_move = low[i-1] - low[i]
            
            if up_move > down_move and up_move > 0:
                plus_dm.append(up_move)
            else:
                plus_dm.append(0)
            
            if down_move > up_move and down_move > 0:
                minus_dm.append(down_move)
            else:
                minus_dm.append(0)
        
        if len(tr_list) < period:
            return {'di_plus': 50, 'di_minus': 50, 'adx': 20}
        
        tr_arr = np.array(tr_list)
        plus_dm_arr = np.array(plus_dm)
        minus_dm_arr = np.array(minus_dm)
        
        wilder_alpha = 1.0 / period
        
        atr_series = pd.Series(tr_arr).ewm(alpha=wilder_alpha, adjust=False).mean()
        smoothed_plus_dm = pd.Series(plus_dm_arr).ewm(alpha=wilder_alpha, adjust=False).mean()
        smoothed_minus_dm = pd.Series(minus_dm_arr).ewm(alpha=wilder_alpha, adjust=False).mean()
        
        di_plus_series = 100 * smoothed_plus_dm / atr_series
        di_minus_series = 100 * smoothed_minus_dm / atr_series
        
        di_plus_series = di_plus_series.replace([np.inf, -np.inf], 50).fillna(50)
        di_minus_series = di_minus_series.replace([np.inf, -np.inf], 50).fillna(50)
        
        dx_series = 100 * (di_plus_series - di_minus_series).abs() / (di_plus_series + di_minus_series)
        dx_series = dx_series.replace([np.inf, -np.inf], 0).fillna(0)
        
        adx_series = dx_series.ewm(alpha=wilder_alpha, adjust=False).mean()
        
        plus_di = di_plus_series.iloc[-1]
        minus_di = di_minus_series.iloc[-1]
        adx = adx_series.iloc[-1]
        
        return {
            'di_plus': round(plus_di, 2),
            'di_minus': round(minus_di, 2),
            'adx': round(adx, 2)
        }
    
    def calculate_macd_review_score(self, price_data):
        """
        MACD核心评分（35分）
        一票否决制：任一小项不达标，整个大项0分
        达标条件：零轴上方 + 多头排列/金叉 + 红柱动能 + 无顶背离
        """
        details = {}
        
        diff = price_data.get('DIFF', 0)
        dea = price_data.get('DEA', 0)
        macd_hist = price_data.get('MACD', 0)
        diff_series = price_data.get('DIFF_series', [diff])
        dea_series = price_data.get('DEA_series', [dea])
        macd_series = price_data.get('MACD_series', [macd_hist])
        close_series = price_data.get('close_series', [price_data.get('close', 0)])
        
        # 1. 零轴判定（8分）
        zero_axis_passed = False
        if diff > 0 and dea > 0:
            zero_axis_passed = True
            zero_axis_status = "零轴上方"
            zero_axis_detail = "快慢线均在零轴上方，多头牛市格局"
        elif diff < 0 and dea < 0:
            zero_axis_status = "零轴下方"
            zero_axis_detail = "快慢线在零轴下方，空头熊市格局"
        elif (diff > 0 and dea < 0) or (diff < 0 and dea > 0):
            zero_axis_status = "零轴临界"
            zero_axis_detail = "首次突破零轴，需观察确认"
        else:
            zero_axis_status = "零轴附近"
            zero_axis_detail = "指标在零轴附近震荡"
        
        details['zero_axis'] = {
            'status': zero_axis_status,
            'detail': zero_axis_detail,
            'passed': zero_axis_passed
        }
        
        # 2. 金叉死叉判断（9分）
        cross_passed = False
        if len(diff_series) >= 2 and len(dea_series) >= 2:
            prev_diff = diff_series[-2]
            curr_diff = diff_series[-1]
            prev_dea = dea_series[-2]
            curr_dea = dea_series[-1]
            
            if curr_diff > curr_dea and prev_diff <= prev_dea:
                cross_passed = True
                cross_status = "金叉形成"
                cross_detail = "零轴上方金叉" if diff > 0 else "零轴下方金叉"
            elif curr_diff < curr_dea and prev_diff >= prev_dea:
                cross_status = "死叉形成"
                cross_detail = "出现死叉信号，注意风险"
            elif curr_diff > curr_dea:
                cross_passed = True
                cross_status = "多头排列"
                cross_detail = "DIFF在DEA上方运行"
            else:
                cross_status = "空头排列"
                cross_detail = "DIFF在DEA下方运行"
        else:
            if diff > dea:
                cross_passed = True
                cross_status = "多头排列"
                cross_detail = "DIFF在DEA上方"
            else:
                cross_status = "空头排列"
                cross_detail = "DIFF在DEA下方"
        
        details['cross'] = {
            'status': cross_status,
            'detail': cross_detail,
            'passed': cross_passed
        }
        
        # 3. 红绿柱动能（9分）
        momentum_passed = False
        if len(macd_series) >= 3:
            curr_macd = macd_series[-1]
            prev_macd = macd_series[-2]
            
            if curr_macd > 0:
                momentum_passed = True
                if curr_macd > prev_macd > macd_series[-3]:
                    momentum_status = "红柱持续放大"
                    momentum_detail = "上涨动能充足，可坚定持有或加仓"
                elif curr_macd < prev_macd:
                    momentum_passed = True
                    momentum_status = "⚠️红柱缩脚⚠️"
                    momentum_detail = "【注意】动能开始衰竭，红柱在缩小，关注减仓机会！"
                else:
                    momentum_status = "红柱持平"
                    momentum_detail = "动能维持，观望为主"
            else:
                if prev_macd <= 0 and curr_macd > 0:
                    momentum_passed = True
                    momentum_status = "绿柱转红柱"
                    momentum_detail = "空头结束，可择机低吸"
                elif curr_macd < prev_macd < macd_series[-3]:
                    momentum_status = "绿柱持续放大"
                    momentum_detail = "下跌动能强劲，坚决回避"
                elif curr_macd > prev_macd:
                    momentum_status = "绿柱缩脚"
                    momentum_detail = "下跌动能衰减，观察企稳信号"
                else:
                    momentum_status = "绿柱持平"
                    momentum_detail = "空头动能维持"
        else:
            if macd_hist > 0:
                momentum_passed = True
                momentum_status = "红柱状态"
                momentum_detail = "当前为多头动能"
            else:
                momentum_status = "绿柱状态"
                momentum_detail = "当前为空头动能"
        
        details['momentum'] = {
            'status': momentum_status,
            'detail': momentum_detail,
            'passed': momentum_passed
        }
        
        # 4. 背离判断（9分）
        divergence_passed = True
        divergence_type = "无背离"
        divergence_detail = "暂无明显背离信号"
        
        if len(close_series) >= 10 and len(macd_series) >= 10:
            recent_closes = close_series[-10:]
            recent_macs = macd_series[-10:]
            
            price_high_idx = np.argmax(recent_closes)
            macd_high_idx = np.argmax(recent_macs)
            
            if price_high_idx == len(recent_closes) - 1 and macd_high_idx < len(recent_macs) - 2:
                divergence_passed = False
                divergence_type = "顶背离"
                divergence_detail = "价格创新高但MACD未创新高，上涨动能枯竭，逢高卖出"
            
            price_low_idx = np.argmin(recent_closes)
            macd_low_idx = np.argmin(recent_macs)
            
            if price_low_idx == len(recent_closes) - 1 and macd_low_idx < len(recent_macs) - 2:
                divergence_type = "底背离"
                divergence_detail = "价格创新低但MACD未创新低，下跌动能枯竭，可择机低吸"
        
        details['divergence'] = {
            'type': divergence_type,
            'detail': divergence_detail,
            'passed': divergence_passed
        }
        
        # 一票否决制：任一小项不达标，整个大项0分
        all_passed = zero_axis_passed and cross_passed and momentum_passed and divergence_passed
        total_score = 35 if all_passed else 0
        
        return {
            'total_score': total_score,
            'max_score': 35,
            'details': details,
            'all_passed': all_passed
        }
    
    def calculate_ma20_review_score(self, price_data):
        """
        20日均线辅助评分（20分）
        一票否决制：任一小项不达标，整个大项0分
        达标条件：多头排列 + MA20在MA60上方 + 乖离率正常
        """
        details = {}
        
        close = price_data.get('close', 0)
        ma20 = price_data.get('MA20', 0)
        ma60 = price_data.get('MA60', 0)
        ma180 = price_data.get('MA180', 0)
        deviation = price_data.get('deviation', 0)
        
        # 1. 多头排列检查（12分）
        alignment_passed = False
        if close > ma20 > ma60 > ma180:
            alignment_passed = True
            trend_status = "强势多头"
            alignment = "完美多头排列（股价>MA20>MA60>MA180）"
        elif close > ma20 and ma20 > ma60 and ma20 > ma180:
            alignment_passed = True
            trend_status = "偏多"
            alignment = "短期多头排列（股价>MA20>MA60>MA180）"
        elif close > ma20 and ma20 > ma60:
            trend_status = "站上MA20但受压制"
            alignment = f"股价>MA20>MA60，但MA180({ma180:.2f})在MA20({ma20:.2f})上方压制"
        elif close > ma20:
            trend_status = "站上MA20"
            alignment = "股价在MA20上方，但均线未完全多头排列"
        elif ma20 > ma60:
            trend_status = "弱势整理"
            alignment = "股价在MA20下方，但MA20仍在MA60上方"
        else:
            trend_status = "空头趋势"
            alignment = "均线空头排列，趋势较弱"
        
        details['alignment'] = {
            'trend': trend_status,
            'detail': alignment,
            'passed': alignment_passed
        }
        
        # 2. 趋势压制检测（4分）
        suppression_passed = True
        suppression_lines = []
        if ma20 < ma180:
            suppression_passed = False
            suppression_lines.append(f"MA180({ma180:.2f})>MA20({ma20:.2f})")
        if ma20 < ma60:
            suppression_passed = False
            suppression_lines.append(f"MA60({ma60:.2f})>MA20({ma20:.2f})")
        
        if suppression_passed:
            suppression_detail = "MA20在所有长期均线上方，无趋势压制"
        else:
            suppression_detail = f"⚠️ MA20被{'、'.join(suppression_lines)}压制，趋势受限"
        
        details['suppression'] = {
            'detail': suppression_detail,
            'suppressed_by': suppression_lines,
            'passed': suppression_passed
        }
        
        # 3. 乖离率风控（4分）
        deviation_passed = False
        if deviation > 8:
            deviation_warning = f"⚠️ 乖离率{deviation:.1f}%过高，禁止追高！"
        elif deviation > 5:
            deviation_warning = f"⚠️ 乖离率{deviation:.1f}%偏高，注意回调风险"
        elif deviation < -5:
            deviation_passed = True
            deviation_warning = f"✅ 负乖离率{deviation:.1f}%，可能存在超跌反弹机会"
        else:
            deviation_passed = True
            deviation_warning = f"乖离率{deviation:.1f}%正常"
        
        details['deviation'] = {
            'value': round(deviation, 2),
            'warning': deviation_warning,
            'passed': deviation_passed
        }
        
        # 一票否决制
        all_passed = alignment_passed and suppression_passed and deviation_passed
        total_score = 20 if all_passed else 0
        
        return {
            'total_score': total_score,
            'max_score': 20,
            'details': details,
            'all_passed': all_passed
        }
    
    def calculate_kline_risk_check(self, price_data):
        """
        K线风控硬性规则（15分）
        一票否决制：任一小项不达标，整个大项0分
        达标条件：无长上影线 + 无巨阴线
        """
        details = {}
        
        open_price = price_data.get('open', 0)
        close_price = price_data.get('close', 0)
        high_price = price_data.get('high', 0)
        low_price = price_data.get('low', 0)
        prev_close = price_data.get('prev_close', 0)
        volume = price_data.get('volume', 0)
        avg_volume_5 = price_data.get('avg_volume_5', volume)
        avg_volume_20 = price_data.get('avg_volume_20', volume)
        
        # 1. 长上影线检测
        body = abs(close_price - open_price)
        upper_shadow = high_price - max(open_price, close_price)
        
        shadow_passed = True
        has_long_upper_shadow = False
        
        if body > 0 and upper_shadow > body * 2:
            has_long_upper_shadow = True
            shadow_passed = False
            shadow_risk = "⚠️ 高风险"
            shadow_detail = f"出现长上影线（上影{upper_shadow:.2f}>实体{body:.2f}的2倍），上方抛压过重，短期回调概率大"
        elif body > 0 and upper_shadow > body * 1.5:
            shadow_risk = "⚠️ 中等风险"
            shadow_detail = f"上影线较长（上影/实体={upper_shadow/body:.1f}），存在一定抛压"
        else:
            shadow_risk = "安全"
            shadow_detail = "无长上影线风险"
        
        details['upper_shadow'] = {
            'risk': shadow_risk,
            'detail': shadow_detail,
            'has_risk': has_long_upper_shadow,
            'passed': shadow_passed
        }
        
        # 2. 巨量长阴线检测
        bearish_passed = True
        has_big_bearish = False
        
        if prev_close > 0:
            price_change = (close_price - prev_close) / prev_close * 100
            volume_ratio = volume / avg_volume_20 if avg_volume_20 > 0 else 1
            body_ratio = abs(close_price - open_price) / prev_close * 100
            is_bearish_candle = close_price < open_price
            
            if price_change < -7:
                has_big_bearish = True
                bearish_passed = False
                bearish_risk = "⛔ 极高风险"
                bearish_detail = f"⛔⛔⛔ 巨量长阴线（跌幅{price_change:.1f}%，量比{volume_ratio:.1f}），暴跌！坚决回避，不可抄底！"
            elif price_change < -5:
                has_big_bearish = True
                bearish_passed = False
                bearish_risk = "⚠️ 高风险"
                bearish_detail = f"⚠️⚠️ 大阴线（跌幅{price_change:.1f}%，量比{volume_ratio:.1f}），空头强力打压，注意风险"
            elif price_change < -3 and is_bearish_candle and body_ratio > 3:
                bearish_passed = False
                bearish_risk = "⚠️ 中等风险"
                bearish_detail = f"⚠️ 阴线下跌（跌幅{price_change:.1f}%，实体占比{body_ratio:.1f}%，量比{volume_ratio:.1f}），短期走弱"
            elif is_bearish_candle and body_ratio > 5 and volume_ratio > 1.5:
                bearish_passed = False
                bearish_risk = "⚠️ 中等风险"
                bearish_detail = f"⚠️ 放量长阴（实体占比{body_ratio:.1f}%，量比{volume_ratio:.1f}），抛压明显"
            else:
                bearish_risk = "安全"
                bearish_detail = "无巨阴线风险"
        else:
            bearish_risk = "安全"
            bearish_detail = "无巨阴线风险"
        
        details['bearish'] = {
            'risk': bearish_risk,
            'detail': bearish_detail,
            'has_risk': has_big_bearish,
            'passed': bearish_passed
        }
        
        # 一票否决制
        all_passed = shadow_passed and bearish_passed
        total_score = 15 if all_passed else 0
        
        return {
            'total_score': total_score,
            'max_score': 15,
            'details': details,
            'all_passed': all_passed,
            'veto_triggered': not all_passed
        }
    
    def calculate_bollinger_review_score(self, price_data):
        """
        布林线共振确认（10分）
        一票否决制：不达标则0分
        达标条件：股价在中轨上方
        """
        details = {}
        
        close = price_data.get('close', 0)
        bb_upper = price_data.get('BB_Upper', 0)
        bb_middle = price_data.get('BB_Middle', 0)
        bb_lower = price_data.get('BB_Lower', 0)
        diff = price_data.get('DIFF', 0)
        
        bollinger_passed = False
        channel_position = ""
        running_state = ""
        
        if bb_upper > 0 and bb_middle > 0:
            bb_width = (bb_upper - bb_lower) / bb_middle * 100
            
            if close > bb_upper:
                bollinger_passed = True
                channel_position = "突破上轨"
                running_state = "股价突破布林带上轨，短期可能回调"
            elif close > bb_middle:
                bollinger_passed = True
                if diff > 0:
                    channel_position = "中轨上方"
                    running_state = "布林通道在零轴上方且股价在中轨上方，强势主升，安心持股"
                else:
                    channel_position = "中轨上方"
                    running_state = "股价在布林带中轨上方运行，趋势向好"
            elif close > bb_lower:
                channel_position = "中轨与下轨之间"
                running_state = "股价接近布林带下轨，处于弱势区域"
            else:
                channel_position = "跌破下轨"
                running_state = "股价跌破布林带下轨，超跌状态"
            
            if bb_width < 5:
                running_state += "；布林通道收口，变盘在即"
        
        details['position'] = channel_position
        details['state'] = running_state
        details['passed'] = bollinger_passed
        
        total_score = 10 if bollinger_passed else 0
        
        return {
            'total_score': total_score,
            'max_score': 10,
            'details': details,
            'all_passed': bollinger_passed
        }
    
    def calculate_dmi_review_score(self, price_data):
        """
        DMI牛熊指标评分（10分）
        一票否决制：不达标则0分
        达标条件：DI+ > DI-（多头主导）
        """
        details = {}
        
        di_plus = price_data.get('DI_PLUS', 50)
        di_minus = price_data.get('DI_MINUS', 50)
        adx = price_data.get('ADX', 20)
        
        dmi_passed = False
        di_comparison = ""
        adx_status = ""
        
        if di_plus > di_minus:
            dmi_passed = True
            di_gap = di_plus - di_minus
            if di_gap > 10:
                di_comparison = "多头主导（DI+明显领先DI-）"
            elif di_gap > 5:
                di_comparison = "偏多（DI+在DI-上方）"
            else:
                di_comparison = "微幅偏多（DI+略高于DI-）"
        else:
            di_gap = di_minus - di_plus
            if di_gap > 10:
                di_comparison = "空头主导（DI-明显领先DI+）"
            elif di_gap > 5:
                di_comparison = "偏空（DI-在DI+上方）"
            else:
                di_comparison = "微幅偏空（DI-略高于DI+）"
        
        if adx > 30:
            adx_status = f"ADX={adx:.1f}>30，趋势明确"
        elif adx > 20:
            adx_status = f"ADX={adx:.1f}，趋势一般"
        else:
            adx_status = f"ADX={adx:.1f}<20，趋势不明"
        
        details['comparison'] = di_comparison
        details['adx'] = adx_status
        details['passed'] = dmi_passed
        
        total_score = 10 if dmi_passed else 0
        
        return {
            'total_score': total_score,
            'max_score': 10,
            'details': details,
            'all_passed': dmi_passed
        }
    
    def get_rating(self, total_score):
        """根据得分获取复审评级"""
        if total_score >= 85:
            return "强烈推荐"
        elif total_score >= 70:
            return "推荐"
        elif total_score >= 55:
            return "中性"
        elif total_score >= 40:
            return "谨慎"
        else:
            return "回避"
    
    def generate_review_opinion(self, stock_name, stock_code, scores, indicators, price_data):
        """
        生成完整的复审意见报告
        一票否决制 + 显目标注不符合项
        """
        macd = scores['macd']
        ma20 = scores['ma20']
        kline = scores['kline']
        bollinger = scores['bollinger']
        dmi = scores['dmi']
        
        total_score = scores['total_score']
        rating = scores['rating']
        review_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        macd_details = macd['details']
        ma20_details = ma20['details']
        kline_details = kline['details']
        bollinger_details = bollinger['details']
        dmi_details = dmi['details']
        
        def mark(passed, text):
            if passed:
                return f"✅ {text}"
            else:
                return f"❌【不达标】{text}"
        
        support_price = price_data.get('BB_Lower', price_data.get('MA20', 0))
        resistance_price = price_data.get('BB_Upper', price_data.get('MA20', 0) * 1.05)
        
        if rating in ['强烈推荐', '推荐']:
            suggestion = "多指标共振向好，建议适量参与或继续持有"
        elif rating == '中性':
            suggestion = "方向不明，观望为主，可轻仓试探"
        elif rating == '谨慎':
            suggestion = "风险较高，不建议操作，等待明确信号"
        else:
            suggestion = "多指标走弱，坚决回避"
        
        risk_warnings = []
        if kline.get('veto_triggered'):
            risk_warnings.append("⛔ K线形态触发一票否决规则")
        if kline_details.get('bearish', {}).get('has_risk', False):
            bearish_risk_level = kline_details.get('bearish', {}).get('risk', '')
            if '极高' in bearish_risk_level:
                risk_warnings.append("⛔⛔⛔ 出现巨量长阴线暴跌！坚决回避！")
            elif '高' in bearish_risk_level:
                risk_warnings.append("⛔ 出现大阴线，空头强力打压")
            elif '中等' in bearish_risk_level:
                risk_warnings.append("⚠️ 阴线下跌，短期走弱")
        if ma20_details.get('deviation', {}).get('value', 0) > 5:
            risk_warnings.append("⛔ 乖离率过高，追高风险大")
        if not ma20_details.get('suppression', {}).get('passed', True):
            suppressed_by = ma20_details.get('suppression', {}).get('suppressed_by', [])
            risk_warnings.append(f"⛔ MA20被长期均线压制({'、'.join(suppressed_by)})，趋势受限")
        if not macd_details.get('cross', {}).get('passed', True):
            risk_warnings.append("⛔ MACD空头排列/死叉，注意离场")
        if macd_details.get('momentum', {}).get('status', '') == '⚠️红柱缩脚⚠️':
            risk_warnings.append("⚠️ MACD红柱缩脚，上涨动能衰减，注意减仓")
        if not macd_details.get('zero_axis', {}).get('passed', True):
            risk_warnings.append("⛔ MACD零轴下方，空头格局")
        if not dmi_details.get('passed', True):
            risk_warnings.append("⛔ DMI空头主导")
        
        risk_warning = "；".join(risk_warnings) if risk_warnings else "当前无明显重大风险"
        
        if total_score >= 80:
            outlook = "技术面多重利好共振，后市看涨概率较大"
        elif total_score >= 60:
            outlook = "技术面偏向积极，但需警惕波动风险"
        elif total_score >= 40:
            outlook = "技术面多空交织，建议耐心等待方向明朗"
        else:
            outlook = "技术面整体偏空，建议保持谨慎或离场观望"
        
        macd_status = "全部达标✅" if macd['all_passed'] else "存在不达标项❌"
        ma20_status = "全部达标✅" if ma20['all_passed'] else "存在不达标项❌"
        kline_status = "全部达标✅" if kline['all_passed'] else "存在不达标项❌"
        bollinger_status = "达标✅" if bollinger['all_passed'] else "不达标❌"
        dmi_status = "达标✅" if dmi['all_passed'] else "不达标❌"
        
        opinion = f"""【{stock_name}({stock_code}) 技术面复审报告】

📊 复审评级：{rating}（{total_score:.1f}分）
📅 复审时间：{review_time}

═══ 一、MACD核心分析（{macd['total_score']:.0f}/35分）{macd_status} ═══
   {mark(macd_details['zero_axis']['passed'], f'零轴位置：{macd_details["zero_axis"]["status"]} - {macd_details["zero_axis"]["detail"]}')}
   {mark(macd_details['cross']['passed'], f'金叉/死叉：{macd_details["cross"]["status"]} - {macd_details["cross"]["detail"]}')}
   {'⚡⚡⚡ 【警告】动能状态：⚠️红柱缩脚⚠️ - 【注意】动能开始衰竭，红柱在缩小，关注减仓机会！ ⚡⚡⚡' if macd_details['momentum']['status'] == '⚠️红柱缩脚⚠️' else mark(macd_details['momentum']['passed'], f'动能状态：{macd_details["momentum"]["status"]} - {macd_details["momentum"]["detail"]}')}
   {mark(macd_details['divergence']['passed'], f'背离情况：{macd_details["divergence"]["type"]} - {macd_details["divergence"]["detail"]}')}

═══ 二、20日均线分析（{ma20['total_score']:.0f}/20分）{ma20_status} ═══
   {mark(ma20_details['alignment']['passed'], f'趋势状态：{ma20_details["alignment"]["trend"]}')}
   {mark(ma20_details['alignment']['passed'], f'排列情况：{ma20_details["alignment"]["detail"]}')}
   {'⛔⛔ 【趋势压制】' + ma20_details['suppression']['detail'] + ' ⛔⛔' if not ma20_details['suppression']['passed'] else mark(ma20_details['suppression']['passed'], f'趋势压制：{ma20_details["suppression"]["detail"]}')}
   {mark(ma20_details['deviation']['passed'], f'乖离率：{ma20_details["deviation"]["value"]:.2f}% {ma20_details["deviation"]["warning"]}')}

═══ 三、K线风控检查（{kline['total_score']:.0f}/15分）{kline_status} ═══
   {mark(kline_details['upper_shadow']['passed'], f'上影线风险：{kline_details["upper_shadow"]["risk"]} - {kline_details["upper_shadow"]["detail"]}')}
   {'⛔⛔⛔ 【严重警告】巨阴线风险：' + kline_details["bearish"]["detail"] + ' ⛔⛔⛔' if kline_details['bearish'].get('has_risk') else mark(kline_details['bearish']['passed'], f'巨阴线风险：{kline_details["bearish"]["risk"]} - {kline_details["bearish"]["detail"]}')}

═══ 四、布林线分析（{bollinger['total_score']:.0f}/10分）{bollinger_status} ═══
   {mark(bollinger_details['passed'], f'通道位置：{bollinger_details["position"]}')}
   {mark(bollinger_details['passed'], f'运行状态：{bollinger_details["state"]}')}

═══ 五、DMI指标分析（{dmi['total_score']:.0f}/10分）{dmi_status} ═══
   {mark(dmi_details['passed'], f'多空对比：{dmi_details["comparison"]}')}
   {mark(dmi_details['passed'], f'趋势强度：{dmi_details["adx"]}')}

═══ 六、综合交易建议 ═══
   🎯 操作建议：{suggestion}
   ⚠️ 风险提示：{risk_warning}
   💡 关键价位：支撑{support_price:.2f} / 压力{resistance_price:.2f}
   🔮 后市展望：{outlook}
"""
        
        return opinion
    
    def review_single_stock(self, stock_code):
        """
        复审单只股票（供Trae AI调用）
        返回完整的复审结果字典
        """
        if not self.conn:
            self.connect()
        
        cursor = self.conn.cursor(pymysql.cursors.DictCursor)
        
        pure_code = stock_code.replace('sh', '').replace('sz', '').replace('bj', '')
        sh_code = f'sh{pure_code}'
        sz_code = f'sz{pure_code}'
        bj_code = f'bj{pure_code}'
        
        cursor.execute('''
            SELECT stock_code, stock_name, industry 
            FROM stock_basic_info 
            WHERE stock_code IN (%s, %s, %s, %s, %s)
            LIMIT 1
        ''', (stock_code, pure_code, sh_code, sz_code, bj_code))
        stock_info = cursor.fetchone()
        
        if not stock_info:
            print(f"❌ 股票 {stock_code} 不在数据库中")
            return None
        
        target_stock_code = stock_info['stock_code']
        stock_name = stock_info['stock_name']
        industry = stock_info.get('industry', '未知')
        
        print(f"\n{'='*60}")
        print(f"🔍 开始复审：{stock_name}({target_stock_code})")
        print(f"{'='*60}")
        
        print("📊 正在获取K线数据...")
        price_data = self.get_stock_price_data(target_stock_code)
        
        if not price_data:
            print(f"❌ 无法获取 {target_stock_code} 的价格数据")
            return None
        
        print(f"✅ 价格数据获取成功: 收盘价 {price_data['close']:.2f}")
        
        print("📐 正在计算MACD核心评分...")
        macd_score = self.calculate_macd_review_score(price_data)
        
        print("📐 正在计算20日均线评分...")
        ma20_score = self.calculate_ma20_review_score(price_data)
        
        print("📐 正在进行K线风控检查...")
        kline_score = self.calculate_kline_risk_check(price_data)
        
        print("📐 正在计算布林线评分...")
        bollinger_score = self.calculate_bollinger_review_score(price_data)
        
        print("📐 正在计算DMI指标评分...")
        dmi_score = self.calculate_dmi_review_score(price_data)
        
        # 汇总总分（去掉板块加分，总分90分）
        total_score = (
            macd_score['total_score'] +
            ma20_score['total_score'] +
            kline_score['total_score'] +
            bollinger_score['total_score'] +
            dmi_score['total_score']
        )
        
        total_score = max(0, min(90, total_score))
        
        rating = self.get_rating(total_score)
        
        scores = {
            'macd': macd_score,
            'ma20': ma20_score,
            'kline': kline_score,
            'bollinger': bollinger_score,
            'dmi': dmi_score,
            'total_score': total_score,
            'rating': rating
        }
        
        print("📝 正在生成复审意见...")
        opinion = self.generate_review_opinion(
            stock_name, target_stock_code, scores, {}, price_data
        )
        
        review_detail = {
            'scores_breakdown': {
                'macd': {'score': macd_score['total_score'], 'max': 35, 'details': macd_score['details'], 'all_passed': macd_score['all_passed']},
                'ma20': {'score': ma20_score['total_score'], 'max': 20, 'details': ma20_score['details'], 'all_passed': ma20_score['all_passed']},
                'kline': {'score': kline_score['total_score'], 'max': 15, 'details': kline_score['details'], 'all_passed': kline_score['all_passed']},
                'bollinger': {'score': bollinger_score['total_score'], 'max': 10, 'details': bollinger_score['details'], 'all_passed': bollinger_score['all_passed']},
                'dmi': {'score': dmi_score['total_score'], 'max': 10, 'details': dmi_score['details'], 'all_passed': dmi_score['all_passed']}
            },
            'indicators': {
                'close': price_data['close'],
                'DIFF': price_data.get('DIFF', 0),
                'DEA': price_data.get('DEA', 0),
                'MACD': price_data.get('MACD', 0),
                'MA20': price_data.get('MA20', 0),
                'MA60': price_data.get('MA60', 0),
                'DI_PLUS': price_data.get('DI_PLUS', 0),
                'DI_MINUS': price_data.get('DI_MINUS', 0),
                'ADX': price_data.get('ADX', 0),
                'deviation': price_data.get('deviation', 0)
            },
            'review_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'veto_triggered': kline_score.get('veto_triggered', False)
        }
        
        result = {
            'stock_code': target_stock_code,
            'stock_name': stock_name,
            'industry': industry,
            'review_score': round(total_score, 2),
            'conform_score': round(total_score, 2),
            'rating': rating,
            'review_opinion': opinion,
            'review_time': datetime.now(),
            'review_detail': review_detail
        }
        
        print("💾 正在保存复审结果...")
        self.save_review_result(target_stock_code, result)
        
        print(f"\n{'='*60}")
        print(f"✅ 复审完成：{stock_name}({target_stock_code})")
        print(f"   评级：{rating} | 得分：{total_score:.1f}分")
        print(f"{'='*60}\n")
        
        return result
    
    def batch_review_all(self):
        """
        批量复审所有符合条件的股票（供Trae AI调用）
        条件：最新评分记录中 composite_score >= 50 的股票
        """
        candidates = self.get_review_candidates()
        
        if not candidates:
            print("⚠️ 没有找到需要复审的股票（需要评分>=50的股票）")
            return []
        
        print(f"\n{'='*60}")
        print(f"🚀 开始批量复审，共 {len(candidates)} 只股票")
        print(f"{'='*60}\n")
        
        results = []
        for i, candidate in enumerate(candidates, 1):
            stock_code = candidate['stock_code']
            stock_name = candidate['stock_name']
            composite_score = candidate.get('composite_score', 0)
            old_rating = candidate.get('rating', '')
            
            print(f"[{i}/{len(candidates)}] 处理：{stock_name}({stock_code}) - 原评级:{old_rating} 原分数:{composite_score}")
            
            try:
                result = self.review_single_stock(stock_code)
                if result:
                    results.append(result)
            except Exception as e:
                print(f"❌ 复审 {stock_name}({stock_code}) 失败: {e}")
                import traceback
                traceback.print_exc()
        
        print(f"\n{'='*60}")
        print(f"✅ 批量复审完成，成功复审 {len(results)}/{len(candidates)} 只股票")
        print(f"{'='*60}\n")
        
        if results:
            rating_counts = {}
            for r in results:
                rat = r['rating']
                rating_counts[rat] = rating_counts.get(rat, 0) + 1
            
            print("\n📊 复审结果汇总：")
            for rat, count in sorted(rating_counts.items()):
                print(f"   {rat}: {count} 只")
        
        return results
    
    def save_review_result(self, stock_code, result):
        """
        保存复审结果到stock_basic_info表
        支持多种股票代码格式匹配
        """
        if not self.conn:
            self.connect()
        
        cursor = self.conn.cursor()
        
        pure_code = stock_code.replace('sh', '').replace('sz', '').replace('bj', '')
        prefix_sh = f'sh{pure_code}'
        prefix_sz = f'sz{pure_code}'
        prefix_bj = f'bj{pure_code}'
        
        try:
            cursor.execute('''
                SELECT stock_code FROM stock_basic_info 
                WHERE stock_code = %s 
                   OR stock_code = %s
                   OR stock_code = %s
                   OR stock_code = %s
                   OR stock_code = %s
            ''', (pure_code, prefix_sh, prefix_sz, prefix_bj, stock_code))
            
            match = cursor.fetchone()
            
            if not match:
                print(f"⚠️ 未在stock_basic_info中找到股票 {stock_code}，尝试插入基础信息...")
                if pure_code.startswith('6'):
                    insert_code = f'sh{pure_code}'
                elif pure_code.startswith('3') or pure_code.startswith('0'):
                    insert_code = f'sz{pure_code}'
                elif pure_code.startswith('8') or pure_code.startswith('4'):
                    insert_code = f'bj{pure_code}'
                else:
                    insert_code = pure_code
                cursor.execute('''
                    INSERT IGNORE INTO stock_basic_info
                    (stock_code, stock_name, create_time, update_time)
                    VALUES (%s, %s, NOW(), NOW())
                ''', (insert_code, result['stock_name']))
                self.conn.commit()
                target_code = insert_code
            else:
                target_code = match['stock_code']
                print(f"📌 匹配到数据库中的代码: {target_code}")
            
            cursor.execute('''
                UPDATE stock_basic_info 
                SET review_score = %s,
                    review_opinion = %s,
                    review_time = %s,
                    review_detail = %s,
                    conform_score = %s,
                    update_time = NOW()
                WHERE stock_code = %s
            ''', (
                result['review_score'],
                result['review_opinion'],
                result['review_time'],
                json.dumps(result['review_detail'], ensure_ascii=False),
                result['conform_score'],
                target_code
            ))
            
            self.conn.commit()
            print(f"✅ 已保存复审结果: {result['stock_name']}({target_code}) - {result['rating']}({result['review_score']:.1f}分)")
            
        except Exception as e:
            self.conn.rollback()
            print(f"❌ 保存复审结果失败 {stock_code}: {e}")
            import traceback
            traceback.print_exc()
            raise Exception(f"保存复审结果失败: {stock_code}")


def run_stock_review(stock_code=None):
    """
    运行股票复审（供外部调用入口）
    
    使用示例：
    # 复审单只股票
    run_stock_review("600519")  # 复审茅台
    
    # 批量复审所有合格股票
    run_stock_review()  # 不传参数则批量复审
    """
    reviewer = StockReviewSkills()
    reviewer.connect()
    
    try:
        if stock_code:
            result = reviewer.review_single_stock(stock_code)
        else:
            result = reviewer.batch_review_all()
        
        return result
    finally:
        reviewer.disconnect()


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1:
        stock_code = sys.argv[1]
        print(f"🎯 复审目标股票：{stock_code}")
        run_stock_review(stock_code)
    else:
        print("🎯 批量复审所有合格股票（评分>=50）")
        run_stock_review()
