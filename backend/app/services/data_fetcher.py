"""
数据获取模块
封装AkShare数据接口，支持股票基本信息、技术指标、实时股价获取
"""
import akshare as ak
import pandas as pd
import numpy as np
from datetime import datetime, date
from typing import Dict, List, Optional, Tuple
import sqlite3
import os

class DataFetcher:
    """数据获取类"""
    
    def __init__(self, db_path: str = 'trading_system.db'):
        """
        初始化数据获取器
        
        Args:
            db_path: 数据库文件路径
        """
        self.db_path = db_path
        self.conn = None
    
    def connect(self):
        """连接数据库"""
        self.conn = sqlite3.connect(self.db_path)
        return self.conn
    
    def disconnect(self):
        """断开数据库连接"""
        if self.conn:
            self.conn.close()
    
    def get_stock_realtime(self, stock_code: str) -> Optional[Dict]:
        """
        获取股票实时行情数据
        
        Args:
            stock_code: 股票代码
        
        Returns:
            实时数据字典
        """
        try:
            realtime_df = ak.stock_zh_a_spot_em()
            stock_data = realtime_df[realtime_df['代码'] == stock_code]
            
            if not stock_data.empty:
                row = stock_data.iloc[0]
                return {
                    'stock_code': stock_code,
                    'stock_name': row['名称'],
                    'last_price': float(row['最新价']),
                    'open': float(row['今开']),
                    'high': float(row['最高']),
                    'low': float(row['最低']),
                    'pre_close': float(row['昨收']),
                    'volume': int(row['成交量']),
                    'amount': float(row['成交额']),
                    'change': float(row['涨跌额']),
                    'change_percent': float(row['涨跌幅']),
                    'turnover_rate': float(row['换手率']) if '换手率' in row else 0,
                    'pe_ratio': float(row['市盈率-动态']) if '市盈率-动态' in row else 0,
                    'pb_ratio': float(row['市净率']) if '市净率' in row else 0,
                    'total_market_value': float(row['总市值']) if '总市值' in row else 0,
                    'circulation_market_value': float(row['流通市值']) if '流通市值' in row else 0,
                }
            return None
        except Exception as e:
            print(f"获取实时行情失败: {e}")
            return None
    
    def get_stock_basic_info(self, stock_code: str) -> Optional[Dict]:
        """
        获取股票基本信息
        
        Args:
            stock_code: 股票代码
        
        Returns:
            股票基本信息字典
        """
        try:
            stock_info_df = ak.stock_individual_info_em(symbol=stock_code)
            
            info_dict = {}
            for _, row in stock_info_df.iterrows():
                info_dict[row['item']] = row['value']
            
            return {
                'stock_code': stock_code,
                'stock_name': info_dict.get('股票简称', ''),
                'stock_abbr': info_dict.get('股票简称', ''),
                'exchange': 'SH' if stock_code.startswith('6') else 'SZ',
                'industry': info_dict.get('行业', ''),
                'sector': info_dict.get('概念板块', ''),
                'list_date': info_dict.get('上市时间', ''),
                'total_shares': self._parse_share_count(info_dict.get('总市值', '0')),
                'float_shares': self._parse_share_count(info_dict.get('流通市值', '0')),
                'market_cap': self._parse_amount(info_dict.get('总市值', '0')),
                'float_market_cap': self._parse_amount(info_dict.get('流通市值', '0')),
                'pe_ratio': self._parse_float(info_dict.get('市盈率', '0')),
                'pb_ratio': self._parse_float(info_dict.get('市净率', '0')),
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
            INSERT OR REPLACE INTO stock_basic_info 
            (stock_code, stock_name, stock_abbr, exchange, industry, sector,
            list_date, total_shares, float_shares, market_cap, float_market_cap,
            pe_ratio, pb_ratio, ps_ratio, dividend_yield, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
            INSERT OR REPLACE INTO score_record 
            (stock_code, stock_name, score_date, 
            fundamental_score, fundamental_reason,
            technical_score, technical_reason,
            ma_score, macd_score, rsi_score, bollinger_score, volume_score, obv_score,
            total_score, rating,
            ma5, ma10, ma20, ma60,
            diff, dea, macd, rsi,
            bb_upper, bb_middle, bb_lower,
            close_price, volume, turnover_rate)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
        获取所有A股股票列表
        
        Returns:
            股票列表
        """
        try:
            stock_list = ak.stock_zh_a_spot_em()
            stocks = []
            for _, row in stock_list.iterrows():
                try:
                    close_price = row['最新价']
                    change_percent = row['涨跌幅']
                    volume = row['成交量']
                    amount = row['成交额']
                    
                    if pd.isna(close_price) or pd.isna(volume):
                        continue
                    
                    stocks.append({
                        'stock_code': row['代码'],
                        'stock_name': row['名称'],
                        'exchange': 'SH' if row['代码'].startswith('6') else 'SZ',
                        'close_price': float(close_price) if close_price else 0,
                        'change_percent': float(change_percent) if not pd.isna(change_percent) else 0,
                        'volume': int(volume) if volume else 0,
                        'amount': float(amount) if not pd.isna(amount) else 0,
                    })
                except (ValueError, TypeError):
                    continue
            return stocks
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
    
    fetcher = DataFetcher('trading_system.db')
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
