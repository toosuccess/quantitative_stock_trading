
"""
调试盈亏计算问题
查询所有交易记录和账户数据，分析盈亏是否正确
"""
import pymysql
from app.database_config import MYSQL_CONFIG

conn = pymysql.connect(**MYSQL_CONFIG, cursorclass=pymysql.cursors.DictCursor)
cursor = conn.cursor()

print("="*80)
print("  盈亏计算调试报告")
print("="*80)

# 1. 查询账户信息
print("\n【1. 账户信息】")
cursor.execute('''
    SELECT account_id, account_name, initial_assets, total_assets, 
           available_cash, market_value, profit_loss
    FROM account_info
''')
accounts = cursor.fetchall()
for acc in accounts:
    print(f"  账户: {acc['account_name']}")
    print(f"    初始资金: {acc['initial_assets']}")
    print(f"    总资产: {acc['total_assets']}")
    print(f"    可用资金: {acc['available_cash']}")
    print(f"    市值: {acc.get('market_value', 'N/A')}")
    print(f"    盈亏(数据库): {acc['profit_loss']}")
    
    # 实时计算盈亏
    initial = float(acc['initial_assets'])
    available = float(acc['available_cash'])
    
    # 计算持仓市值
    cursor.execute('''
        SELECT tr.stock_code, 
               SUM(CASE WHEN tr.trade_type = '买入' THEN tr.trade_quantity ELSE 0 END) -
               SUM(CASE WHEN tr.trade_type = '卖出' THEN tr.trade_quantity ELSE 0 END) as holding_qty,
               SUM(CASE WHEN tr.trade_type = '买入' THEN tr.trade_amount ELSE 0 END) as buy_amount,
               SUM(CASE WHEN tr.trade_type = '卖出' THEN tr.trade_amount ELSE 0 END) as sell_amount
        FROM trade_record tr
        WHERE tr.account_id = %s
        GROUP BY tr.stock_code
        HAVING holding_qty > 0
    ''', (acc['account_id'],))
    holdings = cursor.fetchall()
    
    market_value = 0.0
    if holdings:
        for h in holdings:
            # 获取当前价格
            cursor.execute('''
                SELECT current_price FROM stock_basic_info 
                WHERE stock_code = %s AND current_price > 0
                ORDER BY price_last_update DESC LIMIT 1
            ''', (h['stock_code'].replace('sh','').replace('sz','').replace('bj',''),))
            price_row = cursor.fetchone()
            if price_row and price_row.get('current_price'):
                current_price = float(price_row['current_price'])
            else:
                # 从 score_record 获取
                cursor.execute('''
                    SELECT close_price FROM score_record 
                    WHERE stock_code = %s AND close_price > 0
                    ORDER BY score_date DESC LIMIT 1
                ''', (h['stock_code'].replace('sh','').replace('sz','').replace('bj',''),))
                score_row = cursor.fetchone()
                current_price = float(score_row['close_price']) if score_row else 0
            
            h_value = float(h['holding_qty']) * current_price
            market_value += h_value
            print(f"\n    持仓: {h['stock_code']} - {h['holding_qty']}股 @ {current_price} = {h_value:.2f}")
    
    real_total = available + market_value
    real_profit = real_total - initial
    
    print(f"\n  【实时计算】")
    print(f"    可用资金: {available:.2f}")
    print(f"    持仓市值: {market_value:.2f}")
    print(f"    实际总资产: {real_total:.2f}")
    print(f"    实际盈亏: {real_profit:.2f}")

# 2. 查询所有交易记录
print("\n\n" + "="*80)
print("【2. 所有交易记录】")
print("="*80)
cursor.execute('''
    SELECT record_id, stock_code, stock_name, trade_type, trade_direction,
           trade_price, trade_quantity, trade_amount, trade_date
    FROM trade_record 
    ORDER BY trade_date ASC, trade_time ASC
''')
records = cursor.fetchall()

total_buy = 0
total_sell = 0
buy_count = 0
sell_count = 0

print("\n  按时间顺序:")
for r in records:
    sign = '+' if r['trade_type'] == '卖出' else '-'
    print(f"  {r['trade_date']} | {r['trade_type']:4s} | {r['stock_name']:8s} ({r['stock_code']}) | "
          f"{r['trade_quantity']:6d}股 × {r['trade_price']:8.2f} = {sign}{r['trade_amount']:10.2f}")
    if r['trade_type'] == '买入':
        total_buy += float(r['trade_amount'])
        buy_count += 1
    else:
        total_sell += float(r['trade_amount'])
        sell_count += 1

net_profit = total_sell - total_buy
print(f"\n  【汇总】")
print(f"    买入次数: {buy_count}, 总金额: {total_buy:.2f}")
print(f"    卖出次数: {sell_count}, 总金额: {total_sell:.2f}")
print(f"    净盈亏(卖出-买入): {net_profit:+.2f}")

# 3. 按股票分组统计
print("\n\n" + "="*80)
print("【3. 每只股票的盈亏】")
print("="*80)

cursor.execute('''
    SELECT stock_code, stock_name,
           SUM(CASE WHEN trade_type = '买入' THEN trade_quantity ELSE 0 END) as buy_qty,
           SUM(CASE WHEN trade_type = '买入' THEN trade_amount ELSE 0 END) as buy_amt,
           SUM(CASE WHEN trade_type = '卖出' THEN trade_quantity ELSE 0 END) as sell_qty,
           SUM(CASE WHEN trade_type = '卖出' THEN trade_amount ELSE 0 END) as sell_amt
    FROM trade_record 
    GROUP BY stock_code, stock_name
    ORDER BY stock_name
''')
stocks = cursor.fetchall()

print("\n  股票代码   | 股票名称   | 买入数量 | 卖出数量 | 买入金额  | 卖出金额  | 净盈亏")
print("-"*90)

total_stock_profit = 0
for s in stocks:
    buy_qty = s['buy_qty'] or 0
    sell_qty = s['sell_qty'] or 0
    buy_amt = s['buy_amt'] or 0
    sell_amt = s['sell_amt'] or 0
    profit = sell_amt - buy_amt
    total_stock_profit += profit
    
    status = "✅盈利" if profit >= 0 else "❌亏损"
    print(f"  {s['stock_code']:10s} | {s['stock_name']:8s} | {buy_qty:7d} | {sell_qty:7d} | {buy_amt:9.2f} | {sell_amt:9.2f} | {profit:+8.2f} {status}")

print("-"*90)
print(f"  {'合计':12s} | {'':8s} | {'':7s} | {'':7s} | {total_buy:9.2f} | {total_sell:9.2f} | {total_stock_profit:+8.2f}")

# 4. 分析问题
print("\n\n" + "="*80)
print("【4. 问题分析】")
print("="*80)

account = accounts[0] if accounts else None
if account:
    initial = float(account['initial_assets'])
    available = float(account['available_cash'])
    db_profit = float(account['profit_loss']) if account.get('profit_loss') else 0
    
    print(f"\n  当前账户状态:")
    print(f"    初始资金: {initial:.2f}")
    print(f"    可用资金: {available:.2f}")
    print(f"    数据库盈亏: {db_profit:+.2f}")
    print(f"    交易净盈亏: {net_profit:+.2f}")
    print(f"    各股票总盈亏: {total_stock_profit:+.2f}")
    
    print(f"\n  【关键发现】")
    
    # 计算理论上应该有的可用资金
    expected_available = initial - total_buy + total_sell
    print(f"    理论可用资金(初始-买入+卖出): {expected_available:.2f}")
    print(f"    实际可用资金: {available:.2f}")
    diff = available - expected_available
    print(f"    差异: {diff:+.2f}")
    
    if abs(diff) > 1:
        print(f"\n  ⚠️ 发现问题！实际可用资金与理论值不一致！")
        print(f"     可能原因：")
        print(f"     1. 执行交易时，账户余额更新逻辑有问题")
        print(f"     2. 有其他资金变动未记录在交易记录中")

conn.close()
print("\n\n调试完成！")
