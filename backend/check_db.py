import sqlite3

# 连接数据库
conn = sqlite3.connect('database/trading_system.db')
cursor = conn.cursor()

# 查看所有表
print('数据库中的表:')
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
for table in tables:
    print(f'- {table[0]}')

# 查看 trade_record 表的结构
print('\ntrade_record 表结构:')
cursor.execute("PRAGMA table_info(trade_record)")
columns = cursor.fetchall()
for column in columns:
    print(f'- {column[1]}: {column[2]}')

# 查看 trade_record 表的记录数量
print('\ntrade_record 表记录数量:')
cursor.execute("SELECT COUNT(*) FROM trade_record")
count = cursor.fetchone()[0]
print(f'总记录数: {count}')

# 查看卖出记录
print('\n卖出记录:')
cursor.execute("SELECT * FROM trade_record WHERE trade_type = '卖出' LIMIT 5")
records = cursor.fetchall()
if records:
    for record in records:
        print(record)
else:
    print('没有卖出记录')

conn.close()