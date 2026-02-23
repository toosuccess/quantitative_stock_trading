# 评分详情页面优化计划 - 最终版

## 一、问题分析

### 1.1 数据结构不匹配

**数据库实际结构**（检查结果）：
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

**前端期望结构**：
- 消息面明细：`source`（来源）、`summary`（内容摘要）、`url`（外部链接）
- 政策面明细：`source`（来源）、`url`（外部链接）

### 1.2 问题确认

❌ 数据库中**没有** `source` 字段
❌ 数据库中**没有** `url` 字段
✅ 前端已添加 `summary`（内容摘要）列
✅ 前端已添加 `url`（外部链接）列和操作

## 二、解决方案

### 方案1：移除source列（推荐）

由于数据库中没有 `source` 字段，移除前端显示的 `source` 列。

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

### 方案2：添加url字段到数据库（如需要）

如果需要保留外部链接功能，需要修改后端技能。

**文件**: `skills/stock_evaluator_skills.py`

#### 修改：在消息/政策数据中添加url字段
```python
events.append({
    'date': event_date,
    'type': event_type,
    'title': event_title,
    'score_impact': score_impact,
    'is_recent': is_recent,
    'url': event_url  # 新增
})
```

### 方案3：移除操作列（如不需要）

如果不需要外部链接功能，可以移除"查看详情"按钮。

## 三、执行步骤

### 选项1：移除source列（推荐）

1. 修改消息面明细表格，移除 `source` 列
2. 修改政策面明细表格，移除 `source` 列

### 选项2：添加url字段（可选）

1. 修改后端技能，在消息/政策数据中添加 `url` 字段
2. 测试验证

## 四、验收标准

1. 消息面明细不显示 `source` 列
2. 政策面明细不显示 `source` 列
3. 操作列正常显示（如果有url则显示按钮）

---

**计划状态**: 待审批
**创建时间**: 2026-02-23
