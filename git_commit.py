import subprocess
import os

os.chdir(r'd:\workspace\quantitative_stock_trading')

# 添加所有更改的文件
result = subprocess.run(['git', 'add', '.'], capture_output=True, text=True)
result = subprocess.run(['git', 'commit', '-m', 'Add comments to code files'], capture_output=True, text=True)
print('commit stdout:', result.stdout)
print('commit stderr:', result.stderr)
print('commit returncode:', result.returncode)
