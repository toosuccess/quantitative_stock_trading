<template>
  <div class="trade-execution-page">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>交易执行</span>
          <div>
            <el-button @click="goBack">
              <el-icon><ArrowLeft /></el-icon>
              返回
            </el-button>
            <el-button type="success" @click="showAddStepDialog">
              <el-icon><Plus /></el-icon>
              添加执行计划
            </el-button>
          </div>
        </div>
      </template>
      
      <el-form :inline="true" class="filter-form">
        <el-form-item label="交易计划">
          <el-select v-model="filters.planId" placeholder="全部计划" clearable style="width: 200px">
            <el-option 
              v-for="plan in planOptions" 
              :key="plan.plan_id" 
              :label="`${plan.plan_id} - ${plan.stock_name}`" 
              :value="plan.plan_id" 
            />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="filters.status" placeholder="全部状态" clearable style="width: 120px">
            <el-option label="待执行" value="pending" />
            <el-option label="已完成" value="completed" />
            <el-option label="已取消" value="cancelled" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleFilter">查询</el-button>
          <el-button @click="resetFilter">重置</el-button>
        </el-form-item>
      </el-form>

      <el-tabs v-model="activeTab">
        <el-tab-pane label="执行步骤" name="steps">
          <el-table :data="filteredSteps" style="width: 100%" v-loading="loading">
            <el-table-column prop="stock_code" label="股票代码" width="100" />
            <el-table-column prop="stock_name" label="股票名称" width="100" />
            <el-table-column prop="trade_direction" label="交易方向" width="100">
              <template #default="scope">
                <el-tag :type="getDirectionType(scope.row.trade_direction)">
                  {{ scope.row.trade_direction }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="target_price" label="目标价格" width="100">
              <template #default="scope">
                {{ scope.row.target_price?.toFixed(2) || '-' }}
              </template>
            </el-table-column>
            <el-table-column prop="planned_quantity" label="计划数量" width="100" />
            <el-table-column prop="executed_quantity" label="已执行数量" width="100">
              <template #default="scope">
                <span :class="scope.row.executed_quantity > 0 ? 'executed' : ''">
                  {{ scope.row.executed_quantity || 0 }}
                </span>
              </template>
            </el-table-column>
            <el-table-column prop="reason" label="原因" width="120" />
            <el-table-column prop="status" label="状态" width="100">
              <template #default="scope">
                <el-tag :type="getStatusType(scope.row.status)">
                  {{ getStatusName(scope.row.status) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="150" fixed="right">
              <template #default="scope">
                <el-button 
                  size="small" 
                  type="primary" 
                  @click="showExecuteStepDialog(scope.row)"
                  :disabled="scope.row.status === 'completed' || scope.row.status === 'cancelled' || isPlanCompleted(scope.row.plan_id)"
                >
                  执行
                </el-button>
              </template>
            </el-table-column>
            <el-table-column prop="step_id" label="步骤编号" width="150" />
            <el-table-column prop="plan_id" label="计划编号" width="150" />
          </el-table>
        </el-tab-pane>
        
        <el-tab-pane label="交易记录" name="records">
          <el-table :data="filteredRecords" style="width: 100%" v-loading="loading" show-summary :summary-method="getSummaries">
            <el-table-column prop="record_id" label="记录编号" width="150" />
            <el-table-column prop="stock_code" label="股票代码" width="100" />
            <el-table-column prop="stock_name" label="股票名称" width="100" />
            <el-table-column prop="trade_type" label="交易类型" width="80">
              <template #default="scope">
                <el-tag :type="scope.row.trade_type === '买入' ? 'success' : 'danger'">
                  {{ scope.row.trade_type }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="trade_direction" label="交易方向" width="80">
              <template #default="scope">
                <el-tag :type="getDirectionType(scope.row.trade_direction)">
                  {{ scope.row.trade_direction }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="trade_price" label="成交价格" width="100">
              <template #default="scope">
                {{ scope.row.trade_price?.toFixed(2) }}
              </template>
            </el-table-column>
            <el-table-column prop="trade_quantity" label="成交数量" width="100" />
            <el-table-column prop="trade_amount" label="成交金额" width="120">
              <template #default="scope">
                <span :class="scope.row.trade_type === '卖出' ? 'profit' : 'loss'">
                  {{ scope.row.trade_type === '卖出' ? '+' : '-' }}{{ scope.row.trade_amount?.toFixed(2) }}
                </span>
              </template>
            </el-table-column>
            <el-table-column prop="trade_date" label="交易日期" width="100" />
            <el-table-column prop="trade_time" label="交易时间" width="100" />
          </el-table>
        </el-tab-pane>
      </el-tabs>
    </el-card>

    <el-dialog v-model="addStepDialogVisible" title="添加执行步骤" width="500px">
      <el-form :model="addStepForm" label-width="100px">
        <el-form-item label="计划编号">
          <el-select v-model="addStepForm.plan_id" placeholder="选择计划" style="width: 100%">
            <el-option 
              v-for="plan in executingPlans" 
              :key="plan.plan_id" 
              :label="`${plan.plan_id} - ${plan.stock_name}`" 
              :value="plan.plan_id" 
            />
          </el-select>
        </el-form-item>
        <el-form-item label="步骤类型">
          <el-radio-group v-model="addStepForm.trade_direction">
            <el-radio label="加仓">加仓</el-radio>
            <el-radio label="减仓">减仓</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="计划数量">
          {{ selectedPlan?.planned_quantity || 0 }}
        </el-form-item>
        <el-form-item label="持仓数量">
          {{ selectedPlan?.holding_quantity || 0 }}
        </el-form-item>
        <el-form-item label="剩余数量">
          {{ addStepRemainingQuantity }}
        </el-form-item>
        <el-form-item label="目标价格">
          <el-input-number v-model="addStepForm.target_price" :precision="2" :step="0.1" />
        </el-form-item>
        <el-form-item label="计划数量">
          <el-input-number v-model="addStepForm.planned_quantity" :min="0" :max="addStepMaxQuantity" :step="100" />
        </el-form-item>
        <el-form-item label="原因">
          <el-input v-model="addStepForm.reason" placeholder="请输入原因" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="addStepDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="confirmAddStep" :disabled="isCurrentPlanCompleted || addStepForm.planned_quantity <= 0">确认添加</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="executeStepDialogVisible" title="执行步骤" width="500px">
      <el-form :model="executeStepForm" label-width="100px">
        <el-form-item label="步骤编号">
          <el-input v-model="executeStepForm.step_id" disabled />
        </el-form-item>
        <el-form-item label="股票">
          <el-input :value="`${executeStepForm.stock_name} (${executeStepForm.stock_code})`" disabled />
        </el-form-item>
        <el-form-item label="交易方向">
          <el-tag :type="getDirectionType(executeStepForm.trade_direction)">
            {{ executeStepForm.trade_direction }}
          </el-tag>
        </el-form-item>
        <el-form-item label="计划数量">
          {{ executeStepForm.planned_quantity }}
        </el-form-item>
        <el-form-item label="持仓数量">
          {{ executeStepForm.holding_quantity }}
        </el-form-item>
        <el-form-item label="剩余数量">
          {{ getRemainingQuantity() }}
        </el-form-item>
        <el-form-item label="成交价格">
          <el-input-number v-model="executeStepForm.trade_price" :precision="2" :step="0.01" :min="0" />
        </el-form-item>
        <el-form-item label="成交数量">
          <el-input-number 
            v-model="executeStepForm.trade_quantity" 
            :min="0" 
            :max="getMaxQuantity()"
            :step="100" 
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="executeStepDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="confirmExecuteStep">确认执行</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft, Plus } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { planApi, tradeApi } from '../api'

const route = useRoute()
const router = useRouter()
const loading = ref(false)
const addStepDialogVisible = ref(false)
const executeStepDialogVisible = ref(false)
const activeTab = ref('steps')

const allPlans = ref([])
const allSteps = ref([])
const allRecords = ref([])
const planOptions = ref([])

const filters = ref({
  planId: '',
  status: ''
})

const goBack = () => {
  router.push('/stock-selection')
}

const filteredPlans = computed(() => {
  let result = allPlans.value
  if (filters.value.planId) {
    result = result.filter(p => p.plan_id === filters.value.planId)
  }
  if (filters.value.status) {
    result = result.filter(p => p.status === filters.value.status)
  }
  return result
})

const filteredSteps = computed(() => {
  let result = allSteps.value
  if (filters.value.planId) {
    result = result.filter(s => s.plan_id === filters.value.planId)
  }
  if (filters.value.status) {
    result = result.filter(s => s.status === filters.value.status)
  }
  return result
})

const filteredRecords = computed(() => {
  let result = allRecords.value
  if (filters.value.planId) {
    result = result.filter(r => r.plan_id === filters.value.planId)
  }
  return result
})

const executingPlans = computed(() => {
  return allPlans.value.filter(p => p.status === 'executing')
})

const addStepForm = ref({
  plan_id: '',
  trade_direction: '加仓',
  target_price: 0,
  planned_quantity: 0,
  reason: ''
})

const executeStepForm = ref({
  step_id: '',
  plan_id: '',
  account_id: '',
  stock_code: '',
  stock_name: '',
  trade_direction: '',
  planned_quantity: 0,
  executed_quantity: 0,
  holding_quantity: 0,
  current_price: 0,
  trade_price: 0,
  trade_quantity: 0
})

const getRemainingQuantity = () => {
  const planned = executeStepForm.value.planned_quantity
  const holding = executeStepForm.value.holding_quantity || 0
  return Math.max(0, planned - holding)
}

const getMaxQuantity = () => {
  const direction = executeStepForm.value.trade_direction
  const planned = executeStepForm.value.planned_quantity
  const holding = executeStepForm.value.holding_quantity || 0
  const remaining = planned - holding
  
  if (direction === '建仓' || direction === '加仓') {
    return Math.max(0, remaining)
  } else if (direction === '减仓' || direction === '清仓' || direction === '止损清仓' || direction === '止盈清仓') {
    return holding
  }
  return 0
}

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
    '清仓': 'danger',
    '止损清仓': 'danger',
    '止盈清仓': 'danger'
  }
  return types[direction] || 'info'
}

const isPlanCompleted = (planId) => {
  const plan = allPlans.value.find(p => p.plan_id === planId)
  return plan?.status === 'completed'
}

const isCurrentPlanCompleted = computed(() => {
  const plan = allPlans.value.find(p => p.plan_id === addStepForm.value.plan_id)
  return plan?.status === 'completed'
})

const selectedPlan = computed(() => {
  return allPlans.value.find(p => p.plan_id === addStepForm.value.plan_id)
})

const addStepRemainingQuantity = computed(() => {
  const plan = selectedPlan.value
  if (!plan) return 0
  return plan.planned_quantity - (plan.holding_quantity || 0)
})

const addStepMaxQuantity = computed(() => {
  const direction = addStepForm.value.trade_direction
  if (direction === '加仓') {
    return addStepRemainingQuantity.value
  } else if (direction === '减仓') {
    return selectedPlan.value?.holding_quantity || 0
  }
  return 0
})

const getSummaries = (param) => {
  const { columns, data } = param
  const sums = []
  columns.forEach((column, index) => {
    if (index === 0) {
      sums[index] = '合计'
      return
    }
    if (column.property === 'trade_quantity') {
      const buyQty = data.filter(item => item.trade_type === '买入')
        .reduce((prev, curr) => prev + (curr.trade_quantity || 0), 0)
      const sellQty = data.filter(item => item.trade_type === '卖出')
        .reduce((prev, curr) => prev + (curr.trade_quantity || 0), 0)
      sums[index] = buyQty - sellQty
    } else if (column.property === 'trade_amount') {
      const buyAmount = data.filter(item => item.trade_type === '买入')
        .reduce((prev, curr) => prev + (curr.trade_amount || 0), 0)
      const sellAmount = data.filter(item => item.trade_type === '卖出')
        .reduce((prev, curr) => prev + (curr.trade_amount || 0), 0)
      const netProfit = sellAmount - buyAmount
      sums[index] = `买入: ${buyAmount.toFixed(2)} | 卖出: ${sellAmount.toFixed(2)} | 净盈亏: ${netProfit >= 0 ? '+' : ''}${netProfit.toFixed(2)}`
    } else {
      sums[index] = ''
    }
  })
  return sums
}

const loadData = async () => {
  loading.value = true
  try {
    const plansData = await planApi.getPlanList()
    allPlans.value = plansData.plans || []
    planOptions.value = allPlans.value
    
    const stepsData = await tradeApi.getExecutionSteps()
    allSteps.value = stepsData.steps || []
    
    const recordsData = await tradeApi.getTradeRecords()
    allRecords.value = recordsData.records || []
  } catch (error) {
    console.error('加载数据失败:', error)
    ElMessage.error('加载数据失败')
  } finally {
    loading.value = false
  }
}

const handleFilter = () => {
  ElMessage.success('筛选条件已应用')
}

const resetFilter = () => {
  filters.value = {
    planId: '',
    status: ''
  }
}

const showAddStepDialog = () => {
  const selectedPlan = filters.value.planId || (executingPlans.value[0]?.plan_id || '')
  const plan = allPlans.value.find(p => p.plan_id === selectedPlan)
  
  const currentPrice = plan?.current_price || plan?.target_price || 0
  const plannedQty = plan?.planned_quantity || 0
  const holdingQty = plan?.holding_quantity || 0
  const remainingQty = plannedQty - holdingQty
  
  addStepForm.value = {
    plan_id: selectedPlan,
    trade_direction: '加仓',
    target_price: currentPrice,
    planned_quantity: Math.floor(remainingQty / 2),
    reason: ''
  }
  addStepDialogVisible.value = true
}

const confirmAddStep = async () => {
  if (!addStepForm.value.plan_id) {
    ElMessage.warning('请选择计划')
    return
  }
  
  const plan = allPlans.value.find(p => p.plan_id === addStepForm.value.plan_id)
  if (!plan) {
    ElMessage.warning('计划不存在')
    return
  }
  
  try {
    const result = await tradeApi.createStep({
      plan_id: addStepForm.value.plan_id,
      account_id: plan.account_id,
      stock_code: plan.stock_code,
      stock_name: plan.stock_name,
      trade_direction: addStepForm.value.trade_direction,
      target_price: addStepForm.value.target_price || null,
      planned_quantity: addStepForm.value.planned_quantity,
      reason: addStepForm.value.reason || (addStepForm.value.trade_direction === '加仓' ? '手动添加加仓' : '手动添加减仓')
    })
    
    if (result.step_id) {
      await tradeApi.executeStep(
        result.step_id,
        addStepForm.value.target_price || plan.current_price || 0,
        addStepForm.value.planned_quantity,
        plan.account_id
      )
    }
    
    ElMessage.success('步骤添加并执行成功')
    addStepDialogVisible.value = false
    loadData()
  } catch (error) {
    ElMessage.error('添加步骤失败')
  }
}

const showExecuteStepDialog = (row) => {
  const direction = row.trade_direction
  const planned = row.planned_quantity
  const holding = row.holding_quantity || 0
  const remaining = planned - holding
  const currentPrice = row.current_price || row.target_price || 0
  
  let defaultQuantity = 0
  if (direction === '建仓' || direction === '加仓') {
    defaultQuantity = Math.min(planned, Math.max(0, remaining))
  } else if (direction === '减仓') {
    defaultQuantity = Math.min(planned, holding)
  } else if (direction === '清仓' || direction === '止损清仓' || direction === '止盈清仓') {
    defaultQuantity = holding
  }
  
  let defaultPrice = currentPrice
  if (direction === '止损清仓' || direction === '止盈清仓') {
    defaultPrice = row.target_price || currentPrice
  }
  
  executeStepForm.value = {
    step_id: row.step_id,
    plan_id: row.plan_id,
    account_id: row.account_id,
    stock_code: row.stock_code,
    stock_name: row.stock_name,
    trade_direction: row.trade_direction,
    planned_quantity: row.planned_quantity,
    executed_quantity: row.executed_quantity || 0,
    holding_quantity: holding,
    current_price: currentPrice,
    trade_price: defaultPrice,
    trade_quantity: defaultQuantity
  }
  executeStepDialogVisible.value = true
}

const confirmExecuteStep = async () => {
  if (executeStepForm.value.trade_quantity <= 0) {
    ElMessage.warning('请输入成交数量')
    return
  }
  if (executeStepForm.value.trade_price <= 0) {
    ElMessage.warning('请输入成交价格')
    return
  }
  
  try {
    const result = await tradeApi.executeStep(
      executeStepForm.value.step_id,
      executeStepForm.value.trade_price,
      executeStepForm.value.trade_quantity,
      executeStepForm.value.account_id
    )
    ElMessage.success(`执行成功！已执行${result.executed_quantity}股，步骤状态：${result.step_status === 'completed' ? '已完成' : '待执行'}`)
    executeStepDialogVisible.value = false
    loadData()
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '执行失败')
  }
}

watch(() => route.query.plan_id, (newPlanId) => {
  if (newPlanId) {
    filters.value.planId = newPlanId
    activeTab.value = 'steps'
  }
}, { immediate: true })

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.filter-form {
  margin-bottom: 20px;
}

.executed {
  color: #67c23a;
  font-weight: bold;
}
</style>
