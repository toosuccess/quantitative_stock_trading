"""
修复账户金额脚本
1. 初始化账户的available_cash为total_assets
2. 根据交易记录重新计算账户金额
"""

import sqlite3
from pathlib import Path

def fix_account_balance():
    db_path = Path(__file__).parent / 'database' / 'trading_system.db'
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    print("=" * 50)
    print("修复账户金额")
    print("=" * 50)
    
    # 1. 获取所有账户
    cursor.execute("SELECT * FROM account_info")
    accounts = cursor.fetchall()
    
    for account in accounts:
        account_id = account['account_id']
        account_name = account['account_name']
        total_assets = account['total_assets']
        
        print(f"\n账户: {account_name} ({account_id})")
        print(f"  总资产: {total_assets}")
        
        # 2. 计算该账户的买入总金额
        cursor.execute('''
            SELECT COALESCE(SUM(trade_amount), 0) as total_buy
            FROM trade_record 
            WHERE account_id = ? AND trade_type = '买入'
        ''', (account_id,))
        buy_result = cursor.fetchone()
        total_buy = buy_result['total_buy'] if buy_result else 0
        
        # 3. 计算该账户的卖出总金额
        cursor.execute('''
            SELECT COALESCE(SUM(trade_amount), 0) as total_sell
            FROM trade_record 
            WHERE account_id = ? AND trade_type = '卖出'
        ''', (account_id,))
        sell_result = cursor.fetchone()
        total_sell = sell_result['total_sell'] if sell_result else 0
        
        print(f"  买入总金额: {total_buy}")
        print(f"  卖出总金额: {total_sell}")
        
        # 4. 计算当前市值（买入 - 卖出）
        market_value = total_buy - total_sell
        
        # 5. 计算可用现金（总资产 - 市值）
        available_cash = total_assets - market_value
        
        print(f"  计算后市值: {market_value}")
        print(f"  计算后可用现金: {available_cash}")
        
        # 6. 更新账户
        cursor.execute('''
            UPDATE account_info 
            SET available_cash = ?, market_value = ?
            WHERE account_id = ?
        ''', (available_cash, market_value, account_id))
        
        print(f"  ✓ 账户已更新")
    
    conn.commit()
    
    # 7. 验证更新结果
    print("\n" + "=" * 50)
    print("验证更新结果")
    print("=" * 50)
    
    cursor.execute("SELECT * FROM account_info")
    accounts = cursor.fetchall()
    
    for account in accounts:
        print(f"\n{account['account_name']}:")
        print(f"  总资产: {account['total_assets']}")
        print(f"  可用现金: {account['available_cash']}")
        print(f"  市值: {account['market_value']}")
        print(f"  验证: {account['available_cash']} + {account['market_value']} = {account['available_cash'] + account['market_value']}")
    
    conn.close()
    print("\n修复完成!")

if __name__ == '__main__':
    fix_account_balance()
