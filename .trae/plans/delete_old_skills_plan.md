# 删除旧技能文件计划

## 一、依赖检查结果

### 1.1 新技能依赖分析

**stock_evaluator_skills.py** 依赖：
- akshare, sqlite3, os, json, numpy, pandas, datetime
- ✅ **没有引用旧技能**

**stock_selector_skills.py** 依赖：
- akshare, sqlite3, os, datetime
- ✅ **没有引用旧技能**

### 1.2 后端脚本依赖分析

发现 `backend/scripts/run_stock_selection.py` 引用了旧技能：
```python
from skills.stock_selection_skill import (
    POLICY_ORIENTED_INDUSTRIES,
    INDUSTRY_STOCK_MAPPING,
    build_stock_pool,
    ...
)
```

**需要更新此脚本使用新技能**

## 二、待删除文件清单

### 2.1 旧技能核心文件（2个）

| 文件 | 说明 |
|------|------|
| `stock_selection_skill.py` | 旧选股技能 |
| `multi_dimension_scoring.py` | 旧评分模块 |

### 2.2 辅助/临时文件（13个）

| 文件 | 说明 |
|------|------|
| `stock_selection_parallel.py` | 并行选股 |
| `rescore_stock_pool.py` | 重新评分脚本 |
| `reevaluate_stock.py` | 重新评价脚本 |
| `stock_price_skill.py` | 股价技能 |
| `analyze_bollinger.py` | 布林带分析 |
| `analyze_ma_data.py` | 均线分析 |
| `run_scoring_test.py` | 测试脚本 |
| `run_selection_with_extra.py` | 扩展选股 |
| `run_stock_selection.py` | 运行选股 |
| `test_stock_scoring_skill.py` | 测试文件 |
| `migrate_stock_data.py` | 数据迁移 |
| `stock_scoring_test_report.md` | 测试报告 |
| `选股技能.md` | 旧文档 |

### 2.3 缓存目录

| 目录 | 说明 |
|------|------|
| `__pycache__/` | Python缓存 |

## 三、执行步骤

1. **更新后端脚本** - 修改 `backend/scripts/run_stock_selection.py` 使用新技能
2. **删除旧技能核心文件** - 2个文件
3. **删除辅助/临时文件** - 13个文件
4. **清理缓存目录** - `__pycache__/`

## 四、保留文件

| 文件 | 说明 |
|------|------|
| `stock_selector_skills.py` | 新选股技能 |
| `stock_evaluator_skills.py` | 新评价技能 |

---

**计划状态**: 待审批
**创建时间**: 2026-02-23
