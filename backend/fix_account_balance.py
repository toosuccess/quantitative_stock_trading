
"""
修复账户余额问题
根据交易记录重新计算正确的可用资金和盈亏
"""
import pymysql
from app.database_config import MYSQL_CONFIG

conn = pymysql.connect(**MYSQL_CONFIG, cursorclass=pymysql.cursors.DictCursor)
cursor = conn.cursor()

print("="*80)
print("  修复账户余额")
print("="*80)

# 查询账户信息
cursor.execute('''
    SELECT account_id, account_name, initial_assets, available_cash 
    FROM account_info
''')
account = cursor.fetchone()

if not account:
    print("未找到账户！")
    exit(1)

initial = float(account['initial_assets'])
current_available = float(account['available_cash'])

print(f"\n账户: {account['account_name']}")
print(f"初始资金: {initial:.2f}")
print(f"当前可用资金: {current_available:.2f}")

# 计算所有交易的净影响
cursor.execute('''
    SELECT 
        SUM(CASE WHEN trade_type = '买入' THEN trade_amount ELSE 0 END) as total_buy,
        SUM(CASE WHEN trade_type = '卖出' THEN trade_amount ELSE 0 END) as total_sell,
        COUNT(CASE WHEN trade_type = '买入' THEN 1 END) as buy_count,
        COUNT(CASE WHEN trade_type = '卖出' THEN 1 END) as sell_count
    FROM trade_record 
    WHERE account_id = %s
''', (account['account_id'],))

trade_summary = cursor.fetchone()
total_buy = float(trade_summary['total_buy']) if trade_summary['total_buy'] else 0
total_sell = float(trade_summary['total_sell']) if trade_summary['total_sell'] else 0

print(f"\n交易统计:")
print(f"  买入次数: {trade_summary['buy_count']}, 总额: {total_buy:.2f}")
print(f"  卖出次数: {trade_summary['sell_count']}, 总额: {total_sell:.2f}")

# 计算正确的可用资金
correct_available = initial - total_buy + total_sell
net_profit = total_sell - total_buy

print(f"\n【计算结果】")
print(f"  理论可用资金: {correct_available:.2f}")
print(f"  实际可用资金: {current_available:.2f}")
print(f"  差异: {correct_available - current_available:+.2f}")
print(f"  净盈亏(交易): {net_profit:+.2f}")

if abs(correct_available - current_available) > 0.01:
    print(f"\n⚠️ 发现错误！正在修复...")
    
    # 更新账户的可用资金
    cursor.execute('''
        UPDATE account_info 
        SET available_cash = %s,
            total_assets = %s,
            profit_loss = %s,
            update_time = NOW()
        WHERE account_id = %s
    ''', (correct_available, correct_available, net_profit, account['account_id']))
    
    conn.commit()
    print(f"✅ 已修复！")
    print(f"   可用资金更新为: {correct_available:.2f}")
    print(f"   盈亏更新为: {net_profit:+.2f}")
else:
    print(f"\n✅ 数据正确，无需修复")

conn.close()
print("\n完成！")
