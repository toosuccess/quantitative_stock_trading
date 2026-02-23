<template>
  <el-container class="app-container">
    <el-aside width="220px" class="app-aside">
      <div class="logo">
        <h2>交易系统</h2>
      </div>
      <el-menu
        :default-active="activeMenu"
        router
        class="app-menu"
      >
        <el-menu-item index="/">
          <el-icon><HomeFilled /></el-icon>
          <span>首页</span>
        </el-menu-item>
        <el-menu-item index="/stock-selection">
          <el-icon><Search /></el-icon>
          <span>股票池</span>
        </el-menu-item>
        <el-menu-item index="/trade-plan">
          <el-icon><Document /></el-icon>
          <span>交易计划</span>
        </el-menu-item>
        <el-menu-item index="/trade-execution">
          <el-icon><Position /></el-icon>
          <span>交易执行</span>
        </el-menu-item>
        <el-menu-item index="/review">
          <el-icon><TrendCharts /></el-icon>
          <span>复盘分析</span>
        </el-menu-item>
        <el-menu-item index="/account">
          <el-icon><User /></el-icon>
          <span>账号管理</span>
        </el-menu-item>
      </el-menu>
    </el-aside>
    <el-container>
      <el-header class="app-header">
        <div class="header-title">个人专属交易系统</div>
        <div class="header-info">
          <span>{{ currentDate }}</span>
        </div>
      </el-header>
      <el-main class="app-main">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { 
  HomeFilled, 
  Search, 
  User,
  DataAnalysis, 
  Document, 
  Position, 
  TrendCharts 
} from '@element-plus/icons-vue'

const route = useRoute()
const activeMenu = computed(() => route.path)
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
}
</style>
