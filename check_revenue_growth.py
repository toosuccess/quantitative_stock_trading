import sqlite3
import json

conn = sqlite3.connect('backend/database/trading_system.db')
cursor = conn.cursor()

# 查询泸州老窖的评分记录
cursor.execute('''
    SELECT stock_code, stock_name, fundamental_detail 
    FROM score_record 
    WHERE stock_code = '000568' 
    ORDER BY id DESC 
    LIMIT 1
''')

row = cursor.fetchone()
if row:
    print(f'股票: {row[0]} {row[1]}')
    detail = json.loads(row[2])
    print('详细数据:')
    print(json.dumps(detail, indent=2, ensure_ascii=False))
else:
    print('未找到评分记录')

conn.close()
