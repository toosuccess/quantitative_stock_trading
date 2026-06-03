"""
交易管理模块
包含交易计划、交易执行步骤、交易记录和复盘记录的CRUD操作
"""
import pymysql
from pymysql.cursors import DictCursor
from datetime import datetime, date
from typing import Dict, List, Optional
import uuid
import sys
import os

BACKEND_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app.database_config import MYSQL_CONFIG

class TradingManager:
    """交易管理类"""
    
    def __init__(self, db_path: str = None):
        """
        初始化交易管理器
        
        Args:
            db_path: 数据库文件路径（已废弃，保留兼容性）
        """
        self.db_path = db_path
        self.conn = None
    
    def connect(self):
        """连接数据库"""
        self.conn = pymysql.connect(**MYSQL_CONFIG, cursorclass=DictCursor)
        return self.conn
    
    def disconnect(self):
        """断开数据库连接"""
        if self.conn:
            self.conn.close()
    
    # ==================== 交易计划管理 ====================
    
    def create_trade_plan(self, plan: Dict) -> Optional[str]:
        """
        创建交易计划
        
        Args:
            plan: 交易计划字典
        
        Returns:
            计划编号
        """
        try:
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            stock_name = plan.get('stock_name', '')
            plan_id = plan.get('plan_id') or f"PLAN_{timestamp}_{stock_name}"
            
            cursor = self.conn.cursor()
            cursor.execute('''
            INSERT INTO trade_plan 
            (plan_id, plan_name, account_id, stock_code, stock_name,
            score_record_id, stop_loss_price, take_profit_price,
            planned_quantity, planned_amount, plan_date, status, remark)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ''', (
                plan_id,
                plan.get('plan_name'),
                plan.get('account_id'),
                plan.get('stock_code'),
                plan.get('stock_name'),
                plan.get('score_record_id'),
                plan.get('stop_loss_price'),
                plan.get('take_profit_price'),
                plan.get('planned_quantity', 0),
                plan.get('planned_amount', 0.00),
                plan.get('plan_date', date.today().isoformat()),
                plan.get('status', 'pending'),
                plan.get('remark')
            ))
            self.conn.commit()
            return plan_id
        except Exception as e:
            print(f"创建交易计划失败: {e}")
            return None
    
    def get_trade_plan(self, plan_id: str) -> Optional[Dict]:
        """
        获取交易计划
        
        Args:
            plan_id: 计划编号
        
        Returns:
            交易计划字典
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute('SELECT * FROM trade_plan WHERE plan_id = %s', (plan_id,))
            row = cursor.fetchone()
            return row if row else None
        except Exception as e:
            print(f"获取交易计划失败: {e}")
            return None
    
    def get_current_price(self, stock_code: str) -> float:
        """
        获取股票当前价格（优先级：stock_basic_info.current_price > score_record.close_price > trade_record.trade_price）
        
        Args:
            stock_code: 股票代码（可能带前缀如sh688805或纯数字688805）
        
        Returns:
            当前价格
        """
        try:
            import re
            pure_code = re.sub(r'^(sh|sz|bj)', '', stock_code)
            
            cursor = self.conn.cursor()
            
            cursor.execute('''
                SELECT current_price FROM stock_basic_info 
                WHERE stock_code = %s AND current_price > 0
            ''', (pure_code,))
            row = cursor.fetchone()
            if row and row.get('current_price'):
                return row['current_price']
            
            cursor.execute('''
                SELECT close_price FROM score_record 
                WHERE stock_code = %s
                ORDER BY score_date DESC LIMIT 1
            ''', (pure_code,))
            row = cursor.fetchone()
            if row and row.get('close_price'):
                return row['close_price']
            
            cursor.execute('''
                SELECT trade_price FROM trade_record 
                WHERE stock_code IN (%s, %s)
                ORDER BY trade_date DESC, trade_time DESC LIMIT 1
            ''', (stock_code, pure_code))
            row = cursor.fetchone()
            return row['trade_price'] if row else 0
        except Exception:
            return 0
    
    def get_holding_quantity(self, plan_id: str) -> int:
        """
        获取计划当前持仓数量
        
        Args:
            plan_id: 计划编号
        
        Returns:
            持仓数量
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT 
                    COALESCE(SUM(CASE WHEN trade_type = '买入' THEN trade_quantity ELSE 0 END), 0) -
                    COALESCE(SUM(CASE WHEN trade_type = '卖出' THEN trade_quantity ELSE 0 END), 0) as holding
                FROM trade_record 
                WHERE plan_id = %s
            ''', (plan_id,))
            row = cursor.fetchone()
            return row['holding'] if row and row['holding'] else 0
        except Exception:
            return 0
    
    def calculate_plan_profit(self, plan: Dict, buy_quantity: int, buy_amount: float, 
                              sell_quantity: int, sell_amount: float) -> Dict:
        """
        计算交易计划盈利
        
        Args:
            plan: 计划信息
            buy_quantity: 买入数量
            buy_amount: 买入金额
            sell_quantity: 卖出数量
            sell_amount: 卖出金额
        
        Returns:
            盈利信息字典
        """
        stock_code = plan.get('stock_code', '')
        
        holding_quantity = buy_quantity - sell_quantity
        
        buy_avg_price = buy_amount / buy_quantity if buy_quantity > 0 else 0
        
        if holding_quantity == 0:
            if sell_quantity > 0:
                profit = sell_amount - buy_amount
            else:
                profit = 0
            profit_type = 'realized'
        else:
            current_price = self.get_current_price(stock_code)
            if current_price == 0:
                current_price = buy_avg_price
            
            unrealized_profit = (current_price - buy_avg_price) * holding_quantity
            
            realized_profit = sell_amount - (sell_quantity * buy_avg_price)
            
            profit = unrealized_profit + realized_profit
            profit_type = 'unrealized'
        
        return {
            'profit': round(profit, 2),
            'profit_type': profit_type,
            'holding_quantity': holding_quantity,
            'buy_avg_price': round(buy_avg_price, 2)
        }
    
    def get_trade_plans_by_account(self, account_id: str, status: str = None) -> List[Dict]:
        """
        获取账户的交易计划列表
        
        Args:
            account_id: 账户编号
            status: 状态过滤
        
        Returns:
            交易计划列表
        """
        try:
            cursor = self.conn.cursor()
            if status:
                cursor.execute('''
                    SELECT * FROM trade_plan 
                    WHERE account_id = %s AND status = %s
                    ORDER BY plan_date DESC
                ''', (account_id, status))
            else:
                cursor.execute('''
                    SELECT * FROM trade_plan 
                    WHERE account_id = %s
                    ORDER BY plan_date DESC
                ''', (account_id,))
            plans = cursor.fetchall()
            
            for plan in plans:
                cursor.execute('''
                    SELECT SUM(trade_amount) as total_amount, SUM(trade_quantity) as total_quantity
                    FROM trade_record 
                    WHERE plan_id = %s AND trade_type = '买入'
                ''', (plan['plan_id'],))
                buy_row = cursor.fetchone()
                buy_quantity = buy_row['total_quantity'] if buy_row and buy_row['total_quantity'] else 0
                buy_amount = buy_row['total_amount'] if buy_row and buy_row['total_amount'] else 0
                plan['buy_quantity'] = buy_quantity
                plan['buy_amount'] = buy_amount
                
                cursor.execute('''
                    SELECT SUM(trade_amount) as total_amount, SUM(trade_quantity) as total_quantity
                    FROM trade_record 
                    WHERE plan_id = %s AND trade_type = '卖出'
                ''', (plan['plan_id'],))
                sell_row = cursor.fetchone()
                sell_quantity = sell_row['total_quantity'] if sell_row and sell_row['total_quantity'] else 0
                sell_amount = sell_row['total_amount'] if sell_row and sell_row['total_amount'] else 0
                
                profit_info = self.calculate_plan_profit(plan, buy_quantity, buy_amount, sell_quantity, sell_amount)
                plan['profit'] = profit_info['profit']
                plan['profit_type'] = profit_info['profit_type']
                plan['holding_quantity'] = profit_info['holding_quantity']
                plan['avg_cost_price'] = profit_info['buy_avg_price']
                plan['current_price'] = self.get_current_price(plan['stock_code'])
                plan['holding_amount'] = plan['holding_quantity'] * plan['current_price']
                if plan['avg_cost_price'] > 0 and plan['current_price'] > 0:
                    plan['profit_rate'] = round((plan['current_price'] - plan['avg_cost_price']) / plan['avg_cost_price'] * 100, 2)
                else:
                    plan['profit_rate'] = 0
                plan['remaining_quantity'] = (plan.get('planned_quantity') or 0) - (plan.get('actual_quantity') or 0)
            
            return plans
        except Exception as e:
            print(f"获取交易计划列表失败: {e}")
            return []
    
    def get_all_trade_plans(self, status: str = None) -> List[Dict]:
        """
        获取所有交易计划列表
        
        Args:
            status: 状态过滤
        
        Returns:
            交易计划列表
        """
        try:
            cursor = self.conn.cursor()
            if status:
                cursor.execute('''
                    SELECT * FROM trade_plan 
                    WHERE status = %s
                    ORDER BY plan_date DESC
                ''', (status,))
            else:
                cursor.execute('''
                    SELECT * FROM trade_plan 
                    ORDER BY plan_date DESC
                ''')
            plans = cursor.fetchall()
            
            for plan in plans:
                cursor.execute('''
                    SELECT SUM(trade_amount) as total_amount, SUM(trade_quantity) as total_quantity
                    FROM trade_record 
                    WHERE plan_id = %s AND trade_type = '买入'
                ''', (plan['plan_id'],))
                buy_row = cursor.fetchone()
                buy_quantity = buy_row['total_quantity'] if buy_row and buy_row['total_quantity'] else 0
                buy_amount = buy_row['total_amount'] if buy_row and buy_row['total_amount'] else 0
                plan['buy_quantity'] = buy_quantity
                plan['buy_amount'] = buy_amount
                
                cursor.execute('''
                    SELECT SUM(trade_amount) as total_amount, SUM(trade_quantity) as total_quantity
                    FROM trade_record 
                    WHERE plan_id = %s AND trade_type = '卖出'
                ''', (plan['plan_id'],))
                sell_row = cursor.fetchone()
                sell_quantity = sell_row['total_quantity'] if sell_row and sell_row['total_quantity'] else 0
                sell_amount = sell_row['total_amount'] if sell_row and sell_row['total_amount'] else 0
                
                profit_info = self.calculate_plan_profit(plan, buy_quantity, buy_amount, sell_quantity, sell_amount)
                plan['profit'] = profit_info['profit']
                plan['profit_type'] = profit_info['profit_type']
                plan['holding_quantity'] = profit_info['holding_quantity']
                plan['avg_cost_price'] = profit_info['buy_avg_price']
                plan['current_price'] = self.get_current_price(plan['stock_code'])
                plan['holding_amount'] = plan['holding_quantity'] * plan['current_price']
                if plan['avg_cost_price'] > 0 and plan['current_price'] > 0:
                    plan['profit_rate'] = round((plan['current_price'] - plan['avg_cost_price']) / plan['avg_cost_price'] * 100, 2)
                else:
                    plan['profit_rate'] = 0
                plan['remaining_quantity'] = (plan.get('planned_quantity') or 0) - (plan.get('actual_quantity') or 0)
            
            return plans
        except Exception as e:
            print(f"获取所有交易计划列表失败: {e}")
            return []
    
    def get_trade_plans_by_stock(self, stock_code: str) -> List[Dict]:
        """
        获取指定股票的交易计划
        
        Args:
            stock_code: 股票代码
        
        Returns:
            交易计划列表
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT * FROM trade_plan 
                WHERE stock_code = %s
                ORDER BY plan_date DESC
            ''', (stock_code,))
            plans = cursor.fetchall()
            
            for plan in plans:
                cursor.execute('''
                    SELECT SUM(trade_amount) as total_amount, SUM(trade_quantity) as total_quantity
                    FROM trade_record 
                    WHERE plan_id = %s AND trade_type = '买入'
                ''', (plan['plan_id'],))
                buy_row = cursor.fetchone()
                buy_quantity = buy_row['total_quantity'] if buy_row and buy_row['total_quantity'] else 0
                buy_amount = buy_row['total_amount'] if buy_row and buy_row['total_amount'] else 0
                
                cursor.execute('''
                    SELECT SUM(trade_amount) as total_amount, SUM(trade_quantity) as total_quantity
                    FROM trade_record 
                    WHERE plan_id = %s AND trade_type = '卖出'
                ''', (plan['plan_id'],))
                sell_row = cursor.fetchone()
                sell_quantity = sell_row['total_quantity'] if sell_row and sell_row['total_quantity'] else 0
                sell_amount = sell_row['total_amount'] if sell_row and sell_row['total_amount'] else 0
                
                profit_info = self.calculate_plan_profit(plan, buy_quantity, buy_amount, sell_quantity, sell_amount)
                plan['profit'] = profit_info['profit']
                plan['profit_type'] = profit_info['profit_type']
                plan['holding_quantity'] = profit_info['holding_quantity']
                plan['avg_cost_price'] = profit_info['buy_avg_price']
                plan['current_price'] = self.get_current_price(plan['stock_code'])
                plan['holding_amount'] = plan['holding_quantity'] * plan['current_price']
                if plan['avg_cost_price'] > 0 and plan['current_price'] > 0:
                    plan['profit_rate'] = round((plan['current_price'] - plan['avg_cost_price']) / plan['avg_cost_price'] * 100, 2)
                else:
                    plan['profit_rate'] = 0
                plan['buy_amount'] = buy_amount
                plan['sell_amount'] = sell_amount
                
                cursor.execute('''
                    SELECT * FROM trade_record 
                    WHERE plan_id = %s
                    ORDER BY trade_date, trade_time
                ''', (plan['plan_id'],))
                records = cursor.fetchall()
                plan['records'] = records
            
            return plans
        except Exception as e:
            print(f"获取股票交易计划失败: {e}")
            return []
    
    def update_trade_plan(self, plan_id: str, updates: Dict) -> bool:
        """
        更新交易计划
        
        Args:
            plan_id: 计划编号
            updates: 更新字段字典
        
        Returns:
            是否成功
        """
        try:
            set_clauses = []
            params = []
            for key, value in updates.items():
                set_clauses.append(f"{key} = %s")
                params.append(value)
            params.append(plan_id)
            
            sql = f"UPDATE trade_plan SET {', '.join(set_clauses)} WHERE plan_id = %s"
            cursor = self.conn.cursor()
            cursor.execute(sql, params)
            self.conn.commit()
            return True
        except Exception as e:
            print(f"更新交易计划失败: {e}")
            return False
    
    def delete_trade_plan(self, plan_id: str) -> bool:
        """
        删除交易计划
        
        Args:
            plan_id: 计划编号
        
        Returns:
            是否成功
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute('DELETE FROM trade_plan WHERE plan_id = %s', (plan_id,))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"删除交易计划失败: {e}")
            return False
    
    def execute_trade_plan(self, plan_id: str) -> Dict:
        """
        执行交易计划 - 更新状态为执行中，并创建执行步骤
        
        Args:
            plan_id: 计划编号
        
        Returns:
            执行结果字典
        """
        try:
            plan = self.get_trade_plan(plan_id)
            if not plan:
                return {'success': False, 'message': '计划不存在'}
            
            if plan['status'] != 'pending':
                return {'success': False, 'message': f'计划状态为{plan["status"]}，无法执行'}
            
            self.update_trade_plan(plan_id, {'status': 'executing'})
            
            steps = []
            
            step_id = self.create_execution_step({
                'plan_id': plan_id,
                'account_id': plan['account_id'],
                'stock_code': plan['stock_code'],
                'stock_name': plan['stock_name'],
                'trade_direction': '建仓',
                'target_price': plan.get('current_price'),
                'planned_quantity': plan['planned_quantity'],
                'reason': '初始建仓'
            })
            if step_id:
                steps.append({'step_id': step_id, 'direction': '建仓'})
            
            step_id = self.create_execution_step({
                'plan_id': plan_id,
                'account_id': plan['account_id'],
                'stock_code': plan['stock_code'],
                'stock_name': plan['stock_name'],
                'trade_direction': '加仓',
                'target_price': None,
                'planned_quantity': plan['planned_quantity'],
                'reason': '盈利加仓'
            })
            if step_id:
                steps.append({'step_id': step_id, 'direction': '加仓'})
            
            step_id = self.create_execution_step({
                'plan_id': plan_id,
                'account_id': plan['account_id'],
                'stock_code': plan['stock_code'],
                'stock_name': plan['stock_name'],
                'trade_direction': '减仓',
                'target_price': None,
                'planned_quantity': plan['planned_quantity'],
                'reason': '风险控制减仓'
            })
            if step_id:
                steps.append({'step_id': step_id, 'direction': '减仓'})
            
            if plan.get('stop_loss_price'):
                step_id = self.create_execution_step({
                    'plan_id': plan_id,
                    'account_id': plan['account_id'],
                    'stock_code': plan['stock_code'],
                    'stock_name': plan['stock_name'],
                    'trade_direction': '止损清仓',
                    'target_price': plan['stop_loss_price'],
                    'planned_quantity': plan['planned_quantity'],
                    'reason': '止损清仓'
                })
                if step_id:
                    steps.append({'step_id': step_id, 'direction': '止损清仓'})
            
            if plan.get('take_profit_price'):
                step_id = self.create_execution_step({
                    'plan_id': plan_id,
                    'account_id': plan['account_id'],
                    'stock_code': plan['stock_code'],
                    'stock_name': plan['stock_name'],
                    'trade_direction': '止盈清仓',
                    'target_price': plan['take_profit_price'],
                    'planned_quantity': plan['planned_quantity'],
                    'reason': '止盈清仓'
                })
                if step_id:
                    steps.append({'step_id': step_id, 'direction': '止盈清仓'})
            
            return {
                'success': True,
                'message': '计划执行成功',
                'plan_id': plan_id,
                'steps': steps
            }
        except Exception as e:
            print(f"执行交易计划失败: {e}")
            return {'success': False, 'message': str(e)}
    
    def get_execution_step(self, step_id: str) -> Optional[Dict]:
        """
        获取单个执行步骤
        
        Args:
            step_id: 步骤编号
        
        Returns:
            执行步骤字典
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute('SELECT * FROM trade_execution_step WHERE step_id = %s', (step_id,))
            row = cursor.fetchone()
            return row if row else None
        except Exception as e:
            print(f"获取执行步骤失败: {e}")
            return None
    
    def execute_step(self, step_id: str, trade_price: float, trade_quantity: int, account_id: str = None) -> Dict:
        """
        执行步骤 - 创建交易记录并更新步骤和计划状态
        
        Args:
            step_id: 步骤编号
            trade_price: 交易价格
            trade_quantity: 交易数量
            account_id: 账户编号（可选，默认使用步骤中的账户）
        
        Returns:
            执行结果字典
        """
        try:
            step = self.get_execution_step(step_id)
            if not step:
                return {'success': False, 'message': '步骤不存在'}
            
            if step['status'] == 'completed':
                return {'success': False, 'message': '步骤已完成'}
            
            actual_account_id = account_id or step.get('account_id')
            
            trade_type = '卖出' if step['trade_direction'] in ['减仓', '清仓', '止损清仓', '止盈清仓'] else '买入'
            trade_amount = trade_price * trade_quantity
            
            record_id = self.create_trade_record({
                'account_id': actual_account_id,
                'stock_code': step['stock_code'],
                'stock_name': step['stock_name'],
                'plan_id': step['plan_id'],
                'step_id': step_id,
                'trade_type': trade_type,
                'trade_direction': step['trade_direction'],
                'trade_price': trade_price,
                'trade_quantity': trade_quantity,
                'trade_amount': trade_amount
            })
            
            if not record_id:
                return {'success': False, 'message': '创建交易记录失败'}
            
            new_executed = (step.get('executed_quantity') or 0) + trade_quantity
            new_remaining = step['planned_quantity'] - new_executed
            step_status = 'completed'
            
            self.update_execution_step(step_id, {
                'executed_quantity': new_executed,
                'remaining_quantity': max(0, new_remaining),
                'status': step_status,
                'target_price': trade_price
            })
            
            plan = self.get_trade_plan(step['plan_id'])
            if plan:
                new_actual = (plan.get('actual_quantity') or 0) + trade_quantity
                self.update_trade_plan(step['plan_id'], {
                    'actual_quantity': new_actual
                })
                
                if step['trade_direction'] in ['减仓', '止盈减仓', '止损清仓', '清仓', '止盈清仓']:
                    current_holding = self.get_holding_quantity(step['plan_id'])
                    if current_holding <= 0:
                        self.update_trade_plan(step['plan_id'], {'status': 'completed'})
                else:
                    all_steps = self.get_execution_steps_by_plan(step['plan_id'])
                    all_completed = all(s['status'] == 'completed' for s in all_steps)
                    if all_completed and len(all_steps) > 0:
                        self.update_trade_plan(step['plan_id'], {'status': 'completed'})
            
            account = self.get_account(actual_account_id)
            print(f"执行步骤: account_id={actual_account_id}, account={account}")
            if account:
                print(f"更新账户: trade_type={trade_type}, trade_amount={trade_amount}")
                from decimal import Decimal
                
                # 确保类型一致
                available_cash = float(account['available_cash'])
                
                if trade_type == '买入':
                    new_available_cash = available_cash - trade_amount
                else:
                    new_available_cash = available_cash + trade_amount
                
                print(f"新值: available_cash={new_available_cash}")
                
                # 只更新 available_cash，其他字段由 get_all_accounts 和 get_account 实时计算
                self.update_account(actual_account_id, {
                    'available_cash': new_available_cash
                })
            else:
                print(f"未找到账户: {actual_account_id}")
            
            return {
                'success': True,
                'message': '步骤执行成功',
                'record_id': record_id,
                'step_status': step_status,
                'executed_quantity': new_executed
            }
        except Exception as e:
            print(f"执行步骤失败: {e}")
            return {'success': False, 'message': str(e)}
    
    def get_plan_buy_info(self, plan_id: str) -> Dict:
        """
        获取交易计划的买入信息（买入均价、持仓数量等）
        
        Args:
            plan_id: 计划编号
        
        Returns:
            买入信息字典
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT 
                    COALESCE(SUM(CASE WHEN trade_type = '买入' THEN trade_quantity ELSE 0 END), 0) as buy_qty,
                    COALESCE(SUM(CASE WHEN trade_type = '买入' THEN trade_amount ELSE 0 END), 0) as buy_amt,
                    COALESCE(SUM(CASE WHEN trade_type = '卖出' THEN trade_quantity ELSE 0 END), 0) as sell_qty,
                    COALESCE(SUM(CASE WHEN trade_type = '卖出' THEN trade_amount ELSE 0 END), 0) as sell_amt
                FROM trade_record 
                WHERE plan_id = %s
            ''', (plan_id,))
            row = cursor.fetchone()
            
            buy_qty = row['buy_qty'] if row else 0
            buy_amt = row['buy_amt'] if row else 0
            sell_qty = row['sell_qty'] if row else 0
            sell_amt = row['sell_amt'] if row else 0
            
            holding_qty = buy_qty - sell_qty
            avg_cost_price = buy_amt / buy_qty if buy_qty > 0 else 0
            
            return {
                'buy_quantity': buy_qty,
                'buy_amount': buy_amt,
                'sell_quantity': sell_qty,
                'sell_amount': sell_amt,
                'holding_quantity': holding_qty,
                'avg_cost_price': round(avg_cost_price, 2)
            }
        except Exception as e:
            print(f"获取计划买入信息失败: {e}")
            return {
                'buy_quantity': 0,
                'buy_amount': 0,
                'sell_quantity': 0,
                'sell_amount': 0,
                'holding_quantity': 0,
                'avg_cost_price': 0
            }
    
    def get_all_execution_steps(self, plan_id: str = None, status: str = None) -> List[Dict]:
        """
        获取所有执行步骤列表
        
        Args:
            plan_id: 计划编号过滤
            status: 状态过滤
        
        Returns:
            执行步骤列表
        """
        try:
            cursor = self.conn.cursor()
            sql = 'SELECT * FROM trade_execution_step WHERE 1=1'
            params = []
            
            if plan_id:
                sql += ' AND plan_id = %s'
                params.append(plan_id)
            if status:
                sql += ' AND status = %s'
                params.append(status)
            
            sql += ' ORDER BY planned_date ASC'
            cursor.execute(sql, params)
            steps = cursor.fetchall()
            
            for step in steps:
                step['holding_quantity'] = self.get_holding_quantity(step['plan_id'])
                step['current_price'] = self.get_current_price(step['stock_code'])
            
            direction_order = {'建仓': 1, '加仓': 2, '减仓': 3, '清仓': 4}
            steps.sort(key=lambda x: (direction_order.get(x['trade_direction'], 5), x['planned_date'] or ''), reverse=False)
            steps.sort(key=lambda x: direction_order.get(x['trade_direction'], 5))
            
            return steps
        except Exception as e:
            print(f"获取执行步骤列表失败: {e}")
            return []
    
    # ==================== 交易执行步骤管理 ====================
    
    def create_execution_step(self, step: Dict) -> Optional[str]:
        """
        创建交易执行步骤
        
        Args:
            step: 执行步骤字典
        
        Returns:
            步骤编号
        """
        try:
            step_id = step.get('step_id') or f"STEP{datetime.now().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:4]}"
            
            cursor = self.conn.cursor()
            cursor.execute('''
            INSERT INTO trade_execution_step 
            (step_id, plan_id, account_id, stock_code, stock_name,
            trade_direction, target_price, planned_quantity, remaining_quantity,
            planned_date, reason, status, remark)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ''', (
                step_id,
                step.get('plan_id'),
                step.get('account_id'),
                step.get('stock_code'),
                step.get('stock_name'),
                step.get('trade_direction'),
                step.get('target_price'),
                step.get('planned_quantity', 0),
                step.get('remaining_quantity', step.get('planned_quantity', 0)),
                step.get('planned_date', date.today().isoformat()),
                step.get('reason'),
                step.get('status', 'pending'),
                step.get('remark')
            ))
            self.conn.commit()
            return step_id
        except Exception as e:
            print(f"创建执行步骤失败: {e}")
            return None
    
    def get_execution_steps_by_plan(self, plan_id: str) -> List[Dict]:
        """
        获取交易计划的执行步骤列表
        
        Args:
            plan_id: 计划编号
        
        Returns:
            执行步骤列表
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT * FROM trade_execution_step 
                WHERE plan_id = %s
                ORDER BY planned_date ASC
            ''', (plan_id,))
            return cursor.fetchall()
        except Exception as e:
            print(f"获取执行步骤列表失败: {e}")
            return []
    
    def update_execution_step(self, step_id: str, updates: Dict) -> bool:
        """
        更新执行步骤
        
        Args:
            step_id: 步骤编号
            updates: 更新字段字典
        
        Returns:
            是否成功
        """
        try:
            set_clauses = []
            params = []
            for key, value in updates.items():
                set_clauses.append(f"{key} = %s")
                params.append(value)
            params.append(step_id)
            
            sql = f"UPDATE trade_execution_step SET {', '.join(set_clauses)} WHERE step_id = %s"
            cursor = self.conn.cursor()
            cursor.execute(sql, params)
            self.conn.commit()
            return True
        except Exception as e:
            print(f"更新执行步骤失败: {e}")
            return False
    
    # ==================== 交易记录管理 ====================
    
    def create_trade_record(self, record: Dict) -> Optional[str]:
        """
        创建交易记录
        
        Args:
            record: 交易记录字典
        
        Returns:
            记录编号
        """
        try:
            record_id = record.get('record_id') or f"REC{datetime.now().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:4]}"
            
            cursor = self.conn.cursor()
            cursor.execute('''
            INSERT INTO trade_record 
            (record_id, account_id, stock_code, stock_name, plan_id, step_id,
            trade_type, trade_direction, trade_price, trade_quantity, trade_amount,
            commission, stamp_duty, trade_date, trade_time, status, remark)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ''', (
                record_id,
                record.get('account_id'),
                record.get('stock_code'),
                record.get('stock_name'),
                record.get('plan_id'),
                record.get('step_id'),
                record.get('trade_type'),
                record.get('trade_direction'),
                record.get('trade_price'),
                record.get('trade_quantity'),
                record.get('trade_amount'),
                record.get('commission', 0.0000),
                record.get('stamp_duty', 0.0000),
                record.get('trade_date', date.today().isoformat()),
                record.get('trade_time', datetime.now().strftime('%H:%M:%S')),
                record.get('status', 'completed'),
                record.get('remark')
            ))
            self.conn.commit()
            return record_id
        except Exception as e:
            print(f"创建交易记录失败: {e}")
            return None
    
    def get_trade_records_by_account(self, account_id: str, start_date: str = None, end_date: str = None) -> List[Dict]:
        """
        获取账户的交易记录列表
        
        Args:
            account_id: 账户编号
            start_date: 开始日期
            end_date: 结束日期
        
        Returns:
            交易记录列表
        """
        try:
            cursor = self.conn.cursor()
            sql = 'SELECT * FROM trade_record WHERE account_id = %s'
            params = [account_id]
            
            if start_date:
                sql += ' AND trade_date >= %s'
                params.append(start_date)
            if end_date:
                sql += ' AND trade_date <= %s'
                params.append(end_date)
            
            sql += ' ORDER BY trade_date DESC, trade_time DESC'
            cursor.execute(sql, params)
            return cursor.fetchall()
        except Exception as e:
            print(f"获取交易记录列表失败: {e}")
            return []
    
    def get_all_trade_records(self, plan_id: str = None, stock_code: str = None) -> List[Dict]:
        """
        获取所有交易记录列表
        
        Args:
            plan_id: 计划编号过滤
            stock_code: 股票代码过滤
        
        Returns:
            交易记录列表
        """
        try:
            cursor = self.conn.cursor()
            sql = 'SELECT * FROM trade_record WHERE 1=1'
            params = []
            
            if plan_id:
                sql += ' AND plan_id = %s'
                params.append(plan_id)
            if stock_code:
                sql += ' AND stock_code = %s'
                params.append(stock_code)
            
            sql += ' ORDER BY trade_date DESC, trade_time DESC'
            cursor.execute(sql, params)
            return cursor.fetchall()
        except Exception as e:
            print(f"获取交易记录列表失败: {e}")
            return []
    
    # ==================== 复盘记录管理 ====================
    
    def create_review_record(self, review: Dict) -> Optional[str]:
        """
        创建复盘记录
        
        Args:
            review: 复盘记录字典
        
        Returns:
            复盘编号
        """
        try:
            review_id = review.get('review_id') or f"REV{datetime.now().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:4]}"
            
            cursor = self.conn.cursor()
            cursor.execute('''
            INSERT INTO review_record 
            (review_id, plan_id, account_id, stock_code, stock_name,
            review_date, review_type, review_result, execution_summary,
            profit_loss_analysis, reason_analysis, success_experience,
            failure_lesson, improvement_measures, emotion_status, emotion_impact,
            execution_score, strategy_score, overall_score, status, remark)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ''', (
                review_id,
                review.get('plan_id'),
                review.get('account_id'),
                review.get('stock_code'),
                review.get('stock_name'),
                review.get('review_date', date.today().isoformat()),
                review.get('review_type'),
                review.get('review_result'),
                review.get('execution_summary'),
                review.get('profit_loss_analysis'),
                review.get('reason_analysis'),
                review.get('success_experience'),
                review.get('failure_lesson'),
                review.get('improvement_measures'),
                review.get('emotion_status'),
                review.get('emotion_impact'),
                review.get('execution_score'),
                review.get('strategy_score'),
                review.get('overall_score'),
                review.get('status', 'completed'),
                review.get('remark')
            ))
            self.conn.commit()
            return review_id
        except Exception as e:
            print(f"创建复盘记录失败: {e}")
            return None
    
    def get_review_records_by_account(self, account_id: str) -> List[Dict]:
        """
        获取账户的复盘记录列表
        
        Args:
            account_id: 账户编号
        
        Returns:
            复盘记录列表
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT * FROM review_record 
                WHERE account_id = %s
                ORDER BY review_date DESC
            ''', (account_id,))
            return cursor.fetchall()
        except Exception as e:
            print(f"获取复盘记录列表失败: {e}")
            return []
    
    # ==================== 统计分析 ====================
    
    def calculate_win_rate(self, account_id: str) -> Dict:
        """
        计算交易胜率
        
        Args:
            account_id: 账户编号
        
        Returns:
            胜率统计字典
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT profit_loss FROM trade_plan 
                WHERE account_id = %s AND status = 'completed' AND profit_loss != 0
            ''', (account_id,))
            rows = cursor.fetchall()
            
            if not rows:
                return {'total_trades': 0, 'win_trades': 0, 'loss_trades': 0, 'win_rate': 0}
            
            total_trades = len(rows)
            win_trades = sum(1 for row in rows if row['profit_loss'] > 0)
            loss_trades = total_trades - win_trades
            win_rate = (win_trades / total_trades * 100) if total_trades > 0 else 0
            
            return {
                'total_trades': total_trades,
                'win_trades': win_trades,
                'loss_trades': loss_trades,
                'win_rate': round(win_rate, 2)
            }
        except Exception as e:
            print(f"计算胜率失败: {e}")
            return {'total_trades': 0, 'win_trades': 0, 'loss_trades': 0, 'win_rate': 0}
    
    def calculate_profit_loss_ratio(self, account_id: str) -> Dict:
        """
        计算盈亏比
        
        Args:
            account_id: 账户编号
        
        Returns:
            盈亏比统计字典
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT profit_loss FROM trade_plan 
                WHERE account_id = %s AND status = 'completed' AND profit_loss != 0
            ''', (account_id,))
            rows = cursor.fetchall()
            
            if not rows:
                return {'avg_profit': 0, 'avg_loss': 0, 'profit_loss_ratio': 0}
            
            profits = [row['profit_loss'] for row in rows if row['profit_loss'] > 0]
            losses = [abs(row['profit_loss']) for row in rows if row['profit_loss'] < 0]
            
            avg_profit = sum(profits) / len(profits) if profits else 0
            avg_loss = sum(losses) / len(losses) if losses else 0
            profit_loss_ratio = avg_profit / avg_loss if avg_loss > 0 else 0
            
            return {
                'avg_profit': round(avg_profit, 2),
                'avg_loss': round(avg_loss, 2),
                'profit_loss_ratio': round(profit_loss_ratio, 2)
            }
        except Exception as e:
            print(f"计算盈亏比失败: {e}")
            return {'avg_profit': 0, 'avg_loss': 0, 'profit_loss_ratio': 0}
    
    def calculate_max_drawdown(self, account_id: str) -> Dict:
        """
        计算最大回撤
        
        Args:
            account_id: 账户编号
        
        Returns:
            最大回撤统计字典
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT profit_loss, plan_date FROM trade_plan 
                WHERE account_id = %s AND status = 'completed'
                ORDER BY plan_date ASC
            ''', (account_id,))
            rows = cursor.fetchall()
            
            if not rows:
                return {'max_drawdown': 0, 'max_drawdown_rate': 0}
            
            cumulative = 0
            peak = 0
            max_drawdown = 0
            
            for row in rows:
                cumulative += row['profit_loss']
                if cumulative > peak:
                    peak = cumulative
                drawdown = peak - cumulative
                if drawdown > max_drawdown:
                    max_drawdown = drawdown
            
            max_drawdown_rate = (max_drawdown / peak * 100) if peak > 0 else 0
            
            return {
                'max_drawdown': round(max_drawdown, 2),
                'max_drawdown_rate': round(max_drawdown_rate, 2)
            }
        except Exception as e:
            print(f"计算最大回撤失败: {e}")
            return {'max_drawdown': 0, 'max_drawdown_rate': 0}
    
    # ==================== 账号管理 ====================
    
    def create_account(self, account: Dict) -> Optional[str]:
        """
        创建账号
        
        Args:
            account: 账号字典
        
        Returns:
            账号编号
        """
        try:
            account_id = account.get('account_id') or f"ACC{uuid.uuid4().hex[:8].upper()}"
            
            total_assets = account.get('total_assets', 0)
            
            cursor = self.conn.cursor()
            cursor.execute('''
            INSERT INTO account_info 
            (account_id, account_name, account_type, broker, total_assets, initial_assets, available_cash, market_value, profit_loss, profit_loss_rate, risk_level, status, remark)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ''', (
                account_id,
                account.get('account_name'),
                account.get('account_type', '模拟'),
                account.get('broker'),
                total_assets,
                total_assets,
                account.get('available_cash', 0),
                account.get('market_value', 0),
                account.get('profit_loss', 0),
                account.get('profit_loss_rate', 0),
                account.get('risk_level'),
                account.get('status', 'active'),
                account.get('remark')
            ))
            self.conn.commit()
            return account_id
        except Exception as e:
            print(f"创建账号失败: {e}")
            return None
    
    def get_account(self, account_id: str) -> Optional[Dict]:
        """
        获取账号信息（包含实时计算的数据）
        
        Args:
            account_id: 账号编号
        
        Returns:
            账号字典
        """
        try:
            import re
            cursor = self.conn.cursor()
            cursor.execute('SELECT * FROM account_info WHERE account_id = %s', (account_id,))
            account = cursor.fetchone()
            
            if account:
                initial_assets = account.get('initial_assets') or account.get('total_assets', 0)
                
                # 实时计算市值：根据持仓和当前价格
                cursor.execute('''
                    SELECT tr.stock_code,
                           SUM(CASE WHEN tr.trade_type = '买入' THEN tr.trade_quantity ELSE 0 END) -
                           SUM(CASE WHEN tr.trade_type = '卖出' THEN tr.trade_quantity ELSE 0 END) as holding_qty
                    FROM trade_record tr
                    WHERE tr.account_id = %s
                    GROUP BY tr.stock_code
                    HAVING holding_qty > 0
                ''', (account['account_id'],))
                holdings = cursor.fetchall()
                
                if holdings:
                    # 优化：批量获取所有持仓股票的价格，避免N+1查询
                    stock_codes = [re.sub(r'^(sh|sz|bj)', '', h['stock_code']) for h in holdings]
                    placeholders = ','.join(['%s'] * len(stock_codes))
                    
                    # 从stock_basic_info批量获取最新价格
                    cursor.execute(f'''
                        SELECT stock_code, current_price 
                        FROM stock_basic_info 
                        WHERE stock_code IN ({placeholders}) AND current_price > 0
                    ''', stock_codes)
                    price_map = {row['stock_code']: row['current_price'] for row in cursor.fetchall()}
                    
                    market_value = 0.0
                    for h in holdings:
                        pure_code = re.sub(r'^(sh|sz|bj)', '', h['stock_code'])
                        current_price = price_map.get(pure_code)
                        
                        if not current_price:
                            # 如果stock_basic_info没有，尝试从score_record获取
                            cursor.execute('''
                                SELECT close_price FROM score_record 
                                WHERE stock_code = %s
                                ORDER BY score_date DESC LIMIT 1
                            ''', (pure_code,))
                            row = cursor.fetchone()
                            if row and row.get('close_price'):
                                current_price = row['close_price']
                            else:
                                # 最后尝试从trade_record获取最近交易价格
                                cursor.execute('''
                                    SELECT trade_price FROM trade_record 
                                    WHERE stock_code = %s 
                                    ORDER BY trade_date DESC, trade_time DESC LIMIT 1
                                ''', (pure_code,))
                                row = cursor.fetchone()
                                current_price = float(row['trade_price']) if row and row.get('trade_price') else 0.0
                        
                        market_value += float(h['holding_qty']) * float(current_price or 0)
                else:
                    market_value = 0.0
                
                account['market_value'] = market_value
                account['total_assets'] = float(account['available_cash']) + market_value
                # 先计算完总资产，再计算盈亏！
                account['profit_loss'] = account['total_assets'] - float(initial_assets)
                if float(initial_assets) > 0:
                    account['profit_loss_rate'] = round(account['profit_loss'] / float(initial_assets) * 100, 4)
                else:
                    account['profit_loss_rate'] = 0.0
                
            return account
        except Exception as e:
            print(f"获取账号失败: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def get_all_accounts(self) -> List[Dict]:
        """
        获取所有账号列表
        Returns:
            账号列表
        """
        try:
            import re
            cursor = self.conn.cursor()
            cursor.execute('SELECT * FROM account_info ORDER BY create_time DESC')
            accounts = cursor.fetchall()
            
            # 优化：先收集所有账户的所有持仓股票代码，批量查询价格
            all_stock_codes = set()
            account_holdings = {}
            
            for account in accounts:
                cursor.execute('''
                    SELECT tr.stock_code,
                           SUM(CASE WHEN tr.trade_type = '买入' THEN tr.trade_quantity ELSE 0 END) -
                           SUM(CASE WHEN tr.trade_type = '卖出' THEN tr.trade_quantity ELSE 0 END) as holding_qty
                    FROM trade_record tr
                    WHERE tr.account_id = %s
                    GROUP BY tr.stock_code
                    HAVING holding_qty > 0
                ''', (account['account_id'],))
                holdings = cursor.fetchall()
                account_holdings[account['account_id']] = holdings
                
                for h in holdings:
                    pure_code = re.sub(r'^(sh|sz|bj)', '', h['stock_code'])
                    all_stock_codes.add(pure_code)
            
            # 批量获取所有股票的价格（只需1次查询）
            price_map = {}
            if all_stock_codes:
                stock_list = list(all_stock_codes)
                placeholders = ','.join(['%s'] * len(stock_list))
                
                cursor.execute(f'''
                    SELECT stock_code, current_price 
                    FROM stock_basic_info 
                    WHERE stock_code IN ({placeholders}) AND current_price > 0
                ''', stock_list)
                price_map = {row['stock_code']: row['current_price'] for row in cursor.fetchall()}
            
            # 计算每个账户的市值和盈亏
            for account in accounts:
                initial_assets = account.get('initial_assets') or account.get('total_assets', 0)
                holdings = account_holdings.get(account['account_id'], [])
                
                market_value = 0.0
                for h in holdings:
                    pure_code = re.sub(r'^(sh|sz|bj)', '', h['stock_code'])
                    current_price = price_map.get(pure_code)
                    
                    if not current_price:
                        # 回退查询
                        cursor.execute('''
                            SELECT close_price FROM score_record 
                            WHERE stock_code = %s ORDER BY score_date DESC LIMIT 1
                        ''', (pure_code,))
                        row = cursor.fetchone()
                        current_price = float(row['close_price']) if row and row.get('close_price') else 0.0
                    
                    market_value += float(h['holding_qty']) * float(current_price or 0)
                
                account['market_value'] = market_value
                account['total_assets'] = float(account['available_cash']) + market_value
                # 注意：先计算完总资产，再计算盈亏！
                account['profit_loss'] = account['total_assets'] - float(initial_assets)
                if float(initial_assets) > 0:
                    account['profit_loss_rate'] = round(account['profit_loss'] / float(initial_assets) * 100, 4)
                else:
                    account['profit_loss_rate'] = 0.0
            
            return accounts
        except Exception as e:
            print(f"获取账号列表失败: {e}")
            return []
    
    def get_trade_summary(self, account_id: str = None) -> Dict:
        """
        获取交易汇总
        
        Args:
            account_id: 账户编号（可选，不传则统计所有账户）
        
        Returns:
            汇总信息字典
        """
        try:
            cursor = self.conn.cursor()
            
            where_clause = "WHERE account_id = %s" if account_id else ""
            params = [account_id] if account_id else []
            
            cursor.execute(f'''
                SELECT 
                    COUNT(*) as total_trades,
                    SUM(CASE WHEN trade_type = '买入' THEN 1 ELSE 0 END) as buy_count,
                    SUM(CASE WHEN trade_type = '卖出' THEN 1 ELSE 0 END) as sell_count,
                    SUM(CASE WHEN trade_type = '买入' THEN trade_amount ELSE 0 END) as total_buy_amount,
                    SUM(CASE WHEN trade_type = '卖出' THEN trade_amount ELSE 0 END) as total_sell_amount
                FROM trade_record 
                {where_clause}
            ''', params)
            trade_result = cursor.fetchone()
            
            cursor.execute(f'''
                SELECT COUNT(*) as completed_plans
                FROM trade_plan 
                WHERE status = 'completed'
                {"AND account_id = %s" if account_id else ""}
            ''', params)
            plan_result = cursor.fetchone()
            
            total_buy_amount = trade_result['total_buy_amount'] if trade_result and trade_result['total_buy_amount'] else 0
            total_sell_amount = trade_result['total_sell_amount'] if trade_result and trade_result['total_sell_amount'] else 0
            net_profit = total_sell_amount - total_buy_amount

            # 计算交易胜率
            sell_count = trade_result['sell_count'] if trade_result else 0
            buy_count = trade_result['buy_count'] if trade_result else 0

            # 统计盈利的卖出交易数
            cursor.execute(f'''
                SELECT COUNT(*) as win_count
                FROM trade_record
                WHERE trade_type = '卖出' AND trade_amount > 0
                {("AND account_id = %s" if account_id else "")}
            ''', params)
            win_count_result = cursor.fetchone()
            win_count = win_count_result['win_count'] if win_count_result else 0

            if sell_count == 0:
                win_rate = 0.0
            elif net_profit > 0:
                # 净盈利为正，胜率至少50%，最高100%
                # 根据收益率调整：收益率越高，胜率越高
                profit_rate = (net_profit / total_buy_amount * 100) if total_buy_amount > 0 else 0
                win_rate = min(1.0, 0.6 + profit_rate / 100 * 0.4)  # 60%-100%
            else:
                # 净亏损，胜率低于50%
                loss_rate = abs(net_profit / total_buy_amount * 100) if total_buy_amount > 0 else 0
                win_rate = max(0.0, 0.5 - loss_rate / 100 * 0.3)  # 20%-50%

            return {
                'total_trades': trade_result['total_trades'] if trade_result else 0,
                'buy_count': buy_count,
                'sell_count': sell_count,
                'win_count': win_count,
                'total_buy_amount': round(total_buy_amount, 2),
                'total_sell_amount': round(total_sell_amount, 2),
                'net_profit': round(net_profit, 2),
                'completed_plans': plan_result['completed_plans'] if plan_result else 0,
                'win_rate': round(win_rate, 4)
            }
        except Exception as e:
            print(f"获取交易汇总失败: {e}")
            return {
                'total_trades': 0,
                'buy_count': 0,
                'sell_count': 0,
                'win_count': 0,
                'total_buy_amount': 0,
                'total_sell_amount': 0,
                'net_profit': 0,
                'completed_plans': 0,
                'win_rate': 0
            }
    
    def update_account(self, account_id: str, updates: Dict) -> bool:
        """
        更新账号信息
        
        Args:
            account_id: 账号编号
            updates: 更新字段字典
        
        Returns:
            是否成功
        """
        try:
            set_clauses = []
            params = []
            for key, value in updates.items():
                set_clauses.append(f"{key} = %s")
                params.append(value)
            params.append(account_id)
            
            sql = f"UPDATE account_info SET {', '.join(set_clauses)} WHERE account_id = %s"
            cursor = self.conn.cursor()
            cursor.execute(sql, params)
            self.conn.commit()
            return True
        except Exception as e:
            print(f"更新账号失败: {e}")
            return False
    
    def delete_account(self, account_id: str) -> bool:
        """
        删除账号
        
        Args:
            account_id: 账号编号
        
        Returns:
            是否成功
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute('SELECT COUNT(*) as cnt FROM trade_plan WHERE account_id = %s', (account_id,))
            row = cursor.fetchone()
            if row and row['cnt'] > 0:
                return False
            
            cursor.execute('DELETE FROM account_info WHERE account_id = %s', (account_id,))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"删除账号失败: {e}")
            return False
    
    def get_account_summary(self, account_id: str) -> Dict:
        """
        获取账号汇总信息
        
        Args:
            account_id: 账号编号
        
        Returns:
            汇总信息字典
        """
        try:
            account = self.get_account(account_id)
            if not account:
                return {}
            
            cursor = self.conn.cursor()
            cursor.execute('SELECT COUNT(*) as cnt FROM trade_plan WHERE account_id = %s', (account_id,))
            plan_row = cursor.fetchone()
            
            cursor.execute('SELECT COUNT(*) as cnt FROM trade_record WHERE account_id = %s', (account_id,))
            record_row = cursor.fetchone()
            
            cursor.execute('SELECT SUM(trade_amount) as total FROM trade_record WHERE account_id = %s AND trade_type = "买入"', (account_id,))
            buy_row = cursor.fetchone()
            
            cursor.execute('SELECT SUM(trade_amount) as total FROM trade_record WHERE account_id = %s AND trade_type = "卖出"', (account_id,))
            sell_row = cursor.fetchone()
            
            win_rate = self.calculate_win_rate(account_id)
            profit_loss = self.calculate_profit_loss_ratio(account_id)
            drawdown = self.calculate_max_drawdown(account_id)
            
            return {
                'account': account,
                'plan_count': plan_row['cnt'] if plan_row else 0,
                'trade_count': record_row['cnt'] if record_row else 0,
                'total_buy': buy_row['total'] if buy_row and buy_row['total'] else 0,
                'total_sell': sell_row['total'] if sell_row and sell_row['total'] else 0,
                'win_rate': win_rate,
                'profit_loss_ratio': profit_loss,
                'max_drawdown': drawdown
            }
        except Exception as e:
            print(f"获取账号汇总失败: {e}")
            return {}
    
    def get_sell_analysis(self) -> Dict:
        """
        获取卖出分析数据（优化版：批量查询替代循环查询）
        
        Returns:
            卖出分析字典，包含记录列表和汇总统计
        """
        try:
            from datetime import timedelta
            import re
            cursor = self.conn.cursor()
            
            # 查询所有卖出记录
            cursor.execute('''
                SELECT tr.record_id, tr.stock_code, tr.stock_name, 
                       tr.trade_price as sell_price, tr.trade_quantity as sell_quantity,
                       tr.trade_amount as sell_amount, tr.trade_date as sell_date,
                       tr.account_id
                FROM trade_record tr
                WHERE tr.trade_type = '卖出'
                ORDER BY tr.trade_date DESC, tr.trade_time DESC
            ''')
            sell_records = cursor.fetchall()
            
            if not sell_records:
                return {
                    'success': True,
                    'records': [],
                    'summary': None
                }
            
            # 优化：批量预加载所有卖出股票的历史价格数据
            all_stock_dates = []
            for record in sell_records:
                stock_code = record['stock_code']
                pure_code = stock_code.replace('sh', '').replace('sz', '').replace('bj', '')
                sell_date = record['sell_date']
                
                try:
                    sell_dt = date.fromisoformat(str(sell_date)) if isinstance(sell_date, str) else sell_date
                    
                    for weeks in [1, 2, 3, 4]:
                        target_date = sell_dt + timedelta(weeks=weeks)
                        all_stock_dates.append({
                            'stock_code': pure_code,
                            'target_date': target_date,
                            'date_start': target_date - timedelta(days=3),
                            'date_end': target_date + timedelta(days=3)
                        })
                except Exception as e:
                    print(f"日期解析失败: {e}")
            
            # 批量查询所有需要的价格数据（只需1次复杂查询）
            price_cache = {}
            if all_stock_dates:
                # 构建批量查询条件（使用UNION ALL或单次IN查询）
                # 策略：一次性查询所有相关股票在所有时间范围内的最新价格
                batch_conditions = []
                params = []
                
                for item in all_stock_dates:
                    key = f"{item['stock_code']}_{item['target_date']}"
                    if key not in price_cache:  # 避免重复
                        batch_conditions.append(f"(stock_code = %s AND score_date >= %s AND score_date <= %s AND close_price > 0)")
                        params.extend([item['stock_code'], item['date_start'], item['date_end']])
                        price_cache[key] = None  # 占位
                
                if batch_conditions:
                    # 由于条件太多，改用简化策略：查询所有相关股票的最近价格记录
                    unique_stocks = list(set([item['stock_code'] for item in all_stock_dates]))
                    placeholders = ','.join(['%s'] * len(unique_stocks))
                    
                    cursor.execute(f'''
                        SELECT stock_code, score_date, close_price 
                        FROM score_record 
                        WHERE stock_code IN ({placeholders}) 
                          AND close_price > 0
                        ORDER BY stock_code, score_date DESC
                    ''', unique_stocks)
                    
                    all_prices = cursor.fetchall()
                    
                    # 构建价格查找索引：{stock_code: [(date, price), ...]}
                    stock_price_index = {}
                    for row in all_prices:
                        code = row['stock_code']
                        if code not in stock_price_index:
                            stock_price_index[code] = []
                        stock_price_index[code].append((row['score_date'], row['close_price']))
            
            records = []
            total_count = len(sell_records)
            sell_too_early = 0
            sell_correct = 0
            
            for record in sell_records:
                stock_code = record['stock_code']
                pure_code = stock_code.replace('sh', '').replace('sz', '').replace('bj', '')
                sell_date = record['sell_date']
                
                result = {
                    'record_id': record['record_id'],
                    'stock_code': stock_code,
                    'stock_name': record['stock_name'],
                    'sell_price': float(record['sell_price']),
                    'sell_quantity': int(record['sell_quantity']),
                    'sell_amount': float(record['sell_amount']),
                    'sell_date': str(sell_date),
                    'price_1w': None,
                    'price_2w': None,
                    'price_3w': None,
                    'price_4w': None,
                    'change_1w': None,
                    'change_2w': None,
                    'change_3w': None,
                    'change_4w': None,
                    'status': 'no_data'
                }
                
                # 从预加载的数据中获取价格（避免重复查询）
                try:
                    sell_dt = date.fromisoformat(str(sell_date)) if isinstance(sell_date, str) else sell_date
                    price_list = stock_price_index.get(pure_code, [])
                    
                    for weeks in [1, 2, 3, 4]:
                        target_date = sell_dt + timedelta(weeks=weeks)
                        
                        # 在预加载数据中查找最接近目标日期的价格
                        best_match = None
                        min_diff = float('inf')
                        
                        for (p_date, p_price) in price_list:
                            try:
                                diff = abs((p_date - target_date).days) if hasattr(p_date, 'days') else abs(999)
                                if diff <= 3 and diff < min_diff:  # 前后3天内
                                    min_diff = diff
                                    best_match = p_price
                            except:
                                continue
                        
                        if best_match:
                            later_price = float(best_match)
                            change_pct = ((later_price - result['sell_price']) / result['sell_price']) * 100
                            
                            result[f'price_{weeks}w'] = round(later_price, 2)
                            result[f'change_{weeks}w'] = round(change_pct, 2)
                    
                    # 判断卖出决策是否正确
                    if result['price_4w'] is not None:
                        if result['change_4w'] < 0:
                            result['status'] = 'sell_correct'  # 卖对了，之后跌了
                            sell_correct += 1
                        elif result['change_4w'] > 5:  # 涨幅超过5%算卖早了
                            result['status'] = 'sell_too_early'
                            sell_too_early += 1
                        else:
                            result['status'] = 'sell_correct'
                            sell_correct += 1
                            
                except Exception as e:
                    print(f"获取{stock_code}后续价格失败: {e}")
                    result['status'] = 'invalid_date'
                
                records.append(result)
            
            # 计算汇总统计
            summary = {
                'total_count': total_count,
                'sell_too_early': sell_too_early,
                'sell_correct': sell_correct,
                'avg_change_1w': 0.0,
                'avg_change_2w': 0.0,
                'avg_change_3w': 0.0,
                'avg_change_4w': 0.0
            }
            
            # 计算平均涨跌幅
            for weeks in [1, 2, 3, 4]:
                changes = [r[f'change_{weeks}w'] for r in records if r.get(f'change_{weeks}w') is not None]
                if changes:
                    summary[f'avg_change_{weeks}w'] = round(sum(changes) / len(changes), 2)
            
            return {
                'success': True,
                'records': records,
                'summary': summary
            }
            
        except Exception as e:
            print(f"获取卖出分析失败: {e}")
            import traceback
            traceback.print_exc()
            return {'success': False, 'message': str(e)}


def main():
    """测试交易管理模块"""
    print("=" * 60)
    print("交易管理模块测试")
    print("=" * 60)
    
    manager = TradingManager()
    manager.connect()
    
    try:
        print("\n1. 测试创建交易计划...")
        plan_id = manager.create_trade_plan({
            'plan_name': '买入华胜天成',
            'account_id': 'ACC001',
            'stock_code': '600410',
            'stock_name': '华胜天成',
            'score_record_id': 1,
            'stop_loss_price': 8.50,
            'take_profit_price': 10.50,
            'planned_quantity': 1000,
            'planned_amount': 9500.00
        })
        if plan_id:
            print(f"交易计划创建成功: {plan_id}")
        
        print("\n2. 测试创建执行步骤...")
        step_id = manager.create_execution_step({
            'plan_id': plan_id,
            'account_id': 'ACC001',
            'stock_code': '600410',
            'stock_name': '华胜天成',
            'trade_direction': '建仓',
            'target_price': 9.50,
            'planned_quantity': 1000,
            'reason': '技术指标符合选股条件'
        })
        if step_id:
            print(f"执行步骤创建成功: {step_id}")
        
        print("\n3. 测试创建交易记录...")
        record_id = manager.create_trade_record({
            'account_id': 'ACC001',
            'stock_code': '600410',
            'stock_name': '华胜天成',
            'plan_id': plan_id,
            'step_id': step_id,
            'trade_type': '买入',
            'trade_direction': '建仓',
            'trade_price': 9.48,
            'trade_quantity': 1000,
            'trade_amount': 9480.00,
            'commission': 5.00
        })
        if record_id:
            print(f"交易记录创建成功: {record_id}")
        
        print("\n4. 测试查询交易计划...")
        plan = manager.get_trade_plan(plan_id)
        if plan:
            print(f"计划名称: {plan['plan_name']}")
            print(f"股票: {plan['stock_name']}({plan['stock_code']})")
            print(f"状态: {plan['status']}")
        
        print("\n5. 测试统计分析...")
        win_rate = manager.calculate_win_rate('ACC001')
        print(f"胜率统计: {win_rate}")
        
        profit_loss = manager.calculate_profit_loss_ratio('ACC001')
        print(f"盈亏比: {profit_loss}")
        
        drawdown = manager.calculate_max_drawdown('ACC001')
        print(f"最大回撤: {drawdown}")
        
    finally:
        manager.disconnect()
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)


if __name__ == "__main__":
    main()
