<template>
  <div class="sell-analysis">
    <el-card class="summary-card">
      <template #header>
        <div class="card-header">
          <span>卖出决策分析汇总</span>
          <el-button type="primary" @click="loadData" :loading="loading">
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
        </div>
      </template>
      
      <el-row :gutter="20" v-if="summary">
        <el-col :span="4">
          <el-statistic title="卖出总次数" :value="summary.total_count" />
        </el-col>
        <el-col :span="4">
          <el-statistic title="卖早了" :value="summary.sell_too_early">
            <template #suffix>
              <span style="color: #f56c6c;">次</span>
            </template>
          </el-statistic>
        </el-col>
        <el-col :span="4">
          <el-statistic title="卖对了" :value="summary.sell_correct">
            <template #suffix>
              <span style="color: #67c23a;">次</span>
            </template>
          </el-statistic>
        </el-col>
        <el-col :span="3">
          <el-statistic title="1周后平均" :value="summary.avg_change_1w" :precision="2">
            <template #suffix>
              <span :style="{ color: summary.avg_change_1w >= 0 ? '#f56c6c' : '#67c23a' }">%</span>
            </template>
          </el-statistic>
        </el-col>
        <el-col :span="3">
          <el-statistic title="2周后平均" :value="summary.avg_change_2w" :precision="2">
            <template #suffix>
              <span :style="{ color: summary.avg_change_2w >= 0 ? '#f56c6c' : '#67c23a' }">%</span>
            </template>
          </el-statistic>
        </el-col>
        <el-col :span="3">
          <el-statistic title="3周后平均" :value="summary.avg_change_3w" :precision="2">
            <template #suffix>
              <span :style="{ color: summary.avg_change_3w >= 0 ? '#f56c6c' : '#67c23a' }">%</span>
            </template>
          </el-statistic>
        </el-col>
        <el-col :span="3">
          <el-statistic title="4周后平均" :value="summary.avg_change_4w" :precision="2">
            <template #suffix>
              <span :style="{ color: summary.avg_change_4w >= 0 ? '#f56c6c' : '#67c23a' }">%</span>
            </template>
          </el-statistic>
        </el-col>
      </el-row>
    </el-card>

    <el-card class="table-card">
      <template #header>
        <span>卖出记录详情</span>
      </template>
      
      <el-table :data="records" v-loading="loading" style="width: 100%" height="500" stripe border>
        <el-table-column prop="stock_code" label="股票代码" width="100" fixed />
        <el-table-column prop="stock_name" label="股票名称" width="100" />
        <el-table-column prop="sell_date" label="卖出日期" width="110" />
        <el-table-column prop="sell_price" label="卖出价格" width="100">
          <template #default="scope">
            {{ scope.row.sell_price?.toFixed(2) }}
          </template>
        </el-table-column>
        <el-table-column prop="sell_quantity" label="卖出数量" width="90" />
        
        <el-table-column label="1周后" width="120">
          <template #default="scope">
            <div v-if="scope.row.price_1w">
              <div>{{ scope.row.price_1w.toFixed(2) }}</div>
              <div :style="{ color: scope.row.change_1w >= 0 ? '#f56c6c' : '#67c23a', fontSize: '12px' }">
                {{ scope.row.change_1w >= 0 ? '+' : '' }}{{ scope.row.change_1w }}%
              </div>
            </div>
            <span v-else>-</span>
          </template>
        </el-table-column>
        
        <el-table-column label="2周后" width="120">
          <template #default="scope">
            <div v-if="scope.row.price_2w">
              <div>{{ scope.row.price_2w.toFixed(2) }}</div>
              <div :style="{ color: scope.row.change_2w >= 0 ? '#f56c6c' : '#67c23a', fontSize: '12px' }">
                {{ scope.row.change_2w >= 0 ? '+' : '' }}{{ scope.row.change_2w }}%
              </div>
            </div>
            <span v-else>-</span>
          </template>
        </el-table-column>
        
        <el-table-column label="3周后" width="120">
          <template #default="scope">
            <div v-if="scope.row.price_3w">
              <div>{{ scope.row.price_3w.toFixed(2) }}</div>
              <div :style="{ color: scope.row.change_3w >= 0 ? '#f56c6c' : '#67c23a', fontSize: '12px' }">
                {{ scope.row.change_3w >= 0 ? '+' : '' }}{{ scope.row.change_3w }}%
              </div>
            </div>
            <span v-else>-</span>
          </template>
        </el-table-column>
        
        <el-table-column label="4周后" width="120">
          <template #default="scope">
            <div v-if="scope.row.price_4w">
              <div>{{ scope.row.price_4w.toFixed(2) }}</div>
              <div :style="{ color: scope.row.change_4w >= 0 ? '#f56c6c' : '#67c23a', fontSize: '12px' }">
                {{ scope.row.change_4w >= 0 ? '+' : '' }}{{ scope.row.change_4w }}%
              </div>
            </div>
            <span v-else>-</span>
          </template>
        </el-table-column>
        
        <el-table-column label="判断结果" width="100">
          <template #default="scope">
            <el-tag v-if="scope.row.status === 'sell_too_early'" type="danger">
              卖早了
            </el-tag>
            <el-tag v-else-if="scope.row.status === 'sell_correct'" type="success">
              卖对了
            </el-tag>
            <el-tag v-else-if="scope.row.status === 'no_data'" type="warning">
              数据不完整
            </el-tag>
            <el-tag v-else-if="scope.row.status === 'invalid_date'" type="info">
              日期无效
            </el-tag>
            <span v-else>-</span>
          </template>
        </el-table-column>
        
        <el-table-column label="操作" width="80" fixed="right">
          <template #default="scope">
            <el-button type="primary" size="small" @click="viewIndicator(scope.row.stock_code)">
              指标
            </el-button>
          </template>
        </el-table-column>
      </el-table>
      
      <el-empty v-if="!loading && records.length === 0" description="暂无卖出记录" />
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { Refresh } from '@element-plus/icons-vue'
import { tradeApi } from '../api'
import { ElMessage } from 'element-plus'

const loading = ref(false)
const records = ref([])
const summary = ref(null)

const loadData = async () => {
  loading.value = true
  try {
    const response = await tradeApi.getSellAnalysis()
    if (response.success) {
      records.value = response.records || []
      summary.value = response.summary || null
    } else {
      ElMessage.error('获取数据失败')
    }
  } catch (error) {
    console.error('获取卖出分析数据失败:', error)
    ElMessage.error('获取数据失败')
  } finally {
    loading.value = false
  }
}

const viewIndicator = (stockCode) => {
  const url = `http://www.iwencai.com/unifiedwap/result?w=${stockCode}`
  const width = 1200
  const height = 800
  const left = (window.screen.width - width) / 2
  const top = (window.screen.height - height) / 2
  window.open(url, 'stockIndicator', `width=${width},height=${height},left=${left},top=${top},resizable=yes,scrollbars=yes`)
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.sell-analysis {
  padding: 20px;
}

.summary-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.table-card {
  margin-top: 20px;
}

:deep(.el-statistic__content) {
  font-size: 24px;
}

:deep(.el-statistic__title) {
  font-size: 14px;
  color: #909399;
}
</style>
