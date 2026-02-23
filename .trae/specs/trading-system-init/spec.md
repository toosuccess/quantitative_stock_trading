# 交易系统实现规格说明

## 1. 系统概述

个人专属交易系统是一个基于Vue 3和FastAPI的全栈交易管理平台，实现了从选股、计划、执行到复盘的完整交易流程。

## 2. 技术栈

### 2.1 后端
- **框架**：FastAPI
- **数据库**：SQLite
- **数据处理**：Pandas, TA-Lib
- **数据源**：AkShare

### 2.2 前端
- **框架**：Vue 3
- **UI组件库**：Element Plus
- **图表库**：ECharts
- **构建工具**：Vite

## 3. 数据库设计

### 3.1 数据表

| 表名 | 说明 | 主要字段 |
|------|------|----------|
| account_info | 账户信息表 | account_id, account_name, total_assets, initial_assets, profit_loss |
| stock_basic_info | 股票基本信息表 | stock_code, stock_name, industry, sector |
| score_record | 评分记录表 | stock_code, total_score, rating, ma_score, macd_score |
| trade_plan | 交易计划表 | plan_id, stock_code, planned_quantity, holding_quantity, status |
| trade_execution_step | 交易执行步骤表 | step_id, plan_id, trade_direction, target_price, status |
| trade_record | 交易记录表 | record_id, trade_type, trade_amount, trade_price |
| review_record | 复盘记录表 | review_id, plan_id, review_result |

### 3.2 关键设计

#### 账户盈亏计算
- 新增`initial_assets`字段记录初始资产
- 盈亏 = 总资产 - 初始资产

#### 交易执行步骤
- 支持五种交易方向：建仓、加仓、减仓、止损清仓、止盈清仓
- 每个步骤独立管理状态和执行数量

## 4. API接口

### 4.1 账户管理
```
GET    /accounts              # 获取账户列表
POST   /account               # 创建账户
GET    /account/{id}          # 获取账户详情
PUT    /account/{id}          # 更新账户
DELETE /account/{id}          # 删除账户
GET    /account/{id}/summary  # 获取账户汇总
```

### 4.2 评分管理
```
GET    /scores                # 获取评分记录列表
GET    /scores/{code}         # 获取股票评分历史
GET    /stocks/pool/scores    # 获取股票池评分汇总
```

### 4.3 交易计划
```
POST   /trade/plan            # 创建交易计划
GET    /trade/plans           # 获取计划列表
GET    /trade/plan/{id}       # 获取计划详情
DELETE /trade/plan/{id}       # 删除计划
POST   /trade/plan/{id}/execute # 执行计划
```

### 4.4 交易执行
```
GET    /trade/steps           # 获取执行步骤列表
POST   /trade/step            # 创建执行步骤
POST   /trade/step/{id}/execute # 执行步骤
GET    /trade/records         # 获取交易记录
POST   /trade/record          # 创建交易记录
GET    /trade/statistics/{id} # 获取交易统计
GET    /trade/summary         # 获取交易汇总
```

## 5. 前端页面

### 5.1 首页 (Home.vue)
**功能**：
- 统计卡片：评分股票、交易计划、交易胜率、总盈亏
- 交易汇总：总买入金额、总卖出金额、净盈亏、已完成计划
- 资产曲线图表

**API调用**：
- `scoreApi.getScoreList()`
- `planApi.getPlanList()`
- `tradeApi.getStatistics()`
- `tradeApi.getSummary()`

### 5.2 股票池 (StockSelection.vue)
**功能**：
- 显示股票池评分汇总
- 按评级筛选
- 查看评分详情

### 5.3 账号管理 (AccountManagement.vue)
**功能**：
- 账户列表展示
- 创建/编辑/删除账户
- 显示盈亏情况

### 5.4 交易计划 (TradePlan.vue)
**功能**：
- 创建交易计划
- 设置止损止盈价格
- 自动生成执行步骤
- 查看计划状态和盈利情况
- 已完成计划可查看执行步骤

### 5.5 交易执行 (TradeExecution.vue)
**功能**：
- 执行步骤列表
- 交易记录列表（含合计行）
- 添加执行步骤
- 数量限制验证

**业务规则**：
- 加仓最大数量 = 计划数量 - 持仓数量
- 减仓最大数量 = 持仓数量
- 计划数量为0时禁止添加
- 计划完成后按钮置灰

### 5.6 复盘分析 (Review.vue)
**功能**：
- 交易统计分析
- 胜率、盈亏比、最大回撤

## 6. 业务规则实现

### 6.1 盈亏计算
```python
# 账户盈亏
profit_loss = total_assets - initial_assets

# 交易汇总
net_profit = sell_amount - buy_amount
```

### 6.2 数量限制
```javascript
// 加仓最大数量
const addStepMaxQuantity = computed(() => {
  return planned_quantity - holding_quantity
})

// 减仓最大数量
const addStepMaxQuantity = computed(() => {
  return holding_quantity
})
```

### 6.3 价格默认值
```javascript
// 止损清仓/止盈清仓使用目标价格
if (direction === '止损清仓' || direction === '止盈清仓') {
  defaultPrice = target_price
}
```

### 6.4 状态管理
- 交易计划状态：pending → executing → completed/cancelled
- 执行步骤状态：pending → completed
- 计划完成后禁用执行按钮

## 7. 已实现功能清单

### 7.1 核心功能
- [x] 多账户管理
- [x] 账户盈亏计算
- [x] 交易计划创建
- [x] 执行步骤自动生成
- [x] 手动执行交易
- [x] 交易记录管理
- [x] 交易汇总统计

### 7.2 用户体验
- [x] 首页仪表盘
- [x] 交易记录合计行
- [x] 数量限制验证
- [x] 按钮状态管理
- [x] 成交金额格式化（买入-，卖出+）

### 7.3 数据完整性
- [x] 初始资产记录
- [x] 目标价格记录
- [x] 执行数量验证

## 8. 待完善功能

### 8.1 计划中
- [ ] 定时自动执行
- [ ] 实时行情推送
- [ ] 手续费计算
- [ ] 滑点模拟

### 8.2 优化项
- [ ] 资产曲线实时数据
- [ ] 复盘记录管理
- [ ] 情绪记录功能
- [ ] 策略回测功能
