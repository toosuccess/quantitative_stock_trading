# 评价排名第一股票计划

## 一、任务说明

根据项目规则，评价排名第一的股票（海天精工 sh601882），并将评价结果保存到数据库。

## 二、执行步骤

### 2.1 确认股票信息
- 股票代码：sh601882
- 股票名称：海天精工
- 当前排名：第1名（综合评分95分）

### 2.2 检查数据库
- 确认股票是否在 `stock_basic_info` 表中
- 如果不在，先添加到数据库

### 2.3 创建评价表
创建 `stock_evaluation` 表存储评价结果：

```sql
CREATE TABLE IF NOT EXISTS stock_evaluation (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    stock_code VARCHAR(20) NOT NULL,
    stock_name VARCHAR(50) NOT NULL,
    evaluation_date DATE NOT NULL,
    composite_score DECIMAL(10,2),
    rating VARCHAR(20),
    technical_score DECIMAL(10,2),
    fundamental_score DECIMAL(10,2),
    news_score DECIMAL(10,2),
    policy_score DECIMAL(10,2),
    deduction_score DECIMAL(10,2),
    summary TEXT,
    investment_advice TEXT,
    risk_warning TEXT,
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(stock_code, evaluation_date)
)
```

### 2.4 执行评价
- 调用多维度评分模块
- 生成综合评价
- 生成投资建议
- 生成风险提示

### 2.5 保存评价结果
将评价结果写入 `stock_evaluation` 表

## 三、任务拆分

### 任务1：创建评价表
- 修改 `init_database.py` 添加评价表

### 任务2：创建评价技能
- 创建 `stock_evaluation_skill.py`
- 实现评价逻辑和保存功能

### 任务3：执行评价
- 对海天精工进行评价
- 保存评价结果

---

**计划状态**: 待审批
**创建时间**: 2026-02-21
