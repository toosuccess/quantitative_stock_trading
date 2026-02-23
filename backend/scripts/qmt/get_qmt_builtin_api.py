"""
使用QMT内置API获取东华软件实时数据
注意：此脚本需要在QMT客户端中运行
"""

# QMT内置API示例 - 获取股票数据

def init(ContextInfo):
    """
    初始化函数
    """
    # 设置股票代码
    ContextInfo.stock_code = '002065.SZ'  # 东华软件
    ContextInfo.set_universe([ContextInfo.stock_code])
    
    print("=" * 80)
    print("QMT获取东华软件(002065)数据")
    print("=" * 80)

def handlebar(ContextInfo):
    """
    K线处理函数
    """
    try:
        stock_code = ContextInfo.stock_code
        
        # 获取当前K线索引
        index = ContextInfo.barpos
        
        # 获取当前时间
        realtime = ContextInfo.get_bar_timetag(index)
        
        # 获取周期和复权方式
        period = ContextInfo.period
        dividend_type = ContextInfo.dividend_type
        
        # 获取市场数据
        close = ContextInfo.get_market_data(['close'], stock_code=stock_code, period=period, dividend_type=dividend_type)
        open_price = ContextInfo.get_market_data(['open'], stock_code=stock_code, period=period, dividend_type=dividend_type)
        high = ContextInfo.get_market_data(['high'], stock_code=stock_code, period=period, dividend_type=dividend_type)
        low = ContextInfo.get_market_data(['low'], stock_code=stock_code, period=period, dividend_type=dividend_type)
        volume = ContextInfo.get_market_data(['volume'], stock_code=stock_code, period=period, dividend_type=dividend_type)
        
        # 打印数据
        if close is not None and len(close) > 0:
            print(f"\n股票代码: {stock_code}")
            print(f"最新价: {close[-1]:.2f}元")
            print(f"开盘价: {open_price[-1]:.2f}元")
            print(f"最高价: {high[-1]:.2f}元")
            print(f"最低价: {low[-1]:.2f}元")
            print(f"成交量: {volume[-1]}手")
            
            # 计算技术指标
            if len(close) >= 20:
                import numpy as np
                
                # MA
                ma5 = np.mean(close[-5:])
                ma10 = np.mean(close[-10:])
                ma20 = np.mean(close[-20:])
                
                print(f"\n技术指标:")
                print(f"MA5: {ma5:.2f}")
                print(f"MA10: {ma10:.2f}")
                print(f"MA20: {ma20:.2f}")
                
                # MACD
                import pandas as pd
                ema12 = pd.Series(close).ewm(span=12, adjust=False).mean()
                ema26 = pd.Series(close).ewm(span=26, adjust=False).mean()
                diff = ema12 - ema26
                dea = diff.ewm(span=9, adjust=False).mean()
                macd = (diff - dea) * 2
                
                print(f"DIFF: {diff.iloc[-1]:.4f}")
                print(f"DEA: {dea.iloc[-1]:.4f}")
                print(f"MACD: {macd.iloc[-1]:.4f}")
        
        # 绘制收盘价
        ContextInfo.paint('close', close, -1, 0)
        
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()

# 如果直接运行此脚本（不在QMT中），使用akshare作为替代方案
if __name__ == "__main__":
    print("=" * 80)
    print("注意：此脚本需要在QMT客户端中运行")
    print("=" * 80)
    print("\n如果您想在QMT客户端中运行此脚本，请按以下步骤操作：")
    print("1. 打开QMT客户端")
    print("2. 进入'量化' -> '策略交易'")
    print("3. 新建策略，将此脚本内容复制到策略编辑器中")
    print("4. 运行策略")
    print("\n如果您想直接获取数据，请使用以下命令：")
    print("python get_donghua_realtime_akshare.py")
    print("\n现在将使用akshare获取数据作为替代方案...")
    print("=" * 80)
    
    # 调用akshare版本
    import subprocess
    subprocess.run(["python", "get_donghua_realtime_akshare.py"])
