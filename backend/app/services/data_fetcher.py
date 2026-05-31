"""
数据获取模块
封装AkShare数据接口，支持股票基本信息、技术指标、实时股价获取
"""
import akshare as ak
import pandas as pd
import numpy as np
from datetime import datetime, date
from typing import Dict, List, Optional, Tuple
import pymysql
from pymysql.cursors import DictCursor
import os
import urllib3
import warnings
import requests
from app.database_config import MYSQL_CONFIG

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
warnings.filterwarnings('ignore')

PROXY_HOST = os.environ.get('PROXY_HOST', '127.0.0.1')
PROXY_PORT = os.environ.get('PROXY_PORT', '7897')
PROXY_ENABLED = os.environ.get('PROXY_ENABLED', 'true').lower() == 'true'

def get_proxies():
    if PROXY_ENABLED:
        return {'http': f'http://{PROXY_HOST}:{PROXY_PORT}', 'https': f'http://{PROXY_HOST}:{PROXY_PORT}'}
    return None

def setup_proxy():
    if PROXY_ENABLED:
        os.environ['HTTP_PROXY'] = f'http://{PROXY_HOST}:{PROXY_PORT}'
        os.environ['HTTPS_PROXY'] = f'http://{PROXY_HOST}:{PROXY_PORT}'
        os.environ['NO_PROXY'] = 'localhost,127.0.0.1'
    else:
        os.environ['HTTP_PROXY'] = ''
        os.environ['HTTPS_PROXY'] = ''
        os.environ['http_proxy'] = ''
        os.environ['https_proxy'] = ''

setup_proxy()

class DataFetcher:
    """数据获取类"""
    
    def __init__(self, db_path: str = None):
        """
        初始化数据获取器
        
        Args:
            db_path: 数据库文件路径（已废弃，保留兼容性）
        """
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
    
    def get_stock_realtime(self, stock_code: str) -> Optional[Dict]:
        """
        获取股票实时行情数据（使用东方财富push2delay API）
        
        Args:
            stock_code: 股票代码
        
        Returns:
            实时数据字典
        """
        try:
            import requests
            
            # 去掉股票代码前缀 (sz/sh)
            pure_code = stock_code[2:] if stock_code.startswith(('sz', 'sh')) else stock_code
            secid = f"1.{pure_code}" if pure_code.startswith('6') else f"0.{pure_code}"
            url = 'https://push2delay.eastmoney.com/api/qt/stock/get'
            params = {
                'secid': secid,
                'fields': 'f43,f44,f45,f46,f47,f48,f50,f51,f52,f55,f56,f57,f58,f60,f116,f117,f162,f167,f92,f173,f105,f84,f85,f109,f152'
            }
            
            r = requests.get(url, params=params, timeout=15, proxies={'http': None, 'https': None})
            if r.status_code != 200:
                return None
            
            data = r.json()
            if not data.get('data'):
                return None
            
            d = data['data']
            
            last_price = d.get('f43', 0) / 100 if d.get('f43') else 0
            pre_close = d.get('f60', 0) / 100 if d.get('f60') else 0
            high = d.get('f44', 0) / 100 if d.get('f44') else 0
            low = d.get('f45', 0) / 100 if d.get('f45') else 0
            open_price = d.get('f46', 0) / 100 if d.get('f46') else 0
            volume = d.get('f47', 0)
            amount = d.get('f48', 0)
            change_percent = d.get('f50', 0) / 100 if d.get('f50') else 0
            turnover_rate = d.get('f168', 0) / 100 if d.get('f168') else 0
            pe_ratio = d.get('f162', 0) / 100 if d.get('f162') else 0
            pb_ratio = d.get('f167', 0) / 100 if d.get('f167') else 0
            total_mv = d.get('f116', 0)
            circ_mv = d.get('f117', 0)
            
            change = last_price - pre_close if last_price and pre_close else 0
            
            return {
                'stock_code': stock_code,
                'stock_name': d.get('f58', ''),
                'price': last_price,
                'close': last_price,
                'last_price': last_price,
                'open': open_price,
                'high': high,
                'low': low,
                'pre_close': pre_close,
                'volume': volume,
                'amount': amount,
                'change': round(change, 2),
                'change_percent': round(change_percent, 2),
                'turnover_rate': round(turnover_rate, 2),
                'pe_ratio': round(pe_ratio, 2),
                'pb_ratio': round(pb_ratio, 2),
                'total_market_value': total_mv,
                'circulation_market_value': circ_mv,
            }
        except Exception as e:
            print(f"获取实时行情失败: {e}")
            return None
    
    def get_stock_basic_info(self, stock_code: str) -> Optional[Dict]:
        """
        获取股票基本信息（使用东方财富push2delay API）
        
        Args:
            stock_code: 股票代码
        
        Returns:
            股票基本信息字典
        """
        try:
            import requests
            
            secid = f"1.{stock_code}" if stock_code.startswith('6') else f"0.{stock_code}"
            url = 'https://push2delay.eastmoney.com/api/qt/stock/get'
            params = {
                'secid': secid,
                'fields': 'f57,f58,f162,f167,f116,f117,f173,f105'
            }
            
            r = requests.get(url, params=params, timeout=15, proxies={'http': None, 'https': None})
            if r.status_code != 200:
                return None
            
            data = r.json()
            if not data.get('data'):
                return None
            
            d = data['data']
            
            return {
                'stock_code': stock_code,
                'stock_name': d.get('f58', ''),
                'stock_abbr': d.get('f58', ''),
                'exchange': 'SH' if stock_code.startswith('6') else 'SZ',
                'industry': '',
                'sector': '',
                'list_date': '',
                'total_shares': 0,
                'float_shares': 0,
                'market_cap': d.get('f116', 0),
                'float_market_cap': d.get('f117', 0),
                'pe_ratio': d.get('f162', 0) / 100 if d.get('f162') else 0,
                'pb_ratio': d.get('f167', 0) / 100 if d.get('f167') else 0,
                'ps_ratio': 0,
                'dividend_yield': 0,
            }
        except Exception as e:
            print(f"获取股票基本信息失败: {e}")
            return None
    
    def get_kline_data(self, stock_code: str, days: int = 250) -> Optional[pd.DataFrame]:
        """
        获取K线数据
        
        Args:
            stock_code: 股票代码
            days: 获取天数
        
        Returns:
            K线数据DataFrame
        """
        try:
            if stock_code.startswith('6'):
                symbol = f"sh{stock_code}"
            else:
                symbol = f"sz{stock_code}"
            
            kline_data = ak.stock_zh_a_daily(symbol=symbol, adjust="qfq")
            
            if kline_data is not None and not kline_data.empty:
                return kline_data.tail(days)
            return None
        except Exception as e:
            print(f"获取K线数据失败: {e}")
            return None
    
    def calculate_technical_indicators(self, kline_data: pd.DataFrame) -> Optional[Dict]:
        """
        计算技术指标
        
        Args:
            kline_data: K线数据DataFrame
        
        Returns:
            技术指标字典
        """
        if kline_data is None or len(kline_data) < 20:
            return None
        
        try:
            close = kline_data['close'].values
            high = kline_data['high'].values
            low = kline_data['low'].values
            volume = kline_data['volume'].values
            
            indicators = {}
            
            ma5 = np.mean(close[-5:])
            ma10 = np.mean(close[-10:])
            ma20 = np.mean(close[-20:])
            ma60 = np.mean(close[-60:]) if len(close) >= 60 else ma20
            
            indicators['ma5'] = round(ma5, 4)
            indicators['ma10'] = round(ma10, 4)
            indicators['ma20'] = round(ma20, 4)
            indicators['ma60'] = round(ma60, 4)
            
            ema12 = pd.Series(close).ewm(span=12, adjust=False).mean().values
            ema26 = pd.Series(close).ewm(span=26, adjust=False).mean().values
            diff = ema12 - ema26
            dea = pd.Series(diff).ewm(span=9, adjust=False).mean().values
            macd = (diff - dea) * 2
            
            indicators['diff'] = round(diff[-1], 4)
            indicators['dea'] = round(dea[-1], 4)
            indicators['macd'] = round(macd[-1], 4)
            indicators['diff_gt_dea_and_zero'] = bool(diff[-1] > dea[-1] and diff[-1] > 0)
            
            delta = np.diff(close[-14:])
            gain = delta[delta > 0]
            loss = -delta[delta < 0]
            avg_gain = np.mean(gain) if len(gain) > 0 else 0
            avg_loss = np.mean(loss) if len(loss) > 0 else 0
            
            if avg_loss == 0:
                rsi = 100
            else:
                rs = avg_gain / avg_loss
                rsi = 100 - (100 / (1 + rs))
            
            indicators['rsi'] = round(rsi, 4)
            
            ma20_val = np.mean(close[-20:])
            std_dev = np.std(close[-20:])
            upper_band = ma20_val + 2 * std_dev
            lower_band = ma20_val - 2 * std_dev
            
            indicators['bb_upper'] = round(upper_band, 4)
            indicators['bb_middle'] = round(ma20_val, 4)
            indicators['bb_lower'] = round(lower_band, 4)
            
            indicators['volume'] = int(volume[-1])
            indicators['ma5_volume'] = int(np.mean(volume[-5:]))
            indicators['ma60_volume'] = int(np.mean(volume[-60:])) if len(volume) >= 60 else int(np.mean(volume))
            
            obv = [volume[0]]
            for i in range(1, len(volume)):
                if close[i] > close[i-1]:
                    obv.append(obv[-1] + volume[i])
                elif close[i] < close[i-1]:
                    obv.append(obv[-1] - volume[i])
                else:
                    obv.append(obv[-1])
            
            maobv = np.mean(obv[-20:]) if len(obv) >= 20 else np.mean(obv)
            
            indicators['obv'] = int(obv[-1])
            indicators['maobv'] = int(maobv)
            indicators['obv_gt_maobv'] = bool(obv[-1] > maobv)
            
            indicators['close_price'] = round(close[-1], 4)
            
            return indicators
            
        except Exception as e:
            print(f"计算技术指标失败: {e}")
            return None
    
    def save_stock_basic_info(self, stock_info: Dict) -> bool:
        """
        保存股票基本信息到数据库
        
        Args:
            stock_info: 股票基本信息字典
        
        Returns:
            是否成功
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
            INSERT INTO stock_basic_info 
            (stock_code, stock_name, stock_abbr, exchange, industry, sector,
            list_date, total_shares, float_shares, market_cap, float_market_cap,
            pe_ratio, pb_ratio, ps_ratio, dividend_yield, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
            stock_name=VALUES(stock_name), stock_abbr=VALUES(stock_abbr), exchange=VALUES(exchange),
            industry=VALUES(industry), sector=VALUES(sector), list_date=VALUES(list_date),
            total_shares=VALUES(total_shares), float_shares=VALUES(float_shares),
            market_cap=VALUES(market_cap), float_market_cap=VALUES(float_market_cap),
            pe_ratio=VALUES(pe_ratio), pb_ratio=VALUES(pb_ratio), ps_ratio=VALUES(ps_ratio),
            dividend_yield=VALUES(dividend_yield), status=VALUES(status)
            ''', (
                stock_info.get('stock_code'),
                stock_info.get('stock_name'),
                stock_info.get('stock_abbr'),
                stock_info.get('exchange'),
                stock_info.get('industry'),
                stock_info.get('sector'),
                stock_info.get('list_date'),
                stock_info.get('total_shares'),
                stock_info.get('float_shares'),
                stock_info.get('market_cap'),
                stock_info.get('float_market_cap'),
                stock_info.get('pe_ratio'),
                stock_info.get('pb_ratio'),
                stock_info.get('ps_ratio'),
                stock_info.get('dividend_yield'),
                'normal'
            ))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"保存股票基本信息失败: {e}")
            return False
    
    def save_score_record(self, score_record: Dict) -> bool:
        """
        保存评分记录到数据库
        
        Args:
            score_record: 评分记录字典
        
        Returns:
            是否成功
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
            INSERT INTO score_record 
            (stock_code, stock_name, score_date, 
            fundamental_score, fundamental_reason,
            technical_score, technical_reason,
            ma_score, macd_score, rsi_score, bollinger_score, volume_score, obv_score,
            total_score, rating,
            ma5, ma10, ma20, ma60,
            diff, dea, macd, rsi,
            bb_upper, bb_middle, bb_lower,
            close_price, volume, turnover_rate)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ''', (
                score_record.get('stock_code'),
                score_record.get('stock_name'),
                score_record.get('score_date'),
                score_record.get('fundamental_score', 0),
                score_record.get('fundamental_reason'),
                score_record.get('technical_score', 0),
                score_record.get('technical_reason'),
                score_record.get('ma_score', 0),
                score_record.get('macd_score', 0),
                score_record.get('rsi_score', 0),
                score_record.get('bollinger_score', 0),
                score_record.get('volume_score', 0),
                score_record.get('obv_score', 0),
                score_record.get('total_score', 0),
                score_record.get('rating'),
                score_record.get('ma5'),
                score_record.get('ma10'),
                score_record.get('ma20'),
                score_record.get('ma60'),
                score_record.get('diff'),
                score_record.get('dea'),
                score_record.get('macd'),
                score_record.get('rsi'),
                score_record.get('bb_upper'),
                score_record.get('bb_middle'),
                score_record.get('bb_lower'),
                score_record.get('close_price'),
                score_record.get('volume'),
                score_record.get('turnover_rate')
            ))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"保存评分记录失败: {e}")
            return False
    
    def get_all_stocks(self) -> Optional[List[Dict]]:
        """
        获取所有A股股票列表（使用东方财富push2delay API）
        
        Returns:
            股票列表
        """
        try:
            import requests
            
            all_stocks = []
            url = 'https://push2delay.eastmoney.com/api/qt/clist/get'
            
            for page in range(1, 60):
                params = {
                    'pn': page,
                    'pz': 100,
                    'po': 1,
                    'np': 1,
                    'ut': 'bd1d9ddb04089700cf9c27f6f7426281',
                    'fltt': 2,
                    'invt': 2,
                    'fid': 'f12',
                    'fs': 'm:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23',
                    'fields': 'f12,f14,f2,f3,f5,f6'
                }
                
                r = requests.get(url, params=params, timeout=15, proxies={'http': None, 'https': None})
                if r.status_code == 200:
                    data = r.json()
                    if data.get('data') and data['data'].get('diff'):
                        stocks_batch = data['data']['diff']
                        for stock in stocks_batch:
                            code = stock.get('f12', '')
                            name = stock.get('f14', '')
                            close_price = stock.get('f2', 0)
                            change_percent = stock.get('f3', 0)
                            volume = stock.get('f5', 0)
                            amount = stock.get('f6', 0)
                            
                            if not code or not name:
                                continue
                            
                            all_stocks.append({
                                'stock_code': code,
                                'stock_name': name,
                                'exchange': 'SH' if code.startswith('6') else 'SZ',
                                'close_price': float(close_price) if close_price else 0,
                                'change_percent': float(change_percent) if change_percent else 0,
                                'volume': int(volume) if volume else 0,
                                'amount': float(amount) if amount else 0,
                            })
                        
                        if len(stocks_batch) < 100:
                            break
                    else:
                        break
                else:
                    break
            
            return all_stocks
        except Exception as e:
            print(f"获取股票列表失败: {e}")
            return None
    
    def _parse_share_count(self, value: str) -> int:
        """解析股本数量"""
        try:
            if '亿' in str(value):
                return int(float(str(value).replace('亿', '')) * 100000000)
            elif '万' in str(value):
                return int(float(str(value).replace('万', '')) * 10000)
            return int(float(value))
        except:
            return 0
    
    def _parse_amount(self, value: str) -> float:
        """解析金额"""
        try:
            if '亿' in str(value):
                return float(str(value).replace('亿', '')) * 100000000
            elif '万' in str(value):
                return float(str(value).replace('万', '')) * 10000
            return float(value)
        except:
            return 0.0
    
    def _parse_float(self, value: str) -> float:
        """解析浮点数"""
        try:
            return float(value)
        except:
            return 0.0


def main():
    """测试数据获取模块"""
    print("=" * 60)
    print("数据获取模块测试")
    print("=" * 60)
    
    from database_config import MYSQL_CONFIG
    fetcher = DataFetcher(MYSQL_CONFIG)
    fetcher.connect()
    
    print("\n1. 测试获取实时行情...")
    realtime = fetcher.get_stock_realtime('002065')
    if realtime:
        print(f"股票名称: {realtime['stock_name']}")
        print(f"最新价: {realtime['last_price']}")
        print(f"涨跌幅: {realtime['change_percent']}%")
    
    print("\n2. 测试获取K线数据...")
    kline = fetcher.get_kline_data('002065', 60)
    if kline is not None:
        print(f"获取到{len(kline)}条K线数据")
    
    print("\n3. 测试计算技术指标...")
    if kline is not None:
        indicators = fetcher.calculate_technical_indicators(kline)
        if indicators:
            print(f"MA5: {indicators['ma5']}")
            print(f"MA20: {indicators['ma20']}")
            print(f"DIFF: {indicators['diff']}")
            print(f"DEA: {indicators['dea']}")
            print(f"DIFF>DEA>0: {indicators['diff_gt_dea_and_zero']}")
            print(f"RSI: {indicators['rsi']}")
            print(f"OBV>MAOBV: {indicators['obv_gt_maobv']}")
    
    fetcher.disconnect()
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)


if __name__ == "__main__":
    main()
