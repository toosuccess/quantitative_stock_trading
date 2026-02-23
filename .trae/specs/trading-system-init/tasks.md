# Tasks

## Phase 1: 数据层建设
- [ ] Task 1: 初始化数据库表结构
  - [ ] SubTask 1.1: 执行SQL建表脚本创建7张表
  - [ ] SubTask 1.2: 验证表结构和索引正确性
  - [ ] SubTask 1.3: 插入测试数据验证CRUD操作

- [ ] Task 2: 实现数据获取模块
  - [ ] SubTask 2.1: 创建AkShare数据获取接口封装
  - [ ] SubTask 2.2: 实现股票基本信息获取功能
  - [ ] SubTask 2.3: 实现技术指标数据获取功能（MA、MACD、RSI、布林带、OBV）
  - [ ] SubTask 2.4: 实现实时股价获取功能

## Phase 2: 选股与评分模块
- [ ] Task 3: 实现选股模块
  - [ ] SubTask 3.1: 创建选股策略配置文件
  - [ ] SubTask 3.2: 实现技术面选股逻辑
  - [ ] SubTask 3.3: 实现基本面选股逻辑
  - [ ] SubTask 3.4: 实现选股结果存储到数据库

- [ ] Task 4: 实现评分模块
  - [ ] SubTask 4.1: 创建评分策略配置文件
  - [ ] SubTask 4.2: 实现技术指标评分计算
  - [ ] SubTask 4.3: 实现综合评分计算
  - [ ] SubTask 4.4: 实现评级生成（强烈推荐/推荐/中性/观望/不推荐）
  - [ ] SubTask 4.5: 实现评分结果存储到数据库

## Phase 3: 交易计划模块
- [ ] Task 5: 实现交易计划管理
  - [ ] SubTask 5.1: 创建交易计划创建接口
  - [ ] SubTask 5.2: 实现交易计划查询接口
  - [ ] SubTask 5.3: 实现交易计划更新接口
  - [ ] SubTask 5.4: 实现交易计划删除接口

- [ ] Task 6: 实现交易执行步骤管理
  - [ ] SubTask 6.1: 创建执行步骤创建接口
  - [ ] SubTask 6.2: 实现执行步骤状态更新
  - [ ] SubTask 6.3: 实现执行步骤与交易计划的关联

## Phase 4: 交易执行模块
- [ ] Task 7: 实现交易执行功能
  - [ ] SubTask 7.1: 创建交易记录创建接口
  - [ ] SubTask 7.2: 实现定时任务调度（收盘前15分钟）
  - [ ] SubTask 7.3: 实现手工交易执行入口
  - [ ] SubTask 7.4: 实现交易记录查询接口

## Phase 5: 复盘模块
- [ ] Task 8: 实现复盘分析功能
  - [ ] SubTask 8.1: 创建复盘记录创建接口
  - [ ] SubTask 8.2: 实现交易胜率计算
  - [ ] SubTask 8.3: 实现盈亏比计算
  - [ ] SubTask 8.4: 实现最大回撤计算
  - [ ] SubTask 8.5: 实现夏普比率计算
  - [ ] SubTask 8.6: 实现复盘记录存储到数据库

## Phase 6: 前端界面
- [ ] Task 9: 创建前端看板
  - [ ] SubTask 9.1: 搭建Vue 3项目框架
  - [ ] SubTask 9.2: 实现选股结果展示页面
  - [ ] SubTask 9.3: 实现评分结果展示页面
  - [ ] SubTask 9.4: 实现交易计划管理页面
  - [ ] SubTask 9.5: 实现交易执行操作页面
  - [ ] SubTask 9.6: 实现复盘分析看板页面
  - [ ] SubTask 9.7: 集成ECharts实现K线图和资产曲线可视化

## Phase 7: 测试与验证
- [ ] Task 10: 编写测试用例
  - [ ] SubTask 10.1: 编写数据获取模块单元测试
  - [ ] SubTask 10.2: 编写选股模块单元测试
  - [ ] SubTask 10.3: 编写评分模块单元测试
  - [ ] SubTask 10.4: 编写交易计划模块单元测试
  - [ ] SubTask 10.5: 编写交易执行模块单元测试
  - [ ] SubTask 10.6: 编写复盘模块单元测试
  - [ ] SubTask 10.7: 使用Playwright进行端到端测试

# Task Dependencies
- Task 2 depends on Task 1
- Task 3 depends on Task 2
- Task 4 depends on Task 2
- Task 5 depends on Task 4
- Task 6 depends on Task 5
- Task 7 depends on Task 6
- Task 8 depends on Task 7
- Task 9 depends on Task 8
- Task 10 depends on Task 9

# Parallelizable Tasks
- Task 3 and Task 4 can run in parallel (both depend only on Task 2)
- SubTask 9.2, 9.3, 9.4, 9.5, 9.6 can run in parallel (all depend only on SubTask 9.1)
