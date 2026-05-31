"""
选股技能
职责：根据十五五规划选股，输出到stock_basic_info表
"""

import akshare as ak
import pymysql
from pymysql.cursors import DictCursor
import os
import sys
from datetime import datetime, date
import urllib3
import warnings

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
warnings.filterwarnings('ignore')

PROXY_HOST = os.environ.get('PROXY_HOST', '127.0.0.1')
PROXY_PORT = os.environ.get('PROXY_PORT', '7897')
PROXY_ENABLED = os.environ.get('PROXY_ENABLED', 'false').lower() == 'true'

if PROXY_ENABLED:
    os.environ['HTTP_PROXY'] = f'http://{PROXY_HOST}:{PROXY_PORT}'
    os.environ['HTTPS_PROXY'] = f'http://{PROXY_HOST}:{PROXY_PORT}'
    os.environ['NO_PROXY'] = 'localhost,127.0.0.1'
else:
    os.environ['HTTP_PROXY'] = ''
    os.environ['HTTPS_PROXY'] = ''
    os.environ['http_proxy'] = ''
    os.environ['https_proxy'] = ''

BACKEND_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'backend')
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app.database_config import MYSQL_CONFIG

POLICY_ORIENTED_INDUSTRIES = {
    '新能源': {
        'keywords': ['光伏', '风电', '储能', '锂电池', '新能源汽车', '充电桩', '氢能', '电池', '太阳能', '逆变器', '硅料', '硅片', '组件', '绿电', '特高压'],
        'policy_support': '"十五五"规划重点支持新能源产业发展，推动能源结构转型',
        'industry_type': '战略性新兴产业',
        'growth_potential': '高'
    },
    '新材料': {
        'keywords': ['新材料', '稀土', '磁性材料', '碳纤维', '石墨烯', '半导体材料', '有机硅', '钛合金', '高温合金', '特种玻璃', '陶瓷', '氟化工', '磷化工'],
        'policy_support': '"十五五"规划重点支持新材料产业发展，突破关键材料技术',
        'industry_type': '战略性新兴产业',
        'growth_potential': '高'
    },
    '6G': {
        'keywords': ['6G', '通信', '光通信', '物联网', '卫星通信', '射频', '基站', '光纤', '光模块', '交换机', '路由器', '天线', '滤波器'],
        'policy_support': '"十五五"规划重点支持6G技术研发和产业化',
        'industry_type': '未来产业',
        'growth_potential': '极高'
    },
    '核聚变': {
        'keywords': ['核聚变', '核电', '核能', '超导', '等离子体', '核废料', '铀', '钍'],
        'policy_support': '"十五五"规划重点支持核聚变技术研发',
        'industry_type': '未来产业',
        'growth_potential': '极高'
    },
    '消费升级': {
        'keywords': ['白酒', '食品', '家电', '家居', '化妆品', '旅游', '餐饮', '乳业', '调味品', '啤酒', '免税', '医美', '宠物', '预制菜'],
        'policy_support': '"十五五"规划重点支持消费升级，扩大内需',
        'industry_type': '民生消费',
        'growth_potential': '中高'
    },
    '半导体': {
        'keywords': ['半导体', '芯片', '集成电路', '晶圆', '封测', 'EDA', '光刻', '刻蚀', '薄膜', '设计', 'MCU', 'GPU', 'FPGA', '功率半导体', 'IGBT', 'SiC', 'GaN'],
        'policy_support': '"十五五"规划重点支持半导体产业发展，实现自主可控',
        'industry_type': '战略性新兴产业',
        'growth_potential': '高'
    },
    '人工智能': {
        'keywords': ['人工智能', 'AI', '大模型', '机器学习', '深度学习', '智能驾驶', '机器人', '算力', '智算', 'AIGC', 'ChatGPT', '自动驾驶', '智能座舱'],
        'policy_support': '"十五五"规划重点支持人工智能产业发展',
        'industry_type': '未来产业',
        'growth_potential': '极高'
    },
    '生物医药': {
        'keywords': ['生物', '医药', '创新药', '疫苗', '医疗器械', 'CXO', '基因', '中药', '仿制药', '血液制品', '体外诊断', '医美', '康复'],
        'policy_support': '"十五五"规划重点支持生物医药产业发展',
        'industry_type': '战略性新兴产业',
        'growth_potential': '高'
    },
    '高端制造': {
        'keywords': ['数控', '机床', '工业母机', '机器人', '自动化', '精密制造', '激光', '3D打印', '工业互联网', '传感器', '伺服', 'PLC', '减速器', '轴承'],
        'policy_support': '"十五五"规划重点支持高端制造产业发展，推动制造业升级',
        'industry_type': '战略性新兴产业',
        'growth_potential': '高'
    },
    '数字经济': {
        'keywords': ['云计算', '大数据', '数据中心', '软件', '信息安全', '智慧城市', '数字货币', '信创', '国产化', '操作系统', '数据库', '中间件', 'ERP'],
        'policy_support': '"十五五"规划重点支持数字经济发展',
        'industry_type': '未来产业',
        'growth_potential': '极高'
    },
    '军工': {
        'keywords': ['军工', '航天', '航空', '兵器', '舰船', '导弹', '雷达', '军用', '国防', '战机', '发动机', '卫星'],
        'policy_support': '"十五五"规划重点支持国防军工现代化建设',
        'industry_type': '国家安全',
        'growth_potential': '高'
    },
    '低空经济': {
        'keywords': ['低空', 'eVTOL', '无人机', '飞行汽车', '通航', '航空器', '直升机', '空管'],
        'policy_support': '"十五五"规划重点支持低空经济发展',
        'industry_type': '未来产业',
        'growth_potential': '极高'
    },
    '量子科技': {
        'keywords': ['量子', '量子计算', '量子通信', '量子加密', '量子测量'],
        'policy_support': '"十五五"规划重点支持量子科技研发',
        'industry_type': '未来产业',
        'growth_potential': '极高'
    }
}


class StockSelectorSkills:
    """选股技能类"""
    
    def __init__(self, db_path=None):
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
            import requests
            all_stocks = []
            url = 'https://push2delay.eastmoney.com/api/qt/clist/get'
            
            for page in range(1, 60):
                params = {
                    'pn': page,
                    'pz': 100,
                    'po': 1,
                    'np': 1,
                    'ut': 'bd1d9ddb04089700cf9c27f6f7426281',
                    'fltt': 2,
                    'invt': 2,
                    'fid': 'f12',
                    'fs': 'm:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23',
                    'fields': 'f12,f14,f2,f3,f5,f6'
                }
                r = requests.get(url, params=params, timeout=15)
                if r.status_code == 200:
                    data = r.json()
                    if data.get('data') and data['data'].get('diff'):
                        stocks_batch = data['data']['diff']
                        all_stocks.extend(stocks_batch)
                        if len(stocks_batch) < 100:
                            break
                    else:
                        break
                else:
                    break
            
            for stock in all_stocks:
                name = str(stock.get('f14', ''))
                code = str(stock.get('f12', ''))
                
                if 'ST' in name or 'st' in name:
                    continue
                
                for keyword in keywords:
                    if keyword in name:
                        market = 'sh' if code.startswith('6') else 'sz' if code.startswith('0') or code.startswith('3') else 'bj'
                        stocks.append({
                            'code': f"{market}{code}",
                            'name': name,
                            'industry': industry_name,
                            'price': float(stock.get('f2', 0)) if stock.get('f2') else 0,
                            'change_pct': float(stock.get('f3', 0)) if stock.get('f3') else 0,
                            'volume': int(stock.get('f5', 0)) if stock.get('f5') else 0,
                            'amount': float(stock.get('f6', 0)) if stock.get('f6') else 0
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
                # 提取纯股票代码（去除前缀）
                code = stock['code']
                pure_code = code[2:] if code.startswith(('sh', 'sz', 'bj')) else code
                
                # 根据股票代码判断交易所
                if pure_code.startswith('6'):
                    exchange = 'SH'
                elif pure_code.startswith('0') or pure_code.startswith('3'):
                    exchange = 'SZ'
                elif pure_code.startswith('8'):
                    exchange = 'BJ'
                else:
                    exchange = 'SZ'  # 默认深交所
                
                cursor.execute('''
                    INSERT INTO stock_basic_info 
                    (stock_code, stock_name, industry, exchange, status, create_time, update_time, is_favorite)
                    VALUES (%s, %s, %s, %s, 'normal', %s, %s, 0)
                    ON DUPLICATE KEY UPDATE
                    stock_name=VALUES(stock_name), industry=VALUES(industry), 
                    exchange=VALUES(exchange), update_time=VALUES(update_time)
                ''', (
                    pure_code,
                    stock['name'],
                    stock['industry'],
                    exchange,
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                ))
                saved_count += 1
            except Exception as e:
                print(f"保存{stock['name']}失败: {e}")
        
        self.conn.commit()
        return saved_count
    
    def select_stocks(self, industries=None, max_per_industry=10):
        if industries is None:
            industries = list(POLICY_ORIENTED_INDUSTRIES.keys())
        
        print("=" * 60)
        print("开始选股")
        print(f"行业数量: {len(industries)}")
        print(f"每行业最大股票数: {max_per_industry}")
        print(f"优先行业: {', '.join(industries)}")
        print("=" * 60)
        
        all_stocks = []
        
        for industry in industries:
            print(f"正在获取{industry}行业股票...")
            stocks = self.get_industry_stocks(industry, max_per_industry)
            stocks = self.filter_st_stocks(stocks)
            all_stocks.extend(stocks)
            print(f"{industry}行业: {len(stocks)}只股票")
        
        print(f"\n共获取 {len(all_stocks)} 只股票")
        
        if all_stocks:
            saved_count = self.save_to_database(all_stocks)
            print(f"保存到数据库: {saved_count} 只")
        else:
            saved_count = 0
            print("没有获取到股票数据")
        
        print("=" * 60)
        print("选股完成")
        print("=" * 60)
        
        return {
            'total': len(all_stocks),
            'saved': saved_count,
            'stocks': all_stocks
        }


def run_stock_selection(industries=None, max_per_industry=10):
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
