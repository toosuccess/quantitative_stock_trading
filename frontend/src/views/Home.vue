<template>
  <div class="home-page">
    <el-row :gutter="20">
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-title">评分股票</div>
          <div class="stat-value">{{ stats.scoredStocks }}</div>
          <div class="stat-desc">只股票已评分</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-title">交易计划</div>
          <div class="stat-value">{{ stats.tradePlans }}</div>
          <div class="stat-desc">个待执行计划</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-title">交易胜率</div>
          <div class="stat-value">{{ stats.winRate.toFixed(1) }}%</div>
          <div class="stat-desc">历史胜率</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-title">总盈亏</div>
          <div class="stat-value" :class="stats.totalProfit >= 0 ? 'profit' : 'loss'">
            {{ stats.totalProfit >= 0 ? '+' : '' }}{{ stats.totalProfit.toFixed(2) }}
          </div>
          <div class="stat-desc">元</div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 20px;">
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-title">总买入金额</div>
          <div class="stat-value loss">-{{ summary.total_buy_amount.toFixed(2) }}</div>
          <div class="stat-desc">{{ summary.buy_count }}笔买入</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-title">总卖出金额</div>
          <div class="stat-value profit">+{{ summary.total_sell_amount.toFixed(2) }}</div>
          <div class="stat-desc">{{ summary.sell_count }}笔卖出</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-title">净盈亏</div>
          <div class="stat-value" :class="summary.net_profit >= 0 ? 'profit' : 'loss'">
            {{ summary.net_profit >= 0 ? '+' : '' }}{{ summary.net_profit.toFixed(2) }}
          </div>
          <div class="stat-desc">元</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-title">已完成计划</div>
          <div class="stat-value">{{ summary.completed_plans }}</div>
          <div class="stat-desc">个计划已完成</div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 20px;">
      <el-col :span="16">
        <el-card>
          <template #header>
            <span>资产曲线</span>
          </template>
          <div ref="assetChart" class="chart-container"></div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card>
          <template #header>
            <span>快速操作</span>
          </template>
          <div class="quick-actions">
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
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Search, Plus, TrendCharts } from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import { scoreApi, planApi, tradeApi } from '../api'

const router = useRouter()
const assetChart = ref(null)

const stats = ref({
  scoredStocks: 0,
  tradePlans: 0,
  winRate: 0,
  totalProfit: 0
})

const summary = ref({
  total_trades: 0,
  buy_count: 0,
  sell_count: 0,
  total_buy_amount: 0,
  total_sell_amount: 0,
  net_profit: 0,
  completed_plans: 0
})

const loadStats = async () => {
  try {
    const scoresData = await scoreApi.getScoreList(100)
    stats.value.scoredStocks = scoresData.count || 0
    
    const plansData = await planApi.getPlanList('ACC001')
    stats.value.tradePlans = plansData.plans ? plansData.plans.filter(p => p.status === 'pending').length : 0
    
    const tradeStats = await tradeApi.getStatistics('ACC001')
    stats.value.winRate = tradeStats.win_rate?.win_rate || 0
    stats.value.totalProfit = tradeStats.profit_loss_ratio?.avg_profit || 0
  } catch (error) {
    console.error('加载统计数据失败:', error)
  }
}

const loadSummary = async () => {
  try {
    const data = await tradeApi.getSummary()
    summary.value = data
  } catch (error) {
    console.error('加载汇总数据失败:', error)
  }
}

const viewScoreResults = () => {
  router.push('/stock-selection')
}

const createTradePlan = () => {
  router.push('/trade-plan')
}

const runReview = () => {
  router.push('/review')
}

onMounted(() => {
  loadStats()
  loadSummary()
  
  const chart = echarts.init(assetChart.value)
  const option = {
    tooltip: {
      trigger: 'axis'
    },
    xAxis: {
      type: 'category',
      data: ['1月', '2月', '3月', '4月', '5月', '6月']
    },
    yAxis: {
      type: 'value'
    },
    series: [{
      data: [100000, 102500, 101000, 105000, 108000, 112580],
      type: 'line',
      smooth: true,
      areaStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: 'rgba(64, 158, 255, 0.5)' },
          { offset: 1, color: 'rgba(64, 158, 255, 0.1)' }
        ])
      },
      lineStyle: {
        color: '#409eff'
      }
    }]
  }
  chart.setOption(option)
  
  window.addEventListener('resize', () => chart.resize())
})
</script>

<style scoped>
.home-page {
  padding: 0;
}

.stat-card {
  text-align: center;
  padding: 10px;
}

.stat-title {
  font-size: 14px;
  color: #909399;
  margin-bottom: 10px;
}

.stat-value {
  font-size: 28px;
  font-weight: bold;
  color: #303133;
}

.stat-value.profit {
  color: #67c23a;
}

.stat-value.loss {
  color: #f56c6c;
}

.stat-desc {
  font-size: 12px;
  color: #c0c4cc;
  margin-top: 5px;
}

.chart-container {
  height: 300px;
}

.quick-actions {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.quick-actions .el-button {
  width: 100%;
}
</style>
