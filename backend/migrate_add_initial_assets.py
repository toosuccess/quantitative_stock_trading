import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), 'database', 'trading_system.db')

conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

try:
    cursor.execute("PRAGMA table_info(account_info)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if 'initial_assets' not in columns:
        print("添加 initial_assets 字段...")
        cursor.execute("ALTER TABLE account_info ADD COLUMN initial_assets DECIMAL(20,2) DEFAULT 0.00")
        
        cursor.execute("SELECT account_id, total_assets FROM account_info")
        accounts = cursor.fetchall()
        
        for account in accounts:
            cursor.execute(
                "UPDATE account_info SET initial_assets = ? WHERE account_id = ?",
                (account['total_assets'], account['account_id'])
            )
        
        conn.commit()
        print("✓ initial_assets 字段添加成功")
    else:
        print("initial_assets 字段已存在")
    
    cursor.execute("SELECT account_id, account_name, total_assets, initial_assets FROM account_info")
    accounts = cursor.fetchall()
    print("\n账号信息:")
    for account in accounts:
        print(f"  {account['account_name']}: 总资产={account['total_assets']}, 初始资产={account['initial_assets']}")

except Exception as e:
    print(f"迁移失败: {e}")
    conn.rollback()
finally:
    conn.close()
