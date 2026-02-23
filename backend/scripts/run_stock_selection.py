"""
执行选股技能
从政策导向行业中筛选符合条件的股票
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from skills.stock_selector_skills import (
    POLICY_ORIENTED_INDUSTRIES,
    run_stock_selection
)
from skills.stock_evaluator_skills import run_stock_evaluation
from datetime import date
import sqlite3

def run_selection_and_evaluation(limit=5, evaluate=True):
    """
    执行选股和评价流程
    
    Args:
        limit: 返回股票数量
        evaluate: 是否执行评价
    
    Returns:
        选股结果
    """
    print("=" * 60)
    print("执行选股技能")
    print("=" * 60)
    
    industries = list(POLICY_ORIENTED_INDUSTRIES.keys())
    print(f"\n政策导向行业: {industries}")
    
    result = run_stock_selection(industries, max_per_industry=10)
    
    if not result or result.get('total', 0) == 0:
        print("未找到符合条件的股票")
        return None
    
    print(f"\n选股完成，共 {result['total']} 只股票")
    
    if evaluate:
        print("\n开始评价选中的股票...")
        stocks = result.get('stocks', [])
        evaluated_count = 0
        
        for stock in stocks[:limit]:
            stock_code = stock.get('code')
            stock_name = stock.get('name')
            industry = stock.get('industry')
            
            if stock_code and stock_name:
                try:
                    run_stock_evaluation(stock_code, stock_name, industry)
                    evaluated_count += 1
                except Exception as e:
                    print(f"评价{stock_name}失败: {e}")
        
        print(f"\n评价完成，共评价 {evaluated_count} 只股票")
    
    return result


if __name__ == "__main__":
    result = run_selection_and_evaluation(limit=5)
    
    if result:
        print("\n" + "=" * 60)
        print("选股和评价完成!")
        print("=" * 60)
    else:
        print("\n选股失败，请检查日志")
