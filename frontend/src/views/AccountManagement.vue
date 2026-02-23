<template>
  <div class="account-management-page">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>账号管理</span>
          <el-button type="primary" @click="showCreateDialog">
            <el-icon><Plus /></el-icon>
            新增账号
          </el-button>
        </div>
      </template>
      
      <el-table :data="accountList" style="width: 100%" v-loading="loading">
        <el-table-column prop="account_id" label="账号编号" width="150" />
        <el-table-column prop="account_name" label="账号名称" width="150" />
        <el-table-column prop="account_type" label="类型" width="100">
          <template #default="scope">
            <el-tag :type="scope.row.account_type === '实盘' ? 'success' : 'info'">
              {{ scope.row.account_type }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="broker" label="券商" width="100">
          <template #default="scope">
            {{ scope.row.broker || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="total_assets" label="总资产" width="120">
          <template #default="scope">
            {{ (scope.row.total_assets || 0).toFixed(2) }}
          </template>
        </el-table-column>
        <el-table-column prop="available_cash" label="可用资金" width="120">
          <template #default="scope">
            {{ (scope.row.available_cash || 0).toFixed(2) }}
          </template>
        </el-table-column>
        <el-table-column prop="market_value" label="市值" width="120">
          <template #default="scope">
            {{ (scope.row.market_value || 0).toFixed(2) }}
          </template>
        </el-table-column>
        <el-table-column prop="profit_loss" label="盈亏" width="120">
          <template #default="scope">
            <span :class="scope.row.profit_loss >= 0 ? 'profit' : 'loss'">
              {{ scope.row.profit_loss >= 0 ? '+' : '' }}{{ (scope.row.profit_loss || 0).toFixed(2) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="scope">
            <el-tag :type="scope.row.status === 'active' ? 'success' : 'danger'">
              {{ scope.row.status === 'active' ? '正常' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="scope">
            <el-button size="small" type="primary" @click="editAccount(scope.row)">
              编辑
            </el-button>
            <el-button size="small" type="info" @click="viewSummary(scope.row)">
              汇总
            </el-button>
            <el-button size="small" type="danger" @click="deleteAccount(scope.row)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑账号' : '新增账号'" width="500px">
      <el-form :model="accountForm" label-width="100px">
        <el-form-item label="账号名称">
          <el-input v-model="accountForm.account_name" placeholder="请输入账号名称" />
        </el-form-item>
        <el-form-item label="账号类型">
          <el-radio-group v-model="accountForm.account_type">
            <el-radio label="实盘">实盘</el-radio>
            <el-radio label="模拟">模拟</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="券商">
          <el-input v-model="accountForm.broker" placeholder="请输入券商名称" />
        </el-form-item>
        <el-form-item label="总资产">
          <el-input-number v-model="accountForm.total_assets" :precision="2" :step="1000" />
        </el-form-item>
        <el-form-item label="可用资金">
          <el-input-number v-model="accountForm.available_cash" :precision="2" :step="1000" />
        </el-form-item>
        <el-form-item label="市值">
          <el-input-number v-model="accountForm.market_value" :precision="2" :step="1000" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="accountForm.remark" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveAccount">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="summaryDialogVisible" title="账号汇总" width="600px">
      <el-descriptions :column="2" border>
        <el-descriptions-item label="账号名称">{{ summary.account?.account_name }}</el-descriptions-item>
        <el-descriptions-item label="账号类型">{{ summary.account?.account_type }}</el-descriptions-item>
        <el-descriptions-item label="总资产">{{ (summary.account?.total_assets || 0).toFixed(2) }}</el-descriptions-item>
        <el-descriptions-item label="可用资金">{{ (summary.account?.available_cash || 0).toFixed(2) }}</el-descriptions-item>
        <el-descriptions-item label="市值">{{ (summary.account?.market_value || 0).toFixed(2) }}</el-descriptions-item>
        <el-descriptions-item label="盈亏">
          <span :class="summary.account?.profit_loss >= 0 ? 'profit' : 'loss'">
            {{ (summary.account?.profit_loss || 0).toFixed(2) }}
          </span>
        </el-descriptions-item>
        <el-descriptions-item label="交易计划数">{{ summary.plan_count }}</el-descriptions-item>
        <el-descriptions-item label="交易记录数">{{ summary.trade_count }}</el-descriptions-item>
        <el-descriptions-item label="买入总额">{{ (summary.total_buy || 0).toFixed(2) }}</el-descriptions-item>
        <el-descriptions-item label="卖出总额">{{ (summary.total_sell || 0).toFixed(2) }}</el-descriptions-item>
        <el-descriptions-item label="胜率">{{ summary.win_rate?.win_rate || 0 }}%</el-descriptions-item>
        <el-descriptions-item label="盈亏比">{{ summary.profit_loss_ratio?.ratio || 0 }}</el-descriptions-item>
      </el-descriptions>
      <template #footer>
        <el-button type="primary" @click="summaryDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { Plus } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { accountApi } from '../api'

const loading = ref(false)
const dialogVisible = ref(false)
const summaryDialogVisible = ref(false)
const isEdit = ref(false)

const accountList = ref([])
const summary = ref({})

const accountForm = ref({
  account_id: '',
  account_name: '',
  account_type: '模拟',
  broker: '',
  total_assets: 0,
  available_cash: 0,
  market_value: 0,
  remark: ''
})

const loadAccountList = async () => {
  loading.value = true
  try {
    const data = await accountApi.getAccountList()
    accountList.value = data.accounts || []
  } catch (error) {
    console.error('加载账号列表失败:', error)
    ElMessage.error('加载账号列表失败')
  } finally {
    loading.value = false
  }
}

const showCreateDialog = () => {
  isEdit.value = false
  accountForm.value = {
    account_id: '',
    account_name: '',
    account_type: '模拟',
    broker: '',
    total_assets: 0,
    available_cash: 0,
    market_value: 0,
    remark: ''
  }
  dialogVisible.value = true
}

const editAccount = (row) => {
  isEdit.value = true
  accountForm.value = { ...row }
  dialogVisible.value = true
}

const viewSummary = async (row) => {
  try {
    const data = await accountApi.getAccountSummary(row.account_id)
    summary.value = data
    summaryDialogVisible.value = true
  } catch (error) {
    ElMessage.error('获取汇总信息失败')
  }
}

const deleteAccount = (row) => {
  ElMessageBox.confirm(
    `确认删除账号「${row.account_name}」？`,
    '删除确认',
    {
      confirmButtonText: '确认删除',
      cancelButtonText: '取消',
      type: 'warning'
    }
  ).then(async () => {
    try {
      await accountApi.deleteAccount(row.account_id)
      ElMessage.success('账号已删除')
      loadAccountList()
    } catch (error) {
      ElMessage.error(error.response?.data?.detail || '删除失败')
    }
  })
}

const saveAccount = async () => {
  if (!accountForm.value.account_name) {
    ElMessage.warning('请输入账号名称')
    return
  }
  
  try {
    if (isEdit.value) {
      await accountApi.updateAccount(accountForm.value.account_id, accountForm.value)
      ElMessage.success('账号已更新')
    } else {
      await accountApi.createAccount(accountForm.value)
      ElMessage.success('账号已创建')
    }
    dialogVisible.value = false
    loadAccountList()
  } catch (error) {
    ElMessage.error('保存失败')
  }
}

onMounted(() => {
  loadAccountList()
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
