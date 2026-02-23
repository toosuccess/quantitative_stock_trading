"""
添加评分明细字段到数据库
"""

import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), 'database', 'trading_system.db')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 检查表结构
cursor.execute("PRAGMA table_info(score_record)")
columns = cursor.fetchall()
column_names = [col[1] for col in columns]

print("当前字段:", column_names)

# 需要添加的字段
new_columns = [
    ('technical_detail', 'TEXT'),
    ('fundamental_detail', 'TEXT'),
    ('news_detail', 'TEXT'),
    ('policy_detail', 'TEXT'),
    ('deduction_detail', 'TEXT'),
]

# 添加字段
for col_name, col_type in new_columns:
    if col_name not in column_names:
        try:
            cursor.execute(f"ALTER TABLE score_record ADD COLUMN {col_name} {col_type}")
            print(f"添加字段: {col_name}")
        except Exception as e:
            print(f"添加字段 {col_name} 失败: {e}")

conn.commit()

# 验证
cursor.execute("PRAGMA table_info(score_record)")
columns = cursor.fetchall()
print("\n更新后字段:", [col[1] for col in columns])

conn.close()
