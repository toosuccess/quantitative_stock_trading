# 个人专属交易系统

一个"去情绪化、可量化、可追溯、可重复、可迭代"的交易系统，通过标准化流程解决炒股核心痛点，最终实现稳定盈利。

## 项目结构

```
quantitative_stock_trading/
├── backend/                    # 后端代码
│   ├── app/
│   │   ├── main.py            # FastAPI入口
│   │   ├── config.py          # 配置文件
│   │   ├── services/          # 业务逻辑
│   │   │   ├── data_fetcher.py    # 数据获取服务
│   │   │   ├── stock_selector.py  # 选股服务
│   │   │   └── trading_manager.py # 交易管理服务
│   │   ├── models/            # 数据模型
│   │   └── api/               # API路由
│   ├── scripts/               # 脚本工具
│   │   ├── init_database.py   # 数据库初始化
│   │   ├── run_stock_selection.py # 选股执行
│   │   └── qmt/               # QMT相关脚本
│   ├── tests/                 # 测试文件
│   ├── database/              # 数据库文件
│   └── requirements.txt
│
├── frontend/                   # 前端代码（Vue 3）
│   └── src/
│
├── skills/                     # 选股技能
│   ├── stock_price_skill.py
│   ├── stock_selection_skill.py
│   └── 选股技能.md
│
├── 需求文档/                    # 需求文档
│   ├── 交易系统.md
│   ├── 交易计划说明.md
│   ├── 做T规则.md
│   └── 选股说明.md
│
├── docs/                       # 其他文档
│   ├── 交易系统数据库设计说明.md
│   └── QMT配置说明.md
│
├── reports/                    # 输出报告
│
└── .trae/                      # Trae配置
```

## 核心功能

### 1. 选股模块
- 根据技术指标和基本面数据筛选股票
- 支持MA、MACD、RSI、布林带、OBV等技术指标
- 自动评分和评级

### 2. 交易计划模块
- 标准化入场逻辑
- 仓位管理
- 止损止盈策略

### 3. 交易执行模块
- 定时执行交易计划
- 手工交易执行入口

### 4. 复盘模块
- 交易胜率计算
- 盈亏比分析
- 最大回撤计算

## 快速开始

### 1. 安装依赖

```bash
cd backend
pip install -r requirements.txt
```

### 2. 初始化数据库

```bash
python scripts/init_database.py
```

### 3. 运行选股

```bash
python scripts/run_stock_selection.py
```

### 4. 启动后端服务

```bash
cd backend/app
python main.py
```

## 技术栈

- **后端**: Python + FastAPI
- **数据源**: AkShare
- **数据库**: SQLite
- **前端**: Vue 3 + ECharts（待实现）

## 许可证

MIT License
