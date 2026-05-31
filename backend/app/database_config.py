"""
数据库配置文件
支持 SQLite 和 MySQL 切换
"""
import os

# 数据库类型: 'mysql' 或 'sqlite'
DB_TYPE = os.getenv('DB_TYPE', 'mysql')

# MySQL 配置
MYSQL_CONFIG = {
    'host': '118.25.137.191',
    'user': 'root',
    'password': 'Root@2026Mysql!',
    'database': 'stock',
    'charset': 'utf8mb4'
}

# SQLite 配置（保留作为备份）
SQLITE_CONFIG = {
    'db_path': os.getenv('SQLITE_DB_PATH', 'database/trading_system.db')
}


def get_db_config():
    """获取当前数据库配置"""
    if DB_TYPE == 'mysql':
        return {
            'type': 'mysql',
            'config': MYSQL_CONFIG
        }
    else:
        return {
            'type': 'sqlite',
            'config': SQLITE_CONFIG
        }


def create_connection():
    """创建数据库连接"""
    import pymysql
    import sqlite3
    
    if DB_TYPE == 'mysql':
        conn = pymysql.connect(**MYSQL_CONFIG)
        return conn
    else:
        conn = sqlite3.connect(SQLITE_CONFIG['db_path'])
        conn.row_factory = sqlite3.Row
        return conn
