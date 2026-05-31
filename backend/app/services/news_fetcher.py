"""
股市新闻动态获取服务
定时获取行业动态、股市动态、新闻、机会等
数据来源：东方财富网、新浪财经等
"""
import requests
import re
from datetime import datetime
from typing import List, Dict, Optional
import pymysql
from pymysql.cursors import DictCursor
from app.database_config import MYSQL_CONFIG

class NewsFetcher:
    """新闻获取器"""
    
    def __init__(self):
        self.proxies = {'http': None, 'https': None}
    
    def fetch_market_news(self) -> List[Dict]:
        """
        获取市场综合新闻（东方财富网）
        
        Returns:
            新闻列表
        """
        news_list = []
        
        try:
            # 东方财富网 - 要闻中心
            url = 'https://np-listapi.eastmoney.com/comm/web/getNewsByColumns'
            params = {
                'client': 'web',
                'columnId': '0',  # 0=要闻
                'pageSize': '20',
                'sortEnd': '',
                'sortFields': '',
                'source': '',
                'type': '',
                'callback': ''
            }
            
            r = requests.get(url, params=params, timeout=15, proxies=self.proxies)
            
            if r.status_code == 200:
                data = r.json()
                
                if data.get('data') and data['data'].get('list'):
                    for item in data['data']['list'][:15]:
                        news_list.append({
                            'title': item.get('title', ''),
                            'summary': item.get('content', '')[:200] if item.get('content') else '',
                            'source': '东方财富',
                            'category': '市场要闻',
                            'url': item.get('url', ''),
                            'publish_time': self._parse_time(item.get('showtime', '')),
                            'importance': self._judge_importance(item.get('title', '')),
                            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        })
            
        except Exception as e:
            print(f"获取市场新闻失败: {e}")
        
        return news_list
    
    def fetch_industry_news(self) -> List[Dict]:
        """
        获取行业动态（东方财富行业频道）
        
        Returns:
            行业新闻列表
        """
        news_list = []
        
        try:
            # 东方财富网 - 行业资讯
            url = 'https://np-listapi.eastmoney.com/comm/web/getNewsByColumns'
            params = {
                'client': 'web',
                'columnId': '100',  # 行业
                'pageSize': '15',
                'callback': ''
            }
            
            r = requests.get(url, params=params, timeout=15, proxies=self.proxies)
            
            if r.status_code == 200:
                data = r.json()
                
                if data.get('data') and data['data'].get('list'):
                    for item in data['data']['list'][:10]:
                        news_list.append({
                            'title': item.get('title', ''),
                            'summary': item.get('content', '')[:200] if item.get('content') else '',
                            'source': '东方财富',
                            'category': '行业动态',
                            'url': item.get('url', ''),
                            'publish_time': self._parse_time(item.get('showtime', '')),
                            'importance': self._judge_importance(item.get('title', '')),
                            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        })
                        
        except Exception as e:
            print(f"获取行业新闻失败: {e}")
        
        return news_list
    
    def fetch_stock_opportunities(self) -> List[Dict]:
        """
        获取股票机会（涨停板、异动等）
        
        Returns:
            机会列表
        """
        opportunities = []
        
        try:
            # 获取今日涨停股票
            url = 'https://push2.eastmoney.com/api/qt/clist/get'
            params = {
                'pn': '1',
                'pz': '10',
                'po': '1',
                'np': '1',
                'fltt': '2',
                'invt': '2',
                'fid': 'f3',
                'fs': 'm:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23,m:0+t:81+s:2048',  # 涨停板
                'fields': 'f2,f3,f4,f12,f14'
            }
            
            r = requests.get(url, params=params, timeout=15, proxies=self.proxies)
            
            if r.status_code == 200:
                data = r.json()
                
                if data.get('data') and data['data'].get('diff'):
                    for item in data['data']['diff'][:8]:
                        code = item.get('f12', '')
                        name = item.get('f14', '')
                        change_pct = item.get('f3', 0)
                        price = item.get('f2', 0)
                        
                        opportunities.append({
                            'title': f'🚀 {name}({code}) 涨停！涨幅{change_pct}% 当前价{price}',
                            'summary': f'{name}今日强势涨停，涨幅达到{change_pct}%，值得关注后续走势。',
                            'source': '实时行情',
                            'category': '交易机会',
                            'url': '',
                            'publish_time': datetime.now().strftime('%Y-%m-%d %H:%M'),
                            'importance': 'high',
                            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                            'stock_code': code,
                            'stock_name': name,
                            'change_percent': change_pct / 100 if change_pct else 0
                        })
            
        except Exception as e:
            print(f"获取股票机会失败: {e}")
        
        return opportunities
    
    def _parse_time(self, time_str: str) -> str:
        """
        解析时间字符串
        
        Args:
            time_str: 时间字符串
            
        Returns:
            格式化后的时间
        """
        if not time_str:
            return datetime.now().strftime('%Y-%m-%d %H:%M')
        
        try:
            # 尝试解析各种时间格式
            if 'T' in time_str:
                dt = datetime.fromisoformat(time_str.replace('T', ' ').replace('Z', ''))
                return dt.strftime('%Y-%m-%d %H:%M')
            elif '-' in time_str:
                return time_str[:16]
            else:
                return time_str
        except:
            return datetime.now().strftime('%Y-%m-%d %H:%M')
    
    def _judge_importance(self, title: str) -> str:
        """
        根据标题判断重要程度
        
        Args:
            title: 新闻标题
            
        Returns:
            high/medium/low
        """
        if not title:
            return 'low'
        
        title_lower = title.lower()
        
        # 高频关键词
        high_keywords = ['重磅', '突发', '利好', '利空', '涨停', '跌停', '政策', 
                        '央行', '国务院', '监管', '重组', '并购', '业绩', '财报']
        
        # 中等关键词
        medium_keywords = ['上涨', '下跌', '反弹', '回调', '突破', '支撑', '阻力',
                          '资金流入', '主力', '机构', '北向资金']
        
        for kw in high_keywords:
            if kw in title:
                return 'high'
        
        for kw in medium_keywords:
            if kw in title:
                return 'medium'
        
        return 'low'


def save_news_to_db(news_list: List[Dict]):
    """
    将新闻保存到数据库
    
    Args:
        news_list: 新闻列表
    """
    if not news_list:
        return
    
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
                INDEX idx_publish_time (publish_time),
                UNIQUE KEY uk_title_url (title(200), url(500))
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        ''')
        
        # 插入或更新新闻
        insert_sql = '''
            INSERT INTO market_news 
            (title, summary, source, category, url, publish_time, importance, 
             stock_code, stock_name, change_percent, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE 
                publish_time = VALUES(publish_time),
                importance = VALUES(importance),
                created_at = VALUES(created_at)
        '''
        
        success_count = 0
        for news in news_list:
            try:
                cursor.execute(insert_sql, (
                    news.get('title', ''),
                    news.get('summary', ''),
                    news.get('source', ''),
                    news.get('category', ''),
                    news.get('url', ''),
                    news.get('publish_time', ''),
                    news.get('importance', 'medium'),
                    news.get('stock_code', ''),
                    news.get('stock_name', ''),
                    news.get('change_percent', 0),
                    news.get('created_at', '')
                ))
                success_count += 1
            except Exception as e:
                print(f"插入新闻失败 [{news.get('title', '')[:30]}]: {e}")
        
        conn.commit()
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 新闻更新完成: 成功 {success_count} 条")
        
    except Exception as e:
        print(f"保存新闻到数据库失败: {e}")
        conn.rollback()
    finally:
        conn.close()


def update_all_news():
    """
    更新所有新闻（主函数，供定时任务调用）
    """
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 开始更新新闻动态...")
    
    fetcher = NewsFetcher()
    
    all_news = []
    
    # 1. 获取市场要闻
    print("正在获取市场要闻...")
    market_news = fetcher.fetch_market_news()
    all_news.extend(market_news)
    print(f"  ✓ 市场要闻: {len(market_news)} 条")
    
    # 2. 获取行业动态
    print("正在获取行业动态...")
    industry_news = fetcher.fetch_industry_news()
    all_news.extend(industry_news)
    print(f"  ✓ 行业动态: {len(industry_news)} 条")
    
    # 3. 获取交易机会
    print("正在获取交易机会...")
    opportunities = fetcher.fetch_stock_opportunities()
    all_news.extend(opportunities)
    print(f"  ✓ 交易机会: {len(opportunities)} 条")
    
    # 保存到数据库
    if all_news:
        save_news_to_db(all_news)
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 新闻更新完成，共 {len(all_news)} 条")
    else:
        print("[警告] 未获取到任何新闻")


if __name__ == '__main__':
    update_all_news()
