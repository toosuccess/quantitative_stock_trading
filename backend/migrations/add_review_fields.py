"""
数据库迁移脚本：添加复审相关字段到stock_basic_info表
"""
import pymysql
from pymysql.cursors import DictCursor
import sys
import os

BACKEND_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app.database_config import MYSQL_CONFIG

def migrate_add_review_fields():
    """添加复审字段到stock_basic_info表"""
    
    conn = pymysql.connect(**MYSQL_CONFIG, cursorclass=DictCursor)
    cursor = conn.cursor()
    
    try:
        # 检查review_score列是否已存在
        cursor.execute("""
            SELECT COUNT(*) as cnt FROM information_schema.columns 
            WHERE table_schema = 'stock' 
            AND table_name = 'stock_basic_info' 
            AND column_name = 'review_score'
        """)
        result = cursor.fetchone()
        
        if result['cnt'] > 0:
            print("✅ 复审字段已存在，无需重复添加")
            return True
        
        print("🚀 开始添加复审字段...")
        
        # 添加4个复审字段
        alter_statements = [
            "ALTER TABLE stock_basic_info ADD COLUMN review_score DECIMAL(5,2) DEFAULT NULL COMMENT '复审得分'",
            "ALTER TABLE stock_basic_info ADD COLUMN review_opinion TEXT COMMENT '复审意见'",
            "ALTER TABLE stock_basic_info ADD COLUMN review_time DATETIME COMMENT '复审时间'",
            "ALTER TABLE stock_basic_info ADD COLUMN review_detail JSON COMMENT '复审详细信息'"
        ]
        
        for sql in alter_statements:
            try:
                cursor.execute(sql)
                print(f"✅ 执行成功: {sql[:50]}...")
            except Exception as e:
                if "Duplicate column" in str(e):
                    print(f"⚠️ 字段已存在，跳过: {sql[:50]}...")
                else:
                    raise e
        
        conn.commit()
        
        # 验证字段是否添加成功
        cursor.execute("""
            SELECT column_name, data_type, column_comment 
            FROM information_schema.columns 
            WHERE table_schema = 'stock' 
            AND table_name = 'stock_basic_info' 
            AND column_name LIKE 'review_%'
            ORDER BY ordinal_position
        """)
        columns = cursor.fetchall()
        
        print("\n" + "="*60)
        print("✅ 数据库迁移完成！新增字段如下：")
        print("="*60)
        for col in columns:
            print(f"  • {col['column_name']}: {col['data_type']} - {col['column_comment']}")
        print("="*60)
        
        return True
        
    except Exception as e:
        print(f"❌ 迁移失败: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    success = migrate_add_review_fields()
    sys.exit(0 if success else 1)
