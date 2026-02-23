# 最近打分时间显示时分秒修复计划

## 一、问题分析

### 1.1 当前显示
用户选中的span元素显示：`2026-02-21`（只显示日期）

### 1.2 问题代码位置
文件：`frontend/src/views/StockSelection.vue` 第178-180行

```vue
<el-table-column prop="create_time" label="最近打分时间" width="120">
  <template #default="scope">
    <span>{{ scope.row.create_time ? scope.row.create_time.substring(0, 10) : '-' }}</span>
  </template>
</el-table-column>
```

**问题**：`substring(0, 10)` 只取了前10个字符（日期部分），没有显示时分秒。

### 1.3 数据库中的时间格式
`create_time` 字段存储格式：`2026-02-21 14:30:25`

## 二、修复方案

### 2.1 修改显示格式
将 `substring(0, 10)` 改为显示完整时间，并调整列宽：

```vue
<el-table-column prop="create_time" label="最近打分时间" width="180">
  <template #default="scope">
    <span>{{ scope.row.create_time || '-' }}</span>
  </template>
</el-table-column>
```

### 2.2 或者显示简化格式
显示 `MM-DD HH:mm` 格式：

```vue
<el-table-column prop="create_time" label="最近打分时间" width="140">
  <template #default="scope">
    <span>{{ scope.row.create_time ? scope.row.create_time.substring(5, 16) : '-' }}</span>
  </template>
</el-table-column>
```

## 三、任务拆分

### 任务1：修改 StockSelection.vue 显示时分秒
- 修改列宽和显示格式

---

**计划状态**: 待审批
**创建时间**: 2026-02-21
