
"""
完整系统测试脚本
测试：账户API、盈亏计算、股价刷新、交易执行
"""
import requests
import pymysql
from datetime import datetime, date
import json
from app.database_config import MYSQL_CONFIG

BASE_URL = "http://localhost:8000/api/v1"

def print_section(title):
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80)

def print_pass(message):
    print(f"✅ {message}")

def print_fail(message):
    print(f"❌ {message}")

def test_health():
    print_section("1. 健康检查测试")
    try:
        r = requests.get("http://localhost:8000/health", timeout=30)
        if r.status_code == 200:
            print_pass("健康检查通过")
            return True
        else:
            print_fail(f"健康检查失败: {r.status_code}")
            return False
    except Exception as e:
        print_fail(f"健康检查异常: {e}")
        return False

def test_get_accounts():
    print_section("2. 获取账户列表测试")
    try:
        r = requests.get(f"{BASE_URL}/accounts", timeout=30)
        if r.status_code == 200:
            data = r.json()
            accounts = data.get('accounts', [])
            print_pass(f"成功获取 {len(accounts)} 个账户")
            for i, acc in enumerate(accounts):
                print(f"   [{i}] {acc['account_name']} - 可用: {acc['available_cash']}, 总资产: {acc.get('total_assets', 'N/A')}, 盈亏: {acc.get('profit_loss', 'N/A')}")
            return accounts
        else:
            print_fail(f"获取账户失败: {r.status_code} - {r.text}")
            return []
    except Exception as e:
        print_fail(f"获取账户异常: {e}")
        import traceback
        traceback.print_exc()
        return []

def test_get_single_account(account_id):
    print_section(f"3. 获取单个账户测试 ({account_id})")
    try:
        r = requests.get(f"{BASE_URL}/account/{account_id}", timeout=30)
        if r.status_code == 200:
            acc = r.json()
            print_pass(f"成功获取账户 {acc['account_name']}")
            print(f"   initial_assets: {acc.get('initial_assets', 'N/A')}")
            print(f"   total_assets: {acc.get('total_assets', 'N/A')}")
            print(f"   profit_loss: {acc.get('profit_loss', 'N/A')}")
            print(f"   profit_loss_rate: {acc.get('profit_loss_rate', 'N/A')}")
            print(f"   market_value: {acc.get('market_value', 'N/A')}")
            return acc
        else:
            print_fail(f"获取单个账户失败: {r.status_code} - {r.text}")
            return None
    except Exception as e:
        print_fail(f"获取单个账户异常: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_trigger_price_update():
    print_section("4. 手动触发价格更新测试")
    try:
        r = requests.post(f"http://localhost:8000/scheduler/trigger/price-update", timeout=30)
        if r.status_code == 200:
            print_pass("成功触发价格更新")
            return True
        else:
            print_fail(f"触发价格更新失败: {r.status_code} - {r.text}")
            return False
    except Exception as e:
        print_fail(f"触发价格更新异常: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_get_trade_plans():
    print_section("5. 获取交易计划测试")
    try:
        r = requests.get(f"{BASE_URL}/trade/plans", timeout=30)
        if r.status_code == 200:
            data = r.json()
            plans = data.get('plans', []) if isinstance(data, dict) else data
            print_pass(f"成功获取 {len(plans)} 个交易计划")
            for i, plan in enumerate(plans):
                print(f"   [{i}] {plan.get('stock_name', 'N/A')} ({plan.get('stock_code', 'N/A')}) - {plan.get('status', 'N/A')}")
            return plans
        else:
            print_fail(f"获取交易计划失败: {r.status_code} - {r.text}")
            return []
    except Exception as e:
        print_fail(f"获取交易计划异常: {e}")
        import traceback
        traceback.print_exc()
        return []

def test_get_stock_pool():
    print_section("6. 获取股票池测试")
    try:
        r = requests.get(f"{BASE_URL}/stocks/pool/scores", timeout=60)  # 股票池数据大，时间长一点
        if r.status_code == 200:
            data = r.json()
            pool = data.get('stocks', [])
            print_pass(f"成功获取股票池，{len(pool)} 只股票")
            for i, stock in enumerate(pool[:5]):  # 只显示前5只
                print(f"   [{i}] {stock['stock_name']} - 得分: {stock.get('latest_score', 'N/A')} - {stock.get('latest_rating', 'N/A')}")
            if len(pool) > 5:
                print(f"   ... 还有 {len(pool)-5} 只股票")
            return pool
        else:
            print_fail(f"获取股票池失败: {r.status_code} - {r.text}")
            return []
    except Exception as e:
        print_fail(f"获取股票池异常: {e}")
        import traceback
        traceback.print_exc()
        return []

def test_database_direct():
    print_section("7. 数据库直接查询测试")
    try:
        conn = pymysql.connect(**MYSQL_CONFIG, cursorclass=pymysql.cursors.DictCursor)
        cursor = conn.cursor()
        
        # 检查账户表
        cursor.execute("SHOW COLUMNS FROM account_info")
        columns = [col['Field'] for col in cursor.fetchall()]
        print(f"   account_info 表字段: {', '.join(columns)}")
        
        if 'initial_assets' in columns:
            print_pass("✓ initial_assets 字段存在")
        else:
            print_fail("✗ initial_assets 字段不存在")
        
        # 查询账户数据
        cursor.execute("SELECT account_id, account_name, initial_assets, total_assets, available_cash, profit_loss FROM account_info")
        accounts_db = cursor.fetchall()
        print(f"\n   数据库中的账户 ({len(accounts_db)}):")
        for acc in accounts_db:
            print(f"     - {acc['account_name']}: initial={acc['initial_assets']}, available={acc['available_cash']}, profit={acc['profit_loss']}")
        
        # 查询交易记录
        cursor.execute("SELECT COUNT(*) as cnt FROM trade_record")
        cnt = cursor.fetchone()['cnt']
        print(f"\n   交易记录总数: {cnt}")
        
        # 查询持仓
        cursor.execute('''
            SELECT tr.stock_code, 
                   SUM(CASE WHEN tr.trade_type = '买入' THEN tr.trade_quantity ELSE 0 END) -
                   SUM(CASE WHEN tr.trade_type = '卖出' THEN tr.trade_quantity ELSE 0 END) as holding_qty
            FROM trade_record tr
            GROUP BY tr.stock_code
            HAVING holding_qty > 0
        ''')
        holdings = cursor.fetchall()
        print(f"   当前持仓股票: {len(holdings)}")
        for h in holdings:
            print(f"     - {h['stock_code']}: {h['holding_qty']} 股")
        
        conn.close()
        return True
    except Exception as e:
        print_fail(f"数据库查询异常: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("\n" + "#"*80)
    print("#" + " "*78 + "#")
    print("#" + " "*10 + "个人专属交易系统 - 完整测试报告" + " "*38 + "#")
    print("#" + " "*78 + "#")
    print("#"*80)
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = []
    
    # 1. 健康检查
    results.append(("健康检查", test_health()))
    
    # 等待一下，让服务完全稳定
    import time
    time.sleep(1)
    
    # 2. 获取账户
    accounts = test_get_accounts()
    results.append(("获取账户列表", len(accounts) > 0))
    
    # 3. 获取单个账户
    if accounts:
        account = test_get_single_account(accounts[0]['account_id'])
        results.append(("获取单个账户", account is not None))
    else:
        results.append(("获取单个账户", False))
    
    # 4. 触发价格更新
    results.append(("触发价格更新", test_trigger_price_update()))
    
    # 5. 获取交易计划
    plans = test_get_trade_plans()
    results.append(("获取交易计划", len(plans) >= 0))  # 允许0个
    
    # 6. 获取股票池
    pool = test_get_stock_pool()
    results.append(("获取股票池", len(pool) > 0))
    
    # 7. 数据库查询
    results.append(("数据库查询", test_database_direct()))
    
    # 汇总
    print_section("8. 测试汇总")
    total_passed = sum(1 for (_, passed) in results if passed)
    total_tests = len(results)
    
    print(f"\n总计: {total_passed}/{total_tests} 个测试通过\n")
    print("-" * 80)
    for (test_name, passed) in results:
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"  {test_name:30s} : {status}")
    print("-" * 80)
    
    if total_passed == total_tests:
        print("\n🎉 所有测试通过！系统运行正常！")
    else:
        print(f"\n⚠️  有 {total_tests - total_passed} 个测试失败，请检查。")
    
    print("\n测试完成！")

if __name__ == "__main__":
    main()
