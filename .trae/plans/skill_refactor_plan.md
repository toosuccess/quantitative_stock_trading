# 技能重构计划

## 一、需求分析

### 1.1 当前问题
- skills目录下文件过多，职责不清晰
- 存在临时脚本文件（如rescore_stock_pool.py、reevaluate_stock.py等）
- 技能边界不明确

### 1.2 目标结构
根据项目规则，只需要两个核心技能：

| 技能 | 职责 | 输入 | 输出 |
|------|------|------|------|
| **选股技能** | 根据十五五规划选股，排除ST股 | 行业配置 | stock_basic_info表 |
| **评价技能** | 对股票进行多维度打分 | stock_basic_info中的股票 | score_record表 |

### 1.3 调用关系
```
选股技能 → 调用 → 评价技能
```

## 二、重构方案

### 2.1 新建技能文件

#### 文件1: `skills/stock_selector.py` (选股技能)
```python
"""
选股技能
职责：根据十五五规划选股，输出到stock_basic_info表
"""

class StockSelector:
    def __init__(self):
        pass
    
    def select_stocks(self, industries=None, limit=20):
        """
        选股主流程
        1. 获取行业股票池
        2. 排除ST股
        3. 保存到stock_basic_info
        4. 调用评价技能打分
        """
        pass
    
    def get_industry_stocks(self, industry):
        """获取指定行业的股票列表"""
        pass
    
    def filter_st_stocks(self, stocks):
        """过滤ST股票"""
        pass
    
    def save_to_database(self, stocks):
        """保存到stock_basic_info表"""
        pass
```

#### 文件2: `skills/stock_evaluator.py` (评价技能)
```python
"""
评价技能
职责：对stock_basic_info中的股票打分，输出到score_record表
"""

class StockEvaluator:
    def __init__(self):
        pass
    
    def evaluate_stock(self, stock_code):
        """
        评价单只股票
        返回：综合评分、评级、各维度得分
        """
        pass
    
    def evaluate_all(self):
        """
        评价stock_basic_info中所有股票
        """
        pass
    
    def calculate_technical_score(self, stock_code):
        """计算技术面得分"""
        pass
    
    def calculate_fundamental_score(self, stock_code):
        """计算基本面得分"""
        pass
    
    def calculate_news_score(self, stock_code):
        """计算消息面得分（最近三天）"""
        pass
    
    def calculate_policy_score(self, stock_code, industry):
        """计算政策面得分"""
        pass
    
    def calculate_deduction_score(self, stock_code):
        """计算减项扣分"""
        pass
    
    def save_score_record(self, stock_code, scores):
        """保存评分记录到score_record表"""
        pass
```

### 2.2 保留的辅助模块

| 文件 | 说明 |
|------|------|
| `multi_dimension_scoring.py` | 评分算法实现，被评价技能调用 |

### 2.3 待删除的文件

重构完成并测试通过后，删除以下文件：
- `stock_selection_skill.py` (旧选股技能)
- `stock_selection_parallel.py` (并行选股)
- `rescore_stock_pool.py` (重新评分)
- `reevaluate_stock.py` (重新评价)
- `stock_price_skill.py` (股价技能，合并到评价技能)
- `analyze_bollinger.py` (布林带分析)
- `analyze_ma_data.py` (均线分析)
- `run_scoring_test.py` (测试脚本)
- `run_selection_with_extra.py` (扩展选股)
- `run_stock_selection.py` (运行选股)
- `test_stock_scoring_skill.py` (测试文件)
- `migrate_stock_data.py` (迁移脚本)

## 三、任务拆分

### 任务1：创建新的选股技能
- 创建 `skills/stock_selector.py`
- 实现选股主流程
- 实现行业股票获取
- 实现ST股过滤
- 实现数据库保存

### 任务2：创建新的评价技能
- 创建 `skills/stock_evaluator.py`
- 实现评价主流程
- 实现各维度评分计算
- 实现评分记录保存

### 任务3：测试验证
- 测试选股技能
- 测试评价技能
- 测试选股技能调用评价技能
- 使用东华软件(002065)和茅台(600519)进行真实测试

### 任务4：清理旧文件
- 确认测试通过后删除旧文件
- 更新项目文档

## 四、验收标准

1. 选股技能能正确获取行业股票并保存到stock_basic_info
2. 评价技能能正确对股票进行多维度打分并保存到score_record
3. 选股技能能正确调用评价技能
4. 测试用例覆盖正常场景、边界场景、异常场景
5. 代码符合PEP8规范

---

**计划状态**: 待审批
**创建时间**: 2026-02-21
