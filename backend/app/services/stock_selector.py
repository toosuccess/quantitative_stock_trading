"""
选股模块
根据技术指标和基本面数据筛选符合条件的股票
使用行业股票池进行选股，避免全市场扫描
"""
import pandas as pd
import numpy as np
from datetime import datetime, date
from typing import Dict, List, Optional, Tuple
import sqlite3
from data_fetcher import DataFetcher

INDUSTRY_STOCK_POOL = {
    '新能源': ['sz300750', 'sz002594', 'sh603606', 'sh601012', 'sh600438', 'sz002460', 'sh600732', 'sh601615'],
    '新材料': ['sh600516', 'sh600111', 'sz000831', 'sh600206', 'sz300224', 'sh600390', 'sh600176', 'sz002057'],
    '6G': ['sh600498', 'sh600941', 'sh601318', 'sh600036', 'sh600588', 'sh600104', 'sh600050', 'sz000063'],
    '核聚变': ['sh601985', 'sh600875', 'sh601727', 'sh600202', 'sh600550', 'sh601179', 'sh603333', 'sh600642'],
    '消费升级': ['sh600519', 'sh601319', 'sh600276', 'sh601166', 'sh600887', 'sh600315', 'sh601888', 'sh600779'],
    '半导体': ['sh600703', 'sh600584', 'sh603986', 'sh600460', 'sh688981', 'sh603290', 'sh600171', 'sh603005'],
    '人工智能': ['sh603019', 'sh603986', 'sh600588', 'sh600410', 'sh603229', 'sh688256', 'sh600728', 'sh603083'],
    '生物医药': ['sh600276', 'sh600867', 'sh603259', 'sh600196', 'sh600521', 'sh603882', 'sh600873', 'sh603658'],
    '高端制造': ['sh600031', 'sh601138', 'sh600895', 'sh603997', 'sh603015', 'sh603667', 'sh600114', 'sh603786'],
    '数字经济': ['sh600588', 'sh600410', 'sh603019', 'sh600036', 'sh601318', 'sh600839', 'sh601138', 'sh603881']
}

STOCK_NAME_MAPPING = {
    'sz300750': '宁德时代', 'sz002594': '比亚迪', 'sh603606': '东方电缆', 'sh601012': '隆基绿能',
    'sh600438': '通威股份', 'sz002460': '赣锋锂业', 'sh600732': '爱旭股份', 'sh601615': '明阳智能',
    'sh600516': '方大炭素', 'sh600111': '北方稀土', 'sz000831': '五矿稀土', 'sh600206': '有研新材',
    'sz300224': '正海磁材', 'sh600390': '五矿资本', 'sh600176': '中国巨石', 'sz002057': '中钢天源',
    'sh600498': '烽火通信', 'sh600941': '中国移动', 'sh601318': '中国平安', 'sh600036': '招商银行',
    'sh600588': '用友网络', 'sh600104': '上汽集团', 'sh600050': '中国联通', 'sz000063': '中兴通讯',
    'sh601985': '中国核电', 'sh600875': '东方电气', 'sh601727': '上海电气', 'sh600202': '哈空调',
    'sh600550': '保变电气', 'sh601179': '中国西电', 'sh603333': '明星电力', 'sh600642': '申能股份',
    'sh600519': '贵州茅台', 'sh601319': '中国人保', 'sh600276': '恒瑞医药', 'sh601166': '兴业银行',
    'sh600887': '伊利股份', 'sh600315': '上海家化', 'sh601888': '中国中免', 'sh600779': '水井坊',
    'sh600703': '三安光电', 'sh600584': '长电科技', 'sh603986': '兆易创新', 'sh600460': '士兰微',
    'sh688981': '中芯国际', 'sh603290': '斯达半导', 'sh600171': '上海贝岭', 'sh603005': '晶方科技',
    'sh603019': '中科曙光', 'sh600410': '华胜天成', 'sh603229': '奥翔药业', 'sh688256': '寒武纪',
    'sh600728': '佳都科技', 'sh603083': '剑桥科技', 'sh600867': '通化东宝', 'sh603259': '药明康德',
    'sh600196': '复星医药', 'sh600521': '华海药业', 'sh603882': '金域医学', 'sh600873': '梅花生物',
    'sh603658': '安图生物', 'sh600031': '三一重工', 'sh601138': '工业富联', 'sh600895': '张江高科',
    'sh603997': '继峰股份', 'sh603015': '弘讯科技', 'sh603667': '五洲新春', 'sh600114': '东睦股份',
    'sh603786': '科博达', 'sh600839': '四川长虹', 'sh603881': '数据港'
}

class StockSelector:
    """选股类"""
    
    def __init__(self, db_path: str = 'trading_system.db'):
        """
        初始化选股器
        
        Args:
            db_path: 数据库文件路径
        """
        self.db_path = db_path
        self.fetcher = DataFetcher(db_path)
    
    def select_stocks(self, limit: int = 5, industry: str = None) -> List[Dict]:
        """
        选股主函数 - 从行业股票池选股
        
        Args:
            limit: 返回股票数量
            industry: 行业过滤（可选）
        
        Returns:
            符合条件的股票列表
        """
        print(f"开始选股，目标数量: {limit}，从行业股票池选股")
        
        self.fetcher.connect()
        
        try:
            stock_pool = self._get_industry_stock_pool(industry)
            print(f"行业股票池共{len(stock_pool)}只股票")
            
            selected_stocks = []
            
            for stock_info in stock_pool:
                stock_code = stock_info['code']
                stock_name = stock_info['name']
                stock_industry = stock_info['industry']
                
                realtime = self.fetcher.get_stock_realtime(stock_code[2:])
                if realtime is None:
                    continue
                
                close_price = realtime.get('last_price', 0)
                if close_price <= 0:
                    continue
                
                kline = self.fetcher.get_kline_data(stock_code[2:], 60)
                if kline is None or len(kline) < 20:
                    continue
                
                indicators = self.fetcher.calculate_technical_indicators(kline)
                if indicators is None:
                    continue
                
                stock_data = {
                    'stock_code': stock_code[2:],
                    'stock_name': stock_name,
                    'close_price': close_price,
                    'change_percent': realtime.get('change_percent', 0),
                    'volume': realtime.get('volume', 0)
                }
                
                tech_result = self._check_technical_conditions(indicators, stock_data)
                
                if tech_result['passed']:
                    score = self._calculate_score(indicators, stock_data, tech_result)
                    
                    selected_stocks.append({
                        'stock_code': stock_code[2:],
                        'stock_name': stock_name,
                        'close_price': close_price,
                        'change_percent': realtime.get('change_percent', 0),
                        'volume': realtime.get('volume', 0),
                        'industry': stock_industry,
                        'score': score,
                        'tech_result': tech_result,
                        'indicators': indicators
                    })
            
            selected_stocks.sort(key=lambda x: x['score'], reverse=True)
            
            result = selected_stocks[:limit]
            
            print(f"筛选完成，共{len(result)}只股票符合条件")
            
            return result
            
        finally:
            self.fetcher.disconnect()
    
    def _get_industry_stock_pool(self, industry: str = None) -> List[Dict]:
        """
        获取行业股票池
        
        Args:
            industry: 行业过滤（可选）
        
        Returns:
            股票列表 [{'code': 'sz300750', 'name': '宁德时代', 'industry': '新能源'}, ...]
        """
        stock_list = []
        
        if industry and industry in INDUSTRY_STOCK_POOL:
            for code in INDUSTRY_STOCK_POOL[industry]:
                stock_list.append({
                    'code': code,
                    'name': STOCK_NAME_MAPPING.get(code, f'股票{code}'),
                    'industry': industry
                })
        else:
            for ind, codes in INDUSTRY_STOCK_POOL.items():
                for code in codes:
                    stock_list.append({
                        'code': code,
                        'name': STOCK_NAME_MAPPING.get(code, f'股票{code}'),
                        'industry': ind
                    })
        
        seen = set()
        unique_list = []
        for item in stock_list:
            if item['code'] not in seen:
                seen.add(item['code'])
                unique_list.append(item)
        
        return unique_list
    
    def _check_technical_conditions(self, indicators: Dict, stock: Dict) -> Dict:
        """
        检查技术指标条件
        
        Args:
            indicators: 技术指标字典
            stock: 股票信息字典
        
        Returns:
            检查结果字典
        """
        result = {
            'ma_condition': False,
            'volume_condition': False,
            'macd_condition': False,
            'obv_condition': False,
            'bollinger_condition': False,
            'passed': False,
            'passed_count': 0
        }
        
        close_price = stock['close_price']
        ma20 = indicators.get('ma20', 0)
        ma5 = indicators.get('ma5', 0)
        
        if ma20 > 0 and close_price >= ma20 * 0.98:
            result['ma_condition'] = True
            result['passed_count'] += 1
        
        volume = indicators.get('volume', 0)
        ma5_volume = indicators.get('ma5_volume', 0)
        
        if ma5_volume > 0 and volume > ma5_volume:
            result['volume_condition'] = True
            result['passed_count'] += 1
        
        if indicators.get('diff_gt_dea_and_zero', False):
            result['macd_condition'] = True
            result['passed_count'] += 1
        
        if indicators.get('obv_gt_maobv', False):
            result['obv_condition'] = True
            result['passed_count'] += 1
        
        bb_upper = indicators.get('bb_upper', 0)
        bb_middle = indicators.get('bb_middle', 0)
        bb_lower = indicators.get('bb_lower', 0)
        
        if bb_upper > bb_middle > bb_lower > 0:
            if bb_middle <= close_price <= bb_upper:
                result['bollinger_condition'] = True
                result['passed_count'] += 1
        
        if result['passed_count'] >= 3:
            result['passed'] = True
        
        return result
    
    def _calculate_score(self, indicators: Dict, stock: Dict, tech_result: Dict) -> float:
        """
        计算综合评分
        
        Args:
            indicators: 技术指标字典
            stock: 股票信息字典
            tech_result: 技术检查结果
        
        Returns:
            综合评分
        """
        score = 0.0
        
        if tech_result['ma_condition']:
            score += 25
        if tech_result['volume_condition']:
            score += 25
        if tech_result['macd_condition']:
            score += 20
        if tech_result['obv_condition']:
            score += 15
        if tech_result['bollinger_condition']:
            score += 15
        
        return min(score, 100.0)
    
    def save_selection_results(self, selected_stocks: List[Dict]) -> bool:
        """
        保存选股结果到数据库
        
        Args:
            selected_stocks: 选中的股票列表
        
        Returns:
            是否成功
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            today = date.today().isoformat()
            
            for stock in selected_stocks:
                indicators = stock.get('indicators', {})
                
                cursor.execute('''
                INSERT OR REPLACE INTO score_record 
                (stock_code, stock_name, score_date, total_score, rating,
                ma_score, macd_score, rsi_score, bollinger_score, volume_score, obv_score,
                ma5, ma10, ma20, ma60, diff, dea, macd, rsi,
                bb_upper, bb_middle, bb_lower, close_price, volume)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    stock['stock_code'],
                    stock['stock_name'],
                    today,
                    stock['score'],
                    self._get_rating(stock['score']),
                    25 if stock['tech_result']['ma_condition'] else 0,
                    20 if stock['tech_result']['macd_condition'] else 0,
                    0,
                    15 if stock['tech_result']['bollinger_condition'] else 0,
                    25 if stock['tech_result']['volume_condition'] else 0,
                    15 if stock['tech_result']['obv_condition'] else 0,
                    indicators.get('ma5'),
                    indicators.get('ma10'),
                    indicators.get('ma20'),
                    indicators.get('ma60'),
                    indicators.get('diff'),
                    indicators.get('dea'),
                    indicators.get('macd'),
                    indicators.get('rsi'),
                    indicators.get('bb_upper'),
                    indicators.get('bb_middle'),
                    indicators.get('bb_lower'),
                    stock['close_price'],
                    stock['volume']
                ))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"保存选股结果失败: {e}")
            return False
    
    def _get_rating(self, score: float) -> str:
        """
        根据评分获取评级
        
        Args:
            score: 综合评分
        
        Returns:
            评级字符串
        """
        if score >= 90:
            return '强烈推荐'
        elif score >= 70:
            return '推荐'
        elif score >= 50:
            return '中性'
        elif score >= 30:
            return '观望'
        else:
            return '不推荐'


class StockScorer:
    """评分类"""
    
    def __init__(self, db_path: str = 'trading_system.db'):
        """
        初始化评分器
        
        Args:
            db_path: 数据库文件路径
        """
        self.db_path = db_path
        self.fetcher = DataFetcher(db_path)
    
    def calculate_score(self, stock_code: str) -> Dict:
        """
        计算股票评分
        
        Args:
            stock_code: 股票代码
        
        Returns:
            评分结果字典
        """
        self.fetcher.connect()
        
        try:
            kline = self.fetcher.get_kline_data(stock_code, 60)
            if kline is None:
                return None
            
            indicators = self.fetcher.calculate_technical_indicators(kline)
            if indicators is None:
                return None
            
            realtime = self.fetcher.get_stock_realtime(stock_code)
            
            stock_data = {
                'close_price': indicators.get('close_price', 0),
                'volume': indicators.get('volume', 0)
            }
            if realtime:
                stock_data['close_price'] = realtime.get('last_price', stock_data['close_price'])
            
            tech_score = self._calculate_technical_score(indicators, stock_data)
            
            total_score = tech_score
            
            return {
                'stock_code': stock_code,
                'stock_name': realtime['stock_name'] if realtime else '',
                'score_date': date.today().isoformat(),
                'technical_score': tech_score,
                'total_score': total_score,
                'rating': self._get_rating(total_score),
                'indicators': indicators,
                'ma_score': tech_score * 0.25,
                'macd_score': tech_score * 0.20,
                'rsi_score': tech_score * 0.15,
                'bollinger_score': tech_score * 0.15,
                'volume_score': tech_score * 0.15,
                'obv_score': tech_score * 0.10
            }
        finally:
            self.fetcher.disconnect()
    
    def _calculate_technical_score(self, indicators: Dict, stock_data: Dict = None) -> float:
        """
        计算技术面评分 - 严格按达标条件评分，不达标不给分
        
        Args:
            indicators: 技术指标字典
            stock_data: 股票信息字典（包含close_price）
        
        Returns:
            技术面评分
        """
        score = 0.0
        
        close_price = 0
        if stock_data:
            close_price = stock_data.get('close_price', 0)
        elif indicators:
            close_price = indicators.get('close_price', 0)
        
        ma5 = indicators.get('ma5', 0)
        ma10 = indicators.get('ma10', 0)
        ma20 = indicators.get('ma20', 0)
        
        price_above_ma20 = (close_price >= ma20 * 0.98) if (ma20 > 0 and close_price > 0) else False
        ma20_rising = (ma20 > ma10) if (ma10 > 0 and ma20 > 0) else False
        
        if price_above_ma20 and ma20_rising:
            score += 25
        
        volume = indicators.get('volume', 0)
        ma5_volume = indicators.get('ma5_volume', 0)
        if ma5_volume > 0 and volume > ma5_volume:
            score += 25
        
        if indicators.get('diff_gt_dea_and_zero', False):
            score += 20
        
        if indicators.get('obv_gt_maobv', False):
            score += 15
        
        bb_upper = indicators.get('bb_upper', 0)
        bb_middle = indicators.get('bb_middle', 0)
        if bb_upper > bb_middle > 0 and close_price > 0:
            if bb_middle <= close_price <= bb_upper:
                score += 15
        
        return min(score, 100.0)
    
    def _get_rating(self, score: float) -> str:
        """
        根据评分获取评级
        """
        if score >= 90:
            return '强烈推荐'
        elif score >= 70:
            return '推荐'
        elif score >= 50:
            return '中性'
        elif score >= 30:
            return '观望'
        else:
            return '不推荐'


def main():
    """测试选股和评分模块"""
    print("=" * 60)
    print("选股和评分模块测试")
    print("=" * 60)
    
    selector = StockSelector('trading_system.db')
    scorer = StockScorer('trading_system.db')
    
    print("\n1. 测试选股功能...")
    selected = selector.select_stocks(limit=5)
    
    if selected:
        print(f"\n选中{len(selected)}只股票:")
        for i, stock in enumerate(selected, 1):
            print(f"\n{i}. {stock['stock_name']}({stock['stock_code']})")
            print(f"   收盘价: {stock['close_price']:.2f}")
            print(f"   综合评分: {stock['score']:.2f}")
            print(f"   技术条件通过数: {stock['tech_result']['passed_count']}/5")
        
        print("\n2. 保存选股结果到数据库...")
        if selector.save_selection_results(selected):
            print("保存成功")
    
    print("\n3. 测试单只股票评分...")
    if selected:
        score_result = scorer.calculate_score(selected[0]['stock_code'])
        if score_result:
            print(f"股票: {score_result['stock_name']}")
            print(f"评分: {score_result['total_score']:.2f}")
            print(f"评级: {score_result['rating']}")
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)


if __name__ == "__main__":
    main()
