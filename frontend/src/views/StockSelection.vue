<template>
  <div class="stock-pool-page">
    <!-- 统计概览卡片 -->
    <el-row :gutter="20" style="margin-bottom: 20px;">
      <el-col :span="4">
        <el-card class="stat-card">
          <div class="stat-title">股票总数</div>
          <div class="stat-value">{{ stockPool.length }}</div>
        </el-card>
      </el-col>
      <el-col :span="4">
        <el-card class="stat-card stat-success clickable" :class="{ active: ratingFilter === '强烈推荐' }" @click="filterByRating('强烈推荐')">
          <div class="stat-title">强烈推荐</div>
          <div class="stat-value">{{ ratingStats.strongRecommended }}</div>
        </el-card>
      </el-col>
      <el-col :span="4">
        <el-card class="stat-card stat-primary clickable" :class="{ active: ratingFilter === '推荐' }" @click="filterByRating('推荐')">
          <div class="stat-title">推荐</div>
          <div class="stat-value">{{ ratingStats.recommended }}</div>
        </el-card>
      </el-col>
      <el-col :span="4">
        <el-card class="stat-card stat-warning clickable" :class="{ active: ratingFilter === '中性' }" @click="filterByRating('中性')">
          <div class="stat-title">中性</div>
          <div class="stat-value">{{ ratingStats.neutral }}</div>
        </el-card>
      </el-col>
      <el-col :span="4">
        <el-card class="stat-card stat-info clickable" :class="{ active: ratingFilter === '观望' }" @click="filterByRating('观望')">
          <div class="stat-title">观望</div>
          <div class="stat-value">{{ ratingStats.watch }}</div>
        </el-card>
      </el-col>
      <el-col :span="4">
        <el-card class="stat-card stat-danger clickable" :class="{ active: ratingFilter === '不推荐' }" @click="filterByRating('不推荐')">
          <div class="stat-title">不推荐</div>
          <div class="stat-value">{{ ratingStats.notRecommended }}</div>
        </el-card>
      </el-col>
    </el-row>

    <el-card>
      <template #header>
        <div class="card-header">
          <div class="search-bar">
            <el-input
              v-model="searchText"
              placeholder="搜索股票代码/名称"
              clearable
              style="width: 200px; margin-right: 10px;"
            />
            <el-select v-model="ratingFilter" placeholder="评级筛选" clearable style="width: 120px;">
              <el-option label="强烈推荐" value="强烈推荐" />
              <el-option label="推荐" value="推荐" />
              <el-option label="中性" value="中性" />
              <el-option label="观望" value="观望" />
              <el-option label="不推荐" value="不推荐" />
            </el-select>
          </div>
          <el-button 
            type="warning" 
            :disabled="selectedStocks.length === 0"
            @click="batchEvaluate"
            :loading="batchEvaluating"
          >
            <el-icon><Check /></el-icon>
            批量评价 ({{ selectedStocks.length }})
          </el-button>
        </div>
      </template>
      
      <el-table 
        :data="paginatedData" 
        style="width: 100%" 
        v-loading="loading"
        @sort-change="handleSortChange"
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="55" />
        <el-table-column prop="stock_code" label="股票代码" width="100" />
        <el-table-column prop="stock_name" label="股票名称" width="120">
          <template #default="scope">
            <div style="display: flex; align-items: center; gap: 4px;">
              <el-tag v-if="scope.row.is_leader" type="danger" size="small">龙头</el-tag>
              <span>{{ scope.row.stock_name }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="close_price" label="收盘价" width="80">
          <template #default="scope">
            {{ scope.row.close_price?.toFixed(2) }}
          </template>
        </el-table-column>
        <el-table-column prop="composite_score" label="综合评分" width="140" sortable="custom">
          <template #default="scope">
            <div class="score-cell">
              <el-tag :type="getScoreType(scope.row.composite_score || scope.row.latest_score)">
                {{ (scope.row.composite_score || scope.row.latest_score || 0).toFixed(0) }}
              </el-tag>
              <svg v-if="(scope.row.score_history && scope.row.score_history.length > 1) || (scope.row.price_history && scope.row.price_history.length > 1)" 
                   class="trend-chart" 
                   viewBox="0 0 60 20" 
                  >
                <polyline
                  v-if="scope.row.price_history && scope.row.price_history.length > 1"
                  :points="getPriceTrendPoints(scope.row.price_history)"
                  fill="none"
                  stroke="#409eff"
                  stroke-width="1.5"
                  opacity="0.6"
                />
                <polyline
                  v-if="scope.row.score_history && scope.row.score_history.length > 1"
                  :points="getTrendPoints(scope.row.score_history)"
                  fill="none"
                  :stroke="getTrendColor(scope.row.score_history)"
                  stroke-width="1.5"
                />
              </svg>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="latest_rating" label="评级" width="80">
          <template #default="scope">
            <el-tag :type="getRatingType(scope.row.latest_rating)" size="small">
              {{ scope.row.latest_rating }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="各维度评分" width="180">
          <el-table-column prop="technical_score" label="技术面" width="60" sortable="custom">
            <template #default="scope">
              <el-tooltip placement="top" :disabled="!getTechnicalDetail(scope.row)">
                <template #content>
                  <div class="tooltip-content" v-if="getTechnicalDetail(scope.row)">
                    <div v-for="(item, key) in getTechnicalDetail(scope.row)" :key="key" class="tooltip-item">
                      <strong>{{ getTechnicalLabel(key) }}:</strong> {{ item.score }}分 - {{ item.detail }}
                    </div>
                  </div>
                </template>
                <span :class="getScoreClass(scope.row.technical_score)">
                  {{ (scope.row.technical_score || 0).toFixed(0) }}
                </span>
              </el-tooltip>
            </template>
          </el-table-column>
          <el-table-column prop="fundamental_score" label="基本面" width="60" sortable="custom">
            <template #default="scope">
              <el-tooltip placement="top" :disabled="!getFundamentalDetail(scope.row)">
                <template #content>
                  <div class="tooltip-content" v-if="getFundamentalDetail(scope.row)">
                    <div v-for="(item, key) in getFundamentalDetail(scope.row)" :key="key" class="tooltip-item">
                      <strong>{{ getFundamentalLabel(key) }}:</strong> {{ item.score }}分 ({{ item.value }}) - {{ item.detail }}
                    </div>
                  </div>
                </template>
                <span :class="getScoreClass(scope.row.fundamental_score)">
                  {{ (scope.row.fundamental_score || 0).toFixed(0) }}
                </span>
              </el-tooltip>
            </template>
          </el-table-column>
          <el-table-column prop="news_score" label="消息面" width="60" sortable="custom">
            <template #default="scope">
              <el-tooltip placement="top" :disabled="!getNewsDetail(scope.row)">
                <template #content>
                  <div class="tooltip-content" v-if="getNewsDetail(scope.row)">
                    <div class="tooltip-item"><strong>消息面得分:</strong> {{ formatAdjustmentScore(scope.row.news_score || 0) }}</div>
                    <div v-for="(event, idx) in (getNewsDetail(scope.row).events || [])" :key="idx" class="tooltip-item">
                      [{{ event.date }}] {{ event.type }}: {{ event.title }} ({{ event.score_impact > 0 ? '+' : '' }}{{ event.score_impact }})
                    </div>
                  </div>
                </template>
                <span :class="getAdjustmentScoreClass(scope.row.news_score)">
                  {{ formatAdjustmentScore(scope.row.news_score || 0) }}
                </span>
              </el-tooltip>
            </template>
          </el-table-column>
          <el-table-column prop="policy_score" label="政策面" width="60" sortable="custom">
            <template #default="scope">
              <el-tooltip placement="top" :disabled="!getPolicyDetail(scope.row)">
                <template #content>
                  <div class="tooltip-content" v-if="getPolicyDetail(scope.row)">
                    <div class="tooltip-item"><strong>政策面得分:</strong> {{ formatAdjustmentScore(scope.row.policy_score || 0) }}</div>
                    <div v-for="(policy, idx) in (getPolicyDetail(scope.row).policies || [])" :key="idx" class="tooltip-item">
                      [{{ policy.level }}] {{ policy.title }} ({{ policy.score_impact > 0 ? '+' : '' }}{{ policy.score_impact }})
                    </div>
                  </div>
                </template>
                <span :class="getAdjustmentScoreClass(scope.row.policy_score)">
                  {{ formatAdjustmentScore(scope.row.policy_score || 0) }}
                </span>
              </el-tooltip>
            </template>
          </el-table-column>
          <el-table-column prop="deduction_score" label="扣分" width="50" sortable="custom">
            <template #default="scope">
              <el-tooltip placement="top" :disabled="!getDeductionDetail(scope.row)">
                <template #content>
                  <div class="tooltip-content" v-if="getDeductionDetail(scope.row)">
                    <div v-for="(item, idx) in (getDeductionDetail(scope.row).items || [])" :key="idx" class="tooltip-item">
                      <strong>{{ item.type }}:</strong> -{{ item.deduction }}分 - {{ item.detail }}
                    </div>
                    <div v-if="!(getDeductionDetail(scope.row).items || []).length" class="tooltip-item">
                      暂无明显风险项
                    </div>
                  </div>
                </template>
                <span :class="scope.row.deduction_score > 0 ? 'score-bad' : 'score-good'">
                  {{ (scope.row.deduction_score || 0).toFixed(0) }}
                </span>
              </el-tooltip>
            </template>
          </el-table-column>
        </el-table-column>
        <el-table-column prop="summary" label="综合评价" min-width="200">
          <template #default="scope">
            <div class="summary-text">{{ scope.row.summary || '-' }}</div>
          </template>
        </el-table-column>
        <el-table-column prop="create_time" label="最近打分时间" width="180">
          <template #default="scope">
            <span>{{ scope.row.create_time || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="scope">
            <div class="operation-buttons">
              <el-button size="small" type="primary" @click="viewDetail(scope.row)">
                查看详情
              </el-button>
              <el-button size="small" type="success" @click="createPlan(scope.row)">
                创建计划
              </el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>
      
      <!-- 分页 -->
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50, 100]"
          :total="filteredData.length"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>

    <!-- 批量评价进度对话框 -->
    <el-dialog 
      v-model="showProgressDialog" 
      title="批量评价进度" 
      width="500px" 
      :close-on-click-modal="false"
      :close-on-press-escape="false"
      :show-close="false"
    >
      <div style="text-align: center; padding: 20px;">
        <el-progress 
          :percentage="evaluateProgress.percentage" 
          :format="progressFormat"
          :stroke-width="20"
        />
        <p style="margin-top: 20px; font-size: 16px; color: #606266;">
          {{ evaluateProgress.current }} / {{ evaluateProgress.total }}
        </p>
        <p style="margin-top: 10px; font-size: 14px; color: #909399;">
          正在评价: {{ evaluateProgress.currentStock }}
        </p>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Refresh, Check } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { scoreApi } from '../api'
import api from '../api'

const router = useRouter()

const stockPool = ref([])
const loading = ref(false)
const searchText = ref('')
const ratingFilter = ref('')
const currentPage = ref(1)
const pageSize = ref(20)
const sortProp = ref('composite_score')
const sortOrder = ref('descending')
const selectedStocks = ref([])
const batchEvaluating = ref(false)
const showProgressDialog = ref(false)
const evaluateProgress = ref({
  current: 0,
  total: 0,
  percentage: 0,
  currentStock: ''
})

const filteredData = computed(() => {
  let data = [...stockPool.value]
  
  if (searchText.value) {
    const search = searchText.value.toLowerCase()
    data = data.filter(item => 
      item.stock_code?.toLowerCase().includes(search) ||
      item.stock_name?.toLowerCase().includes(search)
    )
  }
  
  if (ratingFilter.value) {
    data = data.filter(item => item.latest_rating === ratingFilter.value)
  }
  
  if (sortProp.value && sortOrder.value) {
    data.sort((a, b) => {
      const aVal = a[sortProp.value] || 0
      const bVal = b[sortProp.value] || 0
      return sortOrder.value === 'ascending' ? aVal - bVal : bVal - aVal
    })
  }
  
  return data
})

const paginatedData = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return filteredData.value.slice(start, end)
})

const ratingStats = computed(() => {
  const stats = {
    strongRecommended: 0,
    recommended: 0,
    neutral: 0,
    watch: 0,
    notRecommended: 0
  }
  stockPool.value.forEach(item => {
    if (item.latest_rating === '强烈推荐') {
      stats.strongRecommended++
    } else if (item.latest_rating === '推荐') {
      stats.recommended++
    } else if (item.latest_rating === '中性') {
      stats.neutral++
    } else if (item.latest_rating === '观望') {
      stats.watch++
    } else if (item.latest_rating === '不推荐') {
      stats.notRecommended++
    }
  })
  return stats
})

const getScoreType = (score) => {
  if (score >= 90) return 'success'
  if (score >= 70) return 'primary'
  if (score >= 50) return 'warning'
  return 'info'
}

const getTrendPoints = (history) => {
  if (!history || history.length < 2) return ''
  
  const scores = history.map(h => h.score || 0)
  const minScore = Math.min(...scores)
  const maxScore = Math.max(...scores)
  const range = maxScore - minScore || 1
  
  const width = 60
  const height = 20
  const padding = 2
  
  const points = scores.map((score, index) => {
    const x = padding + (index / (scores.length - 1)) * (width - 2 * padding)
    const y = height - padding - ((score - minScore) / range) * (height - 2 * padding)
    return `${x.toFixed(1)},${y.toFixed(1)}`
  })
  
  return points.join(' ')
}

const getTrendColor = (history) => {
  if (!history || history.length < 2) return '#909399'
  
  const firstScore = history[0].score || 0
  const lastScore = history[history.length - 1].score || 0
  
  if (lastScore > firstScore) return '#67c23a'
  if (lastScore < firstScore) return '#f56c6c'
  return '#909399'
}

const getPriceTrendPoints = (history) => {
  if (!history || history.length < 2) return ''
  
  const prices = history.map(h => h.price || 0)
  const minPrice = Math.min(...prices)
  const maxPrice = Math.max(...prices)
  const range = maxPrice - minPrice || 1
  
  const width = 60
  const height = 20
  const padding = 2
  
  const points = prices.map((price, index) => {
    const x = padding + (index / (prices.length - 1)) * (width - 2 * padding)
    const y = height - padding - ((price - minPrice) / range) * (height - 2 * padding)
    return `${x.toFixed(1)},${y.toFixed(1)}`
  })
  
  return points.join(' ')
}

const getScoreClass = (score) => {
  if (score >= 70) return 'score-good'
  if (score >= 50) return 'score-normal'
  return 'score-bad'
}

const getAdjustmentScoreClass = (score) => {
  if (score > 0) return 'score-good'
  if (score < 0) return 'score-bad'
  return 'score-normal'
}

const formatAdjustmentScore = (score) => {
  if (score > 0) return `+${score.toFixed(0)}`
  if (score < 0) return score.toFixed(0)
  return '0'
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

const getTechnicalLabel = (key) => {
  const labels = {
    'ma': '均线系统',
    'volume': '成交量',
    'trend': '趋势指标',
    'fund': '资金指标',
    'bollinger': '布林线'
  }
  return labels[key] || key
}

const getFundamentalLabel = (key) => {
  const labels = {
    'pe': '市盈率PE',
    'pb': '市净率PB',
    'net_profit_growth': '净利润增长率',
    'revenue_growth': '营收增长率',
    'roe': 'ROE',
    'debt_ratio': '负债率'
  }
  return labels[key] || key
}

const parseDetail = (detail) => {
  if (!detail) return null
  try {
    return typeof detail === 'string' ? JSON.parse(detail) : detail
  } catch (e) {
    return null
  }
}

const getTechnicalDetail = (row) => parseDetail(row.technical_detail)
const getFundamentalDetail = (row) => parseDetail(row.fundamental_detail)
const getNewsDetail = (row) => parseDetail(row.news_detail)
const getPolicyDetail = (row) => parseDetail(row.policy_detail)
const getDeductionDetail = (row) => parseDetail(row.deduction_detail)

const handleSortChange = ({ prop, order }) => {
  sortProp.value = prop
  sortOrder.value = order
}

const filterByRating = (rating) => {
  if (ratingFilter.value === rating) {
    ratingFilter.value = ''
  } else {
    ratingFilter.value = rating
  }
}

const handleSizeChange = (val) => {
  pageSize.value = val
  currentPage.value = 1
}

const handleCurrentChange = (val) => {
  currentPage.value = val
}

const loadStockPool = async () => {
  loading.value = true
  try {
    const data = await scoreApi.getStockPoolScores()
    stockPool.value = data.stocks || []
  } catch (error) {
    console.error('加载股票池失败:', error)
    ElMessage.error('加载股票池失败')
  } finally {
    loading.value = false
  }
}

const refreshPool = () => {
  ElMessage.success('正在刷新股票池...')
  loadStockPool()
}

const handleSelectionChange = (selection) => {
  selectedStocks.value = selection
}

const batchEvaluate = async () => {
  if (selectedStocks.value.length === 0) {
    ElMessage.warning('请先选择要评价的股票')
    return
  }
  
  batchEvaluating.value = true
  showProgressDialog.value = true
  const stocks = selectedStocks.value
  const total = stocks.length
  
  evaluateProgress.value = {
    current: 0,
    total: total,
    percentage: 0,
    currentStock: ''
  }
  
  let successCount = 0
  let failCount = 0
  
  for (let i = 0; i < stocks.length; i++) {
    const stock = stocks[i]
    evaluateProgress.value.current = i + 1
    evaluateProgress.value.percentage = Math.round(((i + 1) / total) * 100)
    evaluateProgress.value.currentStock = `${stock.stock_name} (${stock.stock_code})`
    
    try {
      await api.post('/stocks/evaluate', {
        stock_code: stock.stock_code
      }, { timeout: 120000 })
      successCount++
    } catch (error) {
      console.error(`评价 ${stock.stock_code} 失败:`, error)
      failCount++
    }
  }
  
  showProgressDialog.value = false
  batchEvaluating.value = false
  
  if (successCount > 0) {
    ElMessage.success(`批量评价完成！成功: ${successCount}, 失败: ${failCount}`)
  } else {
    ElMessage.error(`批量评价失败，请检查后端服务`)
  }
  selectedStocks.value = []
  loadStockPool()
}

const progressFormat = (percentage) => {
  return `${percentage}%`
}

const viewDetail = (row) => {
  router.push({
    path: '/score-detail',
    query: { stock_code: row.stock_code, stock_name: row.stock_name }
  })
}

const createPlan = (row) => {
  router.push({
    path: '/trade-plan',
    query: { 
      stock_code: row.stock_code, 
      stock_name: row.stock_name,
      close_price: row.close_price
    }
  })
}

onMounted(() => {
  loadStockPool()
})
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.search-bar {
  display: flex;
  align-items: center;
}

.stat-card {
  text-align: center;
  padding: 10px;
}

.stat-card .stat-title {
  font-size: 12px;
  color: #909399;
  margin-bottom: 5px;
}

.stat-card .stat-value {
  font-size: 24px;
  font-weight: bold;
  color: #303133;
}

.stat-card.stat-success .stat-value {
  color: #67c23a;
}

.stat-card.stat-primary .stat-value {
  color: #409eff;
}

.stat-card.stat-warning .stat-value {
  color: #e6a23c;
}

.stat-card.stat-info .stat-value {
  color: #909399;
}

.stat-card.stat-danger .stat-value {
  color: #f56c6c;
}

.stat-card.clickable {
  cursor: pointer;
  transition: all 0.3s ease;
}

.stat-card.clickable:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.stat-card.clickable.active {
  box-shadow: 0 0 0 2px #409eff;
}

.score-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}

.trend-chart {
  width: 60px;
  height: 20px;
  flex-shrink: 0;
}

.score-dimensions {
  display: flex;
  gap: 6px;
}

.score-dimensions span {
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 11px;
  cursor: pointer;
}

.score-good {
  background-color: #f0f9eb;
  color: #67c23a;
}

.score-normal {
  background-color: #fdf6ec;
  color: #e6a23c;
}

.score-bad {
  background-color: #fef0f0;
  color: #f56c6c;
}

.tooltip-content {
  max-width: 400px;
}

.tooltip-item {
  padding: 4px 0;
  border-bottom: 1px dashed #e4e7ed;
  font-size: 12px;
  line-height: 1.5;
}

.tooltip-item:last-child {
  border-bottom: none;
}

.summary-text {
  font-size: 12px;
  color: #606266;
  line-height: 1.5;
  white-space: normal;
  word-break: break-all;
}

.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

.operation-buttons {
  display: flex;
  flex-wrap: nowrap;
  gap: 4px;
}

.operation-buttons .el-button {
  white-space: nowrap;
}
</style>
