import sqlite3

conn = sqlite3.connect('database/trading_system.db')
cursor = conn.cursor()

cursor.execute('DELETE FROM trade_record')
cursor.execute('DELETE FROM trade_execution_step')
cursor.execute('DELETE FROM trade_plan')
cursor.execute("DELETE FROM account_info WHERE account_id != 'ACC001'")

conn.commit()
print('数据清除完成')
conn.close()
