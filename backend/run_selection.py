import sys
sys.path.insert(0, 'app/services')
from stock_selector import StockSelector

selector = StockSelector('database/trading_system.db')
selected = selector.select_stocks(limit=5)

if selected:
    print(f'选中{len(selected)}只股票:')
    for i, stock in enumerate(selected, 1):
        print(f'{i}. {stock["stock_name"]}({stock["stock_code"]}) - 评分: {stock["score"]:.2f}')
    
    selector.save_selection_results(selected)
    print('选股结果已保存到数据库')
else:
    print('未找到符合条件的股票')
