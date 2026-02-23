"""
交易系统SQLite数据库初始化脚本
根据交易系统数据库设计说明创建7张核心表
"""
import sqlite3
import os
from datetime import datetime

def init_database(db_path='trading_system.db'):
    """
    初始化交易系统数据库
    
    Args:
        db_path: 数据库文件路径
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print(f"正在初始化数据库: {db_path}")
    
    # 1. 账户信息表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS account_info (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        account_id VARCHAR(50) NOT NULL UNIQUE,
        account_name VARCHAR(100) NOT NULL,
        account_type VARCHAR(20) NOT NULL,
        broker VARCHAR(50),
        total_assets DECIMAL(20,2) DEFAULT 0.00,
        initial_assets DECIMAL(20,2) DEFAULT 0.00,
        available_cash DECIMAL(20,2) DEFAULT 0.00,
        market_value DECIMAL(20,2) DEFAULT 0.00,
        profit_loss DECIMAL(20,2) DEFAULT 0.00,
        profit_loss_rate DECIMAL(10,4) DEFAULT 0.0000,
        risk_level VARCHAR(20),
        status VARCHAR(20) DEFAULT 'active',
        create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
        update_time DATETIME DEFAULT CURRENT_TIMESTAMP,
        remark TEXT
    )
    ''')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_account_id ON account_info(account_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_account_type ON account_info(account_type)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_status ON account_info(status)')
    print("✓ 账户信息表(account_info)创建成功")
    
    # 2. 股票基本信息表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS stock_basic_info (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        stock_code VARCHAR(20) NOT NULL UNIQUE,
        stock_name VARCHAR(50) NOT NULL,
        stock_abbr VARCHAR(20),
        exchange VARCHAR(10) NOT NULL,
        industry VARCHAR(100),
        sector VARCHAR(100),
        list_date DATE,
        total_shares BIGINT,
        float_shares BIGINT,
        market_cap DECIMAL(20,2),
        float_market_cap DECIMAL(20,2),
        pe_ratio DECIMAL(10,4),
        pb_ratio DECIMAL(10,4),
        ps_ratio DECIMAL(10,4),
        dividend_yield DECIMAL(10,4),
        status VARCHAR(20) DEFAULT 'normal',
        create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
        update_time DATETIME DEFAULT CURRENT_TIMESTAMP,
        remark TEXT
    )
    ''')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_stock_code ON stock_basic_info(stock_code)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_stock_name ON stock_basic_info(stock_name)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_exchange ON stock_basic_info(exchange)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_industry ON stock_basic_info(industry)')
    print("✓ 股票基本信息表(stock_basic_info)创建成功")
    
    # 3. 评分记录表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS score_record (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        stock_code VARCHAR(20) NOT NULL,
        stock_name VARCHAR(50) NOT NULL,
        score_date DATE NOT NULL,
        fundamental_score DECIMAL(10,4) DEFAULT 0.0000,
        fundamental_reason TEXT,
        technical_score DECIMAL(10,4) DEFAULT 0.0000,
        technical_reason TEXT,
        ma_score DECIMAL(10,4) DEFAULT 0.0000,
        macd_score DECIMAL(10,4) DEFAULT 0.0000,
        rsi_score DECIMAL(10,4) DEFAULT 0.0000,
        bollinger_score DECIMAL(10,4) DEFAULT 0.0000,
        volume_score DECIMAL(10,4) DEFAULT 0.0000,
        obv_score DECIMAL(10,4) DEFAULT 0.0000,
        total_score DECIMAL(10,4) DEFAULT 0.0000,
        composite_score DECIMAL(10,4) DEFAULT 0.0000,
        news_score DECIMAL(10,4) DEFAULT 0.0000,
        policy_score DECIMAL(10,4) DEFAULT 0.0000,
        deduction_score DECIMAL(10,4) DEFAULT 0.0000,
        rating VARCHAR(20),
        ma5 DECIMAL(10,4),
        ma10 DECIMAL(10,4),
        ma20 DECIMAL(10,4),
        ma60 DECIMAL(10,4),
        diff DECIMAL(10,4),
        dea DECIMAL(10,4),
        macd DECIMAL(10,4),
        rsi DECIMAL(10,4),
        bb_upper DECIMAL(10,4),
        bb_middle DECIMAL(10,4),
        bb_lower DECIMAL(10,4),
        close_price DECIMAL(10,4),
        volume BIGINT,
        turnover_rate DECIMAL(10,4),
        technical_detail TEXT,
        fundamental_detail TEXT,
        news_detail TEXT,
        policy_detail TEXT,
        deduction_detail TEXT,
        summary TEXT,
        is_leader INTEGER DEFAULT 0,
        create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
        update_time DATETIME DEFAULT CURRENT_TIMESTAMP,
        remark TEXT,
        UNIQUE(stock_code, score_date)
    )
    ''')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_sr_stock_code ON score_record(stock_code)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_score_date ON score_record(score_date)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_total_score ON score_record(total_score)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_rating ON score_record(rating)')
    print("✓ 评分记录表(score_record)创建成功")
    
    # 4. 交易计划表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS trade_plan (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        plan_id VARCHAR(50) NOT NULL UNIQUE,
        plan_name VARCHAR(100) NOT NULL,
        account_id VARCHAR(50) NOT NULL,
        stock_code VARCHAR(20) NOT NULL,
        stock_name VARCHAR(50) NOT NULL,
        score_record_id INTEGER,
        stop_loss_price DECIMAL(10,4),
        take_profit_price DECIMAL(10,4),
        planned_quantity INTEGER DEFAULT 0,
        planned_amount DECIMAL(20,2) DEFAULT 0.00,
        actual_quantity INTEGER DEFAULT 0,
        actual_amount DECIMAL(20,2) DEFAULT 0.00,
        avg_cost_price DECIMAL(10,4),
        profit_loss DECIMAL(20,2) DEFAULT 0.00,
        profit_loss_rate DECIMAL(10,4) DEFAULT 0.0000,
        plan_date DATE NOT NULL,
        status VARCHAR(20) DEFAULT 'pending',
        create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
        update_time DATETIME DEFAULT CURRENT_TIMESTAMP,
        remark TEXT
    )
    ''')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_plan_id ON trade_plan(plan_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_tp_account_id ON trade_plan(account_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_tp_stock_code ON trade_plan(stock_code)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_tp_status ON trade_plan(status)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_plan_date ON trade_plan(plan_date)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_score_record_id ON trade_plan(score_record_id)')
    print("✓ 交易计划表(trade_plan)创建成功")
    
    # 5. 交易执行步骤表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS trade_execution_step (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        step_id VARCHAR(50) NOT NULL UNIQUE,
        plan_id VARCHAR(50) NOT NULL,
        account_id VARCHAR(50) NOT NULL,
        stock_code VARCHAR(20) NOT NULL,
        stock_name VARCHAR(50) NOT NULL,
        trade_direction VARCHAR(20) NOT NULL,
        target_price DECIMAL(10,4),
        planned_quantity INTEGER DEFAULT 0,
        executed_quantity INTEGER DEFAULT 0,
        remaining_quantity INTEGER DEFAULT 0,
        actual_price DECIMAL(10,4),
        planned_date DATE NOT NULL,
        executed_date DATE,
        reason TEXT,
        status VARCHAR(20) DEFAULT 'pending',
        create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
        update_time DATETIME DEFAULT CURRENT_TIMESTAMP,
        remark TEXT
    )
    ''')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_step_id ON trade_execution_step(step_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_tes_plan_id ON trade_execution_step(plan_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_tes_account_id ON trade_execution_step(account_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_tes_stock_code ON trade_execution_step(stock_code)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_trade_direction ON trade_execution_step(trade_direction)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_tes_status ON trade_execution_step(status)')
    print("✓ 交易执行步骤表(trade_execution_step)创建成功")
    
    # 6. 交易记录表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS trade_record (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        record_id VARCHAR(50) NOT NULL UNIQUE,
        account_id VARCHAR(50) NOT NULL,
        stock_code VARCHAR(20) NOT NULL,
        stock_name VARCHAR(50) NOT NULL,
        plan_id VARCHAR(50),
        step_id VARCHAR(50),
        trade_type VARCHAR(20) NOT NULL,
        trade_direction VARCHAR(20),
        trade_price DECIMAL(10,4) NOT NULL,
        trade_quantity INTEGER NOT NULL,
        trade_amount DECIMAL(20,2) NOT NULL,
        commission DECIMAL(10,4) DEFAULT 0.0000,
        stamp_duty DECIMAL(10,4) DEFAULT 0.0000,
        trade_date DATE NOT NULL,
        trade_time TIME NOT NULL,
        order_number VARCHAR(50),
        broker_order_number VARCHAR(50),
        status VARCHAR(20) DEFAULT 'completed',
        create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
        update_time DATETIME DEFAULT CURRENT_TIMESTAMP,
        remark TEXT
    )
    ''')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_record_id ON trade_record(record_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_tr_account_id ON trade_record(account_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_tr_stock_code ON trade_record(stock_code)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_tr_plan_id ON trade_record(plan_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_step_id_tr ON trade_record(step_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_trade_type ON trade_record(trade_type)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_trade_date ON trade_record(trade_date)')
    print("✓ 交易记录表(trade_record)创建成功")
    
    # 7. 复盘记录表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS review_record (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        review_id VARCHAR(50) NOT NULL UNIQUE,
        plan_id VARCHAR(50) NOT NULL,
        account_id VARCHAR(50) NOT NULL,
        stock_code VARCHAR(20) NOT NULL,
        stock_name VARCHAR(50) NOT NULL,
        review_date DATE NOT NULL,
        review_type VARCHAR(20),
        review_result TEXT,
        execution_summary TEXT,
        profit_loss_analysis TEXT,
        reason_analysis TEXT,
        success_experience TEXT,
        failure_lesson TEXT,
        improvement_measures TEXT,
        emotion_status VARCHAR(20),
        emotion_impact TEXT,
        execution_score DECIMAL(5,2),
        strategy_score DECIMAL(5,2),
        overall_score DECIMAL(5,2),
        status VARCHAR(20) DEFAULT 'completed',
        create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
        update_time DATETIME DEFAULT CURRENT_TIMESTAMP,
        remark TEXT
    )
    ''')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_review_id ON review_record(review_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_rr_plan_id ON review_record(plan_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_rr_account_id ON review_record(account_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_rr_stock_code ON review_record(stock_code)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_review_date ON review_record(review_date)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_review_type ON review_record(review_type)')
    print("✓ 复盘记录表(review_record)创建成功")
    
    conn.commit()
    conn.close()
    
    print(f"\n数据库初始化完成！文件位置: {os.path.abspath(db_path)}")
    return True

def verify_database(db_path='trading_system.db'):
    """
    验证数据库表结构
    
    Args:
        db_path: 数据库文件路径
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("\n验证数据库表结构:")
    print("=" * 50)
    
    tables = ['account_info', 'stock_basic_info', 'score_record', 
              'trade_plan', 'trade_execution_step', 'trade_record', 'review_record']
    
    for table in tables:
        cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
        result = cursor.fetchone()
        if result:
            cursor.execute(f"PRAGMA table_info({table})")
            columns = cursor.fetchall()
            print(f"\n✓ {table}: {len(columns)}个字段")
        else:
            print(f"\n✗ {table}: 表不存在")
    
    conn.close()
    return True

def insert_test_data(db_path='trading_system.db'):
    """
    插入测试数据验证CRUD操作
    
    Args:
        db_path: 数据库文件路径
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("\n插入测试数据:")
    print("=" * 50)
    
    # 测试账户信息
    cursor.execute('''
    INSERT OR REPLACE INTO account_info 
    (account_id, account_name, account_type, broker, total_assets, available_cash)
    VALUES (?, ?, ?, ?, ?, ?)
    ''', ('ACC001', '测试账户', '模拟', '国金证券', 100000.00, 100000.00))
    print("✓ 插入测试账户: ACC001")
    
    # 测试股票信息
    cursor.execute('''
    INSERT OR REPLACE INTO stock_basic_info 
    (stock_code, stock_name, exchange, industry, sector)
    VALUES (?, ?, ?, ?, ?)
    ''', ('002065', '东华软件', 'SZ', '软件服务', '计算机应用'))
    print("✓ 插入测试股票: 002065 东华软件")
    
    # 测试评分记录
    cursor.execute('''
    INSERT OR REPLACE INTO score_record 
    (stock_code, stock_name, score_date, total_score, rating, close_price)
    VALUES (?, ?, ?, ?, ?, ?)
    ''', ('002065', '东华软件', '2026-02-17', 100.0000, '强烈推荐', 9.62))
    print("✓ 插入测试评分: 002065 评分100.0000")
    
    # 测试交易计划
    cursor.execute('''
    INSERT OR REPLACE INTO trade_plan 
    (plan_id, plan_name, account_id, stock_code, stock_name, plan_date, status)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', ('PLAN001', '买入东华软件', 'ACC001', '002065', '东华软件', '2026-02-17', 'pending'))
    print("✓ 插入测试计划: PLAN001")
    
    conn.commit()
    conn.close()
    
    print("\n测试数据插入完成！")
    return True

if __name__ == "__main__":
    db_path = 'trading_system.db'
    
    # 初始化数据库
    init_database(db_path)
    
    # 验证表结构
    verify_database(db_path)
    
    # 插入测试数据
    insert_test_data(db_path)
    
    print("\n" + "=" * 50)
    print("数据库初始化完成！")
    print("=" * 50)
