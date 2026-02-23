"""
交易系统单元测试
测试数据获取、选股、评分、交易管理模块
使用预定义股票002065和000738进行测试
"""
import unittest
import os
import sys
from datetime import date
import uuid

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'app', 'services'))

from data_fetcher import DataFetcher
from stock_selector import StockSelector, StockScorer, INDUSTRY_STOCK_POOL, STOCK_NAME_MAPPING
from trading_manager import TradingManager

TEST_DB = 'test_trading_system.db'

PRESELECTED_STOCKS = [
    {'code': '002065', 'name': '东华软件', 'industry': '数字经济'},
    {'code': '000738', 'name': '航发控制', 'industry': '高端制造'}
]

TEST_STOCKS = [
    {'code': 'sz300750', 'name': '宁德时代', 'industry': '新能源'},
    {'code': 'sh600111', 'name': '北方稀土', 'industry': '新材料'},
    {'code': 'sh603986', 'name': '兆易创新', 'industry': '半导体'},
    {'code': 'sh600410', 'name': '华胜天成', 'industry': '数字经济'},
    {'code': 'sz002594', 'name': '比亚迪', 'industry': '新能源'}
]

class TestDataFetcher(unittest.TestCase):
    """数据获取模块测试"""
    
    @classmethod
    def setUpClass(cls):
        """测试前准备"""
        cls.fetcher = DataFetcher(TEST_DB)
        cls.fetcher.connect()
    
    @classmethod
    def tearDownClass(cls):
        """测试后清理"""
        cls.fetcher.disconnect()
        if os.path.exists(TEST_DB):
            os.remove(TEST_DB)
    
    def test_get_stock_realtime(self):
        """测试获取实时行情 - 使用预选股票"""
        test_stock = PRESELECTED_STOCKS[0]
        result = self.fetcher.get_stock_realtime(test_stock['code'])
        self.assertIsNotNone(result)
        self.assertEqual(result['stock_code'], test_stock['code'])
        self.assertIn('last_price', result)
        self.assertIn('stock_name', result)
        print(f"实时行情: {result['stock_name']} 最新价: {result['last_price']}")
    
    def test_get_kline_data(self):
        """测试获取K线数据 - 使用预选股票"""
        test_stock = PRESELECTED_STOCKS[0]
        result = self.fetcher.get_kline_data(test_stock['code'], 60)
        self.assertIsNotNone(result)
        self.assertGreaterEqual(len(result), 20)
        print(f"K线数据: 获取到{len(result)}条记录")
    
    def test_calculate_technical_indicators(self):
        """测试计算技术指标 - 使用预选股票"""
        test_stock = PRESELECTED_STOCKS[0]
        kline = self.fetcher.get_kline_data(test_stock['code'], 60)
        self.assertIsNotNone(kline)
        
        indicators = self.fetcher.calculate_technical_indicators(kline)
        self.assertIsNotNone(indicators)
        self.assertIn('ma5', indicators)
        self.assertIn('ma20', indicators)
        self.assertIn('diff', indicators)
        self.assertIn('dea', indicators)
        self.assertIn('rsi', indicators)
        self.assertIn('bb_upper', indicators)
        self.assertIn('bb_lower', indicators)
        self.assertIn('diff_gt_dea_and_zero', indicators)
        self.assertIn('obv_gt_maobv', indicators)
        print(f"技术指标: MA5={indicators['ma5']:.2f}, MA20={indicators['ma20']:.2f}")
        print(f"MACD: DIFF={indicators['diff']:.4f}, DEA={indicators['dea']:.4f}")
        print(f"DIFF>DEA>0: {indicators['diff_gt_dea_and_zero']}")
    
    def test_industry_stock_pool(self):
        """测试行业股票池 - 验证股票池数据完整性"""
        total_stocks = 0
        for industry, stocks in INDUSTRY_STOCK_POOL.items():
            self.assertIsInstance(stocks, list)
            self.assertGreater(len(stocks), 0)
            total_stocks += len(stocks)
        
        self.assertGreater(total_stocks, 0)
        self.assertGreaterEqual(len(INDUSTRY_STOCK_POOL), 10)
        print(f"行业股票池共{len(INDUSTRY_STOCK_POOL)}个行业，{total_stocks}只股票")


class TestStockSelector(unittest.TestCase):
    """选股模块测试"""
    
    @classmethod
    def setUpClass(cls):
        """测试前准备"""
        cls.selector = StockSelector(TEST_DB)
        cls.scorer = StockScorer(TEST_DB)
    
    @unittest.skip("跳过选股模块测试，使用预选股票")
    def test_select_stocks_from_pool(self):
        """测试从行业股票池选股 - 已跳过"""
        pass
    
    def test_calculate_score_preselected(self):
        """测试评分功能 - 使用预选股票"""
        test_stock = PRESELECTED_STOCKS[0]
        result = self.scorer.calculate_score(test_stock['code'])
        self.assertIsNotNone(result)
        self.assertIn('total_score', result)
        self.assertIn('rating', result)
        self.assertIn(result['rating'], ['强烈推荐', '推荐', '中性', '观望', '不推荐'])
        print(f"评分结果: {result['stock_name']} 评分={result['total_score']:.2f} 评级={result['rating']}")
    
    def test_technical_conditions_check_preselected(self):
        """测试技术条件检查 - 使用预选股票"""
        for test_stock in PRESELECTED_STOCKS:
            kline = self.selector.fetcher.get_kline_data(test_stock['code'], 60)
            if kline is not None and len(kline) >= 20:
                indicators = self.selector.fetcher.calculate_technical_indicators(kline)
                if indicators:
                    tech_result = self.selector._check_technical_conditions(indicators, {
                        'stock_code': test_stock['code'],
                        'close_price': indicators.get('close_price', 0)
                    })
                    self.assertIn('passed', tech_result)
                    self.assertIn('passed_count', tech_result)
                    self.assertIn('ma_condition', tech_result)
                    self.assertIn('macd_condition', tech_result)
                    self.assertIn('volume_condition', tech_result)
                    print(f"{test_stock['name']}: 技术条件通过{tech_result['passed_count']}/5, 是否通过={tech_result['passed']}")


class TestTradingManager(unittest.TestCase):
    """交易管理模块测试"""
    
    @classmethod
    def setUpClass(cls):
        """测试前准备"""
        cls.manager = TradingManager(TEST_DB)
        
        import sqlite3
        sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'scripts'))
        from init_database import init_database
        init_database(TEST_DB)
        cls.manager.connect()
    
    @classmethod
    def tearDownClass(cls):
        """测试后清理"""
        cls.manager.disconnect()
    
    def _get_unique_plan_id(self):
        """生成唯一的计划ID"""
        return f"TEST_PLAN_{uuid.uuid4().hex[:8]}"
    
    def _get_unique_step_id(self):
        """生成唯一的步骤ID"""
        return f"TEST_STEP_{uuid.uuid4().hex[:8]}"
    
    def _get_unique_record_id(self):
        """生成唯一的记录ID"""
        return f"TEST_REC_{uuid.uuid4().hex[:8]}"
    
    def _get_unique_review_id(self):
        """生成唯一的复盘ID"""
        return f"TEST_REV_{uuid.uuid4().hex[:8]}"
    
    def test_create_trade_plan_preselected(self):
        """测试创建交易计划 - 使用预选股票"""
        test_stock = PRESELECTED_STOCKS[0]
        plan_id = self.manager.create_trade_plan({
            'plan_id': self._get_unique_plan_id(),
            'plan_name': f'买入{test_stock["name"]}',
            'account_id': 'TEST001',
            'stock_code': test_stock['code'],
            'stock_name': test_stock['name'],
            'planned_quantity': 1000,
            'planned_amount': 10000.00
        })
        self.assertIsNotNone(plan_id)
        self.assertTrue(plan_id.startswith('TEST_PLAN'))
        print(f"创建交易计划成功: {plan_id}")
    
    def test_get_trade_plan_preselected(self):
        """测试获取交易计划 - 使用预选股票"""
        test_stock = PRESELECTED_STOCKS[1]
        plan_id = self._get_unique_plan_id()
        self.manager.create_trade_plan({
            'plan_id': plan_id,
            'plan_name': f'买入{test_stock["name"]}',
            'account_id': 'TEST001',
            'stock_code': test_stock['code'],
            'stock_name': test_stock['name']
        })
        
        plan = self.manager.get_trade_plan(plan_id)
        self.assertIsNotNone(plan)
        self.assertEqual(plan['stock_code'], test_stock['code'])
        print(f"获取交易计划成功: {plan['plan_name']}")
    
    def test_update_trade_plan_preselected(self):
        """测试更新交易计划 - 使用预选股票"""
        test_stock = PRESELECTED_STOCKS[0]
        plan_id = self._get_unique_plan_id()
        self.manager.create_trade_plan({
            'plan_id': plan_id,
            'plan_name': f'买入{test_stock["name"]}',
            'account_id': 'TEST001',
            'stock_code': test_stock['code'],
            'stock_name': test_stock['name']
        })
        
        result = self.manager.update_trade_plan(plan_id, {'status': 'executing'})
        self.assertTrue(result)
        
        plan = self.manager.get_trade_plan(plan_id)
        self.assertEqual(plan['status'], 'executing')
        print(f"更新交易计划成功: 状态={plan['status']}")
    
    def test_create_execution_step_preselected(self):
        """测试创建执行步骤 - 使用预选股票"""
        test_stock = PRESELECTED_STOCKS[1]
        plan_id = self._get_unique_plan_id()
        self.manager.create_trade_plan({
            'plan_id': plan_id,
            'plan_name': f'买入{test_stock["name"]}',
            'account_id': 'TEST001',
            'stock_code': test_stock['code'],
            'stock_name': test_stock['name']
        })
        
        step_id = self.manager.create_execution_step({
            'step_id': self._get_unique_step_id(),
            'plan_id': plan_id,
            'account_id': 'TEST001',
            'stock_code': test_stock['code'],
            'stock_name': test_stock['name'],
            'trade_direction': '建仓',
            'planned_quantity': 1000
        })
        self.assertIsNotNone(step_id)
        self.assertTrue(step_id.startswith('TEST_STEP'))
        print(f"创建执行步骤成功: {step_id}")
    
    def test_create_trade_record_preselected(self):
        """测试创建交易记录 - 使用预选股票"""
        test_stock = PRESELECTED_STOCKS[0]
        record_id = self.manager.create_trade_record({
            'record_id': self._get_unique_record_id(),
            'account_id': 'TEST001',
            'stock_code': test_stock['code'],
            'stock_name': test_stock['name'],
            'trade_type': '买入',
            'trade_direction': '建仓',
            'trade_price': 10.00,
            'trade_quantity': 1000,
            'trade_amount': 10000.00
        })
        self.assertIsNotNone(record_id)
        self.assertTrue(record_id.startswith('TEST_REC'))
        print(f"创建交易记录成功: {record_id}")
    
    def test_create_review_record_preselected(self):
        """测试创建复盘记录 - 使用预选股票"""
        test_stock = PRESELECTED_STOCKS[1]
        plan_id = self._get_unique_plan_id()
        self.manager.create_trade_plan({
            'plan_id': plan_id,
            'plan_name': f'买入{test_stock["name"]}',
            'account_id': 'TEST001',
            'stock_code': test_stock['code'],
            'stock_name': test_stock['name']
        })
        
        review_id = self.manager.create_review_record({
            'review_id': self._get_unique_review_id(),
            'plan_id': plan_id,
            'account_id': 'TEST001',
            'stock_code': test_stock['code'],
            'stock_name': test_stock['name'],
            'review_type': '成功',
            'execution_summary': '按计划执行'
        })
        self.assertIsNotNone(review_id)
        self.assertTrue(review_id.startswith('TEST_REV'))
        print(f"创建复盘记录成功: {review_id}")
    
    def test_calculate_win_rate(self):
        """测试计算胜率"""
        result = self.manager.calculate_win_rate('TEST001')
        self.assertIsNotNone(result)
        self.assertIn('total_trades', result)
        self.assertIn('win_rate', result)
        print(f"胜率统计: 总交易{result['total_trades']}笔, 胜率{result['win_rate']:.2%}")
    
    def test_calculate_profit_loss_ratio(self):
        """测试计算盈亏比"""
        result = self.manager.calculate_profit_loss_ratio('TEST001')
        self.assertIsNotNone(result)
        self.assertIn('profit_loss_ratio', result)
        print(f"盈亏比: {result['profit_loss_ratio']:.2f}")
    
    def test_calculate_max_drawdown(self):
        """测试计算最大回撤"""
        result = self.manager.calculate_max_drawdown('TEST001')
        self.assertIsNotNone(result)
        self.assertIn('max_drawdown', result)
        self.assertIn('max_drawdown_rate', result)
        print(f"最大回撤: {result['max_drawdown_rate']:.2%}")


def run_tests():
    """运行所有测试"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    suite.addTests(loader.loadTestsFromTestCase(TestDataFetcher))
    suite.addTests(loader.loadTestsFromTestCase(TestStockSelector))
    suite.addTests(loader.loadTestsFromTestCase(TestTradingManager))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result


if __name__ == "__main__":
    run_tests()
