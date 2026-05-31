"""
股票价格定时更新服务（优化版）
每5分钟获取所有相关股票的最新股价，使用异步并发提升性能
"""
import pymysql
from pymysql.cursors import DictCursor
from datetime import datetime
import asyncio
import aiohttp
import re
import time
from app.database_config import MYSQL_CONFIG

async def fetch_stock_realtime_price_async(session: aiohttp.ClientSession, stock_code: str) -> dict:
    """
    异步获取单只股票实时价格
    
    Args:
        session: aiohttp会话
        stock_code: 股票代码（纯数字）
    
    Returns:
        价格信息字典
    """
    try:
        pure_code = re.sub(r'^(sh|sz|bj)', '', stock_code)
        secid = f"1.{pure_code}" if pure_code.startswith('6') else f"0.{pure_code}"
        url = 'https://push2delay.eastmoney.com/api/qt/stock/get'
        params = {
            'secid': secid,
            'fields': 'f43,f44,f45,f46,f47,f48,f50,f51,f52,f55,f56,f57,f58,f60,f116,f117,f162,f167'
        }
        
        async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as r:
            if r.status != 200:
                return None
            
            data = await r.json()
            if not data.get('data'):
                return None
            
            d = data['data']
            last_price = d.get('f43', 0) / 100 if d.get('f43') else 0
            pre_close = d.get('f60', 0) / 100 if d.get('f60') else 0
            change_percent = d.get('f50', 0) / 100 if d.get('f50') else 0
            
            return {
                'stock_code': pure_code,
                'stock_name': d.get('f58', ''),
                'current_price': last_price,
                'change_percent': change_percent,
                'pre_close': pre_close,
                'market_cap': d.get('f116', 0),
                'float_market_cap': d.get('f117', 0),
                'pe_ratio': d.get('f162', 0) / 100 if d.get('f162') else 0,
                'pb_ratio': d.get('f167', 0) / 100 if d.get('f167') else 0,
            }
    except Exception as e:
        print(f"获取 {stock_code} 价格失败: {e}")
        return None

async def update_stock_prices_async():
    """
    异步更新所有相关股票的最新价格（并发执行）
    """
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 开始异步更新股票价格...")
    start_time = time.time()
    
    conn = pymysql.connect(**MYSQL_CONFIG, cursorclass=DictCursor)
    cursor = conn.cursor()
    
    try:
        all_codes = set()
        all_names = {}
        
        # 收集所有股票代码
        for table in ['score_record', 'trade_plan', 'trade_record', 'stock_basic_info']:
            cursor.execute(f'SELECT DISTINCT stock_code, stock_name FROM {table} WHERE stock_code IS NOT NULL AND stock_code != ""')
            for row in cursor.fetchall():
                code = re.sub(r'^(sh|sz|bj)', '', row['stock_code'])
                all_codes.add(code)
                if row.get('stock_name'):
                    all_names[code] = row['stock_name']
        
        stocks = sorted(list(all_codes))
        
        if not stocks:
            print("没有股票需要更新")
            return
        
        print(f"共需更新 {len(stocks)} 只股票，开始并发获取...")
        
        # 使用aiohttp并发获取价格
        async with aiohttp.ClientSession() as session:
            tasks = [fetch_stock_realtime_price_async(session, code) for code in stocks]
            results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 批量更新数据库
        update_score_sql = '''
        UPDATE score_record 
        SET close_price = %s, 
            ma5 = %s,
            update_time = %s
        WHERE stock_code = %s
        '''
        
        update_basic_sql = '''
        UPDATE stock_basic_info 
        SET current_price = %s, 
            change_percent = %s,
            market_cap = %s,
            float_market_cap = %s,
            pe_ratio = %s,
            pb_ratio = %s,
            price_last_update = %s
        WHERE stock_code = %s
        '''
        
        success_count = 0
        fail_count = 0
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        for i, (code, result) in enumerate(zip(stocks, results)):
            if isinstance(result, Exception):
                fail_count += 1
                continue
                
            price_info = result
            
            if price_info and price_info['current_price'] > 0:
                cursor.execute(update_score_sql, (
                    price_info['current_price'],
                    price_info['current_price'],
                    now,
                    code
                ))
                
                cursor.execute(update_basic_sql, (
                    price_info['current_price'],
                    price_info['change_percent'],
                    price_info.get('market_cap', 0),
                    price_info.get('float_market_cap', 0),
                    price_info.get('pe_ratio', 0),
                    price_info.get('pb_ratio', 0),
                    now,
                    code
                ))
                
                success_count += 1
            else:
                fail_count += 1
        
        conn.commit()
        elapsed = time.time() - start_time
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 股票价格更新完成: 成功 {success_count}, 失败 {fail_count}, 耗时 {elapsed:.2f}秒")
        
    except Exception as e:
        print(f"更新股票价格失败: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
    finally:
        conn.close()

def update_stock_prices():
    """
    同步包装函数，用于兼容现有调用
    """
    asyncio.run(update_stock_prices_async())

if __name__ == '__main__':
    update_stock_prices()
