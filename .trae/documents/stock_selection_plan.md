# 选股执行计划

## 任务目标
根据十五五规划的政策导向，使用stock_selector_skills.py技能进行选股，并将结果保存到stock_basic_info表。

## 执行步骤

### 1. 数据库状态检查
- 检查stock_basic_info表的当前状态
- 验证数据库连接是否正常
- 确认表结构是否完整

### 2. 执行选股
- 调用stock_selector_skills.py中的run_stock_selection函数
- 选择所有政策导向行业进行选股
- 每个行业最多选择20只股票
- 排除ST股票

### 3. 验证选股结果
- 检查选股数量和行业分布
- 验证数据是否成功保存到数据库
- 检查stock_basic_info表的更新情况

### 4. 生成选股报告
- 汇总选股结果
- 分析行业分布
- 提供选股统计信息

## 预期结果
- 动态扩充核心股票池
- 排除ST股票
- 保存股票基本信息到stock_basic_info表
- 提供完整的选股报告

## 潜在风险
- 网络请求失败（API调用超时）
- 数据库连接问题
- 数据格式异常

## 风险处理
- 增加异常捕获机制
- 实现重试逻辑
- 确保数据完整性验证

## 执行文件
- 主要执行文件：`skills/stock_selector_skills.py`
- 数据库文件：`backend/database/trading_system.db`
- 验证脚本：`backend/check_db.py`