"""
交易系统数据库操作示例（优化版）
根据新ER图优化：新增复盘记录表，交易计划明细改为交易执行步骤
"""
import sqlite3
import pymysql
from datetime import datetime, date
from typing import List, Dict, Optional, Tuple, List

class TradingDatabase:
    """交易系统数据库操作类"""
    
    def __init__(self, db_type='sqlite', db_config=None):
        """
        初始化数据库连接
        
        Args:
            db_type: 数据库类型（sqlite/mysql）
            db_config: 数据库配置
        """
        self.db_type = db_type
        self.db_config = db_config or {}
        self.conn = None
        self.cursor = None
        
    def connect(self):
        """连接数据库"""
        try:
            if self.db_type == 'sqlite':
                db_path = self.db_config.get('db_path', 'trading_system.db')
                self.conn = sqlite3.connect(db_path)
                self.conn.row_factory = sqlite3.Row
            elif self.db_type == 'mysql':
                self.conn = pymysql.connect(
                    host=self.db_config.get('host', 'localhost'),
                    port=self.db_config.get('port', 3306),
                    user=self.db_config.get('user', 'root'),
                    password=self.db_config.get('password', ''),
                    database=self.db_config.get('database', 'trading_system'),
                    charset='utf8mb4'
                )
            self.cursor = self.conn.cursor()
            print("数据库连接成功")
            return True
        except Exception as e:
            print(f"数据库连接失败: {e}")
            return False
    
    def disconnect(self):
        """断开数据库连接"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
        print("数据库连接已关闭")
    
    def execute(self, sql, params=None):
        """
        执行SQL语句
        
        Args:
            sql: SQL语句
            params: 参数
        """
        try:
            self.cursor.execute(sql, params or ())
            self.conn.commit()
            return True
        except Exception as e:
            print(f"SQL执行失败: {e}")
            self.conn.rollback()
            return False
    
    def fetchall(self):
        """获取所有查询结果"""
        return self.cursor.fetchall()
    
    def fetchone(self):
        """获取单条查询结果"""
        return self.cursor.fetchone()
    
    def insert_account_info(self, account_info: Dict) -> bool:
        """
        插入账户信息
        
        Args:
            account_info: 账户信息字典
        
        Returns:
            bool: 是否成功
        """
        sql = """
        INSERT INTO account_info 
        (account_id, account_name, account_type, broker, total_assets, 
        available_cash, market_value, profit_loss, profit_loss_rate, 
        risk_level, status, remark)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        params = (
            account_info.get('account_id'),
            account_info.get('account_name'),
            account_info.get('account_type'),
            account_info.get('broker'),
            account_info.get('total_assets', 0.00),
            account_info.get('available_cash', 0.00),
            account_info.get('market_value', 0.00),
            account_info.get('profit_loss', 0.00),
            account_info.get('profit_loss_rate', 0.0000),
            account_info.get('risk_level'),
            account_info.get('status', 'active'),
            account_info.get('remark')
        )
        return self.execute(sql, params)
    
    def insert_stock_basic_info(self, stock_info: Dict) -> bool:
        """
        插入股票基本信息
        
        Args:
            stock_info: 股票信息字典
        
        Returns:
            bool: 是否成功
        """
        sql = """
        INSERT INTO stock_basic_info 
        (stock_code, stock_name, stock_abbr, exchange, industry, 
        sector, list_date, total_shares, float_shares, market_cap, 
        float_market_cap, pe_ratio, pb_ratio, ps_ratio, dividend_yield, status, remark)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        params = (
            stock_info.get('stock_code'),
            stock_info.get('stock_name'),
            stock_info.get('stock_abbr'),
            stock_info.get('exchange'),
            stock_info.get('industry'),
            stock_info.get('sector'),
            stock_info.get('list_date'),
            stock_info.get('total_shares'),
            stock_info.get('float_shares'),
            stock_info.get('market_cap'),
            stock_info.get('float_market_cap'),
            stock_info.get('pe_ratio'),
            stock_info.get('pb_ratio'),
            stock_info.get('ps_ratio'),
            stock_info.get('dividend_yield'),
            stock_info.get('status', 'normal'),
            stock_info.get('remark')
        )
        return self.execute(sql, params)
    
    def insert_score_record(self, score_record: Dict) -> bool:
        """
        插入评分记录
        
        Args:
            score_record: 评分记录字典
        
        Returns:
            bool: 是否成功
        """
        sql = """
        INSERT INTO score_record 
        (stock_code, stock_name, score_date, 
        fundamental_score, fundamental_reason, 
        technical_score, technical_reason,
        ma_score, macd_score, rsi_score, bollinger_score, 
        volume_score, obv_score,
        total_score, rating,
        ma5, ma10, ma20, ma60,
        diff, dea, macd, rsi,
        bb_upper, bb_middle, bb_lower,
        close_price, volume, turnover_rate, remark)
        VALUES (%s, %s, %s, 
        %s, %s, %s, %s,
        %s, %s, %s, %s, %s, %s,
        %s, %s,
        %s, %s, %s, %s,
        %s, %s, %s, %s,
        %s, %s, %s, %s, %s, %s)
        """
        params = (
            score_record.get('stock_code'),
            score_record.get('stock_name'),
            score_record.get('score_date', date.today()),
            score_record.get('fundamental_score', 0.0000),
            score_record.get('fundamental_reason'),
            score_record.get('technical_score', 0.0000),
            score_record.get('technical_reason'),
            score_record.get('ma_score', 0.0000),
            score_record.get('macd_score', 0.0000),
            score_record.get('rsi_score', 0.0000),
            score_record.get('bollinger_score', 0.0000),
            score_record.get('volume_score', 0.0000),
            score_record.get('obv_score', 0.0000),
            score_record.get('total_score', 0.0000),
            score_record.get('rating'),
            score_record.get('ma5'),
            score_record.get('ma10'),
            score_record.get('ma20'),
            score_record.get('ma60'),
            score_record.get('diff'),
            score_record.get('dea'),
            score_record.get('macd'),
            score_record.get('rsi'),
            score_record.get('bb_upper'),
            score_record.get('bb_middle'),
            score_record.get('bb_lower'),
            score_record.get('close_price'),
            score_record.get('volume'),
            score_record.get('turnover_rate'),
            score_record.get('remark')
        )
        return self.execute(sql, params)
    
    def insert_trade_plan(self, trade_plan: Dict) -> bool:
        """
        插入交易计划
        
        Args:
            trade_plan: 交易计划字典
        
        Returns:
            bool: 是否成功
        """
        sql = """
        INSERT INTO trade_plan 
        (plan_id, plan_name, account_id, stock_code, stock_name,
        score_record_id, stop_loss_price, take_profit_price,
        planned_quantity, planned_amount,
        actual_quantity, actual_amount, avg_cost_price, profit_loss, profit_loss_rate,
        plan_date, status, remark)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        params = (
            trade_plan.get('plan_id'),
            trade_plan.get('plan_name'),
            trade_plan.get('account_id'),
            trade_plan.get('stock_code'),
            trade_plan.get('stock_name'),
            trade_plan.get('score_record_id'),
            trade_plan.get('stop_loss_price'),
            trade_plan.get('take_profit_price'),
            trade_plan.get('planned_quantity', 0),
            trade_plan.get('planned_amount', 0.00),
            trade_plan.get('actual_quantity', 0),
            trade_plan.get('actual_amount', 0.00),
            trade_plan.get('avg_cost_price'),
            trade_plan.get('profit_loss', 0.00),
            trade_plan.get('profit_loss_rate', 0.0000),
            trade_plan.get('plan_date', date.today()),
            trade_plan.get('status', 'pending'),
            trade_plan.get('remark')
        )
        return self.execute(sql, params)
    
    def insert_trade_execution_step(self, execution_step: Dict) -> bool:
        """
        插入交易执行步骤
        
        Args:
            execution_step: 交易执行步骤字典
        
        Returns:
            bool: 是否成功
        """
        sql = """
        INSERT INTO trade_execution_step 
        (step_id, plan_id, account_id, stock_code, stock_name,
        trade_direction, target_price,
        planned_quantity, executed_quantity, remaining_quantity,
        actual_price, planned_date, executed_date, reason, status, remark)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        params = (
            execution_step.get('step_id'),
            execution_step.get('plan_id'),
            execution_step.get('account_id'),
            execution_step.get('stock_code'),
            execution_step.get('stock_name'),
            execution_step.get('trade_direction'),
            execution_step.get('target_price'),
            execution_step.get('planned_quantity', 0),
            execution_step.get('executed_quantity', 0),
            execution_step.get('remaining_quantity', 0),
            execution_step.get('actual_price'),
            execution_step.get('planned_date', date.today()),
            execution_step.get('executed_date'),
            execution_step.get('reason'),
            execution_step.get('status', 'pending'),
            execution_step.get('remark')
        )
        return self.execute(sql, params)
    
    def insert_trade_record(self, trade_record: Dict) -> bool:
        """
        插入交易记录
        
        Args:
            trade_record: 交易记录字典
        
        Returns:
            bool: 是否成功
        """
        sql = """
        INSERT INTO trade_record 
        (record_id, account_id, stock_code, stock_name,
        plan_id, step_id, trade_type, trade_direction,
        trade_price, trade_quantity, trade_amount,
        commission, stamp_duty,
        trade_date, trade_time, order_number, broker_order_number,
        status, remark)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        params = (
            trade_record.get('record_id'),
            trade_record.get('account_id'),
            trade_record.get('stock_code'),
            trade_record.get('stock_name'),
            trade_record.get('plan_id'),
            trade_record.get('step_id'),
            trade_record.get('trade_type'),
            trade_record.get('trade_direction'),
            trade_record.get('trade_price'),
            trade_record.get('trade_quantity', 0),
            trade_record.get('trade_amount', 0.00),
            trade_record.get('commission', 0.0000),
            trade_record.get('stamp_duty', 0.0000),
            trade_record.get('trade_date', date.today()),
            trade_record.get('trade_time', datetime.now().strftime('%H:%M:%S')),
            trade_record.get('order_number'),
            trade_record.get('broker_order_number'),
            trade_record.get('status', 'completed'),
            trade_record.get('remark')
        )
        return self.execute(sql, params)
    
    def insert_review_record(self, review_record: Dict) -> bool:
        """
        插入复盘记录
        
        Args:
            review_record: 复盘记录字典
        
        Returns:
            bool: 是否成功
        """
        sql = """
        INSERT INTO review_record 
        (review_id, plan_id, account_id, stock_code, stock_name,
        review_date, review_type, review_result,
        execution_summary, profit_loss_analysis, reason_analysis,
        success_experience, failure_lesson, improvement_measures,
        emotion_status, emotion_impact,
        execution_score, strategy_score, overall_score,
        status, remark)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s,
        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        params = (
            review_record.get('review_id'),
            review_record.get('plan_id'),
            review_record.get('account_id'),
            review_record.get('stock_code'),
            review_record.get('stock_name'),
            review_record.get('review_date', date.today()),
            review_record.get('review_type'),
            review_record.get('review_result'),
            review_record.get('execution_summary'),
            review_record.get('profit_loss_analysis'),
            review_record.get('reason_analysis'),
            review_record.get('success_experience'),
            review_record.get('failure_lesson'),
            review_record.get('improvement_measures'),
            review_record.get('emotion_status'),
            review_record.get('emotion_impact'),
            review_record.get('execution_score'),
            review_record.get('strategy_score'),
            review_record.get('overall_score'),
            review_record.get('status', 'completed'),
            review_record.get('remark')
        )
        return self.execute(sql, params)
    
    def get_account_info(self, account_id: str) -> Optional[Dict]:
        """
        获取账户信息
        
        Args:
            account_id: 账户编号
        
        Returns:
            账户信息字典
        """
        sql = "SELECT * FROM account_info WHERE account_id = %s"
        self.execute(sql, (account_id,))
        row = self.fetchone()
        return dict(row) if row else None
    
    def get_stock_basic_info(self, stock_code: str) -> Optional[Dict]:
        """
        获取股票基本信息
        
        Args:
            stock_code: 股票代码
        
        Returns:
            股票信息字典
        """
        sql = "SELECT * FROM stock_basic_info WHERE stock_code = %s"
        self.execute(sql, (stock_code,))
        row = self.fetchone()
        return dict(row) if row else None
    
    def get_score_record(self, stock_code: str, score_date: date = None) -> Optional[Dict]:
        """
        获取评分记录
        
        Args:
            stock_code: 股票代码
            score_date: 评分日期
        
        Returns:
            评分记录字典
        """
        if score_date:
            sql = "SELECT * FROM score_record WHERE stock_code = %s AND score_date = %s"
            self.execute(sql, (stock_code, score_date))
        else:
            sql = "SELECT * FROM score_record WHERE stock_code = %s ORDER BY score_date DESC LIMIT 1"
            self.execute(sql, (stock_code,))
        row = self.fetchone()
        return dict(row) if row else None
    
    def get_trade_plan(self, plan_id: str) -> Optional[Dict]:
        """
        获取交易计划
        
        Args:
            plan_id: 计划编号
        
        Returns:
            交易计划字典
        """
        sql = "SELECT * FROM trade_plan WHERE plan_id = %s"
        self.execute(sql, (plan_id,))
        row = self.fetchone()
        return dict(row) if row else None
    
    def get_trade_execution_step(self, step_id: str) -> Optional[Dict]:
        """
        获取交易执行步骤
        
        Args:
            step_id: 步骤编号
        
        Returns:
            交易执行步骤字典
        """
        sql = "SELECT * FROM trade_execution_step WHERE step_id = %s"
        self.execute(sql, (step_id,))
        row = self.fetchone()
        return dict(row) if row else None
    
    def get_trade_record(self, record_id: str) -> Optional[Dict]:
        """
        获取交易记录
        
        Args:
            record_id: 交易记录编号
        
        Returns:
            交易记录字典
        """
        sql = "SELECT * FROM trade_record WHERE record_id = %s"
        self.execute(sql, (record_id,))
        row = self.fetchone()
        return dict(row) if row else None
    
    def get_review_record(self, review_id: str) -> Optional[Dict]:
        """
        获取复盘记录
        
        Args:
            review_id: 复盘编号
        
        Returns:
            复盘记录字典
        """
        sql = "SELECT * FROM review_record WHERE review_id = %s"
        self.execute(sql, (review_id,))
        row = self.fetchone()
        return dict(row) if row else None


def main():
    """
    主函数 - 使用示例
    """
    print("=" * 80)
    print("交易系统数据库操作示例（优化版）")
    print("=" * 80)
    
    # 创建数据库实例
    db = TradingDatabase(
        db_type='sqlite',
        db_config={'db_path': 'trading_system.db'}
    )
    
    # 连接数据库
    if db.connect():
        # 示例1: 插入账户信息
        print("\n【示例1: 插入账户信息】")
        account = {
            'account_id': 'ACC001',
            'account_name': '我的账户',
            'account_type': '模拟',
            'broker': '国金证券',
            'total_assets': 100000.00,
            'available_cash': 100000.00,
            'market_value': 0.00,
            'profit_loss': 0.00,
            'profit_loss_rate': 0.0000,
            'risk_level': '中',
            'status': 'active',
            'remark': '模拟交易账户'
        }
        if db.insert_account_info(account):
            print("账户信息插入成功")
        
        # 示例2: 插入股票基本信息
        print("\n【示例2: 插入股票基本信息】")
        stock = {
            'stock_code': '002065',
            'stock_name': '东华软件',
            'stock_abbr': '东华软件',
            'exchange': 'SZ',
            'industry': '软件服务',
            'sector': '计算机应用',
            'list_date': date(2006, 8, 23),
            'total_shares': 3205126585,
            'float_shares': 2908118177,
            'market_cap': 30836740448.00,
            'float_market_cap': 27974206263.00,
            'pe_ratio': 65.98,
            'pb_ratio': 2.53,
            'ps_ratio': 0.00,
            'dividend_yield': 0.0000,
            'status': 'normal',
            'remark': '科技股'
        }
        if db.insert_stock_basic_info(stock):
            print("股票基本信息插入成功")
        
        # 示例3: 插入评分记录
        print("\n【示例3: 插入评分记录】")
        score = {
            'stock_code': '002065',
            'stock_name': '东华软件',
            'score_date': date.today(),
            'fundamental_score': 30.0000,
            'fundamental_reason': '软件服务行业，技术创新能力强',
            'technical_score': 70.0000,
            'technical_reason': '技术面表现良好，均线多头排列',
            'ma_score': 20.0000,
            'macd_score': 25.0000,
            'rsi_score': 15.0000,
            'bollinger_score': 15.0000,
            'volume_score': 15.0000,
            'obv_score': 10.0000,
            'total_score': 100.0000,
            'rating': '强烈推荐',
            'ma5': 9.69,
            'ma10': 9.61,
            'ma20': 9.80,
            'ma60': 9.80,
            'diff': -0.0543,
            'dea': -0.0347,
            'macd': -0.0393,
            'rsi': 55.60,
            'bb_upper': 10.26,
            'bb_middle': 9.80,
            'bb_lower': 9.33,
            'close_price': 9.62,
            'volume': 418460,
            'turnover_rate': 1.44,
            'remark': '科技股，建议关注'
        }
        if db.insert_score_record(score):
            print("评分记录插入成功")
        
        # 示例4: 插入交易计划
        print("\n【示例4: 插入交易计划】")
        plan = {
            'plan_id': 'PLAN001',
            'plan_name': '买入东华软件',
            'account_id': 'ACC001',
            'stock_code': '002065',
            'stock_name': '东华软件',
            'score_record_id': 1,
            'stop_loss_price': 9.00,
            'take_profit_price': 10.50,
            'planned_quantity': 1000,
            'planned_amount': 9600.00,
            'actual_quantity': 0,
            'actual_amount': 0.00,
            'profit_loss': 0.00,
            'profit_loss_rate': 0.0000,
            'plan_date': date.today(),
            'status': 'pending',
            'remark': '趋势交易'
        }
        if db.insert_trade_plan(plan):
            print("交易计划插入成功")
        
        # 示例5: 插入交易执行步骤
        print("\n【示例5: 插入交易执行步骤】")
        step = {
            'step_id': 'STEP001',
            'plan_id': 'PLAN001',
            'account_id': 'ACC001',
            'stock_code': '002065',
            'stock_name': '东华软件',
            'trade_direction': '建仓',
            'target_price': 9.62,
            'planned_quantity': 1000,
            'remaining_quantity': 1000,
            'planned_date': date.today(),
            'reason': '价格触及目标位，执行建仓',
            'status': 'pending',
            'remark': '第一步建仓'
        }
        if db.insert_trade_execution_step(step):
            print("交易执行步骤插入成功")
        
        # 示例6: 插入复盘记录
        print("\n【示例6: 插入复盘记录】")
        review = {
            'review_id': 'REVIEW001',
            'plan_id': 'PLAN001',
            'account_id': 'ACC001',
            'stock_code': '002065',
            'stock_name': '东华软件',
            'review_date': date.today(),
            'review_type': '成功',
            'review_result': '按计划执行，盈利5%',
            'execution_summary': '严格按照交易计划执行，在目标价位买入',
            'profit_loss_analysis': '盈利主要来自于趋势判断准确',
            'reason_analysis': '技术面分析准确，趋势判断正确',
            'success_experience': '严格执行交易计划，不情绪化操作',
            'improvement_measures': '可以考虑分批建仓，降低风险',
            'emotion_status': '平稳',
            'emotion_impact': '情绪稳定，有利于理性决策',
            'execution_score': 90.00,
            'strategy_score': 85.00,
            'overall_score': 87.50,
            'status': 'completed',
            'remark': '成功案例'
        }
        if db.insert_review_record(review):
            print("复盘记录插入成功")
        
        print("\n" + "=" * 80)
        print("数据库操作示例完成")
        print("=" * 80)
        
        # 断开连接
        db.disconnect()

if __name__ == "__main__":
    main()
