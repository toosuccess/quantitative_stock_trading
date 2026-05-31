<template>
  <div class="review-page">
    <el-row :gutter="20">
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-title">交易胜率</div>
          <div class="stat-value">{{ stats.winRate.toFixed(1) }}%</div>
          <el-progress :percentage="stats.winRate" :color="'#67c23a'" />
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-title">盈亏比</div>
          <div class="stat-value">{{ stats.profitLossRatio.toFixed(2) }}</div>
          <div class="stat-desc">平均盈利/平均亏损</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-title">最大回撤</div>
          <div class="stat-value loss">{{ stats.maxDrawdown.toFixed(1) }}%</div>
          <div class="stat-desc">历史最大回撤</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-title">总交易次数</div>
          <div class="stat-value">{{ stats.totalTrades }}</div>
          <div class="stat-desc">盈利{{ stats.winTrades }}次 / 亏损{{ stats.lossTrades }}次</div>
        </el-card>
      </el-col>
    </el-row>

    <el-card style="margin-top: 20px;">
      <template #header>
        <div class="card-header">
          <span>交易记录层级</span>
          <el-select v-model="selectedAccountId" placeholder="全部账号" clearable style="width: 200px" @change="loadData">
            <el-option 
              v-for="account in accountList" 
              :key="account.account_id" 
              :label="account.account_name" 
              :value="account.account_id" 
            />
          </el-select>
        </div>
      </template>
      
      <el-collapse v-model="activeAccounts" v-loading="loading">
        <el-collapse-item 
          v-for="account in accountData" 
          :key="account.account_id"
          :name="account.account_id"
        >
          <template #title>
            <div class="account-title">
              <span class="account-name">{{ account.account_name }}</span>
              <span class="account-info">
                总资产: {{ (account.total_assets || 0).toFixed(2) }} | 
                盈亏: <span :class="account.profit_loss >= 0 ? 'profit' : 'loss'">
                  {{ account.profit_loss >= 0 ? '+' : '' }}{{ (account.profit_loss || 0).toFixed(2) }}
                </span> |
                计划数: {{ account.plans?.length || 0 }}
              </span>
            </div>
          </template>
          
          <el-collapse v-model="activePlans" class="plan-collapse">
            <el-collapse-item 
              v-for="plan in account.plans" 
              :key="plan.plan_id"
              :name="plan.plan_id"
            >
              <template #title>
                <div class="plan-title">
                  <span class="plan-name">{{ plan.plan_name }}</span>
                  <span class="plan-info">
                    {{ plan.stock_name }} ({{ plan.stock_code }}) |
                    盈亏: <span :class="plan.profit >= 0 ? 'profit' : 'loss'">
                      {{ plan.profit >= 0 ? '+' : '' }}{{ (plan.profit || 0).toFixed(2) }}
                    </span> |
                    状态: <el-tag :type="getStatusType(plan.status)" size="small">{{ getStatusName(plan.status) }}</el-tag>
                  </span>
                </div>
              </template>
              
              <el-table :data="plan.records" size="small" style="width: 100%">
                <el-table-column prop="trade_type" label="类型" width="60">
                  <template #default="scope">
                    <el-tag :type="scope.row.trade_type === '买入' ? 'success' : 'danger'" size="small">
                      {{ scope.row.trade_type }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="trade_direction" label="方向" width="80">
                  <template #default="scope">
                    <el-tag :type="getDirectionType(scope.row.trade_direction)" size="small">
                      {{ scope.row.trade_direction }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="trade_price" label="价格" width="80">
                  <template #default="scope">
                    {{ scope.row.trade_price?.toFixed(2) }}
                  </template>
                </el-table-column>
                <el-table-column prop="trade_quantity" label="数量" width="80" />
                <el-table-column prop="trade_amount" label="金额" width="100">
                  <template #default="scope">
                    {{ scope.row.trade_amount?.toFixed(2) }}
                  </template>
                </el-table-column>
                <el-table-column prop="trade_date" label="日期" width="100" />
                <el-table-column prop="trade_time" label="时间" width="80" />
                <el-table-column label="操作" width="180">
                  <template #default="scope">
                    <el-button size="small" type="primary" @click="viewStockIndicator(scope.row.stock_code)">
                      指标
                    </el-button>
                    <el-button size="small" type="primary" link @click="viewDetail(scope.row)">
                      详情
                    </el-button>
                  </template>
                </el-table-column>
              </el-table>
            </el-collapse-item>
          </el-collapse>
        </el-collapse-item>
      </el-collapse>
    </el-card>

    <el-dialog v-model="detailDialogVisible" title="交易详情" width="500px">
      <el-descriptions :column="2" border>
        <el-descriptions-item label="记录编号">{{ currentRecord.record_id }}</el-descriptions-item>
        <el-descriptions-item label="股票">{{ currentRecord.stock_name }} ({{ currentRecord.stock_code }})</el-descriptions-item>
        <el-descriptions-item label="交易类型">{{ currentRecord.trade_type }}</el-descriptions-item>
        <el-descriptions-item label="交易方向">{{ currentRecord.trade_direction }}</el-descriptions-item>
        <el-descriptions-item label="成交价格">{{ currentRecord.trade_price?.toFixed(2) }}</el-descriptions-item>
        <el-descriptions-item label="成交数量">{{ currentRecord.trade_quantity }}</el-descriptions-item>
        <el-descriptions-item label="成交金额">{{ currentRecord.trade_amount?.toFixed(2) }}</el-descriptions-item>
        <el-descriptions-item label="交易日期">{{ currentRecord.trade_date }}</el-descriptions-item>
        <el-descriptions-item label="交易时间">{{ currentRecord.trade_time }}</el-descriptions-item>
        <el-descriptions-item label="计划编号">{{ currentRecord.plan_id || '-' }}</el-descriptions-item>
      </el-descriptions>
      <template #footer>
        <el-button type="primary" @click="detailDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { accountApi, planApi, tradeApi } from '../api'

const loading = ref(false)
const detailDialogVisible = ref(false)
const currentRecord = ref({})
const selectedAccountId = ref('')
const activeAccounts = ref([])
const activePlans = ref([])

const accountList = ref([])
const accountData = ref([])

const stats = ref({
  winRate: 0,
  profitLossRatio: 0,
  maxDrawdown: 0,
  totalTrades: 0,
  winTrades: 0,
  lossTrades: 0
})

const getStatusType = (status) => {
  const types = {
    'pending': 'info',
    'executing': 'warning',
    'completed': 'success',
    'cancelled': 'danger'
  }
  return types[status] || 'info'
}

const getStatusName = (status) => {
  const names = {
    'pending': '待执行',
    'executing': '执行中',
    'completed': '已完成',
    'cancelled': '已取消'
  }
  return names[status] || status
}

const getDirectionType = (direction) => {
  const types = {
    '建仓': 'success',
    '加仓': 'primary',
    '减仓': 'warning',
    '清仓': 'danger'
  }
  return types[direction] || 'info'
}

const viewDetail = (row) => {
  currentRecord.value = row
  detailDialogVisible.value = true
}

const viewStockIndicator = (stockCode) => {
  // 跳转到同花顺问财，查看股票技术指标（弹出窗口居中显示）
  const url = `http://www.iwencai.com/unifiedwap/result?w=${stockCode}`
  const width = 1200
  const height = 800
  const left = (window.screen.width - width) / 2
  const top = (window.screen.height - height) / 2
  window.open(url, 'stockIndicator', `width=${width},height=${height},left=${left},top=${top},scrollbars=yes,toolbar=no,resizable=yes`)
}

const loadAccountList = async () => {
  try {
    const data = await accountApi.getAccountList()
    accountList.value = data.accounts || []
  } catch (error) {
    console.error('加载账号列表失败:', error)
  }
}

const loadData = async () => {
  loading.value = true
  try {
    const plansData = await planApi.getPlanList(selectedAccountId.value || null)
    const plans = plansData.plans || []
    
    const recordsData = await tradeApi.getTradeRecords(selectedAccountId.value || null)
    const records = recordsData.records || []
    
    const accountMap = {}
    accountList.value.forEach(acc => {
      accountMap[acc.account_id] = {
        ...acc,
        plans: []
      }
    })
    
    const planMap = {}
    plans.forEach(plan => {
      planMap[plan.plan_id] = {
        ...plan,
        records: []
      }
      
      if (accountMap[plan.account_id]) {
        accountMap[plan.account_id].plans.push(planMap[plan.plan_id])
      }
    })
    
    records.forEach(record => {
      if (record.plan_id && planMap[record.plan_id]) {
        planMap[record.plan_id].records.push(record)
      }
    })
    
    accountData.value = Object.values(accountMap).filter(acc => acc.plans.length > 0)
    
    let totalWin = 0
    let totalLoss = 0
    let winCount = 0
    let lossCount = 0
    let totalProfit = 0
    let totalLossAmount = 0
    
    plans.forEach(plan => {
      if (plan.profit > 0) {
        winCount++
        totalProfit += plan.profit
      } else if (plan.profit < 0) {
        lossCount++
        totalLossAmount += Math.abs(plan.profit)
      }
    })
    
    const totalTrades = winCount + lossCount
    stats.value = {
      winRate: totalTrades > 0 ? (winCount / totalTrades * 100) : 0,
      profitLossRatio: lossCount > 0 ? (totalProfit / winCount) / (totalLossAmount / lossCount) : 0,
      maxDrawdown: 0,
      totalTrades: totalTrades,
      winTrades: winCount,
      lossTrades: lossCount
    }
    
    if (selectedAccountId.value) {
      try {
        const summaryData = await accountApi.getAccountSummary(selectedAccountId.value)
        if (summaryData.win_rate) {
          stats.value.winRate = summaryData.win_rate.win_rate || 0
          stats.value.winTrades = summaryData.win_rate.win_count || 0
          stats.value.lossTrades = summaryData.win_rate.loss_count || 0
          stats.value.totalTrades = stats.value.winTrades + stats.value.lossTrades
        }
        if (summaryData.profit_loss_ratio) {
          stats.value.profitLossRatio = summaryData.profit_loss_ratio.ratio || 0
        }
        if (summaryData.max_drawdown) {
          stats.value.maxDrawdown = summaryData.max_drawdown.max_drawdown_rate || 0
        }
      } catch (error) {
        console.log('获取账号汇总失败')
      }
    }
  } catch (error) {
    console.error('加载数据失败:', error)
    ElMessage.error('加载数据失败')
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  await loadAccountList()
  loadData()
})
</script>

<style scoped>
.stat-card {
  text-align: center;
  padding: 20px;
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

.stat-value.loss {
  color: #f56c6c;
}

.stat-desc {
  font-size: 12px;
  color: #c0c4cc;
  margin-top: 10px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.account-title {
  display: flex;
  align-items: center;
  gap: 20px;
}

.account-name {
  font-weight: bold;
  font-size: 16px;
}

.account-info {
  color: #909399;
  font-size: 14px;
}

.plan-collapse {
  margin-left: 20px;
}

.plan-title {
  display: flex;
  align-items: center;
  gap: 15px;
}

.plan-name {
  font-weight: 500;
}

.plan-info {
  color: #909399;
  font-size: 13px;
}

.profit {
  color: #f56c6c; /* 盈利红色 */
  font-weight: bold;
}

.loss {
  color: #67c23a; /* 亏损绿色 */
  font-weight: bold;
}
</style>
