"""测试API数据"""
import requests
import json

base_url = 'http://localhost:8000/api/v1'

# 测试账户API
print('=' * 60)
print('1. 测试账户API (/accounts)')
print('=' * 60)

try:
    resp = requests.get(f'{base_url}/accounts', timeout=10)
    accounts = resp.json()

    print(f'响应状态: {resp.status_code}')
    print(f'返回类型: {type(accounts).__name__}')

    if isinstance(accounts, list):
        print(f'账户数量: {len(accounts)}')

        if len(accounts) > 0:
            acc = accounts[0]
            print(f'\n第一个账户字段:')
            for key, value in acc.items():
                print(f'  {key}: {value} (类型: {type(value).__name__})')
    else:
        print(f'返回数据: {str(accounts)[:300]}')
except Exception as e:
    print(f'错误: {e}')

# 测试交易汇总API
print('\n' + '=' * 60)
print('2. 测试交易汇总API (/trade/summary)')
print('=' * 60)

try:
    resp = requests.get(f'{base_url}/trade/summary', timeout=10)
    summary = resp.json()

    print(f'响应状态: {resp.status_code}')
    print(f'返回类型: {type(summary).__name__}')

    if isinstance(summary, dict):
        print(f'\n所有字段:')
        for key, value in summary.items():
            print(f'  {key}: {value} (类型: {type(value).__name__})')
    else:
        print(f'返回数据: {str(summary)[:300]}')
except Exception as e:
    print(f'错误: {e}')
