# 各指标得分变化趋势添加股票价格计划

## 一、需求描述

在"各指标得分变化趋势"图表中，添加股票价格曲线。

## 二、数据结构

**数据库字段**: `close_price`（已存在）

**示例数据**:
```
sh601882 | 2026-02-23 11:33:57 | 81.0 | 价格:21.24
```

## 三、功能设计

### 3.1 图表修改

**文件**: `frontend/src/views/ScoreDetail.vue`

#### 修改1：添加双Y轴

由于价格和评分的数值范围不同，需要使用双Y轴：
- 左Y轴：评分（0-100）
- 右Y轴：价格（自适应范围）

```javascript
yAxis: [
  {
    type: 'value',
    name: '得分',
    min: 0,
    max: 100
  },
  {
    type: 'value',
    name: '价格',
    position: 'right'
  }
]
```

#### 修改2：添加价格曲线

```javascript
series: [
  // ... 现有评分曲线 ...
  {
    name: '股票价格',
    type: 'line',
    yAxisIndex: 1,  // 使用右Y轴
    data: sortedHistory.map(s => s.close_price),
    smooth: true,
    itemStyle: { color: '#F56C6C' },
    lineStyle: { type: 'dashed' }
  }
]
```

#### 修改3：更新图例

```javascript
legend: {
  data: ['技术面', '基本面', '消息面', '政策面', '综合评分', '股票价格']
}
```

## 四、执行步骤

1. 修改`renderIndicatorChart`函数
2. 添加双Y轴配置
3. 添加股票价格曲线
4. 更新图例数据
5. 测试验证

## 五、验收标准

1. 图表显示股票价格曲线
2. 左Y轴显示评分（0-100）
3. 右Y轴显示价格
4. 图例包含"股票价格"
5. 鼠标悬停显示价格数据

---

**计划状态**: 待审批
**创建时间**: 2026-02-23
