import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: () => import('../views/Home.vue')
  },
  {
    path: '/stock-selection',
    name: 'StockSelection',
    component: () => import('../views/StockSelection.vue')
  },
  {
    path: '/score',
    name: 'Score',
    component: () => import('../views/Score.vue')
  },
  {
    path: '/score-detail',
    name: 'ScoreDetail',
    component: () => import('../views/ScoreDetail.vue')
  },
  {
    path: '/account',
    name: 'AccountManagement',
    component: () => import('../views/AccountManagement.vue')
  },
  {
    path: '/trade-plan',
    name: 'TradePlan',
    component: () => import('../views/TradePlan.vue')
  },
  {
    path: '/trade-execution',
    name: 'TradeExecution',
    component: () => import('../views/TradeExecution.vue')
  },
  {
    path: '/review',
    name: 'Review',
    component: () => import('../views/Review.vue')
  },
  {
    path: '/sell-analysis',
    name: 'SellAnalysis',
    component: () => import('../views/SellAnalysis.vue')
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
