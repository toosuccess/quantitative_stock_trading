"""
API路由模块
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from datetime import date
import sys
import os
import sqlite3

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'services'))

from data_fetcher import DataFetcher
from stock_selector import INDUSTRY_STOCK_POOL, STOCK_NAME_MAPPING
from trading_manager import TradingManager

router = APIRouter()

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'database', 'trading_system.db')


class TradePlanCreate(BaseModel):
    plan_name: str
    account_id: str
    stock_code: str
    stock_name: str
    planned_quantity: Optional[int] = 0
    planned_amount: Optional[float] = 0.0
    stop_loss_price: Optional[float] = None
    take_profit_price: Optional[float] = None


class TradeRecordCreate(BaseModel):
    account_id: str
    stock_code: str
    stock_name: str
    trade_type: str
    trade_direction: str
    trade_price: float
    trade_quantity: int
    trade_amount: float


class AccountCreate(BaseModel):
    account_name: str
    account_type: str = "模拟"
    broker: Optional[str] = None
    total_assets: Optional[float] = 0.0
    available_cash: Optional[float] = 0.0
    market_value: Optional[float] = 0.0
    profit_loss: Optional[float] = 0.0
    profit_loss_rate: Optional[float] = 0.0
    risk_level: Optional[str] = None
    remark: Optional[str] = None


class BatchEvaluateRequest(BaseModel):
    stock_codes: List[str]


class EvaluateRequest(BaseModel):
    stock_code: str


@router.get("/accounts")
async def list_accounts():
    """获取账号列表"""
    manager = TradingManager(DB_PATH)
    manager.connect()
    try:
        accounts = manager.get_all_accounts()
        return {"accounts": accounts, "count": len(accounts)}
    finally:
        manager.disconnect()


@router.post("/account")
async def create_account(account: AccountCreate):
    """创建账号"""
    manager = TradingManager(DB_PATH)
    manager.connect()
    try:
        account_id = manager.create_account({
            'account_name': account.account_name,
            'account_type': account.account_type,
            'broker': account.broker,
            'total_assets': account.total_assets,
            'available_cash': account.available_cash,
            'market_value': account.market_value,
            'profit_loss': account.profit_loss,
            'profit_loss_rate': account.profit_loss_rate,
            'risk_level': account.risk_level,
            'remark': account.remark
        })
        if account_id:
            return {"account_id": account_id, "message": "账号创建成功"}
        else:
            raise HTTPException(status_code=500, detail="创建账号失败")
    finally:
        manager.disconnect()


@router.get("/account/{account_id}")
async def get_account(account_id: str):
    """获取账号信息"""
    manager = TradingManager(DB_PATH)
    manager.connect()
    try:
        account = manager.get_account(account_id)
        if account is None:
            raise HTTPException(status_code=404, detail="账号不存在")
        return account
    finally:
        manager.disconnect()


@router.put("/account/{account_id}")
async def update_account(account_id: str, account: AccountCreate):
    """更新账号信息"""
    manager = TradingManager(DB_PATH)
    manager.connect()
    try:
        success = manager.update_account(account_id, {
            'account_name': account.account_name,
            'account_type': account.account_type,
            'broker': account.broker,
            'total_assets': account.total_assets,
            'available_cash': account.available_cash,
            'market_value': account.market_value,
            'profit_loss': account.profit_loss,
            'profit_loss_rate': account.profit_loss_rate,
            'risk_level': account.risk_level,
            'remark': account.remark
        })
        if success:
            return {"message": "账号更新成功"}
        else:
            raise HTTPException(status_code=500, detail="更新账号失败")
    finally:
        manager.disconnect()


@router.delete("/account/{account_id}")
async def delete_account(account_id: str):
    """删除账号"""
    manager = TradingManager(DB_PATH)
    manager.connect()
    try:
        success = manager.delete_account(account_id)
        if success:
            return {"message": "账号删除成功"}
        else:
            raise HTTPException(status_code=400, detail="账号下有交易计划，无法删除")
    finally:
        manager.disconnect()


@router.get("/account/{account_id}/summary")
async def get_account_summary(account_id: str):
    """获取账号汇总信息"""
    manager = TradingManager(DB_PATH)
    manager.connect()
    try:
        summary = manager.get_account_summary(account_id)
        if not summary:
            raise HTTPException(status_code=404, detail="账号不存在")
        return summary
    finally:
        manager.disconnect()


@router.get("/scores")
async def get_score_records(limit: int = 20, rating: Optional[str] = None):
    """获取评分记录列表（从数据库读取）"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    try:
        if rating:
            cursor.execute('''
                SELECT * FROM score_record 
                WHERE rating = ?
                ORDER BY score_date DESC, total_score DESC
                LIMIT ?
            ''', (rating, limit))
        else:
            cursor.execute('''
                SELECT * FROM score_record 
                ORDER BY score_date DESC, total_score DESC
                LIMIT ?
            ''', (limit,))
        rows = cursor.fetchall()
        records = [dict(row) for row in rows]
        return {"scores": records, "count": len(records)}
    finally:
        conn.close()


@router.get("/scores/{stock_code}")
async def get_score_by_code(stock_code: str):
    """获取指定股票的评分历史记录（从数据库读取）"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    try:
        # 统一股票代码格式进行匹配
        normalized_code = stock_code.lower().replace('sh', '').replace('sz', '').replace('bj', '')
        # 构建可能的股票代码格式
        possible_codes = [
            stock_code,
            stock_code.upper(),
            stock_code.lower(),
            normalized_code,
            f'sz{normalized_code}',
            f'sh{normalized_code}',
            f'bj{normalized_code}',
            f'SZ{normalized_code}',
            f'SH{normalized_code}',
            f'BJ{normalized_code}'
        ]
        placeholders = ','.join(['?' for _ in possible_codes])
        cursor.execute(f'''
            SELECT * FROM score_record 
            WHERE stock_code IN ({placeholders})
            ORDER BY id DESC
        ''', possible_codes)
        rows = cursor.fetchall()
        if not rows:
            raise HTTPException(status_code=404, detail="未找到该股票的评分记录")
        records = [dict(row) for row in rows]
        
        # 获取股票基本信息
        cursor.execute(f'''
            SELECT stock_code, stock_name, stock_abbr, exchange, industry, sector, 
                   list_date, total_shares, float_shares, market_cap, float_market_cap,
                   pe_ratio, pb_ratio, ps_ratio, dividend_yield, status
            FROM stock_basic_info 
            WHERE stock_code IN ({placeholders})
        ''', possible_codes)
        stock_info_row = cursor.fetchone()
        stock_info = dict(stock_info_row) if stock_info_row else None
        
        return {
            "stock_code": stock_code, 
            "history": records, 
            "count": len(records),
            "stock_info": stock_info
        }
    finally:
        conn.close()


@router.get("/stocks/pool/scores")
async def get_stock_pool_scores():
    """获取股票池评分汇总（去重，显示每只股票的最新评分）"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    try:
        cursor.execute('''
            SELECT 
                stock_code,
                stock_name,
                total_score as latest_score,
                composite_score,
                rating as latest_rating,
                score_date as latest_date,
                create_time,
                is_leader,
                close_price,
                technical_score,
                fundamental_score,
                news_score,
                policy_score,
                deduction_score,
                ma_score,
                macd_score,
                rsi_score,
                bollinger_score,
                volume_score,
                obv_score,
                technical_detail,
                fundamental_detail,
                news_detail,
                policy_detail,
                deduction_detail,
                summary,
                (SELECT COUNT(*) FROM score_record sr2 WHERE sr2.stock_code = sr1.stock_code) as score_count
            FROM score_record sr1
            WHERE id = (
                SELECT MAX(id) FROM score_record sr2 
                WHERE sr2.stock_code = sr1.stock_code
            )
            ORDER BY composite_score DESC, total_score DESC, score_date DESC
        ''')
        rows = cursor.fetchall()
        stocks = [dict(row) for row in rows]
        
        for stock in stocks:
            cursor.execute('''
                SELECT score_date, composite_score, total_score, close_price
                FROM score_record 
                WHERE stock_code = ?
                ORDER BY score_date DESC, id DESC
                LIMIT 10
            ''', (stock['stock_code'],))
            history_rows = cursor.fetchall()
            stock['score_history'] = [
                {'date': row['score_date'], 'score': row['composite_score'] or row['total_score']}
                for row in reversed(history_rows)
            ]
            stock['price_history'] = [
                {'date': row['score_date'], 'price': row['close_price']}
                for row in reversed(history_rows) if row['close_price']
            ]
        
        manager = TradingManager(DB_PATH)
        manager.connect()
        try:
            for stock in stocks:
                plans = manager.get_trade_plans_by_stock(stock['stock_code'])
                unfinished_plans = [p for p in plans if p.get('status') in ['待执行', '执行中', 'pending', 'executing']]
                if unfinished_plans:
                    total_profit = sum(p.get('profit', 0) or 0 for p in unfinished_plans)
                    total_buy_amount = sum(p.get('buy_amount', 0) or 0 for p in unfinished_plans)
                    profit_rate = (total_profit / total_buy_amount * 100) if total_buy_amount > 0 else 0
                    stock['plan_profit'] = total_profit
                    stock['plan_profit_rate'] = profit_rate
                    if total_profit > 0:
                        stock['plan_status'] = 'profit'
                    elif total_profit < 0:
                        stock['plan_status'] = 'loss'
                    else:
                        stock['plan_status'] = 'neutral'
                else:
                    stock['plan_status'] = None
                    stock['plan_profit'] = 0
                    stock['plan_profit_rate'] = 0
        finally:
            manager.disconnect()
        
        return {"stocks": stocks, "count": len(stocks)}
    finally:
        conn.close()


@router.get("/stocks/realtime/{stock_code}")
async def get_stock_realtime(stock_code: str):
    """获取股票实时行情"""
    fetcher = DataFetcher(DB_PATH)
    fetcher.connect()
    try:
        result = fetcher.get_stock_realtime(stock_code)
        if result is None:
            raise HTTPException(status_code=404, detail="股票不存在")
        return result
    finally:
        fetcher.disconnect()


@router.get("/stocks/kline/{stock_code}")
async def get_stock_kline(stock_code: str, days: int = 60):
    """获取股票K线数据"""
    fetcher = DataFetcher(DB_PATH)
    fetcher.connect()
    try:
        result = fetcher.get_kline_data(stock_code, days)
        if result is None:
            raise HTTPException(status_code=404, detail="无法获取K线数据")
        return {"stock_code": stock_code, "data": result.to_dict(orient='records')}
    finally:
        fetcher.disconnect()


@router.get("/stocks/indicators/{stock_code}")
async def get_stock_indicators(stock_code: str):
    """获取股票技术指标"""
    fetcher = DataFetcher(DB_PATH)
    fetcher.connect()
    try:
        kline = fetcher.get_kline_data(stock_code, 60)
        if kline is None:
            raise HTTPException(status_code=404, detail="无法获取K线数据")
        indicators = fetcher.calculate_technical_indicators(kline)
        if indicators is None:
            raise HTTPException(status_code=500, detail="计算技术指标失败")
        return indicators
    finally:
        fetcher.disconnect()


@router.get("/stocks/pool")
async def get_stock_pool():
    """获取行业股票池"""
    return {
        "industries": list(INDUSTRY_STOCK_POOL.keys()),
        "total_stocks": sum(len(stocks) for stocks in INDUSTRY_STOCK_POOL.values()),
        "stock_pool": INDUSTRY_STOCK_POOL
    }


@router.post("/stocks/evaluate")
async def evaluate_single_stock(request: EvaluateRequest):
    """评价单个股票"""
    import sys
    import os
    skills_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'skills')
    sys.path.insert(0, skills_path)
    
    from stock_evaluator_skills import StockEvaluatorSkills
    
    evaluator = StockEvaluatorSkills()
    evaluator.connect()
    
    try:
        result = evaluator.evaluate_stock(request.stock_code)
        return {
            'stock_code': request.stock_code,
            'success': True,
            'composite_score': result.get('composite_score', 0),
            'rating': result.get('rating', ''),
            'result': result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        evaluator.disconnect()


@router.post("/stocks/batch-evaluate")
async def batch_evaluate_stocks(request: BatchEvaluateRequest):
    """批量评价股票"""
    import sys
    import os
    skills_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'skills')
    sys.path.insert(0, skills_path)
    
    from stock_evaluator_skills import StockEvaluatorSkills
    
    evaluator = StockEvaluatorSkills()
    evaluator.connect()
    
    results = []
    success_count = 0
    
    for stock_code in request.stock_codes:
        try:
            result = evaluator.evaluate_stock(stock_code)
            results.append({
                'stock_code': stock_code,
                'success': True,
                'composite_score': result.get('composite_score', 0),
                'rating': result.get('rating', '')
            })
            success_count += 1
        except Exception as e:
            results.append({
                'stock_code': stock_code,
                'success': False,
                'error': str(e)
            })
    
    evaluator.disconnect()
    
    return {
        'results': results,
        'total': success_count,
        'failed': len(request.stock_codes) - success_count
    }


@router.post("/trade/plan")
async def create_trade_plan(plan: TradePlanCreate):
    """创建交易计划"""
    import uuid
    from datetime import datetime
    
    manager = TradingManager(DB_PATH)
    manager.connect()
    try:
        plan_name = plan.plan_name
        if not plan_name or plan_name == plan.stock_name:
            plan_name = f"{plan.stock_name}{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        stop_loss_price = plan.stop_loss_price
        take_profit_price = plan.take_profit_price
        
        if plan.planned_amount and plan.planned_quantity:
            current_price = plan.planned_amount / plan.planned_quantity
            if not stop_loss_price:
                stop_loss_price = round(current_price * 0.92, 2)
            if not take_profit_price:
                take_profit_price = round(current_price * 1.10, 2)
        
        plan_id = manager.create_trade_plan({
            'plan_name': plan_name,
            'account_id': plan.account_id,
            'stock_code': plan.stock_code,
            'stock_name': plan.stock_name,
            'planned_quantity': plan.planned_quantity,
            'planned_amount': plan.planned_amount,
            'stop_loss_price': stop_loss_price,
            'take_profit_price': take_profit_price
        })
        return {"plan_id": plan_id, "message": "交易计划创建成功", "plan_name": plan_name, "stop_loss_price": stop_loss_price, "take_profit_price": take_profit_price}
    finally:
        manager.disconnect()


@router.get("/trade/plan/{plan_id}")
async def get_trade_plan(plan_id: str):
    """获取交易计划"""
    manager = TradingManager(DB_PATH)
    manager.connect()
    try:
        plan = manager.get_trade_plan(plan_id)
        if plan is None:
            raise HTTPException(status_code=404, detail="交易计划不存在")
        return plan
    finally:
        manager.disconnect()


@router.delete("/trade/plan/{plan_id}")
async def delete_trade_plan(plan_id: str):
    """删除交易计划"""
    manager = TradingManager(DB_PATH)
    manager.connect()
    try:
        plan = manager.get_trade_plan(plan_id)
        if plan is None:
            raise HTTPException(status_code=404, detail="交易计划不存在")
        if plan['status'] == 'executing':
            raise HTTPException(status_code=400, detail="执行中的计划无法删除")
        success = manager.delete_trade_plan(plan_id)
        if success:
            return {"success": True, "message": "交易计划已删除"}
        else:
            raise HTTPException(status_code=500, detail="删除失败")
    finally:
        manager.disconnect()


@router.post("/trade/plan/{plan_id}/execute")
async def execute_trade_plan(plan_id: str):
    """执行交易计划"""
    manager = TradingManager(DB_PATH)
    manager.connect()
    try:
        result = manager.execute_trade_plan(plan_id)
        if result['success']:
            return result
        else:
            raise HTTPException(status_code=400, detail=result['message'])
    finally:
        manager.disconnect()


@router.get("/trade/steps")
async def list_execution_steps(plan_id: Optional[str] = None, status: Optional[str] = None):
    """获取执行步骤列表"""
    manager = TradingManager(DB_PATH)
    manager.connect()
    try:
        steps = manager.get_all_execution_steps(plan_id=plan_id, status=status)
        return {"steps": steps, "count": len(steps)}
    finally:
        manager.disconnect()


@router.post("/trade/step")
async def create_execution_step(step: dict):
    """创建执行步骤"""
    manager = TradingManager(DB_PATH)
    manager.connect()
    try:
        step_id = manager.create_execution_step(step)
        if step_id:
            return {"step_id": step_id, "message": "执行步骤创建成功"}
        else:
            raise HTTPException(status_code=500, detail="创建执行步骤失败")
    finally:
        manager.disconnect()


@router.post("/trade/step/{step_id}/execute")
async def execute_step(step_id: str, trade_price: float, trade_quantity: int, account_id: str = 'ACC001'):
    """执行步骤"""
    manager = TradingManager(DB_PATH)
    manager.connect()
    try:
        result = manager.execute_step(step_id, trade_price, trade_quantity, account_id)
        if result['success']:
            return result
        else:
            raise HTTPException(status_code=400, detail=result['message'])
    finally:
        manager.disconnect()


@router.get("/trade/plans")
async def list_trade_plans(account_id: Optional[str] = None):
    """获取交易计划列表"""
    manager = TradingManager(DB_PATH)
    manager.connect()
    try:
        if account_id:
            plans = manager.get_trade_plans_by_account(account_id)
        else:
            plans = manager.get_all_trade_plans()
        return {"plans": plans, "count": len(plans)}
    finally:
        manager.disconnect()


@router.post("/trade/record")
async def create_trade_record(record: TradeRecordCreate):
    """创建交易记录"""
    import uuid
    manager = TradingManager(DB_PATH)
    manager.connect()
    try:
        record_id = manager.create_trade_record({
            'record_id': f"REC_{uuid.uuid4().hex[:8]}",
            'account_id': record.account_id,
            'stock_code': record.stock_code,
            'stock_name': record.stock_name,
            'trade_type': record.trade_type,
            'trade_direction': record.trade_direction,
            'trade_price': record.trade_price,
            'trade_quantity': record.trade_quantity,
            'trade_amount': record.trade_amount
        })
        return {"record_id": record_id, "message": "交易记录创建成功"}
    finally:
        manager.disconnect()


@router.get("/trade/records")
async def list_trade_records(account_id: Optional[str] = None, plan_id: Optional[str] = None, stock_code: Optional[str] = None):
    """获取交易记录列表"""
    manager = TradingManager(DB_PATH)
    manager.connect()
    try:
        if account_id:
            records = manager.get_trade_records_by_account(account_id)
        else:
            records = manager.get_all_trade_records(plan_id=plan_id, stock_code=stock_code)
        return {"records": records, "count": len(records)}
    finally:
        manager.disconnect()


@router.get("/stocks/{stock_code}/trade-plans")
async def get_stock_trade_plans(stock_code: str):
    """获取股票的交易计划"""
    manager = TradingManager(DB_PATH)
    manager.connect()
    try:
        plans = manager.get_trade_plans_by_stock(stock_code)
        return {"plans": plans, "count": len(plans)}
    finally:
        manager.disconnect()


@router.get("/trade/statistics/{account_id}")
async def get_trade_statistics(account_id: str):
    """获取交易统计"""
    manager = TradingManager(DB_PATH)
    manager.connect()
    try:
        win_rate = manager.calculate_win_rate(account_id)
        profit_loss = manager.calculate_profit_loss_ratio(account_id)
        drawdown = manager.calculate_max_drawdown(account_id)
        return {
            "account_id": account_id,
            "win_rate": win_rate,
            "profit_loss_ratio": profit_loss,
            "max_drawdown": drawdown
        }
    finally:
        manager.disconnect()


@router.get("/trade/summary")
async def get_trade_summary(account_id: Optional[str] = None):
    """获取交易汇总"""
    manager = TradingManager(DB_PATH)
    manager.connect()
    try:
        summary = manager.get_trade_summary(account_id)
        return summary
    finally:
        manager.disconnect()
