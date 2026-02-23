import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), 'database', 'trading_system.db')

conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

try:
    cursor.execute("SELECT account_id, account_name, total_assets, initial_assets FROM account_info")
    accounts = cursor.fetchall()
    
    print("修复 initial_assets 字段...")
    
    for account in accounts:
        cursor.execute(
            "UPDATE account_info SET initial_assets = ? WHERE account_id = ?",
            (account['total_assets'], account['account_id'])
        )
        print(f"  {account['account_name']}: initial_assets = {account['total_assets']}")
    
    conn.commit()
    print("\n✓ 修复成功")
    
    cursor.execute("SELECT account_id, account_name, total_assets, initial_assets FROM account_info")
    accounts = cursor.fetchall()
    print("\n账号信息:")
    for account in accounts:
        profit_loss = account['total_assets'] - account['initial_assets']
        print(f"  {account['account_name']}: 总资产={account['total_assets']}, 初始资产={account['initial_assets']}, 盈亏={profit_loss}")

except Exception as e:
    print(f"修复失败: {e}")
    conn.rollback()
finally:
    conn.close()
