# 卖出股票后续走势分析功能 Spec

## Why
用户希望分析历史交易计划中已卖出股票的后续走势，了解卖出后1周、2周、3周、4周内的盈亏情况，以便评估卖出决策的正确性，优化未来的卖出策略。

## What Changes
- 新增"卖出分析"页面，展示已卖出股票的后续走势
- 新增后端API接口，查询卖出记录并计算后续价格变化
- 新增数据库视图或查询逻辑，关联卖出记录与后续股价数据

## Impact
- Affected specs: trading-system-init
- Affected code: 
  - backend/app/api/routes.py (新增API)
  - frontend/src/views/ (新增页面)
  - frontend/src/router/index.js (新增路由)

## ADDED Requirements

### Requirement: 卖出记录查询
系统 SHALL 提供查询已卖出股票记录的功能。

#### Scenario: 查询卖出记录
- **WHEN** 用户访问卖出分析页面
- **THEN** 系统显示所有已卖出的股票记录，包含股票代码、名称、卖出日期、卖出价格、卖出数量

### Requirement: 后续走势计算
系统 SHALL 计算卖出后1周、2周、3周、4周的股价变化。

#### Scenario: 计算后续盈亏
- **WHEN** 系统获取到卖出记录
- **THEN** 系统计算该股票在卖出后1周、2周、3周、4周的价格
- **AND** 计算各时间点的盈亏百分比
- **AND** 显示如果继续持有的盈亏情况

### Requirement: 分析报告展示
系统 SHALL 以表格和图表形式展示分析结果。

#### Scenario: 展示分析报告
- **WHEN** 用户查看卖出分析报告
- **THEN** 系统以表格形式展示每笔卖出记录的后续走势
- **AND** 系统以汇总形式展示整体卖出决策的准确性统计
- **AND** 系统高亮显示"卖早了"（卖出后上涨）和"卖对了"（卖出后下跌）的情况

## MODIFIED Requirements
无

## REMOVED Requirements
无
