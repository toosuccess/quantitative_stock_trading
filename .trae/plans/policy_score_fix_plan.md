# 政策面评分修复计划（修订版）

## 一、问题分析

### 1.1 当前问题
政策面评分（`calculate_policy_score`）没有内容，原因是：
- 方法中只硬编码了8只股票的政策信息
- 其他股票都返回"行业政策信息不足，无加减分"
- 没有使用已有的 `POLICY_ORIENTED_INDUSTRIES` 行业政策数据

### 1.2 问题代码位置
- **文件**: `d:\workspace\quantitative_stock_trading\skills\multi_dimension_scoring.py`
- **方法**: `calculate_policy_score` (第399-443行)

## 二、修复方案

### 2.1 评分规则（降低基础得分）

| 行业类型 | 增长潜力 | 基础得分 |
|----------|----------|----------|
| 未来产业 | 极高 | +10分 |
| 战略性新兴产业 | 高 | +8分 |
| 民生消费 | 中高 | +5分 |
| 其他 | - | +3分 |

### 2.2 修改后的代码结构

```python
def calculate_policy_score(self, stock_code, industry=None):
    """
    计算政策面评分（基于行业政策支持）
    
    Args:
        stock_code: 股票代码
        industry: 所属行业（可选）
    
    Returns: (得分, 详细说明, 明细字典)
    """
    # 1. 获取股票所属行业
    # 2. 匹配行业政策信息
    # 3. 计算政策面得分（降低基础分）
    # 4. 返回结果
```

## 三、任务拆分

### 任务1: 修改 calculate_policy_score 方法
- **内容**: 根据行业动态计算政策得分，降低基础分

### 任务2: 修改调用方传递行业参数
- **内容**: 修改 `stock_selection_parallel.py` 传递行业参数

### 任务3: 测试验证
- **内容**: 验证政策面评分正确显示

## 四、代码修改位置

1. `d:\workspace\quantitative_stock_trading\skills\multi_dimension_scoring.py`
2. `d:\workspace\quantitative_stock_trading\skills\stock_selection_parallel.py`

---

**计划状态**: 待审批
**创建时间**: 2026-02-21
