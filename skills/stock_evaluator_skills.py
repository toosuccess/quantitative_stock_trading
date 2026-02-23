"""
评价技能
职责：对stock_basic_info中的股票打分，输出到score_record表
"""

import akshare as ak
import sqlite3
import os
import json
import numpy as np
import pandas as pd
from datetime import datetime, date, timedelta

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                        'backend', 'database', 'trading_system.db')

POLICY_ORIENTED_INDUSTRIES = {
    '新能源': {'industry_type': '战略性新兴产业', 'growth_potential': '高'},
    '新材料': {'industry_type': '战略性新兴产业', 'growth_potential': '高'},
    '6G': {'industry_type': '未来产业', 'growth_potential': '极高'},
    '核聚变': {'industry_type': '未来产业', 'growth_potential': '极高'},
    '消费升级': {'industry_type': '民生消费', 'growth_potential': '中高'},
    '半导体': {'industry_type': '战略性新兴产业', 'growth_potential': '高'},
    '人工智能': {'industry_type': '未来产业', 'growth_potential': '极高'},
    '生物医药': {'industry_type': '战略性新兴产业', 'growth_potential': '高'},
    '高端制造': {'industry_type': '战略性新兴产业', 'growth_potential': '高'},
    '数字经济': {'industry_type': '未来产业', 'growth_potential': '极高'}
}


class StockEvaluatorSkills:
    """评价技能类"""
    
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
    
    def get_stock_price_data(self, stock_code):
        """获取股票价格数据"""
        pure_code = stock_code.replace('sh', '').replace('sz', '').replace('bj', '')
        
        try:
            df = ak.stock_zh_a_hist(symbol=pure_code, period='daily', adjust='qfq')
            if df is None or len(df) < 60:
                return None
            
            df = df.tail(250)
            latest = df.iloc[-1]
            
            close = df['收盘'].values
            high = df['最高'].values if '最高' in df.columns else close
            low = df['最低'].values if '最低' in df.columns else close
            volume = df['成交量'].values
            
            current_close = float(latest.get('收盘', 0))
            current_volume = float(latest.get('成交量', 0))
            
            ma20 = np.mean(close[-20:]) if len(close) >= 20 else current_close
            ma60 = np.mean(close[-60:]) if len(close) >= 60 else ma20
            ma180 = np.mean(close[-180:]) if len(close) >= 180 else ma60
            ma250 = np.mean(close[-250:]) if len(close) >= 250 else ma180
            
            ema12 = pd.Series(close).ewm(span=12).mean().values
            ema26 = pd.Series(close).ewm(span=26).mean().values
            diff = ema12 - ema26
            dea = pd.Series(diff).ewm(span=9).mean().values
            macd = 2 * (diff - dea)
            
            delta = np.diff(close)
            gain = delta[delta > 0]
            loss = -delta[delta < 0]
            avg_gain = np.mean(gain) if len(gain) > 0 else 0
            avg_loss = np.mean(loss) if len(loss) > 0 else 0
            rsi = 100 - (100 / (1 + avg_gain / avg_loss)) if avg_loss != 0 else 50
            
            obv = [0]
            for i in range(1, len(close)):
                if close[i] > close[i-1]:
                    obv.append(obv[-1] + volume[i])
                elif close[i] < close[i-1]:
                    obv.append(obv[-1] - volume[i])
                else:
                    obv.append(obv[-1])
            obv = np.array(obv)
            maobv = np.mean(obv[-30:]) if len(obv) >= 30 else np.mean(obv)
            
            bb_middle = np.mean(close[-20:]) if len(close) >= 20 else current_close
            bb_std = np.std(close[-20:]) if len(close) >= 20 else 0
            bb_upper = bb_middle + 2 * bb_std
            bb_lower = bb_middle - 2 * bb_std
            
            ma5_volume = np.mean(volume[-5:]) if len(volume) >= 5 else current_volume
            ma60_volume = np.mean(volume[-60:]) if len(volume) >= 60 else ma5_volume
            
            if '换手率' in df.columns:
                turnover_raw = float(latest.get('换手率', 0))
                turnover_rate = turnover_raw / 100
            else:
                turnover_rate = 0.02
            
            return {
                'close': current_close,
                'volume': current_volume,
                'MA5': np.mean(close[-5:]) if len(close) >= 5 else current_close,
                'MA10': np.mean(close[-10:]) if len(close) >= 10 else current_close,
                'MA20': ma20,
                'MA60': ma60,
                'MA180': ma180,
                'MA250': ma250,
                'DIFF': diff[-1],
                'DEA': dea[-1],
                'MACD': macd[-1],
                'RSI': rsi,
                'OBV': obv[-1],
                'MAOBV': maobv,
                'BB_Upper': bb_upper,
                'BB_Middle': bb_middle,
                'BB_Lower': bb_lower,
                'MA5_Volume': ma5_volume,
                'MA60_Volume': ma60_volume,
                'Turnover_Rate': turnover_rate
            }
        except Exception as e:
            print(f"获取{stock_code}价格数据失败: {e}")
            return None
    
    def calculate_technical_score(self, stock_code):
        """计算技术面得分"""
        import numpy as np
        price_data = self.get_stock_price_data(stock_code)
        
        if not price_data:
            return 0, {}, None
        
        ma_score = 0
        volume_score = 0
        macd_score = 0
        obv_score = 0
        bollinger_score = 0
        
        ma_condition = {}
        volume_condition = {}
        trend_condition = {}
        fund_condition = {}
        bollinger_condition = {}
        
        if price_data['close'] > price_data['MA20']:
            ma20_prev = price_data['MA20']
            ma20_up = price_data['MA20'] > ma20_prev * 0.99
            ma_condition['price_above_ma20'] = True
            ma_condition['ma20_up'] = ma20_up
            if ma20_up:
                ma_score = 25
        else:
            ma_condition['price_above_ma20'] = False
            ma_condition['ma20_up'] = False
        
        volume_above_ma5 = price_data['volume'] > price_data['MA5_Volume']
        volume_above_ma60 = price_data['volume'] > price_data['MA60_Volume']
        turnover_rate_range = 0.05 <= price_data['Turnover_Rate'] <= 0.20
        
        volume_condition['volume_above_ma5'] = volume_above_ma5
        volume_condition['volume_above_ma60'] = volume_above_ma60
        volume_condition['turnover_rate_range'] = turnover_rate_range
        
        if volume_above_ma5 and volume_above_ma60 and turnover_rate_range:
            volume_score = 25
        
        diff_gt_dea = price_data['DIFF'] > price_data['DEA']
        macd_above_zero = price_data['MACD'] > 0
        trend_condition['diff_gt_dea_and_zero'] = diff_gt_dea and macd_above_zero
        trend_condition['macd_golden_cross'] = diff_gt_dea
        trend_condition['macd_above_zero'] = macd_above_zero
        trend_condition['dmi_condition'] = True
        
        if diff_gt_dea and macd_above_zero:
            macd_score = 20
        
        obv_above_maobv = price_data['OBV'] > price_data['MAOBV']
        fund_condition['obv_above_maobv'] = obv_above_maobv
        fund_condition['obv_up'] = obv_above_maobv
        
        if obv_above_maobv:
            obv_score = 15
        
        price_between_middle_and_upper = price_data['BB_Lower'] < price_data['close'] < price_data['BB_Upper']
        price_above_middle = price_data['close'] > price_data['BB_Middle']
        not_overbought = price_data['close'] < price_data['BB_Upper'] * 1.02
        
        bollinger_condition['price_between_middle_and_upper'] = price_between_middle_and_upper
        bollinger_condition['price_above_middle_band'] = price_above_middle
        bollinger_condition['not_overbought'] = not_overbought
        
        if price_between_middle_and_upper and not_overbought:
            bollinger_score = 15
        
        total_score = ma_score + volume_score + macd_score + obv_score + bollinger_score
        
        indicators = {
            'ma_condition': ma_condition,
            'volume_condition': volume_condition,
            'trend_condition': trend_condition,
            'fund_condition': fund_condition,
            'bollinger_condition': bollinger_condition
        }
        
        return total_score, indicators, price_data
    
    def get_fundamental_data(self, stock_code):
        """获取基本面数据 - 多数据源合并"""
        pure_code = stock_code.replace('sh', '').replace('sz', '').replace('bj', '')
        result = {
            'pe': 0, 'pb': 0, 'roe': 0,
            'net_profit_growth': 0, 'revenue_growth': 0, 'debt_ratio': 0
        }
        
        try:
            df = ak.stock_individual_info_em(symbol=pure_code)
            if df is not None and len(df) > 0:
                info = dict(zip(df['item'], df['value']))
                if info.get('净资产收益率'):
                    result['roe'] = float(info.get('净资产收益率', 0))
                if info.get('市盈率'):
                    result['pe'] = float(info.get('市盈率', 0))
                if info.get('市净率'):
                    result['pb'] = float(info.get('市净率', 0))
        except Exception as e:
            print(f"方法3获取个股信息失败: {e}")
        
        if result['pe'] == 0 or result['pb'] == 0:
            try:
                df = ak.stock_financial_analysis_indicator(symbol=pure_code)
                if df is not None and len(df) > 0:
                    latest = df.iloc[0]
                    if result['pe'] == 0 and latest.get('市盈率') and float(latest.get('市盈率', 0)) > 0:
                        result['pe'] = float(latest.get('市盈率', 0))
                    if result['pb'] == 0 and latest.get('市净率') and float(latest.get('市净率', 0)) > 0:
                        result['pb'] = float(latest.get('市净率', 0))
                    if result['roe'] == 0 and latest.get('净资产收益率') and float(latest.get('净资产收益率', 0)) != 0:
                        result['roe'] = float(latest.get('净资产收益率', 0))
            except Exception as e:
                print(f"方法1获取财务指标失败: {e}")
        
        if result['pe'] == 0 or result['pb'] == 0:
            try:
                df = ak.stock_zh_a_spot_em()
                stock_data = df[df['代码'] == pure_code]
                if len(stock_data) > 0:
                    row = stock_data.iloc[0]
                    if result['pe'] == 0 and row.get('市盈率-动态'):
                        result['pe'] = float(row.get('市盈率-动态', 0))
                    if result['pb'] == 0 and row.get('市净率'):
                        result['pb'] = float(row.get('市净率', 0))
            except Exception as e:
                print(f"方法2获取行情数据失败: {e}")
        
        if result['net_profit_growth'] == 0 or result['revenue_growth'] == 0 or result['debt_ratio'] == 0:
            try:
                balance_df = ak.stock_financial_report_sina(stock=pure_code, symbol="资产负债表")
                if balance_df is not None and len(balance_df) > 0:
                    latest = balance_df.iloc[0]
                    if result['debt_ratio'] == 0:
                        total_assets = latest.get('资产总计', 0)
                        total_liab = latest.get('负债合计', 0)
                        if total_assets and total_liab and float(total_assets) > 0:
                            result['debt_ratio'] = float(total_liab) / float(total_assets) * 100
            except Exception as e:
                pass
            
            try:
                income_df = ak.stock_financial_report_sina(stock=pure_code, symbol="利润表")
                if income_df is not None and len(income_df) > 1:
                    current = income_df.iloc[0]
                    prev = income_df.iloc[1]
                    
                    if result['net_profit_growth'] == 0:
                        current_np = current.get('净利润', 0)
                        prev_np = prev.get('净利润', 0)
                        if current_np and prev_np and float(prev_np) != 0:
                            result['net_profit_growth'] = (float(current_np) - float(prev_np)) / abs(float(prev_np)) * 100
                    
                    if result['revenue_growth'] == 0:
                        current_rev = current.get('营业收入', 0)
                        prev_rev = prev.get('营业收入', 0)
                        if current_rev and prev_rev and float(prev_rev) != 0:
                            result['revenue_growth'] = (float(current_rev) - float(prev_rev)) / abs(float(prev_rev)) * 100
            except Exception as e:
                pass
        
        return result
    
    def calculate_fundamental_score(self, stock_code):
        """计算基本面得分"""
        data = self.get_fundamental_data(stock_code)
        
        score = 0
        details = {}
        
        # PE评分
        pe_score = 0
        pe_detail = ""
        if 0 < data['pe'] < 30:
            pe_score = 20
            pe_detail = f"PE={data['pe']:.2f},估值适中"
        elif 30 <= data['pe'] < 50:
            pe_score = 10
            pe_detail = f"PE={data['pe']:.2f},估值偏高"
        else:
            pe_detail = f"PE={data['pe']:.2f}"
        score += pe_score
        details['pe'] = {'score': pe_score, 'value': data['pe'], 'detail': pe_detail}
        
        # PB评分
        pb_score = 0
        pb_detail = ""
        if 0 < data['pb'] < 2:
            pb_score = 15
            pb_detail = f"PB={data['pb']:.2f},资产价值高"
        elif 2 <= data['pb'] < 3:
            pb_score = 10
            pb_detail = f"PB={data['pb']:.2f},资产价值适中"
        elif 3 <= data['pb'] < 5:
            pb_score = 5
            pb_detail = f"PB={data['pb']:.2f},资产价值偏低"
        else:
            pb_detail = f"PB={data['pb']:.2f}"
        score += pb_score
        details['pb'] = {'score': pb_score, 'value': data['pb'], 'detail': pb_detail}
        
        # ROE评分
        roe_score = 0
        roe_detail = ""
        if data['roe'] > 15:
            roe_score = 20
            roe_detail = f"ROE={data['roe']:.2f}%,回报优秀"
        elif data['roe'] > 10:
            roe_score = 15
            roe_detail = f"ROE={data['roe']:.2f}%,回报良好"
        elif data['roe'] > 5:
            roe_score = 10
            roe_detail = f"ROE={data['roe']:.2f}%,回报一般"
        else:
            roe_detail = f"ROE={data['roe']:.2f}%"
        score += roe_score
        details['roe'] = {'score': roe_score, 'value': data['roe'], 'detail': roe_detail}
        
        # 净利润增长率评分
        npg_score = 0
        npg_detail = ""
        if data['net_profit_growth'] > 30:
            npg_score = 20
            npg_detail = f"净利润增长{data['net_profit_growth']:.2f}%,增长强劲"
        elif data['net_profit_growth'] > 10:
            npg_score = 10
            npg_detail = f"净利润增长{data['net_profit_growth']:.2f}%,增长稳定"
        else:
            npg_detail = f"净利润增长{data['net_profit_growth']:.2f}%"
        score += npg_score
        details['net_profit_growth'] = {'score': npg_score, 'value': data['net_profit_growth'], 'detail': npg_detail}
        
        # 营收增长率评分
        rg_score = 0
        rg_detail = ""
        if data['revenue_growth'] > 20:
            rg_score = 15
            rg_detail = f"营收增长{data['revenue_growth']:.2f}%,扩张快速"
        elif data['revenue_growth'] > 10:
            rg_score = 10
            rg_detail = f"营收增长{data['revenue_growth']:.2f}%,扩张稳定"
        else:
            rg_detail = f"营收增长{data['revenue_growth']:.2f}%"
        score += rg_score
        details['revenue_growth'] = {'score': rg_score, 'value': data['revenue_growth'], 'detail': rg_detail}
        
        # 负债率评分
        dr_score = 0
        dr_detail = ""
        if data['debt_ratio'] < 50:
            dr_score = 10
            dr_detail = f"负债率{data['debt_ratio']:.2f}%,财务稳健"
        elif data['debt_ratio'] < 70:
            dr_score = 5
            dr_detail = f"负债率{data['debt_ratio']:.2f}%,财务适中"
        else:
            dr_detail = f"负债率{data['debt_ratio']:.2f}%,负债较高"
        score += dr_score
        details['debt_ratio'] = {'score': dr_score, 'value': data['debt_ratio'], 'detail': dr_detail}
        
        return score, details
    
    def calculate_news_score(self, stock_code):
        """计算消息面得分（只对最近三天新闻加减分）"""
        pure_code = stock_code.replace('sh', '').replace('sz', '').replace('bj', '')
        score = 0
        events = []
        
        three_days_ago = (datetime.now() - timedelta(days=3)).strftime('%Y-%m-%d')
        today = datetime.now().strftime('%Y-%m-%d')
        
        try:
            df = ak.stock_news_em(symbol=pure_code)
            if df is not None and len(df) > 0:
                positive_keywords = ['利好', '增长', '盈利', '中标', '合作', '突破', '创新']
                negative_keywords = ['利空', '亏损', '下滑', '风险', '诉讼', '处罚', '减持']
                
                for _, row in df.head(5).iterrows():
                    title = str(row.get('新闻标题', ''))
                    news_time = str(row.get('发布时间', ''))[:10] if row.get('发布时间') else today
                    news_url = str(row.get('新闻链接', ''))
                    news_source = str(row.get('文章来源', ''))
                    news_content = str(row.get('新闻内容', ''))[:100] if row.get('新闻内容') else ''
                    
                    is_recent = (news_time >= three_days_ago and news_time <= today)
                    
                    event_type = '中性'
                    score_impact = 0
                    
                    for kw in positive_keywords:
                        if kw in title:
                            event_type = '利好'
                            if is_recent:
                                score_impact = 5
                                score += 5
                            break
                    
                    for kw in negative_keywords:
                        if kw in title:
                            event_type = '利空'
                            if is_recent:
                                score_impact = -5
                                score -= 5
                            break
                    
                    events.append({
                        'date': news_time, 
                        'type': event_type,
                        'title': title[:50], 
                        'score_impact': score_impact, 
                        'is_recent': is_recent,
                        'url': news_url,
                        'source': news_source,
                        'summary': news_content
                    })
                    
        except Exception as e:
            print(f"获取{stock_code}新闻数据失败: {e}")
        
        return score, events
    
    def calculate_policy_score(self, stock_code, industry):
        """计算政策面得分"""
        score = 3
        policies = []
        
        if industry in POLICY_ORIENTED_INDUSTRIES:
            industry_info = POLICY_ORIENTED_INDUSTRIES[industry]
            industry_type = industry_info.get('industry_type', '')
            policy_support = industry_info.get('policy_support', '')
            
            if industry_type == '未来产业':
                score = 10
            elif industry_type == '战略性新兴产业':
                score = 8
            elif industry_type == '民生消费':
                score = 5
            
            policies.append({
                'date': datetime.now().strftime('%Y-%m-%d'),
                'level': '国家政策',
                'title': f'{industry}产业政策支持',
                'content': policy_support,
                'score_impact': score,
                'url': '',
                'source': '十五五规划'
            })
        
        return score, policies
    
    def calculate_deduction_score(self, stock_code):
        """计算减项扣分"""
        return 0, []
    
    def calculate_composite_score(self, technical_score, fundamental_score, news_score, policy_score, deduction_score):
        """计算综合评分
        技术面60% + 基本面40% + 消息面加减分 + 政策面加减分 - 减项扣分
        """
        return technical_score * 0.6 + fundamental_score * 0.4 + news_score + policy_score - deduction_score
    
    def get_rating(self, total_score):
        """根据得分获取评级"""
        if total_score >= 90: return "强烈推荐"
        elif total_score >= 70: return "推荐"
        elif total_score >= 50: return "中性"
        elif total_score >= 30: return "观望"
        else: return "不推荐"
    
    def save_score_record(self, stock_code, stock_name, industry, scores, price_data):
        """保存评分记录到score_record表"""
        if not self.conn:
            self.connect()
        
        cursor = self.conn.cursor()
        score_date = date.today().strftime('%Y-%m-%d')
        
        try:
            cursor.execute('''
                INSERT INTO score_record 
                (stock_code, stock_name, score_date, 
                fundamental_score, fundamental_reason,
                technical_score, technical_reason,
                ma_score, macd_score, rsi_score, bollinger_score, volume_score, obv_score,
                total_score, composite_score, rating,
                news_score, policy_score, deduction_score,
                close_price, volume, turnover_rate,
                create_time, update_time,
                technical_detail, fundamental_detail, news_detail, policy_detail, deduction_detail,
                summary, is_leader)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                stock_code, stock_name, score_date,
                scores['fundamental_score'], f"基本面得分{scores['fundamental_score']}分",
                scores['technical_score'], f"技术面得分{scores['technical_score']}分",
                scores.get('ma_score', 0), scores.get('macd_score', 0), 0,
                scores.get('bollinger_score', 0), scores.get('volume_score', 0), scores.get('obv_score', 0),
                scores['composite_score'], scores['composite_score'], scores['rating'],
                scores['news_score'], scores['policy_score'], scores['deduction_score'],
                price_data.get('close', 0) if price_data else 0,
                price_data.get('volume', 0) if price_data else 0,
                price_data.get('Turnover_Rate', 0) if price_data else 0,
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                json.dumps({
                    'ma': {'score': scores.get('ma_score', 0), 'detail': f"股价站稳20日均线: {'是' if scores.get('ma_score', 0) > 0 else '否'}"},
                    'volume': {'score': scores.get('volume_score', 0), 'detail': f"成交量放大: {'是' if scores.get('volume_score', 0) > 0 else '否'}"},
                    'trend': {'score': scores.get('macd_score', 0), 'detail': f"MACD金叉: {'是' if scores.get('macd_score', 0) > 0 else '否'}"},
                    'fund': {'score': scores.get('obv_score', 0), 'detail': f"OBV>MAOBV: {'是' if scores.get('obv_score', 0) > 0 else '否'}"},
                    'bollinger': {'score': scores.get('bollinger_score', 0), 'detail': f"布林带中轨上方: {'是' if scores.get('bollinger_score', 0) > 0 else '否'}"}
                }, ensure_ascii=False),
                json.dumps(scores.get('fundamental_detail', {}), ensure_ascii=False),
                json.dumps({'events': scores.get('news_events', [])}, ensure_ascii=False),
                json.dumps({'policies': scores.get('policy_policies', [])}, ensure_ascii=False),
                json.dumps({}, ensure_ascii=False),
                scores.get('summary', ''), 0
            ))
            
            self.conn.commit()
            print(f"✅ 已保存评分记录: {stock_name}({stock_code}) - {scores['composite_score']:.0f}分 - {scores['rating']}")
            return True
            
        except Exception as e:
            print(f"❌ 保存评分记录失败 {stock_code}: {e}")
            return False
    
    def evaluate_stock(self, stock_code, stock_name=None, industry=None):
        """评价单只股票"""
        if not self.conn:
            self.connect()
        
        cursor = self.conn.cursor()
        
        if not stock_name or not industry:
            cursor.execute('SELECT stock_name, industry FROM stock_basic_info WHERE stock_code = ?', (stock_code,))
            result = cursor.fetchone()
            if result:
                stock_name = stock_name or result[0]
                industry = industry or result[1]
        
        stock_name = stock_name or stock_code
        industry = industry or '未知'
        
        print(f"\n正在评价: {stock_name}({stock_code})")
        
        technical_score, indicators, price_data = self.calculate_technical_score(stock_code)
        fundamental_score, fundamental_detail = self.calculate_fundamental_score(stock_code)
        news_score, news_events = self.calculate_news_score(stock_code)
        policy_score, policy_policies = self.calculate_policy_score(stock_code, industry)
        deduction_score, deduction_items = self.calculate_deduction_score(stock_code)
        
        composite_score = self.calculate_composite_score(
            technical_score, fundamental_score, news_score, policy_score, deduction_score
        )
        
        rating = self.get_rating(composite_score)
        
        scores = {
            'technical_score': technical_score,
            'fundamental_score': fundamental_score,
            'news_score': news_score,
            'policy_score': policy_score,
            'deduction_score': deduction_score,
            'composite_score': composite_score,
            'rating': rating,
            'ma_score': 25 if indicators.get('ma_condition', {}).get('price_above_ma20') and indicators.get('ma_condition', {}).get('ma20_up') else 0,
            'macd_score': 20 if indicators.get('trend_condition', {}).get('diff_gt_dea_and_zero') else 0,
            'bollinger_score': 15 if indicators.get('bollinger_condition', {}).get('price_between_middle_and_upper') else 0,
            'volume_score': 25 if indicators.get('volume_condition', {}).get('volume_above_ma5') and indicators.get('volume_condition', {}).get('volume_above_ma60') else 0,
            'obv_score': 15 if indicators.get('fund_condition', {}).get('obv_above_maobv') else 0,
            'fundamental_detail': fundamental_detail,
            'news_events': news_events,
            'news_detail': {'events': news_events},
            'policy_policies': policy_policies,
            'policy_detail': {'policies': policy_policies},
            'summary': f"技术面{technical_score}分,基本面{fundamental_score}分,政策面{policy_score}分"
        }
        
        self.save_score_record(stock_code, stock_name, industry, scores, price_data)
        
        return scores
    
    def evaluate_all(self):
        """评价stock_basic_info中所有股票"""
        if not self.conn:
            self.connect()
        
        cursor = self.conn.cursor()
        cursor.execute('SELECT stock_code, stock_name, industry FROM stock_basic_info WHERE status = "normal"')
        stocks = cursor.fetchall()
        
        print("=" * 60)
        print(f"开始评价股票池，股票数量: {len(stocks)}")
        print("=" * 60)
        
        results = []
        for stock_code, stock_name, industry in stocks:
            result = self.evaluate_stock(stock_code, stock_name, industry)
            results.append(result)
        
        print("\n" + "=" * 60)
        print(f"评价完成，共评价 {len(results)} 只股票")
        print("=" * 60)
        
        return results


def run_stock_evaluation(stock_code=None, stock_name=None, industry=None):
    """运行股票评价（供外部调用）"""
    evaluator = StockEvaluatorSkills()
    evaluator.connect()
    
    if stock_code:
        result = evaluator.evaluate_stock(stock_code, stock_name, industry)
    else:
        result = evaluator.evaluate_all()
    
    evaluator.disconnect()
    return result


if __name__ == '__main__':
    run_stock_evaluation()
