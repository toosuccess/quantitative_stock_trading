"""
选股技能
职责：根据十五五规划选股，输出到stock_basic_info表
"""

import akshare as ak
import sqlite3
import os
from datetime import datetime, date

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                        'backend', 'database', 'trading_system.db')

POLICY_ORIENTED_INDUSTRIES = {
    '新能源': {
        'keywords': ['光伏', '风电', '储能', '锂电池', '新能源汽车', '充电桩', '氢能', '电池'],
        'policy_support': '"十五五"规划重点支持新能源产业发展，推动能源结构转型',
        'industry_type': '战略性新兴产业',
        'growth_potential': '高'
    },
    '新材料': {
        'keywords': ['新材料', '稀土', '磁性材料', '碳纤维', '石墨烯', '半导体材料', '有机硅'],
        'policy_support': '"十五五"规划重点支持新材料产业发展，突破关键材料技术',
        'industry_type': '战略性新兴产业',
        'growth_potential': '高'
    },
    '6G': {
        'keywords': ['6G', '通信', '光通信', '物联网', '卫星通信', '射频', '基站'],
        'policy_support': '"十五五"规划重点支持6G技术研发和产业化',
        'industry_type': '未来产业',
        'growth_potential': '极高'
    },
    '核聚变': {
        'keywords': ['核聚变', '核电', '核能', '超导', '等离子体'],
        'policy_support': '"十五五"规划重点支持核聚变技术研发',
        'industry_type': '未来产业',
        'growth_potential': '极高'
    },
    '消费升级': {
        'keywords': ['白酒', '食品', '家电', '家居', '化妆品', '旅游', '餐饮'],
        'policy_support': '"十五五"规划重点支持消费升级，扩大内需',
        'industry_type': '民生消费',
        'growth_potential': '中高'
    },
    '半导体': {
        'keywords': ['半导体', '芯片', '集成电路', '晶圆', '封测', 'EDA', '光刻'],
        'policy_support': '"十五五"规划重点支持半导体产业发展，实现自主可控',
        'industry_type': '战略性新兴产业',
        'growth_potential': '高'
    },
    '人工智能': {
        'keywords': ['人工智能', 'AI', '大模型', '机器学习', '深度学习', '智能驾驶', '机器人'],
        'policy_support': '"十五五"规划重点支持人工智能产业发展',
        'industry_type': '未来产业',
        'growth_potential': '极高'
    },
    '生物医药': {
        'keywords': ['生物', '医药', '创新药', '疫苗', '医疗器械', 'CXO', '基因'],
        'policy_support': '"十五五"规划重点支持生物医药产业发展',
        'industry_type': '战略性新兴产业',
        'growth_potential': '高'
    },
    '高端制造': {
        'keywords': ['数控', '机床', '工业母机', '机器人', '自动化', '精密制造', '激光'],
        'policy_support': '"十五五"规划重点支持高端制造产业发展，推动制造业升级',
        'industry_type': '战略性新兴产业',
        'growth_potential': '高'
    },
    '数字经济': {
        'keywords': ['云计算', '大数据', '数据中心', '软件', '信息安全', '智慧城市', '数字货币'],
        'policy_support': '"十五五"规划重点支持数字经济发展',
        'industry_type': '未来产业',
        'growth_potential': '极高'
    }
}


class StockSelectorSkills:
    """选股技能类"""
    
    def __init__(self, db_path=None):
        self.db_path = db_path or DB_PATH
        self.conn = None
    
    def connect(self):
        """连接数据库"""
        self.conn = sqlite3.connect(self.db_path)
        return self.conn
    
    def disconnect(self):
        """断开数据库连接"""
        if self.conn:
            self.conn.close()
            self.conn = None
    
    def get_industry_stocks(self, industry_name, max_count=20):
        """
        获取指定行业的股票列表
        
        Args:
            industry_name: 行业名称
            max_count: 最大返回数量
        
        Returns:
            list: 股票列表
        """
        if industry_name not in POLICY_ORIENTED_INDUSTRIES:
            print(f"未知行业: {industry_name}")
            return []
        
        industry_info = POLICY_ORIENTED_INDUSTRIES[industry_name]
        keywords = industry_info['keywords']
        stocks = []
        
        try:
            df = ak.stock_zh_a_spot_em()
            if df is None or len(df) == 0:
                return []
            
            for _, row in df.iterrows():
                name = str(row.get('名称', ''))
                code = str(row.get('代码', ''))
                
                if 'ST' in name or 'st' in name:
                    continue
                
                for keyword in keywords:
                    if keyword in name:
                        market = 'sh' if code.startswith('6') else 'sz' if code.startswith('0') or code.startswith('3') else 'bj'
                        stocks.append({
                            'code': f"{market}{code}",
                            'name': name,
                            'industry': industry_name,
                            'price': float(row.get('最新价', 0)),
                            'change_pct': float(row.get('涨跌幅', 0)),
                            'volume': int(row.get('成交量', 0)),
                            'amount': float(row.get('成交额', 0))
                        })
                        break
                
                if len(stocks) >= max_count:
                    break
            
            print(f"动态获取{industry_name}行业股票: {len(stocks)}只")
            
        except Exception as e:
            print(f"获取{industry_name}行业股票失败: {e}")
        
        return stocks
    
    def filter_st_stocks(self, stocks):
        """
        过滤ST股票
        
        Args:
            stocks: 股票列表
        
        Returns:
            list: 过滤后的股票列表
        """
        return [s for s in stocks if 'ST' not in s.get('name', '') and 'st' not in s.get('name', '')]
    
    def save_to_database(self, stocks):
        """
        保存股票到stock_basic_info表
        
        Args:
            stocks: 股票列表
        
        Returns:
            int: 保存成功的数量
        """
        if not self.conn:
            self.connect()
        
        cursor = self.conn.cursor()
        saved_count = 0
        
        for stock in stocks:
            try:
                cursor.execute('''
                    INSERT OR REPLACE INTO stock_basic_info 
                    (stock_code, stock_name, industry, status, create_time, update_time)
                    VALUES (?, ?, ?, 'normal', ?, ?)
                ''', (
                    stock['code'],
                    stock['name'],
                    stock['industry'],
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                ))
                saved_count += 1
            except Exception as e:
                print(f"保存{stock['name']}失败: {e}")
        
        self.conn.commit()
        return saved_count
    
    def select_stocks(self, industries=None, max_per_industry=20):
        """
        选股主流程
        
        Args:
            industries: 行业列表，None表示所有行业
            max_per_industry: 每个行业最大股票数
        
        Returns:
            dict: 选股结果
        """
        if industries is None:
            industries = list(POLICY_ORIENTED_INDUSTRIES.keys())
        
        print("=" * 60)
        print("开始选股")
        print(f"行业数量: {len(industries)}")
        print(f"每行业最大股票数: {max_per_industry}")
        print("=" * 60)
        
        all_stocks = []
        
        for industry in industries:
            stocks = self.get_industry_stocks(industry, max_per_industry)
            stocks = self.filter_st_stocks(stocks)
            all_stocks.extend(stocks)
        
        print(f"\n共获取 {len(all_stocks)} 只股票")
        
        saved_count = self.save_to_database(all_stocks)
        print(f"保存到数据库: {saved_count} 只")
        
        print("=" * 60)
        print("选股完成")
        print("=" * 60)
        
        return {
            'total': len(all_stocks),
            'saved': saved_count,
            'stocks': all_stocks
        }


def run_stock_selection(industries=None, max_per_industry=20):
    """
    运行选股（供外部调用）
    
    Args:
        industries: 行业列表
        max_per_industry: 每行业最大股票数
    
    Returns:
        dict: 选股结果
    """
    selector = StockSelectorSkills()
    selector.connect()
    result = selector.select_stocks(industries, max_per_industry)
    selector.disconnect()
    return result


if __name__ == '__main__':
    run_stock_selection()
