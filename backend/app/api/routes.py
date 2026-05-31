"""
API路由模块
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from datetime import date
import sys
import os
import json
import pymysql
from pymysql.cursors import DictCursor

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'services'))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

from database_config import MYSQL_CONFIG
from data_fetcher import DataFetcher
from stock_selector import INDUSTRY_STOCK_POOL, STOCK_NAME_MAPPING
from trading_manager import TradingManager

router = APIRouter()


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
    stock_codes: Optional[List[str]] = None


class EvaluateRequest(BaseModel):
    stock_code: str


@router.get("/accounts")
async def list_accounts():
    """获取账号列表"""
    manager = TradingManager()
    manager.connect()
    try:
        accounts = manager.get_all_accounts()
        return {"accounts": accounts, "count": len(accounts)}
    finally:
        manager.disconnect()


@router.post("/account")
async def create_account(account: AccountCreate):
    """创建账号"""
    manager = TradingManager()
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
    manager = TradingManager()
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
    manager = TradingManager()
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
    manager = TradingManager()
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
    manager = TradingManager()
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
    conn = pymysql.connect(**MYSQL_CONFIG, cursorclass=DictCursor)
    cursor = conn.cursor()
    try:
        if rating:
            cursor.execute('''
                SELECT * FROM score_record 
                WHERE rating = %s
                ORDER BY score_date DESC, total_score DESC
                LIMIT %s
            ''', (rating, limit))
        else:
            cursor.execute('''
                SELECT * FROM score_record 
                ORDER BY score_date DESC, total_score DESC
                LIMIT %s
            ''', (limit,))
        records = cursor.fetchall()
        return {"scores": records, "count": len(records)}
    finally:
        conn.close()


@router.get("/scores/{stock_code}")
async def get_score_by_code(stock_code: str):
    """获取指定股票的评分历史记录（从数据库读取）"""
    conn = pymysql.connect(**MYSQL_CONFIG, cursorclass=DictCursor)
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
        placeholders = ','.join(['%s' for _ in possible_codes])
        cursor.execute(f'''
            SELECT * FROM score_record 
            WHERE stock_code IN ({placeholders})
            ORDER BY id DESC
        ''', possible_codes)
        records = cursor.fetchall()
        if not records:
            raise HTTPException(status_code=404, detail="未找到该股票的评分记录")
        
        # 获取股票基本信息
        cursor.execute(f'''
            SELECT stock_code, stock_name, stock_abbr, exchange, industry, sector, 
                   list_date, total_shares, float_shares, market_cap, float_market_cap,
                   pe_ratio, pb_ratio, ps_ratio, dividend_yield, status
            FROM stock_basic_info 
            WHERE stock_code IN ({placeholders})
        ''', possible_codes)
        stock_info = cursor.fetchone()
        
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
    import re
    conn = pymysql.connect(**MYSQL_CONFIG, cursorclass=DictCursor)
    cursor = conn.cursor()
    try:
        # 获取所有股票的最新评分
        cursor.execute('''
            SELECT
                sr1.stock_code,
                sr1.stock_name,
                sr1.total_score as latest_score,
                sr1.composite_score,
                sr1.rating as latest_rating,
                sr1.score_date as latest_date,
                sr1.create_time,
                sr1.is_leader,
                sr1.close_price,
                sr1.technical_score,
                sr1.fundamental_score,
                sr1.news_score,
                sr1.policy_score,
                sr1.deduction_score,
                sr1.ma_score,
                sr1.macd_score,
                sr1.rsi_score,
                sr1.bollinger_score,
                sr1.volume_score,
                sr1.obv_score,
                sr1.technical_detail,
                sr1.fundamental_detail,
                sr1.news_detail,
                sr1.policy_detail,
                sr1.deduction_detail,
                sr1.summary,
                (SELECT COUNT(*) FROM score_record sr2 WHERE sr2.stock_code = sr1.stock_code) as score_count,
                COALESCE(sbi.is_favorite, 0) as is_favorite,
                sbi.review_score,
                sbi.review_opinion,
                sbi.review_time,
                sbi.conform_score
            FROM score_record sr1
            LEFT JOIN stock_basic_info sbi ON (
                sr1.stock_code = sbi.stock_code
                OR sr1.stock_code = CONCAT('sh', sbi.stock_code)
                OR sr1.stock_code = CONCAT('sz', sbi.stock_code)
                OR CONCAT('sh', sr1.stock_code) = sbi.stock_code
                OR CONCAT('sz', sr1.stock_code) = sbi.stock_code
            )
            WHERE sr1.id = (
                SELECT MAX(id) FROM score_record sr2
                WHERE sr2.stock_code = sr1.stock_code
            )
            ORDER BY sr1.composite_score DESC, sr1.total_score DESC, sr1.score_date DESC
        ''')
        stocks = cursor.fetchall()
        
        if not stocks:
            return {"stocks": [], "count": 0}
        
        # 去重：同一股票可能以不同代码格式存在（如300308和sz300308）
        seen_pure_codes = set()
        deduped_stocks = []
        for stock in stocks:
            pure_code = re.sub(r'^(sh|sz|bj)', '', stock['stock_code'])
            if pure_code not in seen_pure_codes:
                seen_pure_codes.add(pure_code)
                deduped_stocks.append(stock)
        stocks = deduped_stocks
        
        # 批量获取所有股票的历史评分
        stock_codes = [stock['stock_code'] for stock in stocks]
        placeholders = ','.join(['%s'] * len(stock_codes))
        
        cursor.execute(f'''
            SELECT stock_code, score_date, composite_score, total_score, close_price
            FROM score_record 
            WHERE stock_code IN ({placeholders})
            ORDER BY stock_code, score_date DESC, id DESC
        ''', stock_codes)
        
        all_history = cursor.fetchall()
        
        # 按股票代码分组历史数据
        history_map = {}
        for row in all_history:
            code = row['stock_code']
            if code not in history_map:
                history_map[code] = []
            if len(history_map[code]) < 10:
                history_map[code].append(row)
        
        # 填充历史数据
        for stock in stocks:
            code = stock['stock_code']
            history_rows = history_map.get(code, [])
            stock['score_history'] = [
                {'date': row['score_date'], 'score': row['composite_score'] or row['total_score']}
                for row in reversed(history_rows)
            ]
            stock['price_history'] = [
                {'date': row['score_date'], 'price': row['close_price']}
                for row in reversed(history_rows) if row['close_price']
            ]
        
        # 批量获取所有股票的交易计划
        manager = TradingManager()
        manager.connect()
        try:
            # 提取所有可能的股票代码格式（纯数字和带前缀）
            pure_codes = set()
            for stock in stocks:
                pure_code = re.sub(r'^(sh|sz|bj)', '', stock['stock_code'])
                pure_codes.add(pure_code)
            
            pure_codes_list = list(pure_codes)
            plan_placeholders = ','.join(['%s'] * len(pure_codes_list))
            
            # 构建所有可能的股票代码查询条件
            all_code_formats = []
            for code in pure_codes_list:
                all_code_formats.extend([code, f'sh{code}', f'sz{code}', f'bj{code}'])
            
            code_placeholders = ','.join(['%s'] * len(all_code_formats))
            
            # 一次性查询所有相关的交易计划
            cursor.execute(f'''
                SELECT * FROM trade_plan 
                WHERE stock_code IN ({code_placeholders})
            ''', all_code_formats)
            
            all_plans = cursor.fetchall()
            
            # 收集所有未完成计划的ID和相关股票代码
            unfinished_plan_ids = []
            plan_map = {}
            stock_codes_with_plans = set()
            for plan in all_plans:
                plan_code = re.sub(r'^(sh|sz|bj)', '', plan['stock_code'])
                if plan_code not in plan_map:
                    plan_map[plan_code] = []
                
                # 只考虑未完成的计划
                if plan.get('status') in ['pending', 'executing']:
                    plan_map[plan_code].append(plan)
                    unfinished_plan_ids.append(plan['plan_id'])
                    stock_codes_with_plans.add(plan_code)
            
            # 批量获取所有计划的交易记录
            trade_info_map = {}
            if unfinished_plan_ids:
                trade_placeholders = ','.join(['%s'] * len(unfinished_plan_ids))
                cursor.execute(f'''
                    SELECT 
                        plan_id,
                        COALESCE(SUM(CASE WHEN trade_type = '买入' THEN trade_amount ELSE 0 END), 0) as buy_amt,
                        COALESCE(SUM(CASE WHEN trade_type = '买入' THEN trade_quantity ELSE 0 END), 0) as buy_qty,
                        COALESCE(SUM(CASE WHEN trade_type = '卖出' THEN trade_amount ELSE 0 END), 0) as sell_amt,
                        COALESCE(SUM(CASE WHEN trade_type = '卖出' THEN trade_quantity ELSE 0 END), 0) as sell_qty
                    FROM trade_record 
                    WHERE plan_id IN ({trade_placeholders})
                    GROUP BY plan_id
                ''', unfinished_plan_ids)
                
                trade_records = cursor.fetchall()
                for record in trade_records:
                    trade_info_map[record['plan_id']] = record
            
            # 批量获取所有相关股票的当前价格
            price_map = {}
            if stock_codes_with_plans:
                price_code_list = list(stock_codes_with_plans)
                price_placeholders = ','.join(['%s'] * len(price_code_list))
                cursor.execute(f'''
                    SELECT stock_code, current_price 
                    FROM stock_basic_info 
                    WHERE stock_code IN ({price_placeholders})
                ''', price_code_list)
                
                price_rows = cursor.fetchall()
                for row in price_rows:
                    if row['current_price']:
                        price_map[row['stock_code']] = row['current_price']
            
            # 处理每只股票的交易计划
            for stock in stocks:
                pure_code = re.sub(r'^(sh|sz|bj)', '', stock['stock_code'])
                plans = plan_map.get(pure_code, [])
                
                if plans:
                    total_profit = 0
                    total_buy_amount = 0
                    
                    for plan in plans:
                        # 获取该计划的交易信息
                        trade_info = trade_info_map.get(plan['plan_id'], {
                            'buy_amt': 0,
                            'buy_qty': 0,
                            'sell_amt': 0,
                            'sell_qty': 0
                        })
                        
                        buy_amt = trade_info['buy_amt'] or 0
                        buy_qty = trade_info['buy_qty'] or 0
                        sell_amt = trade_info['sell_amt'] or 0
                        sell_qty = trade_info['sell_qty'] or 0
                        
                        holding_qty = buy_qty - sell_qty
                        total_buy_amount += buy_amt
                        
                        if holding_qty > 0:
                            # 优先从批量查询的价格映射中获取
                            current_price = price_map.get(pure_code)
                            if not current_price:
                                current_price = manager.get_current_price(pure_code)
                            
                            avg_cost = buy_amt / buy_qty if buy_qty > 0 else 0
                            unrealized_profit = (current_price - avg_cost) * holding_qty
                            realized_profit = sell_amt - (sell_qty * avg_cost) if sell_qty > 0 else 0
                            total_profit += unrealized_profit + realized_profit
                        else:
                            # 已清仓，直接计算已实现盈亏
                            avg_cost = buy_amt / buy_qty if buy_qty > 0 else 0
                            realized_profit = sell_amt - (sell_qty * avg_cost) if sell_qty > 0 else 0
                            total_profit += realized_profit
                    
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
    fetcher = DataFetcher()
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
    fetcher = DataFetcher()
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
    fetcher = DataFetcher()
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


class FavoriteRequest(BaseModel):
    stock_code: str


@router.post("/stocks/favorite")
async def toggle_stock_favorite(request: FavoriteRequest):
    """切换股票收藏状态"""
    import re
    conn = pymysql.connect(**MYSQL_CONFIG, cursorclass=DictCursor)
    cursor = conn.cursor()
    try:
        # 标准化股票代码（去除可能的前缀）
        pure_code = re.sub(r'^(sh|sz|bj)', '', request.stock_code.lower())

        # 查询当前收藏状态
        # 优先匹配纯数字格式（与score_record表保持一致）
        # 按优先级排序：纯数字 > 原始输入 > 带前缀格式
        cursor.execute('''
            SELECT is_favorite, stock_code as db_stock_code
            FROM stock_basic_info
            WHERE stock_code = %s
        ''', (pure_code,))
        result = cursor.fetchone()

        if not result:
            # 尝试原始输入格式
            cursor.execute('''
                SELECT is_favorite, stock_code as db_stock_code
                FROM stock_basic_info
                WHERE stock_code = %s
            ''', (request.stock_code,))
            result = cursor.fetchone()

        if not result:
            # 最后尝试带前缀的格式
            if pure_code.startswith('6'):
                prefix = 'sh'
            else:
                prefix = 'sz'
            cursor.execute('''
                SELECT is_favorite, stock_code as db_stock_code
                FROM stock_basic_info
                WHERE stock_code = %s
            ''', (f'{prefix}{pure_code}',))
            result = cursor.fetchone()

        if not result:
            # 如果还没找到，尝试更宽松的匹配
            cursor.execute('''
                SELECT is_favorite, stock_code as db_stock_code
                FROM stock_basic_info
                WHERE stock_code = %s OR stock_code LIKE %s
            ''', (request.stock_code, f'%{pure_code}%'))
            result = cursor.fetchone()

        if not result:
            return {
                'success': False,
                'message': f'股票 {request.stock_code} 不存在',
                'is_favorite': 0
            }

        # 使用数据库中的实际stock_code进行更新
        db_stock_code = result['db_stock_code']
        current_status = result['is_favorite'] or 0
        new_status = 1 if current_status == 0 else 0

        # 更新收藏状态
        cursor.execute('UPDATE stock_basic_info SET is_favorite = %s WHERE stock_code = %s',
                      (new_status, db_stock_code))
        conn.commit()

        action = "收藏" if new_status == 1 else "取消收藏"
        return {
            'success': True,
            'message': f'已{action}股票 {request.stock_code}',
            'is_favorite': new_status
        }
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f'操作失败: {str(e)}')
    finally:
        cursor.close()
        conn.close()


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
    """批量评价股票（不传参数则评价所有）"""
    import sys
    import os
    skills_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'skills')
    sys.path.insert(0, skills_path)
    
    from stock_evaluator_skills import StockEvaluatorSkills
    
    evaluator = StockEvaluatorSkills()
    evaluator.connect()
    
    # 获取股票代码列表
    stock_codes = request.stock_codes
    if not stock_codes:
        # 如果没传参数，从数据库获取所有股票代码
        cursor = evaluator.conn.cursor()
        try:
            cursor.execute('SELECT DISTINCT stock_code FROM stock_basic_info WHERE stock_code IS NOT NULL')
            stock_codes = [row[0] for row in cursor.fetchall()]
            
            if not stock_codes:
                # 如果stock_basic_info里没有，从score_record获取
                cursor.execute('SELECT DISTINCT stock_code FROM score_record WHERE stock_code IS NOT NULL')
                stock_codes = [row[0] for row in cursor.fetchall()]
        finally:
            cursor.close()
    
    if not stock_codes:
        return {
            'message': '没有找到需要评价的股票',
            'success_count': 0,
            'failed_count': 0
        }
    
    results = []
    success_count = 0
    failed_count = 0
    
    for stock_code in stock_codes:
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
            failed_count += 1
    
    evaluator.disconnect()
    
    return {
        'message': '批量评价完成',
        'results': results,
        'success_count': success_count,
        'failed_count': failed_count
    }


# ==================== 异步评价任务系统 ====================
import threading
import uuid
from datetime import datetime

# 全局任务状态存储
evaluation_tasks = {}

def run_evaluation_task(task_id: str, stock_codes: list, stock_name_map: dict = None):
    """
    在后台线程中执行评价任务
    """
    if stock_name_map is None:
        stock_name_map = {}

    try:
        import sys
        import os
        skills_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'skills')
        sys.path.insert(0, skills_path)

        from stock_evaluator_skills import StockEvaluatorSkills

        evaluator = StockEvaluatorSkills()
        evaluator.connect()

        total = len(stock_codes)
        results = []
        success_count = 0
        failed_count = 0

        for i, stock_code in enumerate(stock_codes):
            # 获取股票名称
            stock_name = stock_name_map.get(stock_code, '')
            current_stock_display = f"{stock_name} ({stock_code})" if stock_name else stock_code

            # 更新进度
            evaluation_tasks[task_id] = {
                'status': 'running',
                'current': i + 1,
                'total': total,
                'percentage': round((i + 1) / total * 100, 1),
                'currentStock': current_stock_display,
                'successCount': success_count,
                'failedCount': failed_count,
                'startTime': evaluation_tasks[task_id]['startTime'],
                'message': f'正在评价 {current_stock_display} ({i+1}/{total})'
            }
            
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
                failed_count += 1
        
        evaluator.disconnect()
        
        # 标记任务完成
        evaluation_tasks[task_id] = {
            'status': 'completed',
            'current': total,
            'total': total,
            'percentage': 100.0,
            'currentStock': '',
            'successCount': success_count,
            'failedCount': failed_count,
            'startTime': evaluation_tasks[task_id]['startTime'],
            'endTime': datetime.now().isoformat(),
            'message': f'评价完成，成功{success_count}只，失败{failed_count}只',
            'results': results
        }
        
    except Exception as e:
        # 标记任务失败
        evaluation_tasks[task_id] = {
            'status': 'failed',
            'error': str(e),
            'message': f'评价任务失败: {str(e)}'
        }


@router.post("/stocks/batch-evaluate-async")
async def start_batch_evaluate_async(request: Optional[BatchEvaluateRequest] = None):
    """
    启动异步批量评价任务（后台运行，不阻塞）
    
    返回task_id，用于查询进度
    """
    # 获取股票代码列表
    stock_codes = request.stock_codes if request else None
    
    if not stock_codes:
        conn = pymysql.connect(**MYSQL_CONFIG, cursorclass=DictCursor)
        cursor = conn.cursor()
        try:
            cursor.execute('SELECT DISTINCT stock_code, stock_name FROM stock_basic_info WHERE stock_code IS NOT NULL')
            rows = cursor.fetchall()
            stock_codes = [row['stock_code'] for row in rows]
            stock_name_map = {row['stock_code']: row['stock_name'] for row in rows}

            if not stock_codes:
                cursor.execute('SELECT DISTINCT stock_code FROM score_record WHERE stock_code IS NOT NULL')
                stock_codes = [row['stock_code'] for row in cursor.fetchall()]
                stock_name_map = {}
        finally:
            cursor.close()
            conn.close()
    else:
        stock_name_map = {}
    
    if not stock_codes:
        return {
            'success': False,
            'message': '没有找到需要评价的股票'
        }
    
    # 创建任务
    task_id = str(uuid.uuid4())
    evaluation_tasks[task_id] = {
        'status': 'pending',
        'current': 0,
        'total': len(stock_codes),
        'percentage': 0.0,
        'currentStock': '',
        'successCount': 0,
        'failedCount': 0,
        'startTime': datetime.now().isoformat(),
        'message': '任务已创建，等待执行...'
    }
    
    # 启动后台线程执行评价
    thread = threading.Thread(target=run_evaluation_task, args=(task_id, stock_codes, stock_name_map))
    thread.daemon = True  # 设置为守护线程，主程序退出时自动结束
    thread.start()
    
    return {
        'success': True,
        'taskId': task_id,
        'message': f'已启动评价任务，共{len(stock_codes)}只股票',
        'total': len(stock_codes)
    }


@router.get("/stocks/evaluate-progress/{task_id}")
async def get_evaluate_progress(task_id: str):
    """
    查询异步评价任务进度
    """
    if task_id not in evaluation_tasks:
        raise HTTPException(status_code=404, detail='任务不存在')
    
    task = evaluation_tasks[task_id]
    
    return {
        'taskId': task_id,
        **task
    }


@router.post("/trade/plan")
async def create_trade_plan(plan: TradePlanCreate):
    """创建交易计划"""
    import uuid
    from datetime import datetime
    
    manager = TradingManager()
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
    manager = TradingManager()
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
    manager = TradingManager()
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
    manager = TradingManager()
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
    manager = TradingManager()
    manager.connect()
    try:
        steps = manager.get_all_execution_steps(plan_id=plan_id, status=status)
        
        plan_cache = {}
        for step in steps:
            pid = step.get('plan_id')
            if pid not in plan_cache:
                plan = manager.get_trade_plan(pid)
                buy_info = manager.get_plan_buy_info(pid)
                plan_cache[pid] = {'plan': plan, 'buy_info': buy_info}
            
            buy_info = plan_cache[pid]['buy_info']
            step['avg_cost_price'] = buy_info['avg_cost_price']
            step['current_price'] = step.get('current_price') or 0
        
        return {"steps": steps, "count": len(steps)}
    finally:
        manager.disconnect()


@router.post("/trade/step")
async def create_execution_step(step: dict):
    """创建执行步骤"""
    manager = TradingManager()
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
    manager = TradingManager()
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
    manager = TradingManager()
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
    manager = TradingManager()
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
    manager = TradingManager()
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
    manager = TradingManager()
    manager.connect()
    try:
        plans = manager.get_trade_plans_by_stock(stock_code)
        return {"plans": plans, "count": len(plans)}
    finally:
        manager.disconnect()


@router.get("/trade/statistics/{account_id}")
async def get_trade_statistics(account_id: str):
    """获取交易统计"""
    manager = TradingManager()
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
    manager = TradingManager()
    manager.connect()
    try:
        summary = manager.get_trade_summary(account_id)
        return summary
    finally:
        manager.disconnect()


@router.get("/trade/sell-analysis")
async def get_sell_analysis():
    """获取卖出分析数据"""
    manager = TradingManager()
    manager.connect()
    try:
        result = manager.get_sell_analysis()
        return result
    finally:
        manager.disconnect()


# ==================== 新闻动态API ====================

@router.get("/news")
async def get_market_news(
    category: Optional[str] = None,
    importance: Optional[str] = None,
    limit: int = 20
):
    """
    获取市场新闻动态
    
    Args:
        category: 分类筛选（市场要闻/行业动态/交易机会）
        importance: 重要程度筛选（high/medium/limit）
        limit: 返回数量限制
    """
    conn = pymysql.connect(**MYSQL_CONFIG, cursorclass=DictCursor)
    cursor = conn.cursor()
    
    try:
        # 确保表存在
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS market_news (
                id INT AUTO_INCREMENT PRIMARY KEY,
                title VARCHAR(500) NOT NULL,
                summary TEXT,
                source VARCHAR(50),
                category VARCHAR(50),
                url VARCHAR(1000),
                publish_time DATETIME,
                importance ENUM('high', 'medium', 'low') DEFAULT 'medium',
                stock_code VARCHAR(20),
                stock_name VARCHAR(50),
                change_percent DECIMAL(10,4),
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_category (category),
                INDEX idx_importance (importance),
                INDEX idx_publish_time (publish_time)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        ''')
        
        # 构建查询条件
        where_conditions = []
        params = []
        
        if category:
            where_conditions.append('category = %s')
            params.append(category)
        
        if importance:
            where_conditions.append('importance = %s')
            params.append(importance)
        
        where_clause = ' AND '.join(where_conditions) if where_conditions else '1=1'
        
        # 查询新闻（按重要程度和时间排序）
        cursor.execute(f'''
            SELECT * FROM market_news 
            WHERE {where_clause}
            ORDER BY 
                CASE importance 
                    WHEN 'high' THEN 1 
                    WHEN 'medium' THEN 2 
                    ELSE 3 
                END,
                publish_time DESC, 
                created_at DESC
            LIMIT %s
        ''', params + [limit])
        
        news_list = cursor.fetchall()
        
        # 获取统计信息
        cursor.execute('SELECT COUNT(*) as total FROM market_news')
        total = cursor.fetchone()['total']
        
        cursor.execute("SELECT COUNT(*) as count FROM market_news WHERE importance = 'high'")
        high_count = cursor.fetchone()['count']
        
        cursor.execute("SELECT MAX(created_at) as last_update FROM market_news")
        last_update = cursor.fetchone()['last_update']
        
        return {
            'success': True,
            'news': news_list,
            'total': total,
            'highlights_count': high_count,
            'last_update': str(last_update) if last_update else None,
            'categories': ['市场要闻', '行业动态', '交易机会']
        }
        
    except Exception as e:
        print(f"获取新闻失败: {e}")
        return {
            'success': False,
            'message': str(e),
            'news': []
        }
    finally:
        conn.close()


@router.post("/news/refresh")
async def refresh_news():
    """
    手动触发新闻刷新（立即获取最新新闻）
    """
    import threading
    from app.services.news_fetcher import update_all_news
    
    # 在后台线程中执行刷新
    def run_refresh():
        try:
            update_all_news()
        except Exception as e:
            print(f"新闻刷新失败: {e}")
    
    thread = threading.Thread(target=run_refresh)
    thread.daemon = True
    thread.start()
    
    return {
        'success': True,
        'message': '新闻刷新任务已启动，请稍后查看'
    }


# ==================== 复审信息查询API（只读） ====================

@router.get("/stocks/{stock_code}/review-info")
async def get_stock_review_info(stock_code: str):
    """
    查询单只股票的复审信息（只读接口）
    
    前端展示用，数据由Trae AI调用复审技能生成并存储
    """
    conn = pymysql.connect(**MYSQL_CONFIG, cursorclass=DictCursor)
    cursor = conn.cursor()
    
    try:
        # 标准化股票代码
        pure_code = stock_code.lower().replace('sh', '').replace('sz', '').replace('bj', '')
        
        cursor.execute('''
            SELECT 
                stock_code,
                stock_name,
                industry,
                review_score,
                review_opinion,
                review_time,
                review_detail,
                conform_score
            FROM stock_basic_info 
            WHERE stock_code = %s OR stock_code = %s
        ''', (pure_code, pure_code.upper()))
        
        result = cursor.fetchone()
        
        if not result:
            raise HTTPException(status_code=404, detail=f"股票 {stock_code} 未找到或尚未进行复审")
        
        if result['review_score'] is None:
            return {
                'success': True,
                'stock_code': pure_code,
                'stock_name': result['stock_name'],
                'reviewed': False,
                'message': '该股票尚未进行复审'
            }
        
        # 解析JSON详情
        review_detail = {}
        if result['review_detail']:
            try:
                if isinstance(result['review_detail'], str):
                    review_detail = json.loads(result['review_detail'])
                else:
                    review_detail = dict(result['review_detail'])
            except Exception as e:
                print(f"解析复审详情JSON失败: {e}")
        
        return {
            'success': True,
            'stock_code': result['stock_code'],
            'stock_name': result['stock_name'],
            'industry': result.get('industry'),
            'reviewed': True,
            'review_score': float(result['review_score']) if result['review_score'] else None,
            'review_rating': review_detail.get('scores_breakdown', {}).get('total_score', {}).get('rating') or _get_rating_from_score(float(result['review_score'])),
            'review_opinion': result['review_opinion'],
            'review_time': str(result['review_time']) if result['review_time'] else None,
            'review_detail': review_detail,
            'conform_score': float(result['conform_score']) if result['conform_score'] is not None else (review_detail.get('conform_score')),
            # 便捷字段：直接提取关键指标
            'macd_score': review_detail.get('indicators', {}),
            'ma_info': {
                'MA20': review_detail.get('indicators', {}).get('MA20'),
                'MA60': review_detail.get('indicators', {}).get('MA60'),
                'deviation': review_detail.get('indicators', {}).get('deviation')
            },
            'dmi_info': {
                'DI_PLUS': review_detail.get('indicators', {}).get('DI_PLUS'),
                'DI_MINUS': review_detail.get('indicators', {}).get('DI_MINUS'),
                'ADX': review_detail.get('indicators', {}).get('ADX')
            },
            'sector_info': review_detail.get('sector_info', {}),
            'veto_triggered': review_detail.get('veto_triggered', False)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"查询复审信息失败: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"查询复审信息失败: {str(e)}")
    finally:
        conn.close()


@router.get("/stocks/review-list")
async def get_review_list(
    rating: Optional[str] = None,
    min_score: Optional[float] = None,
    limit: int = 50
):
    """
    查询所有已完成复审的股票列表（只读接口）
    
    Args:
        rating: 评级筛选（强烈推荐/推荐/中性/谨慎/回避）
        min_score: 最低得分筛选
        limit: 返回数量限制
    """
    conn = pymysql.connect(**MYSQL_CONFIG, cursorclass=DictCursor)
    cursor = conn.cursor()
    
    try:
        where_conditions = ['review_score IS NOT NULL']
        params = []
        
        if rating:
            where_conditions.append('''
                EXISTS (
                    SELECT 1 FROM JSON_EXTRACT(review_detail, '$.scores_breakdown') 
                    WHERE JSON_EXTRACT(review_detail, '$.rating') = %s
                )
            ''')
            params.append(rating)
        
        if min_score is not None:
            where_conditions.append('review_score >= %s')
            params.append(min_score)
        
        where_clause = ' AND '.join(where_conditions)
        
        cursor.execute(f'''
            SELECT 
                stock_code,
                stock_name,
                industry,
                review_score,
                review_time,
                review_opinion,
                JSON_EXTRACT(review_detail, '$.rating') as rating,
                JSON_EXTRACT(review_detail, '$.veto_triggered') as veto_triggered,
                JSON_EXTRACT(review_detail, '$.sector_info.score_impact') as sector_impact,
                JSON_EXTRACT(review_detail, '$.conform_score') as conform_score
            FROM stock_basic_info 
            WHERE {where_clause}
            ORDER BY review_score DESC, review_time DESC
            LIMIT %s
        ''', params + [limit])
        
        results = cursor.fetchall()
        
        # 处理结果
        review_list = []
        for row in results:
            item = {
                'stock_code': row['stock_code'],
                'stock_name': row['stock_name'],
                'industry': row.get('industry'),
                'review_score': float(row['review_score']) if row['review_score'] else None,
                'review_time': str(row['review_time']) if row['review_time'] else None,
                'review_opinion': row.get('review_opinion'),
                'rating': _clean_json_value(row.get('rating')),
                'veto_triggered': _clean_json_value(row.get('veto_triggered')) == True,
                'sector_impact': float(_clean_json_value(row.get('sector_impact')) or 0),
                'conform_score': float(_clean_json_value(row.get('conform_score')) or 0) if row.get('conform_score') is not None else None
            }
            review_list.append(item)
        
        # 统计信息
        cursor.execute('SELECT COUNT(*) as total FROM stock_basic_info WHERE review_score IS NOT NULL')
        total = cursor.fetchone()['total']
        
        cursor.execute('''
            SELECT 
                SUM(CASE WHEN review_score >= 85 THEN 1 ELSE 0 END) as strong_buy,
                SUM(CASE WHEN review_score >= 70 AND review_score < 85 THEN 1 ELSE 0 END) as buy,
                SUM(CASE WHEN review_score >= 55 AND review_score < 70 THEN 1 ELSE 0 END) as neutral,
                SUM(CASE WHEN review_score >= 40 AND review_score < 55 THEN 1 ELSE 0 END) as cautious,
                SUM(CASE WHEN review_score < 40 THEN 1 ELSE 0 END) as avoid
            FROM stock_basic_info 
            WHERE review_score IS NOT NULL
        ''')
        stats = cursor.fetchone()
        
        return {
            'success': True,
            'reviews': review_list,
            'count': len(review_list),
            'total_reviewed': total,
            'statistics': {
                'strong_recommendation': int(stats['strong_buy'] or 0),
                'recommendation': int(stats['buy'] or 0),
                'neutral': int(stats['neutral'] or 0),
                'cautious': int(stats['cautious'] or 0),
                'avoid': int(stats['avoid'] or 0)
            },
            'average_score': sum([r['review_score'] for r in review_list if r['review_score']]) / len(review_list) if review_list else 0
        }
        
    except Exception as e:
        print(f"查询复审列表失败: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"查询复审列表失败: {str(e)}")
    finally:
        conn.close()


def _get_rating_from_score(score):
    """根据分数获取评级"""
    if score >= 85:
        return "强烈推荐"
    elif score >= 70:
        return "推荐"
    elif score >= 55:
        return "中性"
    elif score >= 40:
        return "谨慎"
    else:
        return "回避"


def _clean_json_value(value):
    """清理JSON提取的值（去除引号等）"""
    if value is None:
        return None
    if isinstance(value, str):
        value = value.strip('"').strip("'")
        if value.lower() == 'true':
            return True
        elif value.lower() == 'false':
            return False
        try:
            return float(value)
        except:
            return value


