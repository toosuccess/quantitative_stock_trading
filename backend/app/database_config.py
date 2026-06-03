"""
数据库配置文件
支持 SQLite 和 MySQL 切换
敏感信息通过环境变量读取
"""
import os
from pathlib import Path

_env_file = Path(__file__).resolve().parent.parent.parent / '.env'
if _env_file.exists():
    from dotenv import load_dotenv
    load_dotenv(_env_file, override=True)

DB_TYPE = os.getenv('DB_TYPE', 'mysql')

MYSQL_CONFIG = {
    'host': os.getenv('MYSQL_HOST', '118.25.137.191'),
    'user': os.getenv('MYSQL_USER', 'root'),
    'password': os.getenv('MYSQL_PASSWORD', 'Root@2026Mysql!'),
    'database': os.getenv('MYSQL_DATABASE', 'stock'),
    'charset': 'utf8mb4',
    'port': int(os.getenv('MYSQL_PORT', '3306'))
}

SQLITE_CONFIG = {
    'db_path': os.getenv('SQLITE_DB_PATH', 'database/trading_system.db')
}


def get_db_config():
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
    import pymysql
    import sqlite3

    if DB_TYPE == 'mysql':
        conn = pymysql.connect(**MYSQL_CONFIG)
        return conn
    else:
        conn = sqlite3.connect(SQLITE_CONFIG['db_path'])
        conn.row_factory = sqlite3.Row
        return conn
