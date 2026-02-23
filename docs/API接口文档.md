# API接口文档

## 概述

后端API基于 FastAPI 构建，提供股票池管理、评分、交易计划等功能。

## 基础信息

- **基础URL**: `http://localhost:8000/api/v1`
- **数据格式**: JSON
- **字符编码**: UTF-8

## 一、股票池接口

### 1.1 获取股票池列表

**请求**
```
GET /stocks/pool
```

**响应**
```json
{
  "stocks": [
    {
      "stock_code": "sz000534",
      "stock_name": "万泽股份",
      "exchange": "SZ",
      "industry": "生物医药",
      "pe_ratio": 74.08,
      "pb_ratio": 10.69
    }
  ],
  "count": 189
}
```

### 1.2 获取股票池评分汇总

**请求**
```
GET /stocks/pool/scores
```

**响应**
```json
{
  "stocks": [
    {
      "stock_code": "sz000534",
      "stock_name": "万泽股份",
      "latest_score": 84.0,
      "composite_score": 84.0,
      "latest_rating": "推荐",
      "latest_date": "2026-02-23",
      "close_price": 32.94,
      "technical_score": 100.0,
      "fundamental_score": 40.0,
      "news_score": 0.0,
      "policy_score": 8.0,
      "deduction_score": 0.0,
      "score_history": [
        {"date": "2026-02-21", "score": 73},
        {"date": "2026-02-23", "score": 84}
      ],
      "price_history": [
        {"date": "2026-02-21", "price": 32.94},
        {"date": "2026-02-23", "price": 32.94}
      ]
    }
  ],
  "count": 189
}
```

**字段说明**

| 字段 | 类型 | 说明 |
|------|------|------|
| stock_code | string | 股票代码 |
| stock_name | string | 股票名称 |
| latest_score | float | 最新评分 |
| composite_score | float | 综合评分 |
| latest_rating | string | 评级 |
| latest_date | string | 最新评分日期 |
| close_price | float | 收盘价 |
| technical_score | float | 技术面得分 |
| fundamental_score | float | 基本面得分 |
| news_score | float | 消息面得分 |
| policy_score | float | 政策面得分 |
| deduction_score | float | 减项扣分 |
| score_history | array | 最近10次评分历史 |
| price_history | array | 最近10次股价历史 |

## 二、评分接口

### 2.1 评价单个股票

**请求**
```
POST /stocks/evaluate
Content-Type: application/json

{
  "stock_code": "sz000534"
}
```

**响应**
```json
{
  "stock_code": "sz000534",
  "success": true,
  "composite_score": 84,
  "rating": "推荐",
  "result": {
    "technical_score": 100,
    "fundamental_score": 40,
    "news_score": 0,
    "policy_score": 8,
    "deduction_score": 0,
    "composite_score": 84,
    "rating": "推荐"
  }
}
```

### 2.2 批量评价股票

**请求**
```
POST /stocks/batch-evaluate
Content-Type: application/json

{
  "stock_codes": ["sz000534", "sz300835"]
}
```

**响应**
```json
{
  "total": 2,
  "results": [
    {
      "stock_code": "sz000534",
      "success": true,
      "composite_score": 84
    },
    {
      "stock_code": "sz300835",
      "success": true,
      "composite_score": 84
    }
  ]
}
```

### 2.3 获取评分详情

**请求**
```
GET /stocks/{stock_code}/score-detail
```

**路径参数**

| 参数 | 类型 | 说明 |
|------|------|------|
| stock_code | string | 股票代码 |

**响应**
```json
{
  "stock_code": "sz000534",
  "stock_name": "万泽股份",
  "composite_score": 84,
  "rating": "推荐",
  "technical_score": 100,
  "fundamental_score": 40,
  "news_score": 0,
  "policy_score": 8,
  "deduction_score": 0,
  "technical_detail": {
    "ma": {"score": 25, "detail": "股价站稳20日均线: 是"},
    "volume": {"score": 25, "detail": "成交量放大: 是"},
    "trend": {"score": 20, "detail": "MACD金叉: 是"},
    "fund": {"score": 15, "detail": "OBV>MAOBV: 是"},
    "bollinger": {"score": 15, "detail": "布林带中轨上方: 是"}
  },
  "fundamental_detail": {
    "pe": {"score": 0, "value": 74.08, "detail": "PE=74.08"},
    "pb": {"score": 0, "value": 10.69, "detail": "PB=10.69"},
    "roe": {"score": 0, "value": 0, "detail": "ROE=0.00%"},
    "net_profit_growth": {"score": 20, "value": 40.12, "detail": "净利润增长40.12%,增长强劲"},
    "revenue_growth": {"score": 15, "value": 50.39, "detail": "营收增长50.39%,扩张快速"},
    "debt_ratio": {"score": 5, "value": 60.01, "detail": "负债率60.01%,财务适中"}
  },
  "news_detail": {
    "events": [
      {
        "date": "2026-02-12",
        "type": "中性",
        "title": "34.33亿元资金今日流出医药生物股",
        "url": "http://finance.eastmoney.com/...",
        "source": "证券时报网",
        "summary": "医药生物行业资金流入榜...",
        "score_impact": 0
      }
    ]
  },
  "policy_detail": {
    "policies": [
      {
        "date": "2026-02-23",
        "level": "国家政策",
        "title": "生物医药产业政策支持",
        "content": "生物医药产业政策支持",
        "source": "十五五规划",
        "score_impact": 8
      }
    ]
  },
  "deduction_detail": {
    "items": []
  },
  "history": [
    {
      "score_date": "2026-02-23",
      "composite_score": 84,
      "rating": "推荐",
      "technical_score": 100,
      "fundamental_score": 40,
      "close_price": 32.94
    }
  ]
}
```

## 三、账户接口

### 3.1 获取账户列表

**请求**
```
GET /accounts
```

**响应**
```json
{
  "accounts": [
    {
      "account_id": "acc001",
      "account_name": "主账户",
      "account_type": "股票账户",
      "broker": "华泰证券",
      "total_assets": 1000000.00,
      "available_cash": 500000.00,
      "market_value": 500000.00,
      "profit_loss": 50000.00,
      "profit_loss_rate": 5.26
    }
  ]
}
```

### 3.2 获取账户详情

**请求**
```
GET /accounts/{account_id}
```

**响应**
```json
{
  "account_id": "acc001",
  "account_name": "主账户",
  "account_type": "股票账户",
  "broker": "华泰证券",
  "total_assets": 1000000.00,
  "available_cash": 500000.00,
  "market_value": 500000.00,
  "profit_loss": 50000.00,
  "profit_loss_rate": 5.26,
  "positions": [
    {
      "stock_code": "sz000534",
      "stock_name": "万泽股份",
      "quantity": 1000,
      "available": 1000,
      "cost_price": 30.00,
      "current_price": 32.94,
      "market_value": 32940.00,
      "profit_loss": 2940.00,
      "profit_loss_rate": 9.8
    }
  ]
}
```

## 四、交易计划接口

### 4.1 获取交易计划列表

**请求**
```
GET /trade-plans
```

**查询参数**

| 参数 | 类型 | 说明 |
|------|------|------|
| account_id | string | 账户ID（可选） |
| status | string | 状态（可选） |

**响应**
```json
{
  "plans": [
    {
      "plan_id": "plan001",
      "plan_name": "万泽股份买入计划",
      "account_id": "acc001",
      "stock_code": "sz000534",
      "stock_name": "万泽股份",
      "stop_loss_price": 29.65,
      "take_profit_price": 36.23,
      "planned_quantity": 1000,
      "planned_amount": 32940.00,
      "status": "待执行"
    }
  ]
}
```

### 4.2 创建交易计划

**请求**
```
POST /trade-plans
Content-Type: application/json

{
  "account_id": "acc001",
  "stock_code": "sz000534",
  "stock_name": "万泽股份",
  "stop_loss_price": 29.65,
  "take_profit_price": 36.23,
  "planned_quantity": 1000,
  "plan_date": "2026-02-23"
}
```

**响应**
```json
{
  "plan_id": "plan001",
  "success": true,
  "message": "交易计划创建成功"
}
```

## 五、交易记录接口

### 5.1 获取交易记录

**请求**
```
GET /trade-records
```

**查询参数**

| 参数 | 类型 | 说明 |
|------|------|------|
| account_id | string | 账户ID（可选） |
| stock_code | string | 股票代码（可选） |
| start_date | string | 开始日期（可选） |
| end_date | string | 结束日期（可选） |

**响应**
```json
{
  "records": [
    {
      "record_id": "rec001",
      "account_id": "acc001",
      "stock_code": "sz000534",
      "stock_name": "万泽股份",
      "trade_type": "买入",
      "trade_price": 32.94,
      "trade_quantity": 1000,
      "trade_amount": 32940.00,
      "trade_date": "2026-02-23",
      "status": "已成交"
    }
  ]
}
```

## 六、错误响应

### 错误格式
```json
{
  "detail": "错误信息描述"
}
```

### 常见错误码

| 状态码 | 说明 |
|--------|------|
| 400 | 请求参数错误 |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |

## 七、请求示例

### cURL示例

```bash
# 获取股票池评分
curl -X GET "http://localhost:8000/api/v1/stocks/pool/scores"

# 评价单个股票
curl -X POST "http://localhost:8000/api/v1/stocks/evaluate" \
  -H "Content-Type: application/json" \
  -d '{"stock_code": "sz000534"}'

# 获取评分详情
curl -X GET "http://localhost:8000/api/v1/stocks/sz000534/score-detail"
```

### JavaScript示例

```javascript
// 使用axios
import axios from 'axios'

const api = axios.create({
  baseURL: '/api/v1',
  timeout: 120000
})

// 获取股票池评分
const response = await api.get('/stocks/pool/scores')

// 评价股票
const result = await api.post('/stocks/evaluate', {
  stock_code: 'sz000534'
})
```
