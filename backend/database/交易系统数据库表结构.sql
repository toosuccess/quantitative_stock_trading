-- 交易系统数据库表结构设计（优化版）
-- 数据更新时间：2026-02-17
-- 根据新ER图优化：新增复盘记录表，交易计划明细改为交易执行步骤

-- ============================================================
-- 1. 账户信息表
-- ============================================================
CREATE TABLE IF NOT EXISTS `account_info` (
  `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
  `account_id` VARCHAR(50) NOT NULL UNIQUE COMMENT '账户编号',
  `account_name` VARCHAR(100) NOT NULL COMMENT '账户名称',
  `account_type` VARCHAR(20) NOT NULL COMMENT '账户类型（实盘/模拟）',
  `broker` VARCHAR(50) COMMENT '券商',
  `total_assets` DECIMAL(20,2) DEFAULT 0.00 COMMENT '总资产',
  `available_cash` DECIMAL(20,2) DEFAULT 0.00 COMMENT '可用资金',
  `market_value` DECIMAL(20,2) DEFAULT 0.00 COMMENT '市值',
  `profit_loss` DECIMAL(20,2) DEFAULT 0.00 COMMENT '盈亏',
  `profit_loss_rate` DECIMAL(10,4) DEFAULT 0.0000 COMMENT '盈亏率',
  `risk_level` VARCHAR(20) COMMENT '风险等级',
  `status` VARCHAR(20) DEFAULT 'active' COMMENT '状态（active/inactive）',
  `create_time` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `remark` TEXT COMMENT '备注',
  INDEX idx_account_id (`account_id`),
  INDEX idx_account_type (`account_type`),
  INDEX idx_status (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='账户信息表';

-- ============================================================
-- 2. 股票基本信息表
-- ============================================================
CREATE TABLE IF NOT EXISTS `stock_basic_info` (
  `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
  `stock_code` VARCHAR(20) NOT NULL UNIQUE COMMENT '股票代码',
  `stock_name` VARCHAR(50) NOT NULL COMMENT '股票名称',
  `stock_abbr` VARCHAR(20) COMMENT '股票简称',
  `exchange` VARCHAR(10) NOT NULL COMMENT '交易所（SH/SZ）',
  `industry` VARCHAR(100) COMMENT '所属行业',
  `sector` VARCHAR(100) COMMENT '所属板块',
  `list_date` DATE COMMENT '上市日期',
  `total_shares` BIGINT COMMENT '总股本（股）',
  `float_shares` BIGINT COMMENT '流通股本（股）',
  `market_cap` DECIMAL(20,2) COMMENT '总市值（元）',
  `float_market_cap` DECIMAL(20,2) COMMENT '流通市值（元）',
  `pe_ratio` DECIMAL(10,4) COMMENT '市盈率',
  `pb_ratio` DECIMAL(10,4) COMMENT '市净率',
  `ps_ratio` DECIMAL(10,4) COMMENT '市销率',
  `dividend_yield` DECIMAL(10,4) COMMENT '股息率',
  `status` VARCHAR(20) DEFAULT 'normal' COMMENT '状态（normal/suspended/delisted）',
  `create_time` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `remark` TEXT COMMENT '备注',
  INDEX idx_stock_code (`stock_code`),
  INDEX idx_stock_name (`stock_name`),
  INDEX idx_exchange (`exchange`),
  INDEX idx_industry (`industry`),
  INDEX idx_status (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='股票基本信息表';

-- ============================================================
-- 3. 评分记录表（含选股原因：基本面+技术面）
-- ============================================================
CREATE TABLE IF NOT EXISTS `score_record` (
  `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
  `stock_code` VARCHAR(20) NOT NULL COMMENT '股票代码',
  `stock_name` VARCHAR(50) NOT NULL COMMENT '股票名称',
  `score_date` DATE NOT NULL COMMENT '评分日期',
  
  -- 基本面评分
  `fundamental_score` DECIMAL(10,4) DEFAULT 0.0000 COMMENT '基本面评分',
  `fundamental_reason` TEXT COMMENT '基本面选股原因',
  
  -- 技术面评分
  `technical_score` DECIMAL(10,4) DEFAULT 0.0000 COMMENT '技术面评分',
  `technical_reason` TEXT COMMENT '技术面选股原因',
  
  -- 详细评分项
  `ma_score` DECIMAL(10,4) DEFAULT 0.0000 COMMENT '均线评分',
  `macd_score` DECIMAL(10,4) DEFAULT 0.0000 COMMENT 'MACD评分',
  `rsi_score` DECIMAL(10,4) DEFAULT 0.0000 COMMENT 'RSI评分',
  `bollinger_score` DECIMAL(10,4) DEFAULT 0.0000 COMMENT '布林带评分',
  `volume_score` DECIMAL(10,4) DEFAULT 0.0000 COMMENT '成交量评分',
  `obv_score` DECIMAL(10,4) DEFAULT 0.0000 COMMENT 'OBV评分',
  
  -- 综合评分
  `total_score` DECIMAL(10,4) DEFAULT 0.0000 COMMENT '综合评分',
  `rating` VARCHAR(20) COMMENT '评级（强烈推荐/推荐/中性/观望/不推荐）',
  
  -- 技术指标数据
  `ma5` DECIMAL(10,4) COMMENT 'MA5',
  `ma10` DECIMAL(10,4) COMMENT 'MA10',
  `ma20` DECIMAL(10,4) COMMENT 'MA20',
  `ma60` DECIMAL(10,4) COMMENT 'MA60',
  `diff` DECIMAL(10,4) COMMENT 'DIFF',
  `dea` DECIMAL(10,4) COMMENT 'DEA',
  `macd` DECIMAL(10,4) COMMENT 'MACD',
  `rsi` DECIMAL(10,4) COMMENT 'RSI',
  `bb_upper` DECIMAL(10,4) COMMENT '布林带上轨',
  `bb_middle` DECIMAL(10,4) COMMENT '布林带中轨',
  `bb_lower` DECIMAL(10,4) COMMENT '布林带下轨',
  
  -- 价格和成交量
  `close_price` DECIMAL(10,4) COMMENT '收盘价',
  `volume` BIGINT COMMENT '成交量',
  `turnover_rate` DECIMAL(10,4) COMMENT '换手率',
  
  `create_time` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `remark` TEXT COMMENT '备注',
  INDEX idx_stock_code (`stock_code`),
  INDEX idx_score_date (`score_date`),
  INDEX idx_total_score (`total_score`),
  INDEX idx_rating (`rating`),
  UNIQUE KEY uk_stock_date (`stock_code`, `score_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='评分记录表';

-- ============================================================
-- 4. 交易计划表
-- ============================================================
CREATE TABLE IF NOT EXISTS `trade_plan` (
  `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
  `plan_id` VARCHAR(50) NOT NULL UNIQUE COMMENT '计划编号',
  `plan_name` VARCHAR(100) NOT NULL COMMENT '计划名称',
  `account_id` VARCHAR(50) NOT NULL COMMENT '账户编号',
  `stock_code` VARCHAR(20) NOT NULL COMMENT '股票代码',
  `stock_name` VARCHAR(50) NOT NULL COMMENT '股票名称',
  
  -- 评分记录引用（交易依据）
  `score_record_id` INT COMMENT '关联评分记录ID',
  
  -- 止损止盈
  `stop_loss_price` DECIMAL(10,4) COMMENT '止损价格',
  `take_profit_price` DECIMAL(10,4) COMMENT '止盈价格',
  
  -- 计划数量和金额
  `planned_quantity` INT DEFAULT 0 COMMENT '计划数量（股）',
  `planned_amount` DECIMAL(20,2) DEFAULT 0.00 COMMENT '计划金额（元）',
  
  -- 实际盈亏情况
  `actual_quantity` INT DEFAULT 0 COMMENT '实际成交数量（股）',
  `actual_amount` DECIMAL(20,2) DEFAULT 0.00 COMMENT '实际成交金额（元）',
  `avg_cost_price` DECIMAL(10,4) COMMENT '平均成本价',
  `profit_loss` DECIMAL(20,2) DEFAULT 0.00 COMMENT '盈亏金额（元）',
  `profit_loss_rate` DECIMAL(10,4) DEFAULT 0.0000 COMMENT '盈亏率',
  
  -- 时间
  `plan_date` DATE NOT NULL COMMENT '计划日期',
  
  `status` VARCHAR(20) DEFAULT 'pending' COMMENT '状态（pending/executing/completed/cancelled）',
  `create_time` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `remark` TEXT COMMENT '备注',
  INDEX idx_plan_id (`plan_id`),
  INDEX idx_account_id (`account_id`),
  INDEX idx_stock_code (`stock_code`),
  INDEX idx_status (`status`),
  INDEX idx_plan_date (`plan_date`),
  INDEX idx_score_record_id (`score_record_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='交易计划表';

-- ============================================================
-- 5. 交易执行步骤表（关键点位：含买卖点/止损止盈点/建仓/加仓/减仓/清仓，理由）
-- ============================================================
CREATE TABLE IF NOT EXISTS `trade_execution_step` (
  `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
  `step_id` VARCHAR(50) NOT NULL UNIQUE COMMENT '步骤编号',
  `plan_id` VARCHAR(50) NOT NULL COMMENT '计划编号',
  `account_id` VARCHAR(50) NOT NULL COMMENT '账户编号',
  `stock_code` VARCHAR(20) NOT NULL COMMENT '股票代码',
  `stock_name` VARCHAR(50) NOT NULL COMMENT '股票名称',
  
  -- 交易方向
  `trade_direction` VARCHAR(20) NOT NULL COMMENT '交易类型（建仓/加仓/减仓/清仓）',
  `target_price` DECIMAL(10,4) COMMENT '目标价格',
  
  -- 数量
  `planned_quantity` INT DEFAULT 0 COMMENT '计划数量（股）',
  `executed_quantity` INT DEFAULT 0 COMMENT '已执行数量（股）',
  `remaining_quantity` INT DEFAULT 0 COMMENT '剩余数量（股）',
  
  -- 执行信息
  `actual_price` DECIMAL(10,4) COMMENT '实际成交价格',
  `planned_date` DATE NOT NULL COMMENT '计划日期',
  `executed_date` DATE COMMENT '实际执行日期',
  `reason` TEXT COMMENT '执行理由',
  
  `status` VARCHAR(20) DEFAULT 'pending' COMMENT '状态（pending/partially_executed/completed/cancelled）',
  `create_time` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `remark` TEXT COMMENT '备注',
  INDEX idx_step_id (`step_id`),
  INDEX idx_plan_id (`plan_id`),
  INDEX idx_account_id (`account_id`),
  INDEX idx_stock_code (`stock_code`),
  INDEX idx_trade_direction (`trade_direction`),
  INDEX idx_status (`status`),
  INDEX idx_planned_date (`planned_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='交易执行步骤表';

-- ============================================================
-- 6. 交易记录表
-- ============================================================
CREATE TABLE IF NOT EXISTS `trade_record` (
  `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
  `record_id` VARCHAR(50) NOT NULL UNIQUE COMMENT '交易记录编号',
  `account_id` VARCHAR(50) NOT NULL COMMENT '账户编号',
  `stock_code` VARCHAR(20) NOT NULL COMMENT '股票代码',
  `stock_name` VARCHAR(50) NOT NULL COMMENT '股票名称',
  `plan_id` VARCHAR(50) COMMENT '关联计划编号',
  `step_id` VARCHAR(50) COMMENT '关联执行步骤编号',
  
  `trade_type` VARCHAR(20) NOT NULL COMMENT '交易类型（买入/卖出）',
  `trade_direction` VARCHAR(20) COMMENT '交易方向（建仓/加仓/减仓/清仓）',
  
  -- 价格
  `trade_price` DECIMAL(10,4) NOT NULL COMMENT '成交价格',
  `trade_quantity` INT NOT NULL COMMENT '成交数量（股）',
  `trade_amount` DECIMAL(20,2) NOT NULL COMMENT '成交金额（元）',
  
  -- 费用
  `commission` DECIMAL(10,4) DEFAULT 0.0000 COMMENT '佣金',
  `stamp_duty` DECIMAL(10,4) DEFAULT 0.0000 COMMENT '印花税',
  
  `trade_date` DATE NOT NULL COMMENT '交易日期',
  `trade_time` TIME NOT NULL COMMENT '交易时间',
  `order_number` VARCHAR(50) COMMENT '订单号',
  `broker_order_number` VARCHAR(50) COMMENT '券商订单号',
  
  `status` VARCHAR(20) DEFAULT 'completed' COMMENT '状态（pending/partially_completed/completed/cancelled/failed）',
  `create_time` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `remark` TEXT COMMENT '备注',
  INDEX idx_record_id (`record_id`),
  INDEX idx_account_id (`account_id`),
  INDEX idx_stock_code (`stock_code`),
  INDEX idx_plan_id (`plan_id`),
  INDEX idx_step_id (`step_id`),
  INDEX idx_trade_type (`trade_type`),
  INDEX idx_trade_date (`trade_date`),
  INDEX idx_status (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='交易记录表';

-- ============================================================
-- 7. 复盘记录表
-- ============================================================
CREATE TABLE IF NOT EXISTS `review_record` (
  `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
  `review_id` VARCHAR(50) NOT NULL UNIQUE COMMENT '复盘编号',
  `plan_id` VARCHAR(50) NOT NULL COMMENT '关联计划编号',
  `account_id` VARCHAR(50) NOT NULL COMMENT '账户编号',
  `stock_code` VARCHAR(20) NOT NULL COMMENT '股票代码',
  `stock_name` VARCHAR(50) NOT NULL COMMENT '股票名称',
  
  -- 复盘信息
  `review_date` DATE NOT NULL COMMENT '复盘日期',
  `review_type` VARCHAR(20) COMMENT '复盘类型（成功/失败/中性）',
  `review_result` TEXT COMMENT '复盘结论',
  
  -- 执行情况分析
  `execution_summary` TEXT COMMENT '执行情况总结',
  `profit_loss_analysis` TEXT COMMENT '盈亏分析',
  `reason_analysis` TEXT COMMENT '原因分析',
  
  -- 经验教训
  `success_experience` TEXT COMMENT '成功经验',
  `failure_lesson` TEXT COMMENT '失败教训',
  `improvement_measures` TEXT COMMENT '改进措施',
  
  -- 情绪记录
  `emotion_status` VARCHAR(20) COMMENT '情绪状态（贪婪/焦躁/平稳/恐惧）',
  `emotion_impact` TEXT COMMENT '情绪影响',
  
  -- 评分
  `execution_score` DECIMAL(5,2) COMMENT '执行评分（0-100）',
  `strategy_score` DECIMAL(5,2) COMMENT '策略评分（0-100）',
  `overall_score` DECIMAL(5,2) COMMENT '综合评分（0-100）',
  
  `status` VARCHAR(20) DEFAULT 'completed' COMMENT '状态（draft/completed）',
  `create_time` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `remark` TEXT COMMENT '备注',
  INDEX idx_review_id (`review_id`),
  INDEX idx_plan_id (`plan_id`),
  INDEX idx_account_id (`account_id`),
  INDEX idx_stock_code (`stock_code`),
  INDEX idx_review_date (`review_date`),
  INDEX idx_review_type (`review_type`),
  INDEX idx_status (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='复盘记录表';

-- ============================================================
-- 实体关系说明（根据新ER图）
-- ============================================================
-- 1. account_info（账户信息）
--    └─> trade_record（交易记录）- 一对多
--
-- 2. stock_basic_info（股票基本信息）
--    ├─> trade_plan（交易计划）- 一对多
--    └─> score_record（评分记录）- 一对多
--
-- 3. trade_plan（交易计划）
--    ├─> trade_execution_step（交易执行步骤）- 一对多
--    └─> review_record（复盘记录）- 一对多
--
-- 4. trade_execution_step（交易执行步骤）
--    └─> trade_record（交易记录）- 一对多
-- ============================================================
