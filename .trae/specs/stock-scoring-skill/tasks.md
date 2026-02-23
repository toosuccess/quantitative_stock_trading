# Tasks

- [x] Task 1: 创建评分技能模块结构
  - [x] SubTask 1.1: 创建 `skills/stock_scoring_skill.py` 文件
  - [x] SubTask 1.2: 定义 `StockScoringSkill` 类
  - [x] SubTask 1.3: 定义评分配置常量（评分规则、权重）

- [x] Task 2: 实现股票池读取功能
  - [x] SubTask 2.1: 实现从 `stock_basic_info` 表读取股票列表
  - [x] SubTask 2.2: 实现从 `score_record` 表读取最近评分过的股票
  - [x] SubTask 2.3: 支持按行业筛选股票

- [x] Task 3: 实现技术指标计算功能
  - [x] SubTask 3.1: 实现均线系统计算（MA5, MA10, MA20, MA60）
  - [x] SubTask 3.2: 实现MACD指标计算（DIFF, DEA, MACD）
  - [x] SubTask 3.3: 实现布林线计算（上轨、中轨、下轨）
  - [x] SubTask 3.4: 实现OBV指标计算
  - [x] SubTask 3.5: 实现成交量分析

- [x] Task 4: 实现评分计算功能
  - [x] SubTask 4.1: 实现均线系统评分（25分）
  - [x] SubTask 4.2: 实现成交量评分（25分）
  - [x] SubTask 4.3: 实现趋势指标评分（20分）
  - [x] SubTask 4.4: 实现资金指标评分（15分）
  - [x] SubTask 4.5: 实现布林线评分（15分）
  - [x] SubTask 4.6: 实现综合得分计算和评级输出

- [x] Task 5: 实现评分记录存储功能
  - [x] SubTask 5.1: 实现评分记录插入 `score_record` 表
  - [x] SubTask 5.2: 实现重复记录更新逻辑（同一天同一股票）

- [x] Task 6: 实现主入口函数
  - [x] SubTask 6.1: 实现 `score_stocks()` 主函数
  - [x] SubTask 6.2: 支持批量评分
  - [x] SubTask 6.3: 返回评分结果汇总

# Task Dependencies
- [Task 3] depends on [Task 2]
- [Task 4] depends on [Task 3]
- [Task 5] depends on [Task 4]
- [Task 6] depends on [Task 5]
