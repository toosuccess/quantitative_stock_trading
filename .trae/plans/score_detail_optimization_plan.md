# 评分详情页面优化计划 - 更新

## 一、需求确认

### 问题分析

检查数据库中消息面和政策面明细的数据结构：

**消息面明细（news_detail）**：
```json
{
  "events": [
    {
      "date": "2026-02-05",
      "type": "利好",
      "title": "今日38只个股突破年线",
      "score_impact": 0,
      "is_recent": false
    }
  ]
}
```
- ❌ 没有`source`字段
- ❌ 没有`url`字段

**政策面明细（policy_detail）**：
```json
{
  "policies": [
    {
      "date": "2026-02-23",
      "level": "国家政策",
      "title": "高端制造产业政策支持",
      "score_impact": 8
    }
  ]
}
```
- ❌ 没有`source`字段
- ❌ 没有`url`字段

### 前端已添加的列

前端代码已添加了以下列：
- 消息面明细：`source`（来源）、`summary`（内容摘要）、`操作`（查看详情）
- 政策面明细：`source`（来源）、`操作`（查看详情）

## 二、解决方案

### 方案1：移除source列，只保留操作列

由于数据库中没有`source`字段，移除前端显示的`source`列。

### 方案2：修改后端技能，添加url字段

如果需要保留外部链接功能，需要：
1. 修改`stock_evaluator_skills.py`的`calculate_news_score`方法
2. 在保存消息/政策时，添加`url`字段到数据库

## 三、执行步骤

### 选项1：移除source列（推荐）

**文件**: `frontend/src/views/ScoreDetail.vue`

#### 修改1：移除消息面明细的source列
```vue
<el-table-column prop="title" label="事件标题" show-overflow-tooltip />
<el-table-column prop="summary" label="内容摘要" width="200" show-overflow-tooltip />
```

#### 修改2：移除政策面明细的source列
```vue
<el-table-column prop="title" label="政策名称" show-overflow-tooltip />
<el-table-column prop="content" label="政策内容" show-overflow-tooltip />
```

### 选项2：添加url字段（如需要）

**文件**: `skills/stock_evaluator_skills.py`

#### 修改1：在消息/政策数据中添加url字段
```python
# 在返回的events/policies中添加url字段
events.append({
    'date': event_date,
    'type': event_type,
    'title': event_title,
    'score_impact': score_impact,
    'is_recent': is_recent,
    'url': event_url  # 新增
})
```

## 四、验收标准

1. 移除消息面和政策面明细中的`source`列
2. 操作列正常显示
3. 如果选择选项2，url字段正确保存

---

**计划状态**: 待审批
**创建时间**: 2026-02-23
