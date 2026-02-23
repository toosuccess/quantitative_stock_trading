"""
插入模拟选股数据到数据库
"""
import sqlite3
from datetime import date
import random

def insert_mock_stocks():
    """插入模拟股票数据"""
    
    mock_stocks = [
        {'code': '600410', 'name': '华胜天成', 'industry': '人工智能', 'score': 85, 'rating': '推荐'},
        {'code': '603986', 'name': '兆易创新', 'industry': '半导体', 'score': 82, 'rating': '推荐'},
        {'code': '600703', 'name': '三安光电', 'industry': '半导体', 'score': 78, 'rating': '推荐'},
        {'code': '300750', 'name': '宁德时代', 'industry': '新能源', 'score': 75, 'rating': '推荐'},
        {'code': '600276', 'name': '恒瑞医药', 'industry': '生物医药', 'score': 72, 'rating': '推荐'},
    ]
    
    conn = sqlite3.connect('database/trading_system.db')
    cursor = conn.cursor()
    
    today = date.today().isoformat()
    
    for stock in mock_stocks:
        close_price = random.uniform(10, 100)
        ma5 = close_price * random.uniform(0.95, 1.05)
        ma10 = close_price * random.uniform(0.90, 1.10)
        ma20 = close_price * random.uniform(0.85, 1.15)
        ma60 = close_price * random.uniform(0.80, 1.20)
        
        cursor.execute('''
        INSERT OR REPLACE INTO score_record 
        (stock_code, stock_name, score_date, total_score, rating,
        ma_score, macd_score, bollinger_score, volume_score,
        ma5, ma10, ma20, ma60, diff, dea,
        bb_upper, bb_middle, bb_lower, close_price, volume,
        technical_reason)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            stock['code'],
            stock['name'],
            today,
            stock['score'],
            stock['rating'],
            25,
            20,
            15,
            25,
            round(ma5, 2),
            round(ma10, 2),
            round(ma20, 2),
            round(ma60, 2),
            round(random.uniform(-1, 2), 4),
            round(random.uniform(-0.5, 1), 4),
            round(close_price * 1.05, 2),
            round(close_price, 2),
            round(close_price * 0.95, 2),
            round(close_price, 2),
            random.randint(1000000, 10000000),
            f"{stock['industry']}行业龙头，技术指标符合选股条件"
        ))
        
        print(f"插入: {stock['name']}({stock['code']}) - 评分: {stock['score']}")
    
    conn.commit()
    conn.close()
    print(f"\n成功插入{len(mock_stocks)}只股票到数据库")

if __name__ == "__main__":
    insert_mock_stocks()
