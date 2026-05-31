<template>
  <div class="trade-plan-page">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>交易计划管理</span>
        </div>
      </template>
      
      <el-form :inline="true" class="filter-form">
        <el-form-item label="证券账号">
          <el-select v-model="filterAccountId" placeholder="全部账号" clearable style="width: 200px" @change="loadPlanList">
            <el-option 
              v-for="account in accountList" 
              :key="account.account_id" 
              :label="account.account_name" 
              :value="account.account_id" 
            />
          </el-select>
        </el-form-item>
        <el-form-item label="股票">
          <el-input 
            v-model="filterStock" 
            placeholder="股票代码/名称" 
            clearable 
            style="width: 150px" 
            @input="loadPlanList"
          />
        </el-form-item>
        <el-form-item label="状态">
          <div class="status-filter-group">
            <span
              class="status-filter-item"
              :class="{ active: filterStatus === '' }"
              @click="changeStatus('')"
            >
              全部
            </span>
            <span
              class="status-filter-item"
              :class="{ active: filterStatus === 'pending' }"
              @click="changeStatus('pending')"
            >
              待执行
            </span>
            <span
              class="status-filter-item"
              :class="{ active: filterStatus === 'executing' }"
              @click="changeStatus('executing')"
            >
              执行中
            </span>
            <span
              class="status-filter-item"
              :class="{ active: filterStatus === 'completed' }"
              @click="changeStatus('completed')"
            >
              已完成
            </span>
            <span
              class="status-filter-item"
              :class="{ active: filterStatus === 'cancelled' }"
              @click="changeStatus('cancelled')"
            >
              已取消
            </span>
          </div>
        </el-form-item>
      </el-form>
      
      <el-table :data="planList" style="width: 100%" v-loading="loading">
        <el-table-column prop="stock_code" label="股票代码" width="100" />
        <el-table-column prop="stock_name" label="股票名称" width="100" />
        <el-table-column prop="planned_quantity" label="计划股数" width="100" />
        <el-table-column prop="remaining_quantity" label="剩余股数" width="100">
          <template #default="scope">
            {{ scope.row.remaining_quantity || scope.row.planned_quantity || 0 }}
          </template>
        </el-table-column>
        <el-table-column prop="holding_quantity" label="持仓股数" width="100">
          <template #default="scope">
            {{ scope.row.holding_quantity || 0 }}
          </template>
        </el-table-column>
        <el-table-column prop="holding_amount" label="持仓金额" width="120">
          <template #default="scope">
            {{ (scope.row.holding_amount || 0).toFixed(2) }}
          </template>
        </el-table-column>
        <el-table-column prop="avg_cost_price" label="买入价格" width="100">
          <template #default="scope">
            <span>{{ (scope.row.avg_cost_price || 0).toFixed(2) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="current_price" label="当前价格" width="100">
          <template #default="scope">
            <span>{{ (scope.row.current_price > 0 ? scope.row.current_price : (scope.row.avg_cost_price || 0)).toFixed(2) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="profit_rate" label="涨跌幅" width="100">
          <template #default="scope">
            <span :class="(scope.row.profit_rate || 0) >= 0 ? 'profit' : 'loss'">
              {{ (scope.row.profit_rate || 0) >= 0 ? '+' : '' }}{{ (scope.row.profit_rate || 0).toFixed(2) }}%
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="profit" label="盈利情况" width="120">
          <template #default="scope">
            <span :class="scope.row.profit >= 0 ? 'profit' : 'loss'">
              {{ scope.row.profit >= 0 ? '+' : '' }}{{ (scope.row.profit || 0).toFixed(2) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="scope">
            <el-tag :type="getStatusType(scope.row.status)">
              {{ getStatusName(scope.row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="plan_date" label="计划日期" width="120" />
        <el-table-column prop="plan_id" label="计划编号" width="150" />
        <el-table-column prop="account_name" label="证券账号" width="120">
          <template #default="scope">
            {{ getAccountName(scope.row.account_id) }}
          </template>
        </el-table-column>
        <el-table-column prop="plan_name" label="计划名称" width="180" />
        <el-table-column label="操作" width="300" fixed="right">
          <template #default="scope">
            <el-button 
              size="small" 
              type="primary" 
              @click="viewStockIndicator(scope.row.stock_code)"
            >
              指标
            </el-button>
            <el-button 
              size="small" 
              type="primary" 
              @click="editPlan(scope.row)"
              :disabled="scope.row.status === 'executing'"
            >
              编辑
            </el-button>
            <el-button 
              v-if="scope.row.status === 'pending'"
              size="small" 
              type="success" 
              @click="executePlan(scope.row)"
            >
              执行
            </el-button>
            <el-button 
              v-if="scope.row.status === 'executing' || scope.row.status === 'completed'"
              size="small" 
              type="warning" 
              @click="viewExecution(scope.row)"
            >
              查看
            </el-button>
            <el-button 
              size="small" 
              type="danger" 
              @click="deletePlan(scope.row)"
              :disabled="scope.row.status === 'executing'"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
      
      <div class="summary-row" v-if="planList.length > 0">
        <span class="summary-label">合计:</span>
        <span class="summary-item">持仓金额: <strong>{{ totalHoldingAmount.toFixed(2) }}</strong> 元</span>
        <span class="summary-item">总盈亏: <strong :class="totalProfit >= 0 ? 'profit' : 'loss'">{{ totalProfit >= 0 ? '+' : '' }}{{ totalProfit.toFixed(2) }}</strong> 元</span>
      </div>
      
      <div class="position-rules" v-if="planList.length > 0">
        <div class="rules-title">📋 仓位配置建议</div>
        <div class="rules-content">
          <div class="rule-item">
            <span class="rule-label">现金比例:</span>
            <span class="rule-value">30%-40%（防御性底仓）</span>
          </div>
          <div class="rule-item">
            <span class="rule-label">股票仓位:</span>
            <span class="rule-value">60%-70%（进攻性仓位）</span>
          </div>
          <div class="rule-item">
            <span class="rule-label">持仓数量:</span>
            <span class="rule-value">3-5只（避免过度分散）</span>
          </div>
          <div class="rule-item">
            <span class="rule-label">单只上限:</span>
            <span class="rule-value">20%-25%（防止一损俱损）</span>
          </div>
          <div class="rule-item">
            <span class="rule-label">止损线:</span>
            <span class="rule-value loss">-10%（无条件止损）</span>
          </div>
          <div class="rule-item">
            <span class="rule-label">止盈线:</span>
            <span class="rule-value profit">+20%（分批止盈）</span>
          </div>
        </div>
      </div>
    </el-card>

    <el-dialog v-model="dialogVisible" title="新建交易计划" width="650px">
      <div class="dialog-rules">
        <div class="rules-title">📋 仓位配置建议</div>
        <div class="rules-content">
          <div class="rule-item">
            <span class="rule-label">现金比例:</span>
            <span class="rule-value">30%-40%</span>
          </div>
          <div class="rule-item">
            <span class="rule-label">股票仓位:</span>
            <span class="rule-value">60%-70%</span>
          </div>
          <div class="rule-item">
            <span class="rule-label">持仓数量:</span>
            <span class="rule-value">3-5只</span>
          </div>
          <div class="rule-item">
            <span class="rule-label">单只上限:</span>
            <span class="rule-value">20%-25%</span>
          </div>
          <div class="rule-item">
            <span class="rule-label">止损:</span>
            <span class="rule-value loss">-10%</span>
          </div>
          <div class="rule-item">
            <span class="rule-label">止盈:</span>
            <span class="rule-value profit">+20%</span>
          </div>
        </div>
      </div>
      <el-form :model="planForm" label-width="100px">
        <el-form-item label="证券账号">
          <el-select v-model="planForm.account_id" placeholder="请选择证券账号" style="width: 100%">
            <el-option 
              v-for="account in accountList" 
              :key="account.account_id" 
              :label="account.account_name" 
              :value="account.account_id" 
            />
          </el-select>
        </el-form-item>
        <el-form-item label="可用金额">
          <div class="amount-info">
            <span class="amount-value">💰 {{ availableAmount.toFixed(2) }} 元</span>
            <span class="amount-tip">（建议投入: {{ (availableAmount * 0.7).toFixed(2) }} 元，保留30%现金）</span>
          </div>
        </el-form-item>
        <el-form-item label="股票代码">
          <el-input v-model="planForm.stock_code" placeholder="请输入股票代码" @blur="fetchCurrentPrice" />
        </el-form-item>
        <el-form-item label="股票名称">
          <el-input v-model="planForm.stock_name" placeholder="请输入股票名称" />
        </el-form-item>
        <el-form-item label="当前价格">
          <div style="display: flex; align-items: center; gap: 10px;">
            <el-input-number v-model="planForm.current_price" :precision="2" :step="0.1" @change="calculatePrices" style="flex: 1;" />
            <el-button type="primary" :loading="priceLoading" @click="fetchCurrentPrice">
              刷新价格
            </el-button>
          </div>
        </el-form-item>
        <el-form-item label="可买股数">
          <div class="buyable-info">
            <span class="buyable-value">📊 最多可买: <strong>{{ maxBuyableShares }}</strong> 股</span>
            <span class="buyable-tip">（单只上限: 建议投入金额的25% = {{ maxBuyableAmount.toFixed(2) }} 元）</span>
            <el-button type="success" size="small" @click="planForm.planned_quantity = maxBuyableShares" :disabled="maxBuyableShares <= 0">
              一键填入
            </el-button>
          </div>
        </el-form-item>
        <el-form-item label="计划数量">
          <el-input-number v-model="planForm.planned_quantity" :min="0" :step="100" />
        </el-form-item>
        <el-form-item label="止损比例(%)">
          <el-input-number v-model="planForm.stop_loss_rate" :min="0" :max="50" :step="1" @change="calculatePrices" />
        </el-form-item>
        <el-form-item label="止损价格">
          <el-input-number v-model="planForm.stop_loss_price" :precision="2" :step="0.1" />
        </el-form-item>
        <el-form-item label="止盈比例(%)">
          <el-input-number v-model="planForm.take_profit_rate" :min="0" :max="100" :step="1" @change="calculatePrices" />
        </el-form-item>
        <el-form-item label="止盈价格">
          <el-input-number v-model="planForm.take_profit_price" :precision="2" :step="0.1" />
        </el-form-item>
        <el-form-item label="购买原因">
          <el-input v-model="planForm.remark" type="textarea" :rows="3" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="savePlan">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Plus } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { planApi, stockApi, accountApi } from '../api'

const route = useRoute()
const router = useRouter()
const dialogVisible = ref(false)
const loading = ref(false)
const priceLoading = ref(false)

const planList = ref([])
const accountList = ref([])
const filterAccountId = ref('')
const filterStock = ref('')
const filterStatus = ref('')

const changeStatus = (status) => {
  filterStatus.value = status
  loadPlanList()
}

const totalHoldingAmount = computed(() => {
  return planList.value.reduce((sum, item) => sum + (item.holding_amount || 0), 0)
})

const totalProfit = computed(() => {
  return planList.value.reduce((sum, item) => sum + (item.profit || 0), 0)
})

const totalProfitRate = computed(() => {
  if (totalHoldingAmount.value === 0) return 0
  return (totalProfit.value / totalHoldingAmount.value) * 100
})

const selectedAccount = computed(() => {
  return accountList.value.find(a => a.account_id === planForm.value.account_id)
})

const availableAmount = computed(() => {
  return selectedAccount.value?.available_cash || 0
})

const totalAssets = computed(() => {
  return selectedAccount.value?.total_assets || 0
})

const maxBuyableAmount = computed(() => {
  const suggestedAmount = availableAmount.value * 0.70
  const singleLimit = suggestedAmount * 0.25
  return Math.min(singleLimit, availableAmount.value)
})

const maxBuyableShares = computed(() => {
  if (planForm.value.current_price <= 0) return 0
  return Math.floor(maxBuyableAmount.value / planForm.value.current_price / 100) * 100
})

const planForm = ref({
  plan_name: '',
  account_id: '',
  stock_code: '',
  stock_name: '',
  current_price: 0,
  planned_quantity: 1000,
  stop_loss_rate: 10,
  stop_loss_price: 0,
  take_profit_rate: 20,
  take_profit_price: 0,
  remark: ''
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

const getAccountName = (accountId) => {
  const account = accountList.value.find(a => a.account_id === accountId)
  return account ? account.account_name : accountId
}

const loadAccountList = async () => {
  try {
    const data = await accountApi.getAccountList()
    accountList.value = data.accounts || []
  } catch (error) {
    console.error('加载账号列表失败:', error)
  }
}

const loadPlanList = async () => {
  loading.value = true
  try {
    const data = await planApi.getPlanList(filterAccountId.value || null)
    let plans = data.plans || []
    
    // 前端过滤
    if (filterStock.value) {
      const keyword = filterStock.value.toLowerCase()
      plans = plans.filter(p => 
        p.stock_code?.toLowerCase().includes(keyword) || 
        p.stock_name?.toLowerCase().includes(keyword)
      )
    }
    
    if (filterStatus.value) {
      plans = plans.filter(p => p.status === filterStatus.value)
    }
    
    planList.value = plans
  } catch (error) {
    console.error('加载计划列表失败:', error)
    ElMessage.error('加载计划列表失败')
  } finally {
    loading.value = false
  }
}

const fetchCurrentPrice = async () => {
  if (!planForm.value.stock_code) return
  
  priceLoading.value = true
  try {
    const timeoutPromise = new Promise((_, reject) => 
      setTimeout(() => reject(new Error('请求超时')), 5000)
    )
    
    const data = await Promise.race([
      stockApi.getRealtime(planForm.value.stock_code),
      timeoutPromise
    ])
    
    if (data && data.price) {
      planForm.value.current_price = data.price
      planForm.value.stock_name = data.name || planForm.value.stock_name
      calculatePrices()
    }
  } catch (error) {
    console.log('获取实时价格失败，使用当前价格')
  } finally {
    priceLoading.value = false
  }
}

const calculatePrices = () => {
  if (planForm.value.current_price > 0) {
    planForm.value.stop_loss_price = parseFloat((planForm.value.current_price * (1 - planForm.value.stop_loss_rate / 100)).toFixed(2))
    planForm.value.take_profit_price = parseFloat((planForm.value.current_price * (1 + planForm.value.take_profit_rate / 100)).toFixed(2))
  }
}

const showCreateDialog = () => {
  const reviewOpinion = route.query.review_opinion || ''
  planForm.value = {
    plan_name: '',
    account_id: accountList.value[0]?.account_id || '',
    stock_code: route.query.stock_code || '',
    stock_name: route.query.stock_name || '',
    current_price: parseFloat(route.query.close_price) || 0,
    planned_quantity: 1000,
    stop_loss_rate: 10,
    stop_loss_price: 0,
    take_profit_rate: 20,
    take_profit_price: 0,
    remark: reviewOpinion
  }
  calculatePrices()
  dialogVisible.value = true
}

const editPlan = (row) => {
  planForm.value = { ...row, current_price: row.stop_loss_price ? row.stop_loss_price / 0.92 : 0 }
  dialogVisible.value = true
}

const executePlan = (row) => {
  ElMessageBox.confirm(
    `确认执行交易计划「${row.plan_name}」？\n执行后将自动创建建仓、加仓、减仓、止损、止盈步骤。`,
    '执行确认',
    {
      confirmButtonText: '确认执行',
      cancelButtonText: '取消',
      type: 'warning'
    }
  ).then(async () => {
    try {
      const result = await planApi.executePlan(row.plan_id)
      ElMessage.success(`计划已执行，创建了${result.steps?.length || 0}个执行步骤`)
      loadPlanList()
      router.push({
        path: '/trade-execution',
        query: { plan_id: row.plan_id }
      })
    } catch (error) {
      ElMessage.error(error.response?.data?.detail || '执行失败')
    }
  })
}

const viewExecution = (row) => {
  router.push({
    path: '/trade-execution',
    query: { plan_id: row.plan_id }
  })
}

const viewStockIndicator = (stockCode) => {
  const url = `http://www.iwencai.com/unifiedwap/result?w=${stockCode}`
  const width = 1200
  const height = 800
  const left = (window.screen.width - width) / 2
  const top = (window.screen.height - height) / 2
  window.open(url, 'stockIndicator', `width=${width},height=${height},left=${left},top=${top},scrollbars=yes,toolbar=no,resizable=yes`)
}

const deletePlan = (row) => {
  ElMessageBox.confirm(
    `确认删除交易计划「${row.plan_name}」？`,
    '删除确认',
    {
      confirmButtonText: '确认删除',
      cancelButtonText: '取消',
      type: 'warning'
    }
  ).then(async () => {
    try {
      await planApi.deletePlan(row.plan_id)
      ElMessage.success('交易计划已删除')
      loadPlanList()
    } catch (error) {
      ElMessage.error(error.response?.data?.detail || '删除失败')
    }
  })
}

const savePlan = async () => {
  if (!planForm.value.account_id) {
    ElMessage.warning('请选择证券账号')
    return
  }
  if (!planForm.value.stock_code) {
    ElMessage.warning('请输入股票代码')
    return
  }
  if (!planForm.value.stock_name) {
    ElMessage.warning('请输入股票名称')
    return
  }
  
  const account = accountList.value.find(a => a.account_id === planForm.value.account_id)
  const totalAssets = account?.total_assets || 0
  const availableCash = account?.available_cash || 0
  const plannedAmount = planForm.value.planned_quantity * planForm.value.current_price
  
  const ruleWarnings = []
  
  if (totalAssets > 0) {
    const singlePositionRatio = plannedAmount / totalAssets
    if (singlePositionRatio > 0.25) {
      ruleWarnings.push(`单只个股仓位 ${singlePositionRatio.toFixed(1)}% 超过25%上限`)
    }
    
    const activePlans = planList.value.filter(p => 
      p.account_id === planForm.value.account_id && 
      ['pending', 'executing'].includes(p.status)
    )
    
    if (activePlans.length >= 5) {
      ruleWarnings.push(`当前持仓 ${activePlans.length} 只，已达上限5只`)
    }
    
    const totalStockValue = activePlans.reduce((sum, p) => sum + (p.holding_amount || 0), 0)
    const newStockValue = totalStockValue + plannedAmount
    const stockPositionRatio = newStockValue / totalAssets
    
    if (stockPositionRatio > 0.70) {
      ruleWarnings.push(`总股票仓位 ${stockPositionRatio.toFixed(1)}% 超过70%上限`)
    }
    
    const cashRatio = (availableCash - plannedAmount) / totalAssets
    if (cashRatio < 0.30) {
      ruleWarnings.push(`现金比例 ${cashRatio.toFixed(1)}% 低于30%下限`)
    }
  }
  
  if (ruleWarnings.length > 0) {
    try {
      await ElMessageBox.confirm(
        `以下规则警告：\n${ruleWarnings.map(w => `• ${w}`).join('\n')}\n\n是否仍要保存？`,
        '仓位规则警告',
        {
          confirmButtonText: '仍要保存',
          cancelButtonText: '取消',
          type: 'warning'
        }
      )
    } catch {
      return
    }
  }
  
  try {
    const result = await planApi.createPlan({
      plan_name: planForm.value.stock_name,
      account_id: planForm.value.account_id,
      stock_code: planForm.value.stock_code,
      stock_name: planForm.value.stock_name,
      planned_quantity: planForm.value.planned_quantity,
      planned_amount: plannedAmount,
      stop_loss_price: planForm.value.stop_loss_price || null,
      take_profit_price: planForm.value.take_profit_price || null
    })
    
    if (result.warnings && result.warnings.length > 0) {
      ElMessage.warning({
        message: `交易计划已保存，但存在警告：\n${result.warnings.join('\n')}`,
        duration: 5000
      })
    } else {
      ElMessage.success(`交易计划已保存\n计划名称: ${result.plan_name}\n止损价: ${result.stop_loss_price}\n止盈价: ${result.take_profit_price}`)
    }
    dialogVisible.value = false
    loadPlanList()
  } catch (error) {
    ElMessage.error('保存失败')
  }
}

onMounted(async () => {
  await loadAccountList()
  loadPlanList()
  if (route.query.stock_code) {
    showCreateDialog()
  }
})
</script>

<style scoped>
.trade-plan-page {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.status-filter-group {
  display: inline-flex;
  gap: 8px;
  flex-wrap: wrap;
}

.status-filter-item {
  padding: 6px 16px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  color: #606266;
  background-color: #f5f7fa;
  border: 1px solid #dcdfe6;
  transition: all 0.3s ease;
  user-select: none;
}

.status-filter-item:hover {
  color: #409eff;
  border-color: #c6e2ff;
  background-color: #ecf5ff;
}

.status-filter-item.active {
  color: #fff;
  background-color: #409eff;
  border-color: #409eff;
}

.profit {
  color: #f56c6c;
  font-weight: bold;
}

.loss {
  color: #67c23a;
  font-weight: bold;
}

.summary-row {
  display: flex;
  align-items: center;
  padding: 16px 20px;
  background: #f5f7fa;
  border-top: 1px solid #ebeef5;
  margin-top: 16px;
  border-radius: 4px;
}

.summary-label {
  font-weight: 600;
  color: #303133;
  margin-right: 30px;
}

.summary-item {
  margin-right: 40px;
  color: #606266;
}

.position-rules {
  display: flex;
  align-items: center;
  padding: 16px 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 8px;
  margin-top: 16px;
  color: #fff;
}

.rules-title {
  font-weight: 600;
  font-size: 16px;
  margin-right: 30px;
  white-space: nowrap;
}

.rules-content {
  display: flex;
  flex-wrap: wrap;
  gap: 20px;
}

.rule-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.rule-label {
  color: rgba(255, 255, 255, 0.8);
  font-size: 13px;
}

.rule-value {
  font-weight: 600;
  font-size: 14px;
  padding: 2px 8px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 4px;
}

.rule-value.profit {
  color: #ffd700;
}

.rule-value.loss {
  color: #90ee90;
}

.dialog-rules {
  display: flex;
  align-items: center;
  padding: 12px 16px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 8px;
  margin-bottom: 20px;
  color: #fff;
}

.dialog-rules .rules-title {
  font-weight: 600;
  font-size: 14px;
  margin-right: 20px;
  white-space: nowrap;
}

.dialog-rules .rules-content {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.dialog-rules .rule-item {
  display: flex;
  align-items: center;
  gap: 4px;
}

.dialog-rules .rule-label {
  color: rgba(255, 255, 255, 0.8);
  font-size: 12px;
}

.dialog-rules .rule-value {
  font-weight: 600;
  font-size: 12px;
  padding: 1px 6px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 3px;
}

.dialog-rules .rule-value.profit {
  color: #ffd700;
}

.dialog-rules .rule-value.loss {
  color: #90ee90;
}

.amount-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.amount-value {
  font-size: 18px;
  font-weight: 600;
  color: #409eff;
}

.amount-tip {
  font-size: 12px;
  color: #909399;
}

.buyable-info {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.buyable-value {
  font-size: 16px;
  color: #67c23a;
}

.buyable-value strong {
  font-size: 20px;
  font-weight: 600;
}

.buyable-tip {
  font-size: 12px;
  color: #909399;
}

.summary-item strong {
  font-size: 16px;
}
</style>
