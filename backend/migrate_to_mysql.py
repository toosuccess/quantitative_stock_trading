"""
SQLite 数据迁移到 MySQL 脚本
根据 SQLite 实际表结构动态生成 MySQL 表
"""
import sqlite3
import pymysql

# MySQL 配置
MYSQL_CONFIG = {
    'host': '118.25.137.191',
    'user': 'root',
    'password': 'Root@2026Mysql!',
    'database': 'stock',
    'charset': 'utf8mb4'
}

# SQLite 数据库路径
SQLITE_DB = 'database/trading_system.db'

# SQLite 类型到 MySQL 类型映射
TYPE_MAP = {
    'INTEGER': 'INT',
    'INT': 'INT',
    'REAL': 'DECIMAL(20,4)',
    'FLOAT': 'DECIMAL(20,4)',
    'BLOB': 'BLOB',
    'NUMERIC': 'DECIMAL(20,4)',
}

# 表中文注释
TABLE_COMMENTS = {
    'account_info': '账户信息表',
    'stock_basic_info': '股票基本信息表',
    'score_record': '评分记录表',
    'trade_plan': '交易计划表',
    'trade_execution_step': '交易执行步骤表',
    'trade_record': '交易记录表',
    'review_record': '复盘记录表',
    'fundamental_data_cache': '财务数据缓存表',
    'sqlite_sequence': None,  # 跳过
}

# 列中文注释
COLUMN_COMMENTS = {
    'account_info': {
        'id': '主键ID',
        'account_id': '账户编号',
        'account_name': '账户名称',
        'account_type': '账户类型',
        'broker': '券商',
        'total_assets': '总资产',
        'initial_assets': '初始资产',
        'available_cash': '可用资金',
        'market_value': '市值',
        'profit_loss': '盈亏',
        'profit_loss_rate': '盈亏率',
        'risk_level': '风险等级',
        'status': '状态',
        'create_time': '创建时间',
        'update_time': '更新时间',
        'remark': '备注',
    },
    'stock_basic_info': {
        'id': '主键ID',
        'stock_code': '股票代码',
        'stock_name': '股票名称',
        'stock_abbr': '股票简称',
        'exchange': '交易所',
        'industry': '所属行业',
        'sector': '所属板块',
        'list_date': '上市日期',
        'total_shares': '总股本',
        'float_shares': '流通股本',
        'market_cap': '总市值',
        'float_market_cap': '流通市值',
        'pe_ratio': '市盈率',
        'pb_ratio': '市净率',
        'ps_ratio': '市销率',
        'dividend_yield': '股息率',
        'status': '状态',
        'is_favorite': '是否收藏',
        'create_time': '创建时间',
        'update_time': '更新时间',
        'remark': '备注',
    },
    'score_record': {
        'id': '主键ID',
        'stock_code': '股票代码',
        'stock_name': '股票名称',
        'score_date': '评分日期',
        'fundamental_score': '基本面评分',
        'fundamental_reason': '基本面原因',
        'technical_score': '技术面评分',
        'technical_reason': '技术面原因',
        'ma_score': '均线评分',
        'macd_score': 'MACD评分',
        'rsi_score': 'RSI评分',
        'bollinger_score': '布林带评分',
        'volume_score': '成交量评分',
        'obv_score': 'OBV评分',
        'total_score': '综合评分',
        'composite_score': '综合评分',
        'news_score': '新闻评分',
        'policy_score': '政策评分',
        'deduction_score': '扣分',
        'rating': '评级',
        'ma5': 'MA5',
        'ma10': 'MA10',
        'ma20': 'MA20',
        'ma60': 'MA60',
        'diff': 'DIFF',
        'dea': 'DEA',
        'macd': 'MACD',
        'rsi': 'RSI',
        'bb_upper': '布林带上轨',
        'bb_middle': '布林带中轨',
        'bb_lower': '布林带下轨',
        'close_price': '收盘价',
        'volume': '成交量',
        'turnover_rate': '换手率',
        'technical_detail': '技术面详情',
        'fundamental_detail': '基本面详情',
        'news_detail': '新闻详情',
        'policy_detail': '政策详情',
        'deduction_detail': '扣分详情',
        'summary': '总结',
        'is_leader': '是否龙头',
        'create_time': '创建时间',
        'update_time': '更新时间',
        'remark': '备注',
    },
    'trade_plan': {
        'id': '主键ID',
        'plan_id': '计划编号',
        'plan_name': '计划名称',
        'account_id': '账户编号',
        'stock_code': '股票代码',
        'stock_name': '股票名称',
        'score_record_id': '评分记录ID',
        'stop_loss_price': '止损价格',
        'take_profit_price': '止盈价格',
        'planned_quantity': '计划数量',
        'planned_amount': '计划金额',
        'actual_quantity': '实际数量',
        'actual_amount': '实际金额',
        'avg_cost_price': '平均成本价',
        'profit_loss': '盈亏',
        'profit_loss_rate': '盈亏率',
        'plan_date': '计划日期',
        'status': '状态',
        'create_time': '创建时间',
        'update_time': '更新时间',
        'remark': '备注',
    },
    'trade_execution_step': {
        'id': '主键ID',
        'step_id': '步骤编号',
        'plan_id': '计划编号',
        'account_id': '账户编号',
        'stock_code': '股票代码',
        'stock_name': '股票名称',
        'trade_direction': '交易方向',
        'target_price': '目标价格',
        'planned_quantity': '计划数量',
        'executed_quantity': '已执行数量',
        'remaining_quantity': '剩余数量',
        'actual_price': '实际价格',
        'planned_date': '计划日期',
        'executed_date': '执行日期',
        'reason': '理由',
        'status': '状态',
        'create_time': '创建时间',
        'update_time': '更新时间',
        'remark': '备注',
    },
    'trade_record': {
        'id': '主键ID',
        'record_id': '记录编号',
        'account_id': '账户编号',
        'stock_code': '股票代码',
        'stock_name': '股票名称',
        'plan_id': '计划编号',
        'step_id': '步骤编号',
        'trade_type': '交易类型',
        'trade_direction': '交易方向',
        'trade_price': '交易价格',
        'trade_quantity': '交易数量',
        'trade_amount': '交易金额',
        'commission': '佣金',
        'stamp_duty': '印花税',
        'trade_date': '交易日期',
        'trade_time': '交易时间',
        'order_number': '订单号',
        'broker_order_number': '券商订单号',
        'status': '状态',
        'create_time': '创建时间',
        'update_time': '更新时间',
        'remark': '备注',
    },
    'review_record': {
        'id': '主键ID',
        'review_id': '复盘编号',
        'plan_id': '计划编号',
        'account_id': '账户编号',
        'stock_code': '股票代码',
        'stock_name': '股票名称',
        'review_date': '复盘日期',
        'review_type': '复盘类型',
        'review_result': '复盘结论',
        'execution_summary': '执行总结',
        'profit_loss_analysis': '盈亏分析',
        'reason_analysis': '原因分析',
        'success_experience': '成功经验',
        'failure_lesson': '失败教训',
        'improvement_measures': '改进措施',
        'emotion_status': '情绪状态',
        'emotion_impact': '情绪影响',
        'execution_score': '执行评分',
        'strategy_score': '策略评分',
        'overall_score': '综合评分',
        'status': '状态',
        'create_time': '创建时间',
        'update_time': '更新时间',
        'remark': '备注',
    },
    'fundamental_data_cache': {
        'stock_code': '股票代码',
        'pe': '市盈率',
        'pb': '市净率',
        'roe': 'ROE',
        'net_profit_growth': '净利润增长率',
        'revenue_growth': '营收增长率',
        'debt_ratio': '资产负债率',
        'gross_margin': '毛利率',
        'operating_margin': '营业利润率',
        'current_ratio': '流动比率',
        'asset_turnover': '资产周转率',
        'cash_flow_ratio': '现金流比率',
        'update_time': '更新时间',
    },
}


def sqlite_type_to_mysql(sqlite_type, is_pk=False, has_default=False):
    """SQLite 类型转 MySQL 类型"""
    if not sqlite_type:
        if has_default:
            return 'VARCHAR(255)'
        return 'VARCHAR(255)' if is_pk else 'TEXT'
    
    type_upper = sqlite_type.upper()
    
    # 注意：必须先检查 DATETIME，因为 'DATETIME' 包含 'TIME' 和 'DATE'
    if 'DATETIME' in type_upper:
        return 'DATETIME'
    if 'DECIMAL' in type_upper or 'NUMERIC' in type_upper:
        return 'DECIMAL(20,4)'
    if 'INT' in type_upper:
        return 'INT'
    if 'REAL' in type_upper or 'FLOAT' in type_upper or 'DOUBLE' in type_upper:
        return 'DECIMAL(20,4)'
    if 'BLOB' in type_upper:
        return 'BLOB'
    if 'TEXT' in type_upper or 'CHAR' in type_upper or 'VARCHAR' in type_upper or 'STRING' in type_upper:
        if has_default:
            return 'VARCHAR(255)'
        return 'VARCHAR(255)' if is_pk else 'TEXT'
    if 'TIME' in type_upper:
        return 'TIME'
    if 'DATE' in type_upper:
        return 'DATE'
    if 'BOOL' in type_upper:
        return 'TINYINT(1)'
    
    return TYPE_MAP.get(type_upper, 'TEXT')


def get_mysql_column_def(col_info, table_name, is_pk=False):
    """生成 MySQL 列定义"""
    col_name = col_info[1]
    col_type = col_info[2]
    not_null = col_info[3]
    default_val = col_info[4]
    pk = col_info[5]
    
    # 根据列名特殊处理：仅当 SQLite 没有明确类型时才根据列名推断
    # 如果 SQLite 已经有明确类型（如 DATETIME、DATE、TIME），则保留原类型
    if not col_type:
        if col_name == 'trade_time':
            col_type = 'TIME'
        elif col_name in ('create_time', 'update_time'):
            col_type = 'DATETIME'
        elif col_name.endswith('_date'):
            col_type = 'DATE'
    
    # 判断是否有默认值
    has_default = default_val is not None and not pk and default_val.upper() != 'NULL' if isinstance(default_val, str) else default_val is not None and not pk
    
    mysql_type = sqlite_type_to_mysql(col_type, is_pk=is_pk or bool(pk), has_default=has_default)
    
    # 列名处理
    col_def = f"  `{col_name}` {mysql_type}"
    
    # NOT NULL
    if not_null and not pk:
        col_def += " NOT NULL"
    
    # 默认值（修复双引号问题）
    if default_val is not None and not pk:
        if isinstance(default_val, str):
            if default_val.upper() == 'CURRENT_TIMESTAMP':
                col_def += " DEFAULT CURRENT_TIMESTAMP"
            elif default_val.upper() == 'NULL':
                pass
            else:
                # 清理多余引号
                clean_default = default_val.strip("'\"")
                col_def += f" DEFAULT '{clean_default}'"
        elif isinstance(default_val, (int, float)):
            col_def += f" DEFAULT {default_val}"
    
    # 注释
    comments = COLUMN_COMMENTS.get(table_name, {})
    if col_name in comments:
        col_def += f" COMMENT '{comments[col_name]}'"
    
    return col_def


def create_mysql_table_from_sqlite(sqlite_cursor, mysql_cursor, table_name):
    """根据 SQLite 表结构创建 MySQL 表"""
    # 获取 SQLite 列信息
    columns = sqlite_cursor.execute(f"PRAGMA table_info({table_name})").fetchall()
    
    if not columns:
        return False
    
    # 调试输出
    print(f"  [DEBUG] {table_name} 列信息:")
    for col in columns:
        print(f"    {col[1]}: type='{col[2]}', not_null={col[3]}, default='{col[4]}', pk={col[5]}")
    
    # 查找主键
    pk_col = None
    pk_col_type = ''
    for col in columns:
        if col[5]:  # pk
            pk_col = col[1]
            pk_col_type = col[2]
            break
    
    # 构建 CREATE TABLE 语句
    col_defs = []
    for col in columns:
        is_pk = (col[1] == pk_col)
        col_def = get_mysql_column_def(col, table_name, is_pk=is_pk)
        col_defs.append(col_def)
    
    # 主键
    if pk_col:
        col_defs.append(f"  PRIMARY KEY (`{pk_col}`)")
    
    # 自动递增
    if pk_col and pk_col_type.upper() in ('INTEGER', 'INT'):
        for i, col in enumerate(columns):
            if col[1] == pk_col:
                col_defs[i] = col_defs[i].replace(' INT ', ' INT AUTO_INCREMENT ')
                break
    
    comment = TABLE_COMMENTS.get(table_name, table_name)
    
    create_sql = f"CREATE TABLE `{table_name}` (\n" + ",\n".join(col_defs) + f"\n) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='{comment}'"
    
    try:
        mysql_cursor.execute(f"DROP TABLE IF EXISTS `{table_name}`")
        mysql_cursor.execute(create_sql)
        print(f"  创建表成功: {table_name}")
        return True
    except Exception as e:
        print(f"  创建表失败 {table_name}: {e}")
        print(f"  SQL: {create_sql}")
        return False


def migrate_data(sqlite_cursor, mysql_cursor, table_name):
    """迁移表数据"""
    # 获取数据
    sqlite_cursor.execute(f"SELECT * FROM {table_name}")
    data = sqlite_cursor.fetchall()
    
    if not data:
        print(f"  无数据，跳过")
        return
    
    # 获取列信息
    columns = sqlite_cursor.execute(f"PRAGMA table_info({table_name})").fetchall()
    column_names = [col[1] for col in columns]
    
    # 移除 id 列
    if 'id' in column_names:
        id_index = column_names.index('id')
        insert_columns = [c for c in column_names if c != 'id']
        filtered_data = [tuple(row[i] for i in range(len(row)) if i != id_index) for row in data]
    else:
        insert_columns = column_names
        filtered_data = [tuple(row) for row in data]
    
    # 构建 INSERT 语句
    placeholders = ', '.join(['%s'] * len(insert_columns))
    columns_str = ', '.join([f'`{c}`' for c in insert_columns])
    insert_sql = f"INSERT INTO `{table_name}` ({columns_str}) VALUES ({placeholders})"
    
    try:
        mysql_cursor.executemany(insert_sql, filtered_data)
        print(f"  成功迁移 {len(filtered_data)} 条记录")
    except Exception as e:
        print(f"  迁移失败: {e}")
        import traceback
        traceback.print_exc()


def main():
    """主函数"""
    print("=" * 60)
    print("SQLite 数据迁移到 MySQL")
    print("=" * 60)
    
    # 连接 SQLite
    sqlite_conn = sqlite3.connect(SQLITE_DB)
    sqlite_cursor = sqlite_conn.cursor()
    
    # 连接 MySQL
    mysql_conn = pymysql.connect(**MYSQL_CONFIG)
    mysql_cursor = mysql_conn.cursor()
    
    try:
        # 获取 SQLite 中所有表
        sqlite_cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in sqlite_cursor.fetchall()]
        tables = [t for t in tables if t != 'sqlite_sequence']
        
        print(f"\n找到 {len(tables)} 个表: {tables}")
        
        # 1. 创建表结构
        print("\n[步骤 1/2] 创建 MySQL 表结构...")
        for table in tables:
            create_mysql_table_from_sqlite(sqlite_cursor, mysql_cursor, table)
        
        mysql_conn.commit()
        
        # 2. 迁移数据
        print("\n[步骤 2/2] 迁移数据...")
        for table in tables:
            print(f"\n迁移表: {table}")
            migrate_data(sqlite_cursor, mysql_cursor, table)
        
        mysql_conn.commit()
        
        print("\n" + "=" * 60)
        print("数据迁移完成！")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n迁移失败: {e}")
        import traceback
        traceback.print_exc()
        mysql_conn.rollback()
    finally:
        sqlite_conn.close()
        mysql_conn.close()


if __name__ == '__main__':
    main()
