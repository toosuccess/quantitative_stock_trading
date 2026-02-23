"""
配置QMT环境并获取东华软件实时数据
"""
import sys
import os
from datetime import datetime

# 设置QMT的Python路径
qmt_python_path = r"D:\迅投极速交易终端\bin.x64"
qmt_lib_path = r"D:\迅投极速交易终端\bin.x64\Lib\site-packages"

# 添加到系统路径
if qmt_lib_path not in sys.path:
    sys.path.insert(0, qmt_lib_path)

if qmt_python_path not in sys.path:
    sys.path.insert(0, qmt_python_path)

print(f"已添加QMT路径到系统路径:")
print(f"  - {qmt_python_path}")
print(f"  - {qmt_lib_path}")
print(f"\n当前Python路径:")
for i, path in enumerate(sys.path[:5], 1):
    print(f"  {i}. {path}")

# 尝试导入xtquant
try:
    from xtquant import xtdata
    print("\n✅ 成功导入xtquant库！")
    
    # 获取东华软件实时数据
    stock_code = '002065'
    full_code = f'SZ.{stock_code}'
    
    print(f"\n{'='*80}")
    print(f"从QMT获取东华软件({stock_code})实时数据")
    print(f"{'='*80}")
    
    # 1. 获取实时行情快照
    print("\n=== 获取实时行情数据 ===")
    try:
        snapshot = xtdata.get_full_tick([full_code])
        
        if snapshot and full_code in snapshot:
            tick_data = snapshot[full_code]
            
            print(f"股票代码: {stock_code}")
            print(f"最新价: {tick_data.get('lastPrice', 0):.2f}元")
            print(f"开盘价: {tick_data.get('open', 0):.2f}元")
            print(f"最高价: {tick_data.get('high', 0):.2f}元")
            print(f"最低价: {tick_data.get('low', 0):.2f}元")
            print(f"昨收价: {tick_data.get('lastClose', 0):.2f}元")
            print(f"成交量: {tick_data.get('volume', 0)}股")
            print(f"成交额: {tick_data.get('amount', 0):.2f}元")
            
            # 计算涨跌
            last_price = tick_data.get('lastPrice', 0)
            pre_close = tick_data.get('lastClose', 0)
            if pre_close > 0:
                change = last_price - pre_close
                change_pct = (change / pre_close) * 100
                print(f"涨跌额: {change:.2f}元")
                print(f"涨跌幅: {change_pct:.2f}%")
        else:
            print(f"警告：无法获取{full_code}的实时行情数据")
            print("可能原因：")
            print("  1. QMT客户端未运行")
            print("  2. 不在交易时间段")
            print("  3. 股票代码错误")
            
    except Exception as e:
        print(f"获取实时行情失败: {e}")
        import traceback
        traceback.print_exc()
    
    # 2. 获取历史K线数据
    print("\n=== 获取历史K线数据 ===")
    try:
        kline_data = xtdata.get_market_data_ex(
            field_list=['open', 'high', 'low', 'close', 'volume', 'amount'],
            stock_list=[full_code],
            period='1d',
            count=250,
            dividend_type='front'
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
            import pandas as pd
            import numpy as np
            
            close = stock_kline['close'].values
            
            # MA
            ma5 = np.mean(close[-5:])
            ma10 = np.mean(close[-10:])
            ma20 = np.mean(close[-20:])
            ma60 = np.mean(close[-60:]) if len(close) >= 60 else ma20
            
            print(f"MA5: {ma5:.2f}")
            print(f"MA10: {ma10:.2f}")
            print(f"MA20: {ma20:.2f}")
            print(f"MA60: {ma60:.2f}")
            
            # MACD
            ema12 = pd.Series(close).ewm(span=12, adjust=False).mean().values
            ema26 = pd.Series(close).ewm(span=26, adjust=False).mean().values
            diff = ema12 - ema26
            dea = pd.Series(diff).ewm(span=9, adjust=False).mean().values
            macd = (diff - dea) * 2
            
            print(f"DIFF: {diff[-1]:.4f}")
            print(f"DEA: {dea[-1]:.4f}")
            print(f"MACD: {macd[-1]:.4f}")
            
        else:
            print(f"警告：无法获取{full_code}的K线数据")
            
    except Exception as e:
        print(f"获取K线数据失败: {e}")
        import traceback
        traceback.print_exc()
    
    print(f"\n{'='*80}")
    print("数据获取完成！")
    print(f"{'='*80}")
    
except ImportError as e:
    print(f"\n❌ 导入xtquant库失败: {e}")
    print("\n请检查以下内容：")
    print("1. QMT客户端是否已安装")
    print("2. QMT客户端是否正在运行")
    print("3. xtquant库路径是否正确")
    print(f"\n当前查找路径: {qmt_lib_path}")
    print("\n请尝试以下解决方案：")
    print("方案1: 启动QMT客户端后重试")
    print("方案2: 检查QMT安装目录下是否有xtquant相关文件")
    print("方案3: 使用akshare版本获取数据: python get_donghua_realtime_akshare.py")
    
except Exception as e:
    print(f"\n❌ 发生错误: {e}")
    import traceback
    traceback.print_exc()
