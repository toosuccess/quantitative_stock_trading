import axios from 'axios'

const api = axios.create({
  baseURL: '/api/v1',
  timeout: 120000
})

api.interceptors.response.use(
  response => response.data,
  error => {
    console.error('API Error:', error)
    return Promise.reject(error)
  }
)

export const scoreApi = {
  getScoreList: (limit, rating) => api.get(`/scores?limit=${limit || 20}${rating ? `&rating=${rating}` : ''}`),
  getScoreByCode: (code) => api.get(`/scores/${code}`),
  getStockPoolScores: () => api.get('/stocks/pool/scores')
}

export const stockApi = {
  getStockPool: () => api.get('/stocks/pool'),
  getRealtime: (code) => api.get(`/stocks/realtime/${code}`),
  getIndicators: (code) => api.get(`/stocks/indicators/${code}`)
}

export const accountApi = {
  getAccountList: () => api.get('/accounts'),
  getAccount: (id) => api.get(`/account/${id}`),
  createAccount: (data) => api.post('/account', data),
  updateAccount: (id, data) => api.put(`/account/${id}`, data),
  deleteAccount: (id) => api.delete(`/account/${id}`),
  getAccountSummary: (id) => api.get(`/account/${id}/summary`)
}

export const planApi = {
  getPlanList: (accountId, stockCode, status) => {
    let url = '/trade/plans?'
    if (accountId) url += `account_id=${accountId}&`
    if (stockCode) url += `stock_code=${stockCode}&`
    if (status) url += `status=${status}&`
    return api.get(url)
  },
  getPlan: (id) => api.get(`/trade/plan/${id}`),
  createPlan: (data) => api.post('/trade/plan', data),
  updatePlan: (id, data) => api.put(`/trade/plan/${id}`, data),
  deletePlan: (id) => api.delete(`/trade/plan/${id}`),
  executePlan: (id) => api.post(`/trade/plan/${id}/execute`)
}

export const tradeApi = {
  getTradeRecords: (accountId, planId, stockCode) => {
    let url = '/trade/records?'
    if (accountId) url += `account_id=${accountId}&`
    if (planId) url += `plan_id=${planId}&`
    if (stockCode) url += `stock_code=${stockCode}&`
    return api.get(url)
  },
  executeTrade: (data) => api.post('/trade/record', data),
  getStatistics: (accountId) => api.get(`/trade/statistics/${accountId}`),
  getSummary: (accountId) => {
    let url = '/trade/summary?'
    if (accountId) url += `account_id=${accountId}&`
    return api.get(url)
  },
  getExecutionSteps: (planId, status) => {
    let url = '/trade/steps?'
    if (planId) url += `plan_id=${planId}&`
    if (status) url += `status=${status}&`
    return api.get(url)
  },
  createStep: (data) => api.post('/trade/step', data),
  executeStep: (stepId, tradePrice, tradeQuantity, accountId) => 
    api.post(`/trade/step/${stepId}/execute?trade_price=${tradePrice}&trade_quantity=${tradeQuantity}&account_id=${accountId || 'ACC001'}`)
}

export default api
