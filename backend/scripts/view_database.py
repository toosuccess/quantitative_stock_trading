"""
SQLite数据库查看工具
"""
import sqlite3
import os
import sys

def view_database(db_path):
    """查看SQLite数据库内容"""
    if not os.path.exists(db_path):
        print(f'数据库文件不存在: {db_path}')
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print('=' * 60)
    print(f'数据库: {db_path}')
    print('=' * 60)
    print('\n数据库中的表:')
    for t in tables:
        print(f'  - {t[0]}')
    
    for table in tables:
        table_name = table[0]
        cursor.execute(f'SELECT COUNT(*) FROM {table_name}')
        count = cursor.fetchone()[0]
        print(f'\n{"=" * 60}')
        print(f'表: {table_name} (共{count}条记录)')
        print('=' * 60)
        
        cursor.execute(f'PRAGMA table_info({table_name})')
        columns = [col[1] for col in cursor.fetchall()]
        print(f'列名: {", ".join(columns)}')
        
        if count > 0:
            cursor.execute(f'SELECT * FROM {table_name} LIMIT 10')
            rows = cursor.fetchall()
            print('\n数据预览:')
            for i, row in enumerate(rows, 1):
                print(f'  [{i}] {row}')
        else:
            print('\n  (空表)')
    
    conn.close()

if __name__ == '__main__':
    db_path = sys.argv[1] if len(sys.argv) > 1 else 'test_trading_system.db'
    view_database(db_path)
