# 图表显示交易计划盈亏情况计划

## 一、需求描述

在"各指标得分变化趋势"图表中，如果股票有执行计划，需要显示该股票计划过程中的盈亏情况。

## 二、数据结构

### 2.1 trade_plan表
| 字段 | 说明 |
|------|------|
| stock_code | 股票代码 |
| profit_loss | 盈亏金额 |
| profit_loss_rate | 盈亏比例 |
| status | 状态（pending/executing/completed） |
| plan_date | 计划日期 |

### 2.2 trade_record表
| 字段 | 说明 |
|------|------|
| stock_code | 股票代码 |
| trade_date | 交易日期 |
| trade_price | 交易价格 |
| trade_type | 交易类型（buy/sell） |

## 三、功能设计

### 3.1 后端API

**文件**: `backend/app/api/routes.py`

#### 新增API：获取股票交易计划
```python
@router.get("/stocks/{stock_code}/trade-plans")
async def get_stock_trade_plans(stock_code: str):
    """获取股票的交易计划"""
    plans = manager.get_trade_plans_by_stock(stock_code)
    return {"plans": plans}
```

### 3.2 前端修改

**文件**: `frontend/src/views/ScoreDetail.vue`

#### 修改1：获取交易计划数据
```javascript
const tradePlans = ref([])

const loadTradePlans = async () => {
  try {
    const response = await api.get(`/stocks/${stockCode.value}/trade-plans`)
    tradePlans.value = response.plans || []
  } catch (error) {
    console.error('加载交易计划失败:', error)
  }
}
```

#### 修改2：在图表上标记买卖点
- 买入点：绿色三角形标记
- 卖出点：红色三角形标记
- 盈亏区域：盈利用绿色填充，亏损用红色填充

#### 修改3：添加盈亏曲线
- 显示累计盈亏比例曲线
- 使用右Y轴（与价格共用）

## 四、执行步骤

1. 后端添加获取股票交易计划API
2. 前端获取交易计划数据
3. 在图表上添加买卖点标记
4. 添加盈亏曲线
5. 测试验证

## 五、验收标准

1. 图表显示买入点（绿色三角形）
2. 图表显示卖出点（红色三角形）
3. 图表显示盈亏曲线
4. 鼠标悬停显示交易详情
5. 如果没有交易计划，不影响原有图表

---

**计划状态**: 待审批
**创建时间**: 2026-02-23
