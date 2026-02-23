# 图表添加止损止盈点和盈亏区间计划

## 一、需求描述

根据交易计划中的止损价和止盈价，在图表中标记止损点、止盈点，并绘制盈亏区间。

## 二、数据结构

### 2.1 trade_plan表字段
| 字段 | 说明 | 示例 |
|------|------|------|
| stop_loss_price | 止损价 | 9.4 |
| take_profit_price | 止盈价 | 11.24 |
| avg_cost_price | 成本价 | 10.22 |

### 2.2 示例数据
```
吉大通信: 止损价=9.4, 止盈价=11.24, 成本价=10.22
万泽股份: 止损价=30.3, 止盈价=36.23
```

## 三、功能设计

### 3.1 图表元素

**文件**: `frontend/src/views/ScoreDetail.vue`

#### 1. 止损线（红色虚线）
- 水平线，显示止损价位
- 标签：止损价: 9.4

#### 2. 止盈线（绿色虚线）
- 水平线，显示止盈价位
- 标签：止盈价: 11.24

#### 3. 成本线（蓝色虚线）
- 水平线，显示成本价位
- 标签：成本价: 10.22

#### 4. 盈亏区间
- 盈利区间：成本价到止盈价之间，绿色半透明填充
- 亏损区间：成本价到止损价之间，红色半透明填充

### 3.2 ECharts配置

```javascript
series: [
  // ... 现有曲线 ...
  {
    name: '止损线',
    type: 'line',
    yAxisIndex: 1,
    data: Array(times.length).fill(stopLossPrice),
    lineStyle: { type: 'dashed', color: '#F56C6C' },
    itemStyle: { color: '#F56C6C' },
    symbol: 'none'
  },
  {
    name: '止盈线',
    type: 'line',
    yAxisIndex: 1,
    data: Array(times.length).fill(takeProfitPrice),
    lineStyle: { type: 'dashed', color: '#67C23A' },
    itemStyle: { color: '#67C23A' },
    symbol: 'none'
  },
  {
    name: '成本线',
    type: 'line',
    yAxisIndex: 1,
    data: Array(times.length).fill(avgCostPrice),
    lineStyle: { type: 'dashed', color: '#409EFF' },
    itemStyle: { color: '#409EFF' },
    symbol: 'none'
  }
]
```

### 3.3 盈亏区间标记

使用 `markArea` 在价格曲线上标记盈亏区间：

```javascript
{
  name: '股票价格',
  type: 'line',
  yAxisIndex: 1,
  markArea: {
    data: [
      [
        { yAxis: avgCostPrice, name: '成本' },
        { yAxis: takeProfitPrice, name: '盈利区', itemStyle: { color: 'rgba(103,194,58,0.2)' } }
      ],
      [
        { yAxis: stopLossPrice, name: '止损' },
        { yAxis: avgCostPrice, name: '亏损区', itemStyle: { color: 'rgba(245,108,108,0.2)' } }
      ]
    ]
  }
}
```

## 四、执行步骤

1. 从交易计划中获取止损价、止盈价、成本价
2. 在图表中添加止损线、止盈线、成本线
3. 添加盈亏区间标记
4. 更新图例
5. 测试验证

## 五、验收标准

1. 图表显示止损线（红色虚线）
2. 图表显示止盈线（绿色虚线）
3. 图表显示成本线（蓝色虚线）
4. 盈利区间用绿色半透明填充
5. 亏损区间用红色半透明填充
6. 如果没有交易计划，不影响原有图表

---

**计划状态**: 待审批
**创建时间**: 2026-02-23
