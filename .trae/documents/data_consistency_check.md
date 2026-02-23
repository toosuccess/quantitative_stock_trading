# 数据一致性问题检查报告

## 一、问题分析

### 1.1 发现的问题
从前端页面显示的数据来看：
- 消息面得分：显示为0
- 政策面得分：显示为0
- 扣分：显示为0

### 1.2 根本原因

**数据库表结构不匹配！**

#### 数据库表定义（init_database.py）
```sql
CREATE TABLE IF NOT EXISTS score_record (
    -- 缺少以下字段：
    -- news_score
    -- policy_score
    -- deduction_score
    -- composite_score
    -- technical_detail
    -- fundamental_detail
    -- news_detail
    -- policy_detail
    -- deduction_detail
    -- summary
    -- is_leader
)
```

#### 代码尝试插入的字段（stock_selection_skill.py）
```python
INSERT INTO score_record 
(stock_code, stock_name, score_date, 
 fundamental_score, fundamental_reason,
 technical_score, technical_reason,
 ma_score, macd_score, rsi_score, bollinger_score, volume_score, obv_score,
 total_score, composite_score, rating,
 close_price, volume, turnover_rate,
 create_time, update_time,
 technical_detail, fundamental_detail, news_detail, policy_detail, deduction_detail,
 summary, is_leader)
```

### 1.3 问题影响
- SQL插入可能失败或字段被忽略
- 前端查询时这些字段返回NULL或0
- 数据不完整

## 二、修复方案

### 方案1：修改数据库表结构（推荐）
添加缺失的字段到 `score_record` 表：

```sql
ALTER TABLE score_record ADD COLUMN news_score DECIMAL(10,4) DEFAULT 0;
ALTER TABLE score_record ADD COLUMN policy_score DECIMAL(10,4) DEFAULT 0;
ALTER TABLE score_record ADD COLUMN deduction_score DECIMAL(10,4) DEFAULT 0;
ALTER TABLE score_record ADD COLUMN composite_score DECIMAL(10,4) DEFAULT 0;
ALTER TABLE score_record ADD COLUMN technical_detail TEXT;
ALTER TABLE score_record ADD COLUMN fundamental_detail TEXT;
ALTER TABLE score_record ADD COLUMN news_detail TEXT;
ALTER TABLE score_record ADD COLUMN policy_detail TEXT;
ALTER TABLE score_record ADD COLUMN deduction_detail TEXT;
ALTER TABLE score_record ADD COLUMN summary TEXT;
ALTER TABLE score_record ADD COLUMN is_leader INTEGER DEFAULT 0;
```

### 方案2：重新初始化数据库
修改 `init_database.py`，添加缺失字段后重新创建表。

## 三、任务拆分

### 任务1：修改数据库初始化脚本
- 修改 `init_database.py` 添加缺失字段

### 任务2：对现有数据库执行ALTER TABLE
- 添加缺失字段到现有表

### 任务3：验证修复结果
- 重新运行选股评分
- 检查前端显示是否正确

---

**计划状态**: 待审批
**创建时间**: 2026-02-21
