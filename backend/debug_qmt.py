"""
调试QMT数据获取
"""
from xtquant import xtdata
import os

print("=" * 60)
print("QMT数据获取调试")
print("=" * 60)

print(f"\nQMT数据目录: {xtdata.get_data_dir()}")

test_code = 'SH.600410'
print(f"\n测试股票: {test_code}")

print("\n1. 尝试 get_local_data:")
try:
    data = xtdata.get_local_data(
        stock_list=[test_code],
        period='1d',
        count=10
    )
    print(f"   结果类型: {type(data)}")
    if data:
        print(f"   数据: {data}")
except Exception as e:
    print(f"   错误: {e}")

print("\n2. 尝试 get_market_data_ex:")
try:
    data = xtdata.get_market_data_ex(
        field_list=['open', 'high', 'low', 'close', 'volume'],
        stock_list=[test_code],
        period='1d',
        count=10
    )
    print(f"   结果类型: {type(data)}")
    if data:
        print(f"   键: {data.keys() if hasattr(data, 'keys') else 'N/A'}")
        if test_code in data:
            print(f"   数据长度: {len(data[test_code])}")
            print(f"   数据: {data[test_code]}")
except Exception as e:
    print(f"   错误: {e}")

print("\n3. 尝试 get_full_tick:")
try:
    data = xtdata.get_full_tick([test_code])
    print(f"   结果类型: {type(data)}")
    if data:
        print(f"   数据: {data}")
except Exception as e:
    print(f"   错误: {e}")

print("\n4. 检查本地数据文件:")
data_dir = xtdata.get_data_dir()
if os.path.exists(data_dir):
    print(f"   数据目录存在: {data_dir}")
    for root, dirs, files in os.walk(data_dir):
        level = root.replace(data_dir, '').count(os.sep)
        if level < 2:
            indent = ' ' * 2 * level
            print(f'{indent}{os.path.basename(root)}/')
            subindent = ' ' * 2 * (level + 1)
            for file in files[:5]:
                print(f'{subindent}{file}')
            if len(files) > 5:
                print(f'{subindent}... 还有 {len(files)-5} 个文件')
else:
    print(f"   数据目录不存在: {data_dir}")
