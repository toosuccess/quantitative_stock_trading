<template>
  <div class="home-page">
    <!-- 欢迎横幅 -->
    <div class="welcome-banner">
      <div class="banner-content">
        <div class="greeting">
          <h1>欢迎回来，量化交易者</h1>
          <p class="subtitle">去情绪化 · 可量化 · 可追溯 · 可重复 · 可迭代</p>
        </div>
        <div class="market-status">
          <el-tag :type="isMarketOpen ? 'success' : 'info'" size="large">
            {{ isMarketOpen ? '交易中' : '已休市' }}
          </el-tag>
          <span class="current-time">{{ currentTime }}</span>
        </div>
      </div>
    </div>

    <!-- 核心指标卡片 -->
    <el-row :gutter="16" class="metrics-row">
      <el-col :span="6">
        <div class="metric-card">
          <div class="metric-icon total-assets-icon">
            <svg viewBox="0 0 24 24" width="28" height="28" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 6v12M8 10h8M9 14h6"/></svg>
          </div>
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
        <div class="metric-card">
          <div class="metric-icon profit-rate-icon">
            <svg viewBox="0 0 24 24" width="28" height="28" fill="none" stroke="currentColor" stroke-width="2"><polyline points="22 7 13.5 15.5 8.5 10.5 2 17"/><polyline points="16 7 22 7 22 13"/></svg>
          </div>
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
        <div class="metric-card">
          <div class="metric-icon holdings-icon">
            <svg viewBox="0 0 24 24" width="28" height="28" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="3" width="20" height="14" rx="2"/><path d="M8 21h8M12 17v4"/></svg>
          </div>
          <div class="metric-content">
            <div class="metric-label">持仓市值</div>
            <div class="metric-value">{{ formatMoney(accountInfo.market_value || 0) }}</div>
            <div class="metric-desc">可用资金: {{ formatMoney(accountInfo.available_cash || 0) }}</div>
          </div>
        </div>
      </el-col>

      <el-col :span="6">
        <div class="metric-card">
          <div class="metric-icon win-rate-icon">
            <svg viewBox="0 0 24 24" width="28" height="28" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/></svg>
          </div>
          <div class="metric-content">
            <div class="metric-label">交易胜率</div>
            <div class="metric-value">{{ winRateDisplay }}%</div>
            <div class="metric-desc">已完成{{ summary.completed_plans }}笔交易</div>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 待办事项 -->
    <el-row :gutter="16" class="todo-row">
      <!-- 待执行计划 -->
      <el-col :span="8">
        <div class="todo-card">
          <div class="todo-card-header">
            <span class="todo-card-title">待执行计划</span>
            <span class="todo-badge" v-if="todos.pending_plans.count > 0">{{ todos.pending_plans.count }}</span>
          </div>
          <div class="todo-list">
            <div
              v-for="(item, index) in todos.pending_plans.items.slice(0, 5)"
              :key="'plan-' + index"
              class="todo-item"
            >
              <span class="todo-item-name">{{ item.stock_name || item.stock_code }}</span>
              <el-tag
                :type="item.trade_direction === 'buy' ? 'danger' : 'success'"
                size="small"
              >
                {{ item.trade_direction === 'buy' ? '买入' : '卖出' }}
              </el-tag>
            </div>
            <div v-if="todos.pending_plans.items.length === 0" class="todo-empty">暂无待办</div>
          </div>
          <div class="todo-card-footer" v-if="todos.pending_plans.count > 0" @click="goToTradePlan">
            查看全部 &rarr;
          </div>
        </div>
      </el-col>

      <!-- 待判定预判 -->
      <el-col :span="8">
        <div class="todo-card">
          <div class="todo-card-header">
            <span class="todo-card-title">待判定预判</span>
            <span class="todo-badge" v-if="todos.pending_predictions.count > 0">{{ todos.pending_predictions.count }}</span>
          </div>
          <div class="todo-list">
            <div
              v-for="(item, index) in todos.pending_predictions.items.slice(0, 5)"
              :key="'pred-' + index"
              class="todo-item"
            >
              <span class="todo-item-name">{{ item.stock_name || item.stock_code }}</span>
              <el-tag
                :type="item.prediction_direction === '看涨' ? 'danger' : 'success'"
                size="small"
              >
                {{ item.prediction_direction }}
              </el-tag>
              <span class="todo-item-date">{{ item.target_date }}</span>
            </div>
            <div v-if="todos.pending_predictions.items.length === 0" class="todo-empty">暂无待办</div>
          </div>
          <div class="todo-card-footer" v-if="todos.pending_predictions.count > 0" @click="goToStockPool">
            查看全部 &rarr;
          </div>
        </div>
      </el-col>

      <!-- 待复审股票 -->
      <el-col :span="8">
        <div class="todo-card">
          <div class="todo-card-header">
            <span class="todo-card-title">待复审股票</span>
            <span class="todo-badge" v-if="todos.pending_reviews.count > 0">{{ todos.pending_reviews.count }}</span>
          </div>
          <div class="todo-list">
            <div
              v-for="(item, index) in todos.pending_reviews.items.slice(0, 5)"
              :key="'review-' + index"
              class="todo-item"
            >
              <span class="todo-item-name">{{ item.stock_code }} {{ item.stock_name }}</span>
              <span class="todo-item-date">{{ item.last_score_date || '未复审' }}</span>
            </div>
            <div v-if="todos.pending_reviews.items.length === 0" class="todo-empty">暂无待办</div>
          </div>
          <div class="todo-card-footer" v-if="todos.pending_reviews.count > 0" @click="goToReview">
            查看全部 &rarr;
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 市场动态 + 快速操作 -->
    <el-row :gutter="16" class="bottom-row">
      <!-- 市场动态 -->
      <el-col :span="14">
        <div class="news-card">
          <div class="card-header">
            <span class="card-header-title">市场动态</span>
            <div class="header-actions">
              <el-button size="small" @click="refreshNews" :loading="refreshing">
                <el-icon><Refresh /></el-icon> 刷新
              </el-button>
              <el-tag size="small" type="info">每30分钟更新</el-tag>
            </div>
          </div>

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
                <span>{{ item.stock_name }}({{ item.stock_code }})</span>
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
        </div>
      </el-col>

      <!-- 快速操作 + 今日统计 -->
      <el-col :span="10">
        <div class="action-card">
          <div class="card-header">
            <span class="card-header-title">快速操作</span>
          </div>
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
        </div>

        <div class="summary-card">
          <div class="card-header">
            <span class="card-header-title">今日统计</span>
          </div>
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
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  Search,
  Plus,
  TrendCharts,
  DataAnalysis,
  Refresh
} from '@element-plus/icons-vue'
import { accountApi, tradeApi, newsApi, stockApi } from '../api'

const router = useRouter()

const currentTime = ref('')
const isMarketOpen = ref(false)
const newsCategory = ref('')
const loadingNews = ref(false)
const refreshing = ref(false)
const lastUpdateTime = ref('')
const newsTotal = ref(0)

let timeTimer = null

const stats = reactive({
  scoredStocks: 0,
  tradePlans: 0
})

const summary = ref({
  total_buy_amount: 0,
  total_sell_amount: 0,
  buy_count: 0,
  sell_count: 0,
  win_count: 0,
  net_profit: 0,
  completed_plans: 0,
  win_rate: null
})

const accountInfo = ref({
  total_assets: 0,
  available_cash: 0,
  market_value: 0,
  profit_loss: 0,
  profit_loss_rate: 0,
  initial_assets: 0
})

const todos = ref({
  pending_plans: { items: [], count: 0 },
  pending_predictions: { items: [], count: 0 },
  pending_reviews: { items: [], count: 0 },
  stats: { scored_stocks: 0, active_plans: 0 }
})

const allNews = ref([])

const displayNews = computed(() => {
  if (!newsCategory.value) {
    return allNews.value.slice(0, 15)
  }
  return allNews.value.filter(n => n.category === newsCategory.value).slice(0, 15)
})

const winRateDisplay = computed(() => {
  if (summary.value.win_rate !== null && summary.value.win_rate !== undefined) {
    return (parseFloat(summary.value.win_rate) * 100).toFixed(1)
  }
  if (summary.value.sell_count > 0) {
    return (summary.value.win_count / summary.value.sell_count * 100).toFixed(1)
  }
  return '0.0'
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
  try {
    const [accountsRes, summaryRes] = await Promise.all([
      accountApi.getAccountList(),
      tradeApi.getSummary()
    ])

    // 兼容两种返回格式
    let accountsList = []
    if (Array.isArray(accountsRes)) {
      accountsList = accountsRes
    } else if (accountsRes && Array.isArray(accountsRes.accounts)) {
      accountsList = accountsRes.accounts
    }

    if (accountsList.length > 0) {
      const acc = accountsList[0]
      accountInfo.value = {
        total_assets: parseFloat(acc.total_assets) || 0,
        available_cash: parseFloat(acc.available_cash) || 0,
        market_value: parseFloat(acc.market_value) || 0,
        profit_loss: parseFloat(acc.profit_loss) || 0,
        profit_loss_rate: parseFloat(acc.profit_loss_rate) || 0,
        initial_assets: parseFloat(acc.initial_assets) || 0
      }
    }

    if (summaryRes) {
      summary.value = {
        total_buy_amount: parseFloat(summaryRes.total_buy_amount) || 0,
        total_sell_amount: parseFloat(summaryRes.total_sell_amount) || 0,
        buy_count: parseInt(summaryRes.buy_count) || 0,
        sell_count: parseInt(summaryRes.sell_count) || 0,
        win_count: parseInt(summaryRes.win_count) || 0,
        net_profit: parseFloat(summaryRes.net_profit) || 0,
        completed_plans: parseInt(summaryRes.completed_plans) || 0,
        win_rate: summaryRes.win_rate !== undefined && summaryRes.win_rate !== null
          ? parseFloat(summaryRes.win_rate)
          : null
      }
    }
  } catch (error) {
    console.error('加载统计数据失败:', error)
  }
}

const loadTodos = async () => {
  try {
    const result = await stockApi.getDashboardTodos()
    if (result.success) {
      todos.value = result
      // 从 todos.stats 更新 stats
      stats.scoredStocks = result.stats?.scored_stocks || 0
      stats.tradePlans = result.stats?.active_plans || 0
    }
  } catch (e) {
    console.warn('加载待办事项失败:', e)
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

const viewScoreResults = () => router.push('/stock-selection')
const createTradePlan = () => router.push('/trade-plan')
const runReview = () => router.push('/review')
const viewSellAnalysis = () => router.push('/sell-analysis')

const goToStockPool = () => router.push('/stock-selection')
const goToTradePlan = () => router.push('/trade-plan')
const goToReview = () => router.push('/review')

onMounted(async () => {
  checkMarketStatus()
  await Promise.all([
    loadStats(),
    loadTodos(),
    loadNews()
  ])
})

onUnmounted(() => {
  if (timeTimer) clearInterval(timeTimer)
})
</script>

<style scoped>
.home-page {
  padding: 20px;
  background: #f5f7fa;
  min-height: calc(100vh - 84px);
}

/* 欢迎横幅 */
.welcome-banner {
  background: linear-gradient(135deg, #e8f4fd 0%, #f0f7ff 100%);
  border-radius: 8px;
  padding: 20px 24px;
  margin-bottom: 16px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
}

.banner-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.greeting h1 {
  font-size: 20px;
  margin: 0 0 4px 0;
  font-weight: 600;
  color: #303133;
}

.subtitle {
  font-size: 13px;
  color: #606266;
  margin: 0;
  letter-spacing: 1px;
}

.market-status {
  display: flex;
  align-items: center;
  gap: 16px;
}

.current-time {
  font-size: 16px;
  font-weight: 500;
  color: #303133;
  font-family: 'Courier New', monospace;
}

/* 核心指标卡片 */
.metrics-row {
  margin-bottom: 16px;
}

.metric-card {
  background: white;
  border-radius: 8px;
  padding: 20px;
  display: flex;
  gap: 16px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.metric-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
}

.metric-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.total-assets-icon {
  background: #ecf5ff;
  color: #409EFF;
}

.profit-rate-icon {
  background: #f0f9eb;
  color: #67c23a;
}

.holdings-icon {
  background: #fdf6ec;
  color: #e6a23c;
}

.win-rate-icon {
  background: #fef0f0;
  color: #f56c6c;
}

.metric-content {
  flex: 1;
  min-width: 0;
}

.metric-label {
  font-size: 14px;
  color: #909399;
  margin-bottom: 8px;
  font-weight: 400;
}

.metric-value {
  font-size: 24px;
  font-weight: 700;
  color: #303133;
  margin-bottom: 4px;
  line-height: 1.2;
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
  font-weight: 400;
}

/* 待办事项 */
.todo-row {
  margin-bottom: 16px;
}

.todo-card {
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
  overflow: hidden;
}

.todo-card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px 12px;
  border-bottom: 1px solid #f0f2f5;
}

.todo-card-title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.todo-badge {
  background: #f56c6c;
  color: white;
  font-size: 12px;
  font-weight: 600;
  min-width: 20px;
  height: 20px;
  border-radius: 10px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 0 6px;
}

.todo-list {
  padding: 4px 0;
  min-height: 200px;
}

.todo-item {
  display: flex;
  align-items: center;
  padding: 10px 20px;
  gap: 8px;
  cursor: pointer;
  transition: background 0.2s;
  border-left: 3px solid transparent;
}

.todo-item:hover {
  background: #ecf5ff;
  border-left-color: #409EFF;
}

.todo-item-name {
  flex: 1;
  font-size: 14px;
  color: #303133;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.todo-item-date {
  font-size: 12px;
  color: #909399;
  flex-shrink: 0;
}

.todo-empty {
  text-align: center;
  color: #c0c4cc;
  padding: 40px 0;
  font-size: 14px;
}

.todo-card-footer {
  padding: 12px 20px;
  text-align: center;
  color: #409EFF;
  font-size: 14px;
  cursor: pointer;
  border-top: 1px solid #f0f2f5;
  transition: background 0.2s;
}

.todo-card-footer:hover {
  background: #ecf5ff;
}

/* 底部区域 */
.bottom-row {
  margin-bottom: 20px;
}

/* 通用卡片头部 */
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.card-header-title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.header-actions {
  display: flex;
  gap: 8px;
  align-items: center;
}

/* 新闻卡片 */
.news-card {
  background: white;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
}

.news-tabs {
  margin-bottom: 16px;
}

.news-list {
  max-height: 420px;
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
  padding: 14px 0;
  border-bottom: 1px solid #f0f2f5;
  transition: background 0.2s;
  cursor: pointer;
}

.news-item:hover {
  background: #fafafa;
}

.news-item.high-importance {
  background: #fef0f0;
  border-left: 3px solid #f56c6c;
  padding-left: 12px;
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
  border-top: 1px solid #f0f2f5;
  font-size: 12px;
  color: #909399;
  margin-top: 12px;
}

/* 快速操作卡片 */
.action-card {
  background: white;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
  margin-bottom: 16px;
}

.quick-actions-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}

.quick-actions-grid .el-button {
  width: 100%;
}

/* 今日统计卡片 */
.summary-card {
  background: white;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
}

.summary-items {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 0;
}

.summary-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 0;
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
  margin-top: 4px;
}

.summary-item .label {
  color: #909399;
  font-size: 13px;
}

.summary-item .value {
  font-weight: 600;
  color: #303133;
  font-size: 14px;
}

.summary-item .value.profit {
  color: #f56c6c;
}

.summary-item .value.loss {
  color: #67c23a;
}
</style>
