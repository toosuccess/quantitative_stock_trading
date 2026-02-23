# 修复买卖点显示问题计划

## 一、问题分析

### 1.1 数据检查

**交易记录**：
| 日期 | 类型 | 价格 | 数量 |
|------|------|------|------|
| 2026-02-21 | 买入 | 10.22 | 1000 |
| 2026-02-23 | 卖出 | 11.24 | 1000 |

**评分记录时间格式**：
```
2026-02-23 09:56:05 | 价格: 10.22
2026-02-23 09:08:11 | 价格: 10.22
2026-02-22 21:25:56 | 价格: 10.22
2026-02-21 09:45:40 | 价格: 10.22
```

### 1.2 问题定位

**问题1**：`findIndex` 只找到第一个匹配的索引，但图表数据是按时间升序排列的，可能导致索引错误

**问题2**：买卖点应该显示交易价格，而不是评分记录的收盘价

**问题3**：买卖点应该在正确的日期位置显示

## 二、解决方案

### 2.1 修复买卖点数据

**修改文件**: `frontend/src/views/ScoreDetail.vue`

**修改逻辑**：
1. 使用交易价格而不是评分记录的收盘价
2. 正确匹配日期索引
3. 添加调试日志帮助排查

```javascript
tradePlans.value.forEach(plan => {
  if (plan.records) {
    plan.records.forEach(record => {
      const tradeDate = record.trade_date
      const dateIndex = times.findIndex(t => t && t.startsWith(tradeDate))
      
      console.log('交易记录:', record.trade_date, record.trade_type, '匹配索引:', dateIndex)
      
      if (dateIndex !== -1) {
        const point = {
          name: record.trade_type,
          value: [dateIndex, record.trade_price],  // 使用交易价格
          trade_price: record.trade_price,
          trade_quantity: record.trade_quantity,
          trade_amount: record.trade_amount,
          plan_name: plan.plan_name
        }
        if (record.trade_type === '买入') {
          buyPoints.push(point)
        } else if (record.trade_type === '卖出') {
          sellPoints.push(point)
        }
      }
    })
  }
})
```

### 2.2 改进日期匹配

如果同一天有多条评分记录，需要找到最接近交易时间的记录：

```javascript
const findBestMatchIndex = (tradeDate, tradeTime, times, sortedHistory) => {
  let bestIndex = -1
  let bestDiff = Infinity
  
  times.forEach((t, index) => {
    if (t && t.startsWith(tradeDate)) {
      if (tradeTime) {
        const recordTime = new Date(t).getTime()
        const tradeDateTime = new Date(`${tradeDate} ${tradeTime}`).getTime()
        const diff = Math.abs(recordTime - tradeDateTime)
        if (diff < bestDiff) {
          bestDiff = diff
          bestIndex = index
        }
      } else if (bestIndex === -1) {
        bestIndex = index
      }
    }
  })
  
  return bestIndex
}
```

## 三、执行步骤

1. 修改买卖点数据，使用交易价格
2. 添加调试日志
3. 测试验证

## 四、验收标准

1. 买入点显示在正确的日期位置
2. 卖出点显示在正确的日期位置
3. 买卖点使用交易价格而不是收盘价
4. 鼠标悬停显示正确的交易信息

---

**计划状态**: 待审批
**创建时间**: 2026-02-23
