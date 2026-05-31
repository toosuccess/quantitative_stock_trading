<template>
  <el-container class="app-container">
    <el-aside :width="isCollapse ? '64px' : '220px'" class="app-aside">
      <div class="logo">
        <h2 v-if="!isCollapse">交易系统</h2>
        <span v-else class="logo-mini">交</span>
      </div>
      <el-menu
        :default-active="activeMenu"
        :collapse="isCollapse"
        router
        class="app-menu"
      >
        <el-menu-item index="/">
          <el-icon><HomeFilled /></el-icon>
          <template #title>首页</template>
        </el-menu-item>
        <el-menu-item index="/stock-selection">
          <el-icon><Search /></el-icon>
          <template #title>股票池</template>
        </el-menu-item>
        <el-menu-item index="/trade-plan">
          <el-icon><Document /></el-icon>
          <template #title>交易计划</template>
        </el-menu-item>
        <el-menu-item index="/trade-execution">
          <el-icon><Position /></el-icon>
          <template #title>交易执行</template>
        </el-menu-item>
        <el-sub-menu index="/review">
          <template #title>
            <el-icon><TrendCharts /></el-icon>
            <span>复盘分析</span>
          </template>
          <el-menu-item index="/review">复盘</el-menu-item>
          <el-menu-item index="/sell-analysis">卖出分析</el-menu-item>
        </el-sub-menu>
        <el-menu-item index="/account">
          <el-icon><User /></el-icon>
          <template #title>账号管理</template>
        </el-menu-item>
      </el-menu>
    </el-aside>
    <el-container>
      <el-header class="app-header">
        <div class="header-left">
          <el-icon 
            class="collapse-btn" 
            @click="toggleCollapse"
          >
            <Fold v-if="!isCollapse" />
            <Expand v-else />
          </el-icon>
          <span class="header-title">个人专属交易系统</span>
        </div>
        <div class="header-info">
          <span>{{ currentDate }}</span>
        </div>
      </el-header>
      <el-main class="app-main" ref="mainRef">
        <router-view />
      </el-main>
    </el-container>
    
    <div class="floating-buttons">
      <el-tooltip content="返回上一页" placement="left">
        <el-button 
          circle 
          type="primary" 
          @click="goBack"
          :disabled="!canGoBack"
        >
          <el-icon><Back /></el-icon>
        </el-button>
      </el-tooltip>
      <el-tooltip content="返回顶部" placement="left">
        <el-button 
          circle 
          type="success" 
          @click="scrollToTop"
        >
          <el-icon><Top /></el-icon>
        </el-button>
      </el-tooltip>
    </div>
  </el-container>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { 
  HomeFilled, 
  Search, 
  User,
  DataAnalysis, 
  Document, 
  Position, 
  TrendCharts,
  Fold,
  Expand,
  Back,
  Top
} from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const activeMenu = computed(() => route.path)
const isCollapse = ref(false)
const mainRef = ref(null)

const canGoBack = computed(() => {
  return window.history.length > 1
})

const toggleCollapse = () => {
  isCollapse.value = !isCollapse.value
}

const goBack = () => {
  router.back()
}

const scrollToTop = () => {
  const mainEl = document.querySelector('.app-main')
  if (mainEl) {
    mainEl.scrollTo({
      top: 0,
      behavior: 'smooth'
    })
  }
}

const currentDate = computed(() => {
  const now = new Date()
  return now.toLocaleDateString('zh-CN', { 
    year: 'numeric', 
    month: 'long', 
    day: 'numeric',
    weekday: 'long'
  })
})
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: 'Helvetica Neue', Helvetica, 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', Arial, sans-serif;
}

.app-container {
  height: 100vh;
}

.app-aside {
  background-color: #304156;
  color: #fff;
  transition: width 0.3s;
  overflow: hidden;
}

.logo {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #263445;
}

.logo h2 {
  color: #fff;
  font-size: 18px;
}

.logo-mini {
  color: #fff;
  font-size: 20px;
  font-weight: bold;
}

.app-menu {
  border-right: none;
  background-color: #304156;
}

.app-menu .el-menu-item {
  color: #bfcbd9;
}

.app-menu .el-menu-item:hover,
.app-menu .el-menu-item.is-active {
  background-color: #263445;
  color: #409eff;
}

.app-header {
  background-color: #fff;
  border-bottom: 1px solid #e6e6e6;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 15px;
}

.collapse-btn {
  font-size: 20px;
  cursor: pointer;
  color: #606266;
  transition: color 0.3s;
}

.collapse-btn:hover {
  color: #409eff;
}

.header-title {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}

.header-info {
  color: #909399;
}

.app-main {
  background-color: #f5f7fa;
  padding: 20px;
  overflow-y: auto;
}

.floating-buttons {
  position: fixed;
  bottom: 30px;
  right: 30px;
  display: flex;
  flex-direction: row;
  gap: 12px;
  z-index: 1000;
}

.floating-buttons .el-button {
  width: 44px;
  height: 44px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  transition: all 0.3s;
}

.floating-buttons .el-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.2);
}

.floating-buttons .el-button.is-disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
