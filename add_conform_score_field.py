import pymysql
import sys
import os

# 添加后端目录到路径
backend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backend')
sys.path.insert(0, backend_dir)

from app.database_config import MYSQL_CONFIG

def add_conform_score_field():
    """添加 conform_score 字段到 stock_basic_info 表"""
    conn = pymysql.connect(**MYSQL_CONFIG)
    cursor = conn.cursor()
    
    try:
        # 检查字段是否存在
        cursor.execute('''
            SHOW COLUMNS FROM stock_basic_info LIKE 'conform_score'
        ''')
        result = cursor.fetchone()
        
        if result:
            print("✅ conform_score 字段已存在，无需添加")
        else:
            # 添加字段
            cursor.execute('''
                ALTER TABLE stock_basic_info 
                ADD COLUMN conform_score DECIMAL(10,2) DEFAULT NULL COMMENT '符合得分'
                AFTER review_detail
            ''')
            conn.commit()
            print("✅ 成功添加 conform_score 字段")
        
        print("\n📊 表结构信息：")
        cursor.execute('''
            SHOW COLUMNS FROM stock_basic_info
        ''')
        columns = cursor.fetchall()
        for col in columns:
            print(f"  - {col[0]}: {col[1]}")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ 操作失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    add_conform_score_field()
