"""
从QMT获取东华软件实时数据
"""
import sys
import os
from datetime import datetime

def get_qmt_realtime_data(stock_code='002065'):
    """
    从QMT获取股票实时数据
    
    Args:
        stock_code: 股票代码，默认为东华软件(002065)
    
    Returns:
        dict: 实时数据字典
    """
    print(f"正在从QMT获取{stock_code}的实时数据...")
    
    try:
        # 尝试导入xtquant库
        try:
            from xtquant import xtdata
            print("成功导入xtquant库")
        except ImportError:
            print("错误：未安装xtquant库")
            print("请确保已安装QMT客户端，并配置好Python环境")
            print("安装方法：")
            print("1. 安装QMT客户端")
            print("2. 将QMT安装目录下的xtquant文件夹复制到Python的site-packages目录")
            print("   或者设置PYTHONPATH环境变量指向QMT的Python目录")
            return None
        
        # 构建完整的股票代码（QMT格式）
        # 深圳股票：SZ.代码，上海股票：SH.代码
        if stock_code.startswith('6'):
            full_code = f'SH.{stock_code}'
        else:
            full_code = f'SZ.{stock_code}'
        
        print(f"完整股票代码: {full_code}")
        
        # 1. 获取实时行情数据
        print("\n=== 获取实时行情数据 ===")
        try:
            # 获取最新行情快照
            snapshot = xtdata.get_full_tick([full_code])
            
            if snapshot and full_code in snapshot:
                tick_data = snapshot[full_code]
                
                realtime_data = {
                    'stock_code': stock_code,
                    'full_code': full_code,
                    'stock_name': '东华软件',
                    'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    
                    # 价格数据
                    'lastPrice': tick_data.get('lastPrice', 0),  # 最新价
                    'open': tick_data.get('open', 0),  # 开盘价
                    'high': tick_data.get('high', 0),  # 最高价
                    'low': tick_data.get('low', 0),  # 最低价
                    'preClose': tick_data.get('lastClose', 0),  # 昨收价
                    
                    # 成交数据
                    'volume': tick_data.get('volume', 0),  # 成交量（股）
                    'amount': tick_data.get('amount', 0),  # 成交额（元）
                    
                    # 涨跌数据
                    'change': 0,
                    'changePercent': 0,
                    
                    # 买卖盘数据
                    'bidPrice1': tick_data.get('bidPrice', [0])[0] if tick_data.get('bidPrice') else 0,  # 买一价
                    'bidVolume1': tick_data.get('bidVol', [0])[0] if tick_data.get('bidVol') else 0,  # 买一量
                    'askPrice1': tick_data.get('askPrice', [0])[0] if tick_data.get('askPrice') else 0,  # 卖一价
                    'askVolume1': tick_data.get('askVol', [0])[0] if tick_data.get('askVol') else 0,  # 卖一量
                }
                
                # 计算涨跌额和涨跌幅
                if realtime_data['preClose'] > 0:
                    realtime_data['change'] = realtime_data['lastPrice'] - realtime_data['preClose']
                    realtime_data['changePercent'] = (realtime_data['change'] / realtime_data['preClose']) * 100
                
                print(f"股票名称: {realtime_data['stock_name']}")
                print(f"股票代码: {realtime_data['stock_code']}")
                print(f"最新价: {realtime_data['lastPrice']:.2f}元")
                print(f"开盘价: {realtime_data['open']:.2f}元")
                print(f"最高价: {realtime_data['high']:.2f}元")
                print(f"最低价: {realtime_data['low']:.2f}元")
                print(f"昨收价: {realtime_data['preClose']:.2f}元")
                print(f"涨跌额: {realtime_data['change']:.2f}元")
                print(f"涨跌幅: {realtime_data['changePercent']:.2f}%")
                print(f"成交量: {realtime_data['volume']}股")
                print(f"成交额: {realtime_data['amount']:.2f}元")
                print(f"买一价: {realtime_data['bidPrice1']:.2f}元")
                print(f"买一量: {realtime_data['bidVolume1']}股")
                print(f"卖一价: {realtime_data['askPrice1']:.2f}元")
                print(f"卖一量: {realtime_data['askVolume1']}股")
                print(f"更新时间: {realtime_data['update_time']}")
                
            else:
                print(f"警告：无法获取{full_code}的实时行情数据")
                realtime_data = None
                
        except Exception as e:
            print(f"获取实时行情数据失败: {e}")
            realtime_data = None
        
        # 2. 获取历史K线数据（用于计算技术指标）
        print("\n=== 获取历史K线数据 ===")
        try:
            # 获取日K线数据
            kline_data = xtdata.get_market_data_ex(
                field_list=['open', 'high', 'low', 'close', 'volume', 'amount'],
                stock_list=[full_code],
                period='1d',  # 日线
                count=250,  # 获取250个交易日数据
                dividend_type='front'  # 前复权
            )
            
            if kline_data and full_code in kline_data:
                stock_kline = kline_data[full_code]
                print(f"成功获取{len(stock_kline)}个交易日的K线数据")
                
                # 显示最近5天的K线数据
                print("\n最近5个交易日K线数据：")
                print("-" * 80)
                print(f"{'日期':<12} {'开盘价':<10} {'最高价':<10} {'最低价':<10} {'收盘价':<10} {'成交量':<15}")
                print("-" * 80)
                
                for i in range(-5, 0):
                    if i < len(stock_kline):
                        row = stock_kline.iloc[i]
                        date_str = stock_kline.index[i].strftime('%Y-%m-%d')
                        print(f"{date_str:<12} {row['open']:<10.2f} {row['high']:<10.2f} {row['low']:<10.2f} {row['close']:<10.2f} {int(row['volume']):<15}")
                print("-" * 80)
                
                # 计算技术指标
                print("\n=== 计算技术指标 ===")
                technical_indicators = calculate_technical_indicators_from_qmt(stock_kline)
                
                return {
                    'realtime_data': realtime_data,
                    'kline_data': stock_kline,
                    'technical_indicators': technical_indicators
                }
            else:
                print(f"警告：无法获取{full_code}的K线数据")
                return {
                    'realtime_data': realtime_data,
                    'kline_data': None,
                    'technical_indicators': None
                }
                
        except Exception as e:
            print(f"获取K线数据失败: {e}")
            return {
                'realtime_data': realtime_data,
                'kline_data': None,
                'technical_indicators': None
            }
            
    except Exception as e:
        print(f"从QMT获取数据失败: {e}")
        import traceback
        traceback.print_exc()
        return None

def calculate_technical_indicators_from_qmt(kline_data):
    """
    从QMT的K线数据计算技术指标
    
    Args:
        kline_data: K线数据DataFrame
    
    Returns:
        dict: 技术指标字典
    """
    import pandas as pd
    import numpy as np
    
    if kline_data is None or len(kline_data) < 20:
        print("K线数据不足，无法计算技术指标")
        return None
    
    try:
        close = kline_data['close'].values
        high = kline_data['high'].values
        low = kline_data['low'].values
        volume = kline_data['volume'].values
        
        indicators = {}
        
        # 1. 均线系统
        ma5 = np.mean(close[-5:])
        ma10 = np.mean(close[-10:])
        ma20 = np.mean(close[-20:])
        ma60 = np.mean(close[-60:]) if len(close) >= 60 else ma20
        
        indicators['MA5'] = round(ma5, 2)
        indicators['MA10'] = round(ma10, 2)
        indicators['MA20'] = round(ma20, 2)
        indicators['MA60'] = round(ma60, 2)
        
        print(f"MA5: {indicators['MA5']}")
        print(f"MA10: {indicators['MA10']}")
        print(f"MA20: {indicators['MA20']}")
        print(f"MA60: {indicators['MA60']}")
        
        # 2. MACD指标
        ema12 = pd.Series(close).ewm(span=12, adjust=False).mean().values
        ema26 = pd.Series(close).ewm(span=26, adjust=False).mean().values
        diff = ema12 - ema26
        dea = pd.Series(diff).ewm(span=9, adjust=False).mean().values
        macd = (diff - dea) * 2
        
        indicators['DIFF'] = round(diff[-1], 4)
        indicators['DEA'] = round(dea[-1], 4)
        indicators['MACD'] = round(macd[-1], 4)
        
        print(f"DIFF: {indicators['DIFF']}")
        print(f"DEA: {indicators['DEA']}")
        print(f"MACD: {indicators['MACD']}")
        
        # 3. RSI指标
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
        
        indicators['RSI'] = round(rsi, 2)
        print(f"RSI(14): {indicators['RSI']}")
        
        # 4. 布林带
        ma20_val = np.mean(close[-20:])
        std_dev = np.std(close[-20:])
        upper_band = ma20_val + 2 * std_dev
        lower_band = ma20_val - 2 * std_dev
        
        indicators['BB_Upper'] = round(upper_band, 2)
        indicators['BB_Middle'] = round(ma20_val, 2)
        indicators['BB_Lower'] = round(lower_band, 2)
        
        print(f"布林带上轨: {indicators['BB_Upper']}")
        print(f"布林带中轨: {indicators['BB_Middle']}")
        print(f"布林带下轨: {indicators['BB_Lower']}")
        
        # 5. 成交量指标
        ma5_volume = np.mean(volume[-5:])
        ma10_volume = np.mean(volume[-10:])
        
        indicators['Volume'] = int(volume[-1])
        indicators['MA5_Volume'] = int(ma5_volume)
        indicators['MA10_Volume'] = int(ma10_volume)
        
        print(f"成交量: {indicators['Volume']}")
        print(f"5日均量: {indicators['MA5_Volume']}")
        print(f"10日均量: {indicators['MA10_Volume']}")
        
        return indicators
        
    except Exception as e:
        print(f"计算技术指标失败: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    """
    主函数
    """
    print("=" * 80)
    print("从QMT获取东华软件(002065)实时数据")
    print("=" * 80)
    
    # 获取东华软件的实时数据
    result = get_qmt_realtime_data('002065')
    
    if result:
        print("\n" + "=" * 80)
        print("数据获取成功！")
        print("=" * 80)
        
        # 保存数据到文件
        save_to_file(result)
    else:
        print("\n" + "=" * 80)
        print("数据获取失败！")
        print("=" * 80)
        print("\n可能的原因：")
        print("1. 未安装QMT客户端")
        print("2. 未正确配置xtquant库")
        print("3. QMT客户端未运行")
        print("4. 不在交易时间段（部分数据可能无法获取）")

def save_to_file(result):
    """
    将数据保存到文件
    
    Args:
        result: 数据字典
    """
    try:
        import json
        
        # 准备保存的数据
        save_data = {
            'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'realtime_data': result.get('realtime_data'),
            'technical_indicators': result.get('technical_indicators')
        }
        
        # 保存为JSON文件
        filename = f"donghua_software_realtime_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = os.path.join(os.path.dirname(__file__), filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(save_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n数据已保存到文件: {filepath}")
        
    except Exception as e:
        print(f"保存数据到文件失败: {e}")

if __name__ == "__main__":
    main()
