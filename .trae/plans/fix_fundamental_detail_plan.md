# 基本面明细显示问题修复计划

## 一、问题分析

### 前端期望格式
```json
{
  "pe": {"score": 20, "value": 24.63, "detail": "PE=24.63,估值适中"},
  "pb": {"score": 10, "value": 3.88, "detail": "PB=3.88,资产价值偏低"},
  "roe": {"score": 0, "value": 0, "detail": "ROE=0%"},
  ...
}
```

### 新技能保存格式
```json
{
  "pe": 24.63,
  "pb": 3.88,
  "roe": 0,
  "net_profit_growth": 42.5,
  "revenue_growth": 51.6,
  "debt_ratio": 44.5
}
```

## 二、修复方案

修改 `stock_evaluator_skills.py` 中的 `calculate_fundamental_score` 方法，返回包含score的详细格式。

## 三、修改内容

```python
def calculate_fundamental_score(self, stock_code):
    """计算基本面得分"""
    data = self.get_fundamental_data(stock_code)
    
    score = 0
    details = {}
    
    # PE评分
    pe_score = 0
    if 0 < data['pe'] < 30:
        pe_score = 20
    elif 30 <= data['pe'] < 50:
        pe_score = 10
    score += pe_score
    details['pe'] = {'score': pe_score, 'value': data['pe'], 'detail': f"PE={data['pe']:.2f}"}
    
    # PB评分
    pb_score = 0
    if 0 < data['pb'] < 2:
        pb_score = 15
    elif 2 <= data['pb'] < 3:
        pb_score = 10
    elif 3 <= data['pb'] < 5:
        pb_score = 5
    score += pb_score
    details['pb'] = {'score': pb_score, 'value': data['pb'], 'detail': f"PB={data['pb']:.2f}"}
    
    # ... 其他指标类似
    
    return score, details
```

---

**计划状态**: 待审批
**创建时间**: 2026-02-22
