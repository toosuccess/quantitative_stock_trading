# 基本面评分体系全系统同步更新计划

## 问题分析
前端页面仍显示旧的基本面评分体系（PE 20分, PB 15分, ROE 20分, 净利润增长率 20分, 营收增长率 15分, 负债率 10分），需要全系统替换为新5大类评分体系。

## 新评分体系
- **盈利能力（30分）**：ROE（20分）+ 净利率（10分）
- **成长能力（25分）**：净利润增长率（15分）+ 营收增长率（10分）
- **估值（20分）**：PE（12分）+ PB（8分）
- **财务健康（15分）**：负债率（10分）+ 流动比率（5分）
- **现金流&运营（10分）**：资产周转率（5分）+ 现金流动比率（5分）

## 需要修改的文件

### 1. 前端 StockSelection.vue
- 修改 `getFundamentalLabel` 函数，添加新指标映射：
  - `net_margin` → 净利率
  - `current_ratio` → 流动比率
  - `asset_turnover` → 资产周转率
  - `cash_flow_ratio` → 现金流动比率

### 2. 前端 ScoreDetail.vue
- 修改 `getFundamentalLabel` 函数，添加新指标映射（同上）
- 修改评价体系说明卡片，替换为新5大类评分体系说明

### 3. 后端 stock_evaluator_skills.py（已完成）
- `calculate_fundamental_score` 已更新为新5大类评分体系 ✅
- `get_fundamental_data` 已扩展获取更多字段 ✅
- `fundamental_data_cache` 表已更新 ✅

### 4. 数据库 score_record 表
- 旧评分记录的 `fundamental_detail` 字段仍是旧格式（6个指标）
- 新评分记录已使用新格式（10个指标）
- 前端需要兼容新旧格式

## 执行步骤

1. 修改 StockSelection.vue 的 `getFundamentalLabel` 函数
2. 修改 ScoreDetail.vue 的 `getFundamentalLabel` 函数
3. 修改 ScoreDetail.vue 的评价体系说明卡片
4. 重启前后端验证
