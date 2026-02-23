# 新技能评分标准调整计划

## 一、调整内容

### 1. 成交量评分
**保持新技能算法**（更严格、更合理）：
- 成交量 > MA5
- 成交量 > MA60
- 换手率 5%-20%

### 2. 技术面占比调整
将技术面权重从40%调整为**60%**：
```python
# 旧公式
composite_score = technical_score * 0.4 + fundamental_score * 0.3 + news_score + policy_score - deduction_score

# 新公式
composite_score = technical_score * 0.6 + fundamental_score * 0.2 + news_score + policy_score - deduction_score
```

### 3. PB评分标准对比

| PB范围 | 旧技能 | 新技能 | 建议标准 |
|--------|--------|--------|----------|
| PB < 2 | 15分 | 15分 | 15分 |
| 2 ≤ PB < 3 | 10分 | 15分 | 10分 |
| 3 ≤ PB < 5 | 5分 | 10分 | 5分 |
| PB ≥ 5 | 0分 | 0分 | 0分 |

**建议采用旧技能标准**（更合理）：
- PB < 2: 15分（资产价值高）
- 2 ≤ PB < 3: 10分（资产价值适中）
- 3 ≤ PB < 5: 5分（资产价值偏低）
- PB ≥ 5: 0分（资产价值低）

## 二、修改文件

`stock_evaluator_skills.py`

### 修改1：调整技术面权重
```python
def calculate_composite_score(self, technical_score, fundamental_score, news_score, policy_score, deduction_score):
    return technical_score * 0.6 + fundamental_score * 0.2 + news_score + policy_score - deduction_score
```

### 修改2：调整PB评分标准
```python
if 0 < data['pb'] < 2: score += 15
elif 2 <= data['pb'] < 3: score += 10
elif 3 <= data['pb'] < 5: score += 5
```

## 三、验证测试

修改后重新测试5只股票，验证评分差异是否缩小。

---

**计划状态**: 待审批
**创建时间**: 2026-02-22
