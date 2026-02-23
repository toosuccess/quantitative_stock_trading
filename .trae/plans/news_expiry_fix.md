# 消息面过期消息不加分修复计划（最终版）

## 一、问题分析

### 1.1 当前问题
`calculate_news_score` 方法没有检查新闻日期，所有新闻都会影响评分。

### 1.2 用户需求
**只对最近三天的消息进行加减分**，超过三天的消息不加分。

## 二、修复方案

### 2.1 添加最近三天检查逻辑
只对**最近三天**的新闻进行加分，过期新闻只记录不加分：

```python
from datetime import datetime, timedelta

# 获取三天前的日期
three_days_ago = (datetime.now() - timedelta(days=3)).strftime('%Y-%m-%d')
today = datetime.now().strftime('%Y-%m-%d')

for _, row in recent_news.iterrows():
    title = str(row.get('新闻标题', ''))
    news_time_str = str(row.get('发布时间', ''))[:10]
    
    # 检查新闻是否在最近三天内
    is_recent = (news_time_str >= three_days_ago and news_time_str <= today)
    
    # 只有最近三天的新闻才加分
    for kw in positive_keywords:
        if kw in title:
            event_type = '利好'
            score_impact = 5 if is_recent else 0
            if is_recent:
                score += 5
            break
```

### 2.2 评分规则

| 新闻状态 | 记录到events | 加分 |
|----------|-------------|------|
| 最近三天利好 | ✅ | +5分 |
| 超过三天利好 | ✅ | 0分 |
| 最近三天利空 | ✅ | -5分 |
| 超过三天利空 | ✅ | 0分 |
| 中性新闻 | ✅ | 0分 |

## 三、任务拆分

### 任务1：修改 calculate_news_score 方法
- 添加最近三天检查逻辑
- 超过三天的新闻不加分但仍记录

---

**计划状态**: 待审批
**创建时间**: 2026-02-21
