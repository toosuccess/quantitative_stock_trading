# 股票复审技能开发计划（修订版）

## 一、需求概述

### 1.1 功能目标
开发一个**股票复审技能**（stock_review_skills.py），对股票池中评价得分为**强烈推荐、推荐、中性**的股票进行深度技术面复审。

### 1.2 使用场景与运行方式 ⭐重要变更⭐
- **运行方式**：在 **Trae IDE** 中通过 **AI能力** 调用技能完成复审
- **前端职责**：**只做查询展示**已存储的复审结果，不发起复审请求
- **数据流**：`Trae AI调用技能 → 计算复审 → 存储数据库 → 前端查询展示`

### 1.3 复审核心体系（基于用户提供的提示词）
以 **MACD** 为核心主指标，搭配：
- 20日均线（趋势生命线）
- 布林线（BOLL）
- DMI指标（牛熊判断）
- K线风控规则（一票否决）

### 1.4 输出要求
- ✅ 复审得分（0-100分）
- ✅ 复审意见（详细技术分析结论 + 板块表现分析）
- ✅ 复审时间
- ✅ 存储位置：**stock_basic_info** 表（新增字段）

### 1.5 新增需求：板块表现分析 ⭐新增⭐
复审时需包含股票所属**板块/行业**的最近市场表现：
- 板块近5日/10日/20日涨跌幅
- 板块在所有行业中的排名
- 板块资金流向情况
- 板块技术形态（是否处于上升趋势）

---

## 二、技术架构设计

### 2.1 文件结构
```
skills/
├── stock_selector_skills.py      # 选股技能（已有）
├── stock_evaluator_skills.py     # 评价技能（已有）
└── stock_review_skills.py        # 复审技能（新建）⭐
```

### 2.2 数据库变更
在 `stock_basic_info` 表新增以下字段：

```sql
ALTER TABLE stock_basic_info ADD COLUMN review_score DECIMAL(5,2) DEFAULT NULL COMMENT '复审得分';
ALTER TABLE stock_basic_info ADD COLUMN review_opinion TEXT COMMENT '复审意见';
ALTER TABLE stock_basic_info ADD COLUMN review_time DATETIME COMMENT '复审时间';
ALTER TABLE stock_basic_info ADD COLUMN review_detail JSON COMMENT '复审详细信息';
```

### 2.3 类设计（优化版）

```python
class StockReviewSkills:
    """复审技能类 - 供Trae AI调用"""
    
    def __init__(self):
        # 初始化数据库连接
        
    # ==================== 数据获取层 ====================
    def get_review_candidates(self):
        """获取待复审股票列表（评分≥50分的股票）"""
        
    def get_stock_price_data(self, stock_code):
        """获取股票K线数据（复用evaluator的接口）"""
        
    def get_sector_performance(self, sector_name):
        """获取板块最近表现数据 ⭐新增⭐"""
        # - 板块涨跌幅排名
        # - 资金流向
        # - 技术趋势
        
    # ==================== 指标计算层 ====================
    def calculate_macd_review_score(self, price_data):
        """MACD核心评分（40分）"""
        
    def calculate_ma20_review_score(self, price_data):
        """20日均线辅助评分（25分）"""
        
    def calculate_kline_risk_check(self, kline_data):
        """K线风控硬性规则（一票否决）"""
        
    def calculate_bollinger_review_score(self, price_data):
        """布林线共振确认（15分）"""
        
    def calculate_dmi_review_score(self, price_data):
        """DMI牛熊指标（20分）"""
        
    def calculate_sector_bonus_score(self, sector_data):
        """板块表现加分项（额外±10分）⭐新增⭐"""
        
    # ==================== 综合评审层 ====================
    def generate_review_opinion(self, scores, indicators, sector_info):
        """生成完整复审意见（含板块分析）"""
        
    def review_single_stock(self, stock_code):
        """复审单只股票（供AI调用）"""
        
    def batch_review_all(self):
        """批量复审所有符合条件的股票（供AI调用）"""
        
    # ==================== 数据持久化层 ====================
    def save_review_result(self, stock_code, result):
        """保存复审结果到stock_basic_info表"""
```

---

## 三、评分细则设计（总分100分 + 板块加分±10分）

### 3.1 MACD核心评分（40分）

| 指标 | 条件 | 得分 |
|------|------|------|
| **零轴判定**（10分） | 快慢线长期在零轴上方 | +10 |
| | 零轴下方 | +3 |
| | 首次突破零轴（观望） | +5 |
| **金叉死叉**（10分） | 零轴上方金叉 | +10 |
| | 零轴下方金叉 | +5 |
| | 死叉出现 | -10 |
| **红绿柱动能**（10分） | 红柱持续放大 | +10 |
| | 红柱缩脚未转绿 | +5 |
| | 绿柱缩脚 | +3 |
| | 绿柱放大 | -5 |
| **背离判断**（10分） | 底背离（买入信号） | +10 |
| | 顶背离（卖出信号） | -10 |
| | 无背离 | +5 |

### 3.2 20日均线辅助（25分）

| 条件 | 得分 |
|------|------|
| 股价在MA20上方 + MA20>MA60>MA180>MA250（多头排列） | +15 |
| MA20自下而上穿越MA60（趋势转强） | +5 |
| 股价回踩站稳MA20（加仓点） | +5 |
| 乖离率>8%（禁止追高） | **-10** |
| MA20被多条均线压制 | **-10** |

### 3.3 K线风控（一票否决，基础分20分）

| 条件 | 得分 |
|------|------|
| 无风险形态 | +20 |
| 出现长上影线（上影线>实体2倍） | **-20**（直接放弃） |
| 出现放量巨阴线（跌幅>5%且放量>2倍） | **-20**（直接放弃） |

### 3.4 布林线共振（15分）

| 条件 | 得分 |
|------|------|
| 布林通道在零轴上方 + 股价紧贴上轨 | +15 |
| 股价在中轨上方运行 | +10 |
| 股价触及下轨 | -5 |
| 布林收口（变盘信号） | 0 |

### 3.5 DMI指标（20分）

| 条件 | 得分 |
|------|------|
| DI1（多头线）持续在DI2（空头线上方） | +20 |
| DI1上穿DI2（金叉） | +15 |
| DI1下穿DI2（死叉） | -15 |
| ADX>30（趋势明确） | +5额外加分 |

### 3.6 板块表现加分（±10分）⭐新增⭐

| 条件 | 加分 |
|------|------|
| 板块近20日涨幅排名前10% | +10 |
| 板块近20日涨幅排名前30% | +5 |
| 板块处于上升趋势且资金净流入 | +8 |
| 板块处于下降趋势或资金大幅流出 | **-8** |
| 板块近期无特殊表现 | 0 |

---

## 四、复审评级标准

| 总分区间 | 评级 | 操作建议 |
|----------|------|----------|
| ≥85 | **强烈推荐** | 多指标共振+板块强势，可重仓持有 |
| 70-84 | **推荐** | 趋势向好，可适量参与 |
| 55-69 | **中性** | 观望为主，轻仓试探 |
| 40-54 | **谨慎** | 风险较高，不建议操作 |
| <40 | **回避** | 多指标走弱，坚决不碰 |

---

## 五、复审意见模板（增强版，含板块分析）

```python
REVIEW_OPINION_TEMPLATE = """
【{stock_name}({stock_code}) 技术面复审报告】

📊 复审评级：{rating}（{score}分）
📅 复审时间：{review_time}
🏢 所属板块：{sector_name}

═══ 一、MACD核心分析（{macd_score}/40分）═══
   • 零轴位置：{zero_axis_status} {zero_axis_detail}
   • 金叉/死叉：{cross_status} {cross_detail}
   • 动能状态：{momentum_status} {momentum_detail}
   • 背离情况：{divergence_status} {divergence_detail}

═══ 二、20日均线分析（{ma20_score}/25分）═══
   • 趋势状态：{trend_status}
   • 排列情况：{alignment}
   • 乖离率：{deviation}% {deviation_warning}

═══ 三、K线风控检查（{kline_score}/20分）═══
   • 上影线风险：{upper_shadow_risk} {shadow_detail}
   • 巨阴线风险：{big_bearish_risk} {bearish_detail}

═══ 四、布林线分析（{bollinger_score}/15分）═══
   • 通道位置：{channel_position}
   • 运行状态：{running_state}

═══ 五、DMI指标分析（{dmi_score}/20分）═══
   • 多空对比：{di_comparison}
   • 趋势强度：ADX={adx_value} {adx_status}

═══ 六、板块表现分析（{sector_score}/±10分）⭐新增⭐═══
   📈 板块近5日涨跌：{sector_5d_change}%
   📊 板块近20日涨跌：{sector_20d_change}%
   🏆 行业排名：{sector_rank}/{total_sectors}
   💰 资金流向：{fund_flow}（近5日净流入{fund_net_inflow}亿）
   📐 技术形态：{sector_trend}
   🎯 板块结论：{sector_conclusion}

═══ 七、综合交易建议 ═══
   🎯 操作建议：{suggestion}
   ⚠️ 风险提示：{risk_warning}
   💡 关键价位：支撑{support_price} / 压力{resistance_price}
   🔮 后市展望：{outlook}
"""
```

---

## 六、实施步骤（修订版）

### Step 1: 数据库表结构变更
- [ ] 修改 `stock_basic_info` 表，添加4个复审字段
- [ ] 编写数据库迁移脚本

### Step 2: 创建复审技能主文件
- [ ] 创建 `skills/stock_review_skills.py`
- [ ] 实现 `StockReviewSkills` 类框架
- [ ] 实现数据库连接管理（复用MYSQL_CONFIG）

### Step 3: 实现MACD核心评分模块
- [ ] 实现零轴判定逻辑
- [ ] 实现金叉/死叉识别
- [ ] 实现红绿柱动能分析
- [ ] 实现顶底背离检测算法

### Step 4: 实现辅助指标模块
- [ ] 实现20日均线趋势分析
- [ ] 实现K线风控规则（长上影、巨阴线检测）
- [ ] 实现布林线位置判断
- [ ] 实现DMI指标计算（DI+, DI-, ADX）

### Step 5: 实现板块表现分析模块 ⭐新增⭐
- [ ] 接入akshare板块数据接口
- [ ] 实现板块涨跌幅计算
- [ ] 实现板块排名算法
- [ ] 实现资金流向获取
- [ ] 实现板块技术趋势判断
- [ ] 实现板块加分逻辑

### Step 6: 实现综合评审与输出
- [ ] 实现加权评分算法（含板块加分）
- [ ] 实现评级映射
- [ ] 实现增强版复审意见生成器（含板块分析段落）
- [ ] 实现结果持久化到stock_basic_info表

### Step 7: 前端查询接口（只读）
- [ ] 在 `routes.py` 中添加**查询**端点（非触发端点）
- [ ] `GET /api/stocks/{code}/review-info` - 查询单股复审信息
- [ ] `GET /api/stocks/review-list` - 查询所有已完成复审的股票列表
- [ ] 确保返回字段包含：review_score, review_opinion, review_time, review_detail

### Step 8: 测试验证
- [ ] 单元测试：各指标计算准确性
- [ ] 集成测试：完整复审流程（含板块分析）
- [ ] 使用真实股票测试：
  - 600519 茅台（龙头股）
  - 002065 东华软件
- [ ] Playwright端到端测试：验证前端展示效果

---

## 七、关键技术实现细节

### 7.1 MACD背离检测算法
```python
def detect_divergence(prices, macd_values, window=20):
    """
    检测顶背离和底背离
    顶背离：价格新高 + MACD未新高 → 卖出信号
    底背离：价格新低 + MACD未新低 → 买入信号
    
    Returns:
        dict: {'type': 'top'|'bottom'|'none', 'strength': 0-10}
    """
```

### 7.2 K线形态识别
```python
def detect_upper_shadow(open_price, close_price, high_price):
    """检测长上影线（上影线长度 > 实体长度的2倍）"""

def detect_big_bearish_candle(close_price, prev_close, volume, avg_volume):
    """检测放量巨阴线（跌幅>5% 且 成交量>2倍均量）"""
```

### 7.3 DMI指标计算
```python
def calculate_dmi(high_prices, low_prices, close_prices, period=14):
    """
    计算DMI指标
    Returns:
        dict: {
            'di_plus': DI+,      # 多头线
            'di_minus': DI-,     # 空头线
            'adx': ADX,          # 平均趋向指数
            'dx': DX             # 趋向值
        }
    """
```

### 7.4 板块表现数据获取 ⭐新增⭐
```python
def get_sector_performance(self, sector_name):
    """
    获取板块最近表现数据（使用akshare）
    
    Data Sources:
    1. ak.stock_board_industry_name_em() - 行业板块行情
    2. ak.stock_board_concept_name_em() - 概念板块行情  
    3. ak.stock_fund_flow_stock() - 个股资金流向
    4. ak.stock_board_fund_flow_rank() - 板块资金流向排名
    
    Returns:
        dict: {
            'sector_name': str,
            'change_5d': float,       # 5日涨跌幅
            'change_20d': float,      # 20日涨跌幅
            'rank': int,              # 行业排名
            'total_sectors': int,     # 行业总数
            'fund_net_inflow': float, # 资金净流入（亿）
            'trend': 'up'|'down'|'sideways',  # 技术趋势
            'score_impact': float     # 对复审得分的影响（-10到+10）
        }
    """
```

---

## 八、预期产出物

1. **代码文件**
   - `skills/stock_review_skills.py`（核心技能文件，约800-1000行）
   - `backend/migrations/add_review_fields.sql`（数据库迁移脚本）

2. **API接口文档（仅查询接口）**
   - `GET /api/stocks/{code}/review-info` - 查询复审详情
   - `GET /api/stocks/review-list` - 查询复审列表

3. **使用示例（Trae AI调用）**
```python
# 示例1：复审单只股票
from skills.stock_review_skills import StockReviewSkills

reviewer = StockReviewSkills()
reviewer.connect()
result = reviewer.review_single_stock("600519")  # 复审茅台
print(result['review_opinion'])  # 打印复审报告
reviewer.disconnect()

# 示例2：批量复审所有合格股票
results = reviewer.batch_review_all()
for r in results:
    print(f"{r['stock_name']}: {r['rating']}({r['score']}分)")
```

4. **测试报告**
   - 单元测试覆盖率≥80%
   - 真实股票测试用例（茅台、东华软件）
   - Playwright E2E测试截图

---

## 九、风险评估与应对

| 风险 | 影响 | 应对措施 |
|------|------|----------|
| API限流导致数据获取失败 | 无法完成复审 | 多级降级策略（akshare→东方财富→缓存） |
| 板块数据接口不稳定 | 缺少板块分析 | 设置容错机制，板块数据缺失时跳过该维度并提示 |
| 计算耗时过长 | AI等待体验差 | 支持异步执行模式，提供进度回调 |
| DMI/背离算法复杂度高 | 性能问题 | numpy向量化运算优化 |
| K线数据不足（新股<60天） | 指标无法计算 | 最小数据量门槛，不足则标记"数据不足"并给出基础评分 |

---

## 十、验收标准

✅ **运行方式正确**：可在Trae中通过AI直接调用技能完成复审  
✅ **数据存储正确**：复审结果成功写入stock_basic_info表的4个新字段  
✅ **前端展示正常**：能够查询并展示复审得分、意见、时间、详情  
✅ **MACD四大维度**（零轴、金叉死叉、动能、背离）评分准确  
✅ **K线风控规则**能够有效识别高风险形态（长上影、巨阴线）  
✅ **板块分析完整**：包含涨跌幅、排名、资金流向、技术趋势、加分逻辑  
✅ **复审报告详实**：七大章节内容完整、数据准确、可读性强  
✅ **真实股票测试通过**：600519茅台、002065东华软件复审结果合理  
✅ **端到端测试通过**：Playwright自动化验证前端展示效果  
✅ **代码规范符合PEP8**：注释清晰、模块化良好、异常处理完善
