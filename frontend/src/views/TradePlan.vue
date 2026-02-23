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
        <el-table-column label="操作" width="250" fixed="right">
          <template #default="scope">
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
    </el-card>

    <el-dialog v-model="dialogVisible" title="新建交易计划" width="600px">
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
        <el-form-item label="备注">
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
import { ref, onMounted } from 'vue'
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

const planForm = ref({
  plan_name: '',
  account_id: '',
  stock_code: '',
  stock_name: '',
  current_price: 0,
  planned_quantity: 1000,
  stop_loss_rate: 8,
  stop_loss_price: 0,
  take_profit_rate: 10,
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
    planList.value = data.plans || []
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
  planForm.value = {
    plan_name: '',
    account_id: accountList.value[0]?.account_id || '',
    stock_code: route.query.stock_code || '',
    stock_name: route.query.stock_name || '',
    current_price: parseFloat(route.query.close_price) || 0,
    planned_quantity: 1000,
    stop_loss_rate: 8,
    stop_loss_price: 0,
    take_profit_rate: 10,
    take_profit_price: 0,
    remark: ''
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
  
  try {
    const result = await planApi.createPlan({
      plan_name: planForm.value.stock_name,
      account_id: planForm.value.account_id,
      stock_code: planForm.value.stock_code,
      stock_name: planForm.value.stock_name,
      planned_quantity: planForm.value.planned_quantity,
      planned_amount: planForm.value.planned_quantity * planForm.value.current_price,
      stop_loss_price: planForm.value.stop_loss_price || null,
      take_profit_price: planForm.value.take_profit_price || null
    })
    ElMessage.success(`交易计划已保存\n计划名称: ${result.plan_name}\n止损价: ${result.stop_loss_price}\n止盈价: ${result.take_profit_price}`)
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
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.profit {
  color: #67c23a;
  font-weight: bold;
}

.loss {
  color: #f56c6c;
  font-weight: bold;
}
</style>
