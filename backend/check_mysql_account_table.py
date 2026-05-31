
import pymysql
from datetime import date, datetime

MYSQL_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'root',
    'password': '123456',
    'database': 'trading_system',
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
}

def check_account_table():
    conn = pymysql.connect(**MYSQL_CONFIG)
    cursor = conn.cursor()
    
    try:
        print("=== 检查 account_info 表结构 ===")
        
        cursor.execute("SHOW COLUMNS FROM account_info")
        columns = cursor.fetchall()
        print("\n表字段:")
        for col in columns:
            print(f"  {col['Field']}: {col['Type']}")
        
        has_initial = any(col['Field'] == 'initial_assets' for col in columns)
        print(f"\nhas_initial_assets: {has_initial}")
        
        print("\n=== 现有账户数据 ===")
        cursor.execute("SELECT account_id, account_name, total_assets, available_cash, market_value, profit_loss FROM account_info")
        accounts = cursor.fetchall()
        for acc in accounts:
            print(acc)
        
        if not has_initial:
            print("\n添加 initial_assets 字段...")
            try:
                cursor.execute("ALTER TABLE account_info ADD COLUMN initial_assets DECIMAL(20,2) DEFAULT 0.00 COMMENT '初始资金'")
                print("字段添加成功")
            except Exception as e:
                print(f"字段可能已存在: {e}")
            
            print("\n初始化 initial_assets 为当前 total_assets...")
            cursor.execute("SELECT account_id, total_assets FROM account_info")
            accounts = cursor.fetchall()
            for acc in accounts:
                if acc['total_assets'] and acc['total_assets'] > 0:
                    cursor.execute(
                        "UPDATE account_info SET initial_assets = %s WHERE account_id = %s",
                        (acc['total_assets'], acc['account_id'])
                    )
            conn.commit()
            print("初始化完成")
        
        print("\n=== 最终账户数据 ===")
        cursor.execute("SELECT account_id, account_name, total_assets, available_cash, market_value, profit_loss, initial_assets FROM account_info")
        accounts = cursor.fetchall()
        for acc in accounts:
            print(acc)
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()

if __name__ == "__main__":
    check_account_table()
