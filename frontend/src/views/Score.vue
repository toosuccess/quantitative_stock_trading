<template>
  <div class="score-page">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>股票评分详情</span>
          <el-button @click="goBack">返回</el-button>
        </div>
      </template>
      
      <div v-if="loading" class="loading-container">
        <el-skeleton :rows="10" animated />
      </div>
      
      <div v-else-if="stockInfo">
        <el-descriptions :title="`${stockInfo.stock_name} (${stockInfo.stock_code})`" :column="4" border>
          <el-descriptions-item label="最新评分">
            <el-tag :type="getScoreType(stockInfo.total_score)" size="large">
              {{ stockInfo.total_score?.toFixed(1) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="最新评级">
            <el-tag :type="getRatingType(stockInfo.rating)" size="large">
              {{ stockInfo.rating }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="评分次数">
            <el-badge :value="scoreHistory.length" type="primary" />
          </el-descriptions-item>
          <el-descriptions-item label="最新收盘价">{{ stockInfo.close_price?.toFixed(2) }}</el-descriptions-item>
        </el-descriptions>

        <el-divider content-position="left">技术指标评分</el-divider>

        <el-row :gutter="20">
          <el-col :span="4" v-for="item in techScores" :key="item.name">
            <el-card class="score-card">
              <div class="score-name">{{ item.name }}</div>
              <div class="score-value">{{ item.score }}</div>
              <el-progress :percentage="item.percentage" :color="item.color" />
            </el-card>
          </el-col>
        </el-row>

        <el-divider content-position="left">评分历史</el-divider>

        <el-table :data="scoreHistory" style="width: 100%" max-height="300">
          <el-table-column prop="score_date" label="评分日期" width="120" />
          <el-table-column prop="total_score" label="综合评分" width="100">
            <template #default="scope">
              <el-tag :type="getScoreType(scope.row.total_score)">
                {{ scope.row.total_score?.toFixed(1) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="rating" label="评级" width="100" />
          <el-table-column prop="close_price" label="收盘价" width="100">
            <template #default="scope">
              {{ scope.row.close_price?.toFixed(2) }}
            </template>
          </el-table-column>
          <el-table-column prop="ma_score" label="MA" width="60" />
          <el-table-column prop="macd_score" label="MACD" width="60" />
          <el-table-column prop="rsi_score" label="RSI" width="60" />
          <el-table-column prop="bollinger_score" label="布林带" width="60" />
          <el-table-column prop="volume_score" label="成交量" width="60" />
          <el-table-column prop="obv_score" label="OBV" width="60" />
        </el-table>

        <el-divider content-position="left">技术指标趋势</el-divider>

        <div ref="trendChart" class="chart-container"></div>
      </div>
      
      <el-empty v-else description="请从股票池选择股票查看详情" />
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import * as echarts from 'echarts'
import { scoreApi } from '../api'

const route = useRoute()
const router = useRouter()

const loading = ref(false)
const stockInfo = ref(null)
const scoreHistory = ref([])
const trendChart = ref(null)
let chartInstance = null

const techScores = computed(() => {
  if (!stockInfo.value) return []
  return [
    { name: '均线', score: stockInfo.value.ma_score || 0, percentage: stockInfo.value.ma_score || 0, color: '#409eff' },
    { name: 'MACD', score: stockInfo.value.macd_score || 0, percentage: (stockInfo.value.macd_score || 0) * 5, color: '#67c23a' },
    { name: 'RSI', score: stockInfo.value.rsi_score || 0, percentage: stockInfo.value.rsi_score || 0, color: '#e6a23c' },
    { name: '布林带', score: stockInfo.value.bollinger_score || 0, percentage: stockInfo.value.bollinger_score || 0, color: '#f56c6c' },
    { name: '成交量', score: stockInfo.value.volume_score || 0, percentage: stockInfo.value.volume_score || 0, color: '#909399' },
    { name: 'OBV', score: stockInfo.value.obv_score || 0, percentage: stockInfo.value.obv_score || 0, color: '#9c27b0' }
  ]
})

const getScoreType = (score) => {
  if (score >= 90) return 'success'
  if (score >= 70) return 'primary'
  if (score >= 50) return 'warning'
  return 'info'
}

const getRatingType = (rating) => {
  const types = {
    '强烈推荐': 'success',
    '推荐': 'primary',
    '中性': 'warning',
    '观望': 'info',
    '不推荐': 'danger'
  }
  return types[rating] || 'info'
}

const loadScoreHistory = async (stockCode) => {
  loading.value = true
  try {
    const data = await scoreApi.getScoreByCode(stockCode)
    scoreHistory.value = data.history || []
    if (scoreHistory.value.length > 0) {
      stockInfo.value = scoreHistory.value[0]
      await nextTick()
      renderTrendChart()
    }
  } catch (error) {
    console.error('加载评分历史失败:', error)
  } finally {
    loading.value = false
  }
}

const renderTrendChart = () => {
  if (!trendChart.value || scoreHistory.value.length === 0) return
  
  if (chartInstance) {
    chartInstance.dispose()
  }
  
  chartInstance = echarts.init(trendChart.value)
  
  const dates = scoreHistory.value.map(item => item.score_date).reverse()
  const series = [
    { name: '综合评分', data: scoreHistory.value.map(item => item.total_score).reverse() },
    { name: 'MA', data: scoreHistory.value.map(item => item.ma_score).reverse() },
    { name: 'MACD', data: scoreHistory.value.map(item => item.macd_score).reverse() },
    { name: '布林带', data: scoreHistory.value.map(item => item.bollinger_score).reverse() },
    { name: '成交量', data: scoreHistory.value.map(item => item.volume_score).reverse() },
    { name: 'OBV', data: scoreHistory.value.map(item => item.obv_score).reverse() }
  ]
  
  const option = {
    tooltip: {
      trigger: 'axis'
    },
    legend: {
      data: series.map(s => s.name)
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: dates
    },
    yAxis: {
      type: 'value'
    },
    series: series.map(s => ({
      name: s.name,
      type: 'line',
      smooth: true,
      data: s.data
    }))
  }
  
  chartInstance.setOption(option)
}

const goBack = () => {
  router.push('/stock-selection')
}

onMounted(() => {
  const stockCode = route.query.stock_code
  if (stockCode) {
    loadScoreHistory(stockCode)
  }
})

watch(() => route.query.stock_code, (newCode) => {
  if (newCode) {
    loadScoreHistory(newCode)
  }
})
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.loading-container {
  padding: 20px;
}

.score-card {
  text-align: center;
  padding: 10px;
}

.score-name {
  font-size: 14px;
  color: #909399;
  margin-bottom: 10px;
}

.score-value {
  font-size: 24px;
  font-weight: bold;
  color: #303133;
  margin-bottom: 10px;
}

.chart-container {
  height: 350px;
  width: 100%;
}
</style>
