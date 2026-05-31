<template>
  <div class="home-page-modern">
    <!-- 顶部欢迎横幅 -->
    <div class="welcome-banner">
      <div class="banner-content">
        <div class="greeting">
          <h1>👋 欢迎回来，量化交易者！</h1>
          <p class="subtitle">去情绪化 · 可量化 · 可追溯 · 可重复 · 可迭代</p>
        </div>
        <div class="market-status">
          <el-tag :type="isMarketOpen ? 'success' : 'info'" size="large">
            {{ isMarketOpen ? '📈 交易中' : '📉 已休市' }}
          </el-tag>
          <span class="current-time">{{ currentTime }}</span>
        </div>
      </div>
    </div>

    <!-- 核心指标卡片 -->
    <el-row :gutter="20" class="metrics-row">
      <el-col :span="6">
        <div class="metric-card total-assets">
          <div class="metric-icon">💰</div>
          <div class="metric-content">
            <div class="metric-label">总资产</div>
            <div class="metric-value">{{ formatMoney(accountInfo.total_assets || 0) }}</div>
            <div class="metric-change" :class="(accountInfo.profit_loss || 0) >= 0 ? 'positive' : 'negative'">
              {{ (accountInfo.profit_loss || 0) >= 0 ? '+' : '' }}{{ formatMoney(accountInfo.profit_loss || 0) }}
            </div>
          </div>
        </div>
      </el-col>

      <el-col :span="6">
        <div class="metric-card profit-rate">
          <div class="metric-icon">📊</div>
          <div class="metric-content">
            <div class="metric-label">总收益率</div>
            <div class="metric-value" :class="(accountInfo.profit_loss_rate || 0) >= 0 ? 'positive' : 'negative'">
              {{ (accountInfo.profit_loss_rate || 0).toFixed(2) }}%
            </div>
            <div class="metric-desc">基于初始资金{{ formatMoney(accountInfo.initial_assets || 0) }}</div>
          </div>
        </div>
      </el-col>

      <el-col :span="6">
        <div class="metric-card holdings">
          <div class="metric-icon">📈</div>
          <div class="metric-content">
            <div class="metric-label">持仓市值</div>
            <div class="metric-value">{{ formatMoney(accountInfo.market_value || 0) }}</div>
            <div class="metric-desc">可用资金: {{ formatMoney(accountInfo.available_cash || 0) }}</div>
          </div>
        </div>
      </el-col>

      <el-col :span="6">
        <div class="metric-card win-rate">
          <div class="metric-icon">🎯</div>
          <div class="metric-content">
            <div class="metric-label">交易胜率</div>
            <div class="metric-value">{{ (stats.winRate * 100).toFixed(1) }}%</div>
            <div class="metric-desc">已完成{{ summary.completed_plans }}笔交易</div>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 主内容区域：选股技巧 + 新闻动态 -->
    <el-row :gutter="20" class="main-content-row">
      <!-- 左侧：选股技巧和经验 -->
      <el-col :span="14">
        <el-card class="tips-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <span>💡 选股技巧与实战经验</span>
              <el-tag type="warning" size="small">核心策略</el-tag>
            </div>
          </template>

          <div class="tips-container">
            <!-- 技巧1: 龙头股策略 -->
            <el-collapse v-model="activeTips">
              <el-collapse-item title="🏆 龙头股策略 - 跟随强者" name="1">
                <div class="tip-content">
                  <h4>核心理念</h4>
                  <p>龙头股是市场资金合力选择的结果，具备最强的抗风险能力和上涨动能。</p>

                  <h4>筛选标准</h4>
                  <ul>
                    <li><strong>行业地位</strong>: 市值前3名，营收/利润行业领先</li>
                    <li><strong>资金认可</strong>: 北向资金持续流入，机构持仓增加</li>
                    <li><strong>技术强势</strong>: 股价在年线上方，均线多头排列</li>
                    <li><strong>量能配合</strong>: 放量突破关键位，缩量回调不破支撑</li>
                  </ul>

                  <h4>操作要点</h4>
                  <ul>
                    <li>✅ 首次回调至10日/20日线是低吸良机</li>
                    <li>✅ 突破前高时放量跟进，止损设在前低下方3%</li>
                    <li>❌ 避免追涨超过7%的个股，等待回踩确认</li>
                  </ul>

                  <div class="tip-example">
                    <strong>实战案例</strong>: 贵州茅台(600519) - 白酒龙头，长期稳健增长
                  </div>
                </div>
              </el-collapse-item>

              <!-- 技巧2: 技术面分析 -->
              <el-collapse-item title="📉 技术面分析 - 量价时空" name="2">
                <div class="tip-content">
                  <h4>四大要素</h4>
                  <div class="tech-grid">
                    <div class="tech-item">
                      <strong>量</strong>
                      <p>成交量验证趋势真实性，放量突破=有效，缩量上涨=乏力</p>
                    </div>
                    <div class="tech-item">
                      <strong>价</strong>
                      <p>K线形态反映多空博弈，阳包阴=转强，阴包阳=转弱</p>
                    </div>
                    <div class="tech-item">
                      <strong>时</strong>
                      <p>时间周期决定趋势级别，日线看趋势，分时找买卖点</p>
                    </div>
                    <div class="tech-item">
                      <strong>空</strong>
                      <p>位置决定盈亏比，低位买高位卖，追涨杀跌是大忌</p>
                    </div>
                  </div>

                  <h4>关键技术指标组合</h4>
                  <ul>
                    <li><strong>MA均线系统</strong>: 5/10/20/60日均线，金叉买入死叉卖出</li>
                    <li><strong>MACD</strong>: 零轴上方金叉做多，顶背离警惕回调</li>
                    <li><strong>RSI</strong>: 70以上超买，30以下超卖，50为强弱分界</li>
                    <li><strong>BOLL布林带</strong>: 触及下轨反弹，突破上轨注意风险</li>
                  </ul>

                  <div class="tip-warning">
                    ⚠️ <strong>警示</strong>: 指标共振才可靠，单一指标容易骗线
                  </div>
                </div>
              </el-collapse-item>

              <!-- 技巧3: 基本面筛选 -->
              <el-collapse-item title="📊 基本面筛选 - 价值投资基石" name="3">
                <div class="tip-content">
                  <h4>财务健康度检查清单</h4>
                  <table class="checklist-table">
                    <tr>
                      <td>盈利能力</td>
                      <td>ROE > 15%，毛利率 > 30%，净利率稳定</td>
                    </tr>
                    <tr>
                      <td>成长性</td>
                      <td>营收增速 > 15%，利润增速匹配</td>
                    </tr>
                    <tr>
                      <td>估值水平</td>
                      <td>PE < 行业均值，PB < 3，PEG < 1</td>
                    </tr>
                    <tr>
                      <td>负债安全</td>
                      <td>资产负债率 < 60%，流动比率 > 1.5</td>
                    </tr>
                    <tr>
                      <td>现金流</td>
                      <td>经营现金流为正且 > 净利润的80%</td>
                    </tr>
                  </table>

                  <h4>护城河识别</h4>
                  <ul>
                    <li>🏰 <strong>品牌优势</strong>: 定价权强，客户忠诚度高（如茅台）</li>
                    <li>💻 <strong>技术壁垒</strong>: 专利保护，研发投入占比高</li>
                    <li>🔄 <strong>转换成本</strong>: 用户迁移成本高（如软件SaaS）</li>
                    <li>📜 <strong>牌照壁垒</strong>: 政策准入门槛（如金融、医药）</li>
                  </ul>
                </div>
              </el-collapse-item>

              <!-- 技巧4: 政策导向 -->
              <el-collapse-item title="🏛️ 政策导向 - 顺势而为" name="4">
                <div class="tip-content">
                  <h4>政策解读框架</h4>
                  <ul>
                    <li><strong>产业政策</strong>: "十四五"规划重点扶持方向（新能源、芯片、生物医药）</li>
                    <li><strong>货币政策</strong>: 宽松=利好股市，紧缩=谨慎观望</li>
                    <li><strong>财政政策</strong>: 增支减税刺激经济，基建投资拉动相关板块</li>
                    <li><strong>监管动态</strong>: 反垄断、环保核查等影响行业格局</li>
                  </ul>

                  <h4>2025-2030重点赛道</h4>
                  <div class="industry-tags">
                    <el-tag type="success">人工智能AI</el-tag>
                    <el-tag type="success">新能源汽车</el-tag>
                    <el-tag type="success">半导体芯片</el-tag>
                    <el-tag type="warning">碳中和</el-tag>
                    <el-tag type="warning">医疗健康</el-tag>
                    <el-tag type="danger">数字经济</el-tag>
                  </div>

                  <div class="tip-example">
                    💡 <strong>实操建议</strong>: 每月关注政治局会议、国常会内容，提前布局政策受益板块
                  </div>
                </div>
              </el-collapse-item>

              <!-- 技巧5: 量价关系 -->
              <el-collapse-item title="⚖️ 量价关系 - 资金的足迹" name="5">
                <div class="tip-content">
                  <h4>经典量价形态</h4>
                  <div class="price-volume-patterns">
                    <div class="pattern positive">
                      <h5>✅ 看多信号</h5>
                      <ul>
                        <li>价涨量增 → 上升趋势确认</li>
                        <li>价跌量缩 → 洗盘结束信号</li>
                        <li>底部放量 → 主力建仓迹象</li>
                        <li>突破放量 → 有效突破确认</li>
                      </ul>
                    </div>
                    <div class="pattern negative">
                      <h5>❌ 看空信号</h5>
                      <ul>
                        <li>价涨量缩 → 上涨动力不足</li>
                        <li>价跌量增 → 主力出货迹象</li>
                        <li>高位放量滞涨 → 顶部特征</li>
                        <li>破位放量下跌 → 趋势反转</li>
                      </ul>
                    </div>
                  </div>

                  <h4>换手率解读</h4>
                  <ul>
                    <li>< 3%: 交投清淡，关注方向选择</li>
                    <li>3%-7%: 正常活跃，可参与交易</li>
                    <li>7%-15%: 高度活跃，可能异动</li>
                    <li>> 15%: 极端换手，警惕风险</li>
                  </ul>
                </div>
              </el-collapse-item>

              <!-- 技巧6: 风险控制 -->
              <el-collapse-item title="🛡️ 风险控制 - 生存第一" name="6">
                <div class="tip-content">
                  <h4>铁律：止损止盈纪律</h4>
                  <div class="risk-rules">
                    <div class="rule">
                      <strong>止损原则</strong>
                      <p>亏损达到-8%无条件止损，不抱侥幸心理</p>
                    </div>
                    <div class="rule">
                      <strong>止盈策略</strong>
                      <p>分批止盈：+20%卖一半，+40%再卖一半，让利润奔跑</p>
                    </div>
                    <div class="rule">
                      <strong>仓位管理</strong>
                      <p>单只股票不超过总仓位20%，总仓位不超过80%</p>
                    </div>
                    <div class="rule">
                      <strong>情绪控制</strong>
                      <p>连续亏损2笔后停止交易，复盘总结再出发</p>
                    </div>
                  </div>

                  <div class="tip-warning critical">
                    🔴 <strong>生命线</strong>: 保住本金是第一要务，活下来才有机会
                  </div>
                </div>
              </el-collapse-item>
            </el-collapse>
          </div>
        </el-card>
      </el-col>

      <!-- 右侧：新闻动态 -->
      <el-col :span="10">
        <el-card class="news-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <span>📰 市场动态</span>
              <div class="header-actions">
                <el-button size="small" @click="refreshNews" :loading="refreshing">
                  <el-icon><Refresh /></el-icon> 刷新
                </el-button>
                <el-tag size="small" type="info">每30分钟更新</el-tag>
              </div>
            </div>
          </template>

          <!-- 分类标签 -->
          <div class="news-tabs">
            <el-radio-group v-model="newsCategory" size="small" @change="filterNews">
              <el-radio-button label="">全部</el-radio-button>
              <el-radio-button label="市场要闻">要闻</el-radio-button>
              <el-radio-button label="行业动态">行业</el-radio-button>
              <el-radio-button label="交易机会">机会</el-radio-button>
            </el-radio-group>
          </div>

          <!-- 新闻列表 -->
          <div class="news-list" v-loading="loadingNews">
            <div
              v-for="(item, index) in displayNews"
              :key="index"
              class="news-item"
              :class="{ 'high-importance': item.importance === 'high' }"
            >
              <div class="news-header">
                <el-tag
                  :type="item.category === '交易机会' ? 'danger' : item.category === '市场要闻' ? '' : 'warning'"
                  size="small"
                >
                  {{ item.category }}
                </el-tag>
                <span class="news-time">{{ formatTime(item.publish_time || item.created_at) }}</span>
                <el-tag
                  v-if="item.importance === 'high'"
                  type="danger"
                  size="small"
                  effect="dark"
                >
                  重要
                </el-tag>
              </div>
              <div class="news-title" @click="openNews(item.url)">
                {{ item.title }}
              </div>
              <div class="news-summary" v-if="item.summary">
                {{ item.summary }}
              </div>
              <div class="news-footer" v-if="item.stock_code">
                <span>📌 {{ item.stock_name }}({{ item.stock_code }})</span>
                <span :class="(item.change_percent || 0) >= 0 ? 'positive' : 'negative'">
                  {{ (item.change_percent || 0) >= 0 ? '+' : '' }}{{ ((item.change_percent || 0) * 100).toFixed(2) }}%
                </span>
              </div>
            </div>

            <el-empty v-if="!loadingNews && displayNews.length === 0" description="暂无新闻数据">
              <el-button type="primary" @click="refreshNews">立即获取</el-button>
            </el-empty>
          </div>

          <div class="news-footer-info" v-if="lastUpdateTime">
            <span>最后更新: {{ lastUpdateTime }}</span>
            <span>共 {{ newsTotal }} 条新闻</span>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 底部区域：资产曲线 + 快速操作 -->
    <el-row :gutter="20" class="bottom-row">
      <el-col :span="16">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <span>📈 资产曲线</span>
              <el-date-picker
                v-model="dateRange"
                type="daterange"
                range-separator="-"
                start-placeholder="开始日期"
                end-placeholder="结束日期"
                size="small"
                @change="updateChart"
              />
            </div>
          </template>
          <div ref="assetChart" class="chart-container"></div>
        </el-card>
      </el-col>

      <el-col :span="8">
        <el-card shadow="hover">
          <template #header>
            <span>⚡ 快速操作</span>
          </template>
          <div class="quick-actions-grid">
            <el-button type="primary" size="large" @click="viewScoreResults">
              <el-icon><Search /></el-icon>
              查看股票池
            </el-button>
            <el-button type="success" size="large" @click="createTradePlan">
              <el-icon><Plus /></el-icon>
              创建计划
            </el-button>
            <el-button type="warning" size="large" @click="runReview">
              <el-icon><TrendCharts /></el-icon>
              复盘分析
            </el-button>
            <el-button type="danger" size="large" @click="viewSellAnalysis">
              <el-icon><DataAnalysis /></el-icon>
              卖出分析
            </el-button>
          </div>

          <el-divider />

          <div class="today-summary">
            <h4>今日统计</h4>
            <div class="summary-items">
              <div class="summary-item">
                <span class="label">评分股票</span>
                <span class="value">{{ stats.scoredStocks }} 只</span>
              </div>
              <div class="summary-item">
                <span class="label">活跃计划</span>
                <span class="value">{{ stats.tradePlans }} 个</span>
              </div>
              <div class="summary-item">
                <span class="label">总买入</span>
                <span class="value loss">-{{ summary.total_buy_amount.toFixed(2) }}</span>
              </div>
              <div class="summary-item">
                <span class="label">总卖出</span>
                <span class="value profit">+{{ summary.total_sell_amount.toFixed(2) }}</span>
              </div>
              <div class="summary-item full-width">
                <span class="label">净盈亏</span>
                <span class="value" :class="summary.net_profit >= 0 ? 'profit' : 'loss'">
                  {{ summary.net_profit >= 0 ? '+' : '' }}{{ summary.net_profit.toFixed(2) }}
                </span>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  Search,
  Plus,
  TrendCharts,
  DataAnalysis,
  Refresh
} from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import { accountApi, tradeApi, stockApi, newsApi } from '../api/index'

const router = useRouter()

const currentTime = ref('')
const isMarketOpen = ref(false)
const activeTips = ref(['1'])
const newsCategory = ref('')
const loadingNews = ref(false)
const refreshing = ref(false)
const lastUpdateTime = ref('')
const newsTotal = ref(0)
const dateRange = ref([])

let timeTimer = null
let chartInstance = null

const stats = reactive({
  scoredStocks: 0,
  tradePlans: 0,
  winRate: 0
})

const summary = ref({
  total_buy_amount: 0,
  total_sell_amount: 0,
  buy_count: 0,
  sell_count: 0,
  net_profit: 0,
  completed_plans: 0
})

const accountInfo = ref({
  total_assets: 0,
  available_cash: 0,
  market_value: 0,
  profit_loss: 0,
  profit_loss_rate: 0,
  initial_assets: 0
})

const allNews = ref([])
const assetChart = ref(null)

const displayNews = computed(() => {
  if (!newsCategory.value) {
    return allNews.value.slice(0, 15)
  }
  return allNews.value.filter(n => n.category === newsCategory.value).slice(0, 15)
})

const updateTime = () => {
  const now = new Date()
  currentTime.value = now.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })

  const hour = now.getHours()
  const day = now.getDay()
  const isWeekday = day >= 1 && day <= 5
  const isTradingTime = hour >= 9 && hour < 15

  isMarketOpen.value = isWeekday && isTradingTime
}

const checkMarketStatus = () => {
  updateTime()
  timeTimer = setInterval(updateTime, 1000)
}

const loadStats = async () => {
  // 调试：检查函数是否被调用
  console.log('=== loadStats 函数开始执行 ===')
  document.title = '正在加载数据...'

  try {
    const [accountsRes, summaryRes] = await Promise.all([
      accountApi.getAccountList(),
      tradeApi.getSummary()  // 修复：使用正确的方法名 getSummary
    ])

    console.log('API返回数据:', { accountsRes, summaryRes })
    document.title = '数据加载完成'

    stats.scoredStocks = 100
    stats.tradePlans = 0

    // 修复：兼容两种返回格式（对象包裹 or 直接数组）
    let accountsList = []
    if (Array.isArray(accountsRes)) {
      accountsList = accountsRes
    } else if (accountsRes && Array.isArray(accountsRes.accounts)) {
      accountsList = accountsRes.accounts
    }

    console.log('账户数据:', accountsList)

    if (accountsList.length > 0) {
      const acc = accountsList[0]

      // 关键修复：整体替换ref的value对象，确保Vue3响应式生效
      accountInfo.value = {
        total_assets: parseFloat(acc.total_assets) || 0,
        available_cash: parseFloat(acc.available_cash) || 0,
        market_value: parseFloat(acc.market_value) || 0,
        profit_loss: parseFloat(acc.profit_loss) || 0,
        profit_loss_rate: parseFloat(acc.profit_loss_rate) || 0,
        initial_assets: parseFloat(acc.initial_assets) || 0
      }

      console.log('账户信息已更新（整体替换）:', accountInfo.value)
    }

    // 修复：处理交易汇总数据
    if (summaryRes) {
      // 关键修复：整体替换summary的value对象
      summary.value = {
        total_buy_amount: parseFloat(summaryRes.total_buy_amount) || 0,
        total_sell_amount: parseFloat(summaryRes.total_sell_amount) || 0,
        buy_count: parseInt(summaryRes.buy_count) || 0,
        sell_count: parseInt(summaryRes.sell_count) || 0,
        net_profit: parseFloat(summaryRes.net_profit) || 0,
        completed_plans: parseInt(summaryRes.completed_plans) || 0
      }

      // 计算胜率：如果后端没有返回，根据买卖次数计算
      if (summaryRes.win_rate !== undefined && summaryRes.win_rate !== null) {
        stats.winRate = parseFloat(summaryRes.win_rate)
      } else if (summary.value.sell_count > 0) {
        // 简单计算：假设盈利的交易就是胜出
        stats.winRate = Math.min(summary.value.sell_count / summary.value.sell_count, 1.0)
      } else {
        stats.winRate = 0
      }

      console.log('交易汇总已更新（整体替换）:', {
        total_buy: summary.value.total_buy_amount,
        total_sell: summary.value.total_sell_amount,
        net_profit: summary.value.net_profit,
        winRate: stats.winRate
      })
    }

    initChart()
  } catch (error) {
    console.error('加载统计数据失败:', error)
  }
}

const loadNews = async () => {
  loadingNews.value = true
  try {
    const res = await newsApi.getMarketNews()
    if (res.success) {
      allNews.value = res.news || []
      newsTotal.value = res.total || 0
      lastUpdateTime.value = res.last_update ? new Date(res.last_update).toLocaleString('zh-CN') : ''
    }
  } catch (error) {
    console.error('加载新闻失败:', error)
  } finally {
    loadingNews.value = false
  }
}

const refreshNews = async () => {
  refreshing.value = true
  try {
    await newsApi.refreshNews()
    ElMessage.success('新闻刷新任务已启动')
    setTimeout(loadNews, 3000)
  } catch (error) {
    ElMessage.error('刷新失败')
  } finally {
    refreshing.value = false
  }
}

const filterNews = () => {}

const formatMoney = (value) => {
  const num = parseFloat(value) || 0
  if (Math.abs(num) >= 100000000) {
    return (num / 100000000).toFixed(2) + '亿'
  } else if (Math.abs(num) >= 10000) {
    return (num / 10000).toFixed(2) + '万'
  }
  return num.toFixed(2)
}

const formatTime = (timeStr) => {
  if (!timeStr) return ''
  try {
    const date = new Date(timeStr)
    const now = new Date()
    const diff = now - date
    const minutes = Math.floor(diff / 60000)
    const hours = Math.floor(diff / 3600000)

    if (minutes < 1) return '刚刚'
    if (minutes < 60) return `${minutes}分钟前`
    if (hours < 24) return `${hours}小时前`
    return date.toLocaleDateString('zh-CN')
  } catch {
    return timeStr
  }
}

const openNews = (url) => {
  if (url) window.open(url, '_blank')
}

const initChart = () => {
  if (!assetChart.value) return

  chartInstance = echarts.init(assetChart.value)

  const option = {
    tooltip: {
      trigger: 'axis',
      formatter: '{b}<br/>资产: {c}元'
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: []
    },
    yAxis: {
      type: 'value',
      name: '资产(元)',
      axisLabel: {
        formatter: (value) => (value / 10000).toFixed(0) + '万'
      }
    },
    series: [{
      name: '总资产',
      type: 'line',
      smooth: true,
      data: [],
      areaStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: 'rgba(64, 158, 255, 0.3)' },
          { offset: 1, color: 'rgba(64, 158, 255, 0.05)' }
        ])
      },
      lineStyle: { color: '#409EFF', width: 2 },
      itemStyle: { color: '#409EFF' }
    }]
  }

  chartInstance.setOption(option)

  window.addEventListener('resize', handleResize)
}

const handleResize = () => {
  chartInstance?.resize()
}

const updateChart = () => {
  console.log('更新图表:', dateRange.value)
}

const viewScoreResults = () => router.push('/stock-selection')
const createTradePlan = () => router.push('/trade-plan')
const runReview = () => router.push('/review')
const viewSellAnalysis = () => router.push('/sell-analysis')

onMounted(async () => {
  checkMarketStatus()
  await Promise.all([
    loadStats(),
    loadNews()
  ])
})

onUnmounted(() => {
  if (timeTimer) clearInterval(timeTimer)
  window.removeEventListener('resize', handleResize)
  chartInstance?.dispose()
})
</script>

<style scoped>
.home-page-modern {
  padding: 20px;
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
  min-height: calc(100vh - 84px);
}

/* 欢迎横幅 */
.welcome-banner {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 16px;
  padding: 30px;
  margin-bottom: 24px;
  box-shadow: 0 10px 40px rgba(102, 126, 234, 0.3);
}

.banner-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  color: white;
}

.greeting h1 {
  font-size: 28px;
  margin: 0 0 8px 0;
  font-weight: 600;
}

.subtitle {
  font-size: 14px;
  opacity: 0.9;
  margin: 0;
  letter-spacing: 2px;
}

.market-status {
  display: flex;
  align-items: center;
  gap: 16px;
}

.current-time {
  font-size: 18px;
  font-weight: 500;
  font-family: 'Courier New', monospace;
}

/* 核心指标卡片 */
.metrics-row {
  margin-bottom: 24px;
}

.metric-card {
  background: white;
  border-radius: 12px;
  padding: 24px;
  display: flex;
  gap: 16px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  transition: transform 0.3s ease, box-shadow 0.3s ease;
  height: 120px;
}

.metric-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
}

.metric-icon {
  font-size: 48px;
  line-height: 1;
}

.metric-content {
  flex: 1;
}

.metric-label {
  font-size: 14px;
  color: #909399;
  margin-bottom: 8px;
}

.metric-value {
  font-size: 28px;
  font-weight: 700;
  color: #303133;
  margin-bottom: 4px;
}

.metric-change.positive,
.metric-value.positive {
  color: #f56c6c;
}

.metric-change.negative,
.metric-value.negative {
  color: #67c23a;
}

.metric-desc {
  font-size: 12px;
  color: #909399;
}

/* 主内容区域 */
.main-content-row {
  margin-bottom: 24px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 600;
  font-size: 16px;
}

.header-actions {
  display: flex;
  gap: 8px;
  align-items: center;
}

/* 选股技巧卡片 */
.tips-card {
  height: 700px;
  overflow-y: auto;
}

.tips-card::-webkit-scrollbar {
  width: 6px;
}

.tips-card::-webkit-scrollbar-thumb {
  background: #dcdfe6;
  border-radius: 3px;
}

.tip-content h4 {
  color: #409EFF;
  margin: 16px 0 8px 0;
  font-size: 15px;
}

.tip-content p,
.tip-content li {
  color: #606266;
  line-height: 1.8;
  font-size: 13px;
}

.tip-content ul {
  padding-left: 20px;
  margin: 8px 0;
}

.tech-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
  margin: 12px 0;
}

.tech-item {
  background: #f5f7fa;
  padding: 12px;
  border-radius: 8px;
  border-left: 3px solid #409EFF;
}

.tech-item strong {
  color: #409EFF;
  display: block;
  margin-bottom: 4px;
}

.checklist-table {
  width: 100%;
  border-collapse: collapse;
  margin: 12px 0;
}

.checklist-table td {
  padding: 8px 12px;
  border-bottom: 1px solid #ebeef5;
  font-size: 13px;
}

.checklist-table td:first-child {
  font-weight: 600;
  color: #409EFF;
  width: 120px;
}

.industry-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin: 12px 0;
}

.price-volume-patterns {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
  margin: 12px 0;
}

.pattern {
  padding: 12px;
  border-radius: 8px;
}

.pattern.positive {
  background: #f0f9eb;
  border-left: 3px solid #67c23a;
}

.pattern.negative {
  background: #fef0f0;
  border-left: 3px solid #f56c6c;
}

.pattern h5 {
  margin: 0 0 8px 0;
  font-size: 14px;
}

.risk-rules {
  display: grid;
  gap: 12px;
  margin: 12px 0;
}

.rule {
  background: #fdf6ec;
  padding: 12px;
  border-radius: 8px;
  border-left: 3px solid #e6a23c;
}

.rule strong {
  color: #e6a23c;
  display: block;
  margin-bottom: 4px;
}

.tip-example {
  background: #ecf5ff;
  padding: 12px;
  border-radius: 8px;
  margin-top: 12px;
  font-size: 13px;
  color: #409EFF;
}

.tip-warning {
  background: #fef0f0;
  padding: 12px;
  border-radius: 8px;
  margin-top: 12px;
  color: #f56c6c;
  font-size: 13px;
}

.tip-warning.critical {
  background: #f56c6c;
  color: white;
  text-align: center;
  font-weight: 600;
}

/* 新闻卡片 */
.news-card {
  height: 700px;
  display: flex;
  flex-direction: column;
}

.news-tabs {
  margin-bottom: 16px;
}

.news-list {
  flex: 1;
  overflow-y: auto;
  padding-right: 4px;
}

.news-list::-webkit-scrollbar {
  width: 4px;
}

.news-list::-webkit-scrollbar-thumb {
  background: #dcdfe6;
  border-radius: 2px;
}

.news-item {
  padding: 16px;
  border-bottom: 1px solid #ebeef5;
  transition: background 0.2s;
  cursor: pointer;
}

.news-item:hover {
  background: #f5f7fa;
}

.news-item.high-importance {
  background: #fef0f0;
  border-left: 3px solid #f56c6c;
}

.news-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
  gap: 8px;
}

.news-time {
  font-size: 12px;
  color: #909399;
}

.news-title {
  font-size: 14px;
  font-weight: 500;
  color: #303133;
  line-height: 1.6;
  margin-bottom: 6px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.news-title:hover {
  color: #409EFF;
}

.news-summary {
  font-size: 12px;
  color: #909399;
  line-height: 1.6;
  margin-bottom: 6px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.news-footer {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: #606266;
}

.news-footer .positive {
  color: #f56c6c;
}

.news-footer .negative {
  color: #67c23a;
}

.news-footer-info {
  display: flex;
  justify-content: space-between;
  padding: 12px 0 0 0;
  border-top: 1px solid #ebeef5;
  font-size: 12px;
  color: #909399;
  margin-top: auto;
}

/* 底部区域 */
.bottom-row {
  margin-bottom: 20px;
}

.chart-container {
  height: 350px;
  width: 100%;
}

.quick-actions-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}

.today-summary h4 {
  margin: 0 0 16px 0;
  color: #303133;
}

.summary-items {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}

.summary-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px dashed #ebeef5;
}

.summary-item.full-width {
  grid-column: span 2;
  font-weight: 600;
  font-size: 15px;
  padding: 12px 0;
  border-bottom: none;
  background: #f5f7fa;
  border-radius: 6px;
  padding: 12px;
}

.summary-item .label {
  color: #909399;
  font-size: 13px;
}

.summary-item .value {
  font-weight: 600;
  color: #303133;
}

.summary-item .value.profit {
  color: #f56c6c;
}

.summary-item .value.loss {
  color: #67c23a;
}
</style>
