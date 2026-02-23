# 股票池多选评价功能计划

## 一、需求描述

在股票池页面，允许用户勾选（多选）股票，进行再次评价。

## 二、功能设计

### 2.1 前端修改

**文件**: `frontend/src/views/StockSelection.vue`

#### 修改1：添加多选列
在表格中添加多选列：
```vue
<el-table 
  :data="paginatedData" 
  @selection-change="handleSelectionChange"
>
  <el-table-column type="selection" width="55" />
  ...
</el-table>
```

#### 修改2：添加批量操作按钮
在卡片头部添加批量评价按钮：
```vue
<el-button 
  type="warning" 
  :disabled="selectedStocks.length === 0"
  @click="batchEvaluate"
>
  批量评价 ({{ selectedStocks.length }})
</el-button>
```

#### 修改3：添加数据和方法
```javascript
const selectedStocks = ref([])

const handleSelectionChange = (selection) => {
  selectedStocks.value = selection
}

const batchEvaluate = async () => {
  // 调用后端API批量评价
}
```

### 2.2 后端修改

**文件**: `backend/app/api/routes.py`

#### 添加批量评价API
```python
@router.post("/stocks/batch-evaluate")
async def batch_evaluate_stocks(stock_codes: List[str]):
    """批量评价股票"""
    results = []
    for stock_code in stock_codes:
        result = evaluator.evaluate_stock(stock_code)
        results.append(result)
    return {"results": results, "total": len(results)}
```

## 三、执行步骤

1. 修改前端表格添加多选列
2. 添加批量操作按钮
3. 添加批量评价方法
4. 添加后端批量评价API
5. 端到端测试

## 四、验收标准

1. 用户可以多选股票
2. 显示已选数量
3. 点击批量评价后，调用评价技能
4. 评价完成后刷新列表

---

**计划状态**: 待审批
**创建时间**: 2026-02-23
