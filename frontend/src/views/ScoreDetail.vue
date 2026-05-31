<template>
  <div class="score-detail-page">
    <el-page-header @back="goBack" :title="'股票池'">
      <template #content>
        <span class="page-title">{{ stockName }} ({{ stockCode }}) 评分详情</span>
      </template>
    </el-page-header>

    <el-row :gutter="20" style="margin-top: 20px;">
      <el-col :span="4">
        <el-card class="stat-card">
          <div class="stat-title">评分次数</div>
          <div class="stat-value">{{ scoreHistory.length }}</div>
          <div class="stat-desc">次评分</div>
        </el-card>
      </el-col>
      <el-col :span="4">
        <el-card class="stat-card">
          <div class="stat-title">综合评分</div>
          <div class="stat-value" :class="getScoreClass(latestCompositeScore)">
            {{ latestCompositeScore?.toFixed(0) }}
          </div>
          <div class="stat-desc">{{ latestRating }}</div>
        </el-card>
      </el-col>
      <el-col :span="4">
        <el-card class="stat-card clickable" @click="scrollToTab('technical')">
          <div class="stat-title">技术面</div>
          <div class="stat-value" :class="getScoreClass(latestTechnicalScore)">
            {{ latestTechnicalScore?.toFixed(0) }}
          </div>
          <div class="stat-desc">/100</div>
        </el-card>
      </el-col>
      <el-col :span="4">
        <el-card class="stat-card clickable" @click="scrollToTab('fundamental')">
          <div class="stat-title">基本面</div>
          <div class="stat-value" :class="getScoreClass(latestFundamentalScore)">
            {{ latestFundamentalScore?.toFixed(0) }}
          </div>
          <div class="stat-desc">/100</div>
        </el-card>
      </el-col>
      <el-col :span="4">
        <el-card class="stat-card clickable" @click="scrollToTab('news')">
          <div class="stat-title">消息面</div>
          <div class="stat-value" :class="getAdjustmentScoreClass(latestNewsScore)">
            {{ formatAdjustmentScore(latestNewsScore) }}
          </div>
          <div class="stat-desc">加减分</div>
        </el-card>
      </el-col>
      <el-col :span="4">
        <el-card class="stat-card clickable" @click="scrollToTab('policy')">
          <div class="stat-title">政策面</div>
          <div class="stat-value" :class="getAdjustmentScoreClass(latestPolicyScore)">
            {{ formatAdjustmentScore(latestPolicyScore) }}
          </div>
          <div class="stat-desc">加减分</div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 股票基本信息卡片 -->
    <el-card style="margin-top: 20px;" v-if="stockInfo">
      <template #header>
        <span>股票基本信息</span>
      </template>
      <el-row :gutter="20">
        <el-col :span="6">
          <div class="info-item">
            <span class="info-label">股票代码：</span>
            <span class="info-value">{{ stockInfo.stock_code }}</span>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="info-item">
            <span class="info-label">股票名称：</span>
            <span class="info-value">{{ stockInfo.stock_name }}</span>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="info-item">
            <span class="info-label">交易所：</span>
            <span class="info-value">{{ stockInfo.exchange }}</span>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="info-item">
            <span class="info-label">行业：</span>
            <el-tag type="primary" size="small">{{ stockInfo.industry || '未知' }}</el-tag>
          </div>
        </el-col>
      </el-row>
      <el-row :gutter="20" style="margin-top: 12px;">
        <el-col :span="6">
          <div class="info-item">
            <span class="info-label">板块：</span>
            <el-tag type="success" size="small">{{ stockInfo.sector || '未知' }}</el-tag>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="info-item">
            <span class="info-label">市盈率PE：</span>
            <span class="info-value">{{ stockInfo.pe_ratio || '-' }}</span>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="info-item">
            <span class="info-label">市净率PB：</span>
            <span class="info-value">{{ stockInfo.pb_ratio || '-' }}</span>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="info-item">
            <span class="info-label">上市日期：</span>
            <span class="info-value">{{ stockInfo.list_date || '-' }}</span>
          </div>
        </el-col>
      </el-row>
    </el-card>

    <!-- 综合评价卡片 -->
    <el-card style="margin-top: 20px;" v-if="latestSummary">
      <template #header>
        <span>综合评价</span>
      </template>
      <div class="summary-content">{{ latestSummary }}</div>
    </el-card>

    <!-- 评分明细展示 -->
    <el-card style="margin-top: 20px;" v-if="latestRecord">
      <template #header>
        <div class="card-header">
          <span>最新评分明细（{{ latestRecord.create_time || latestRecord.score_date }}）</span>
          <div style="display: flex; align-items: center; gap: 12px; font-size: 13px;">
            <span style="color: #606266;">综合评分公式：技术面×0.6 + 基本面×0.4 + 消息面加减分 + 政策面加减分 - 减项扣分</span>
            <el-tag type="success" size="small">90-100 强烈推荐</el-tag>
            <el-tag type="primary" size="small">70-89 推荐</el-tag>
            <el-tag type="warning" size="small">50-69 中性</el-tag>
            <el-tag type="info" size="small">30-49 观望</el-tag>
            <el-tag type="danger" size="small">0-29 不推荐</el-tag>
          </div>
        </div>
      </template>
      
      <el-tabs v-model="activeTab">
        <!-- 技术面明细 -->
        <el-tab-pane label="技术面明细" name="technical">
          <el-alert type="info" :closable="false" style="margin-bottom: 16px;">
            <template #title>
              <span style="font-weight: 600;">技术面评分规则（满分100分）</span>
            </template>
            <div style="font-size: 13px; line-height: 2;">
              <div>均线系统（25分）：股价站稳20日均线且M20向上，20日均线在60日均线上方，均线多头排列</div>
              <div>成交量（25分）：当日成交量＞5日/60日均量，换手率5%-20%</div>
              <div>趋势指标（20分）：DMI的+DI＞-DI且ADX/ADXR上升，MACD金叉</div>
              <div>资金指标（15分）：OBV＞MAOBV且持续上行，资金净流入</div>
              <div>布林线（15分）：股价位于上轨和中轨之间，且未超买</div>
            </div>
          </el-alert>
          <div class="detail-section" v-if="technicalDetail">
            <el-row :gutter="20">
              <el-col :span="8" v-for="(item, key) in technicalDetail" :key="key">
                <div class="indicator-card">
                  <div class="indicator-header">
                    <span class="indicator-name">{{ getTechnicalLabel(key) }}</span>
                    <el-tag :type="item.score > 0 ? 'success' : 'info'" size="small">
                      {{ item.score }}分
                    </el-tag>
                  </div>
                  <div class="indicator-detail">{{ item.detail }}</div>
                </div>
              </el-col>
            </el-row>
          </div>
          <el-empty v-else description="暂无技术面明细数据" />
        </el-tab-pane>
        
        <!-- 基本面明细 -->
        <el-tab-pane label="基本面明细" name="fundamental">
          <el-alert type="info" :closable="false" style="margin-bottom: 16px;">
            <template #title>
              <span style="font-weight: 600;">基本面评分规则（满分100分）</span>
            </template>
            <div style="font-size: 13px; line-height: 2;">
              <div><strong>一、盈利能力（30分）</strong></div>
              <div style="padding-left: 12px;">ROE（20分）：≥20%=20分 | ≥15%=16分 | ≥10%=12分 | ≥5%=6分 | &lt;5%=0分</div>
              <div style="padding-left: 12px;">净利率（10分）：≥20%=10分 | ≥10%=8分 | ≥5%=5分 | &gt;0%=2分 | ≤0%=0分</div>
              <div><strong>二、成长能力（25分）</strong></div>
              <div style="padding-left: 12px;">净利润增长率（15分）：≥50%=15分 | ≥20%=12分 | ≥10%=8分 | ≥0%=4分 | &lt;0%=0分</div>
              <div style="padding-left: 12px;">营收增长率（10分）：≥30%=10分 | ≥15%=8分 | ≥5%=5分 | ≥0%=2分 | &lt;0%=0分</div>
              <div><strong>三、估值（20分）</strong></div>
              <div style="padding-left: 12px;">PE（12分）：0-15=12分 | 15-25=10分 | 25-40=6分 | &gt;40=2分 | ≤0=0分</div>
              <div style="padding-left: 12px;">PB（8分）：0-2=8分 | 2-4=6分 | 4-6=3分 | &gt;6=1分 | ≤0=0分</div>
              <div><strong>四、财务健康（15分）</strong></div>
              <div style="padding-left: 12px;">负债率（10分）：≤30%=10分 | ≤50%=8分 | ≤70%=5分 | &gt;70%=0分</div>
              <div style="padding-left: 12px;">流动比率（5分）：≥2=5分 | ≥1.5=4分 | ≥1=3分 | &gt;0=1分 | ≤0=0分</div>
              <div><strong>五、现金流&amp;运营（10分）</strong></div>
              <div style="padding-left: 12px;">资产周转率（5分）：≥30%=5分 | ≥20%=4分 | ≥10%=3分 | &gt;0%=1分 | ≤0=0分</div>
              <div style="padding-left: 12px;">现金流动比率（5分）：≥1.5=5分 | ≥1=4分 | ≥0.5=3分 | &gt;0=1分 | ≤0=0分</div>
            </div>
          </el-alert>
          <div class="detail-section" v-if="fundamentalDetail">
            <el-row :gutter="20">
              <el-col :span="8" v-for="(item, key) in fundamentalDetail" :key="key">
                <div class="indicator-card">
                  <div class="indicator-header">
                    <span class="indicator-name">{{ getFundamentalLabel(key) }}</span>
                    <el-tag :type="item.score > 10 ? 'success' : item.score > 5 ? 'warning' : 'info'" size="small">
                      {{ item.score }}分
                    </el-tag>
                  </div>
                  <div class="indicator-value" v-if="item.value">数值: {{ item.value }}</div>
                  <div class="indicator-detail">{{ item.detail }}</div>
                </div>
              </el-col>
            </el-row>
          </div>
          <el-empty v-else description="暂无基本面明细数据" />
        </el-tab-pane>
        
        <!-- 消息面明细 -->
        <el-tab-pane label="消息面明细" name="news">
          <el-alert type="info" :closable="false" style="margin-bottom: 16px;">
            <template #title>
              <span style="font-weight: 600;">消息面加减分规则</span>
            </template>
            <div style="font-size: 13px; line-height: 2;">
              <div>行业利好：行业政策支持、行业景气度提升（+5~+15分）</div>
              <div>公司利好：业绩预告、中标、合作等利好消息（+5~+15分）</div>
              <div>机构评级：券商研报评级、目标价（+5~+15分）</div>
              <div>资金动向：北向资金、机构持仓变化（+5~+10分）</div>
              <div>负面消息：业绩下滑、诉讼等负面新闻（-5~-15分）</div>
              <div style="color: #909399; margin-top: 4px;">注：根据消息利好利空直接加减分，无基准分</div>
            </div>
          </el-alert>
          <div class="detail-section" v-if="newsDetail && newsDetail.events && newsDetail.events.length > 0">
            <el-table :data="newsDetail.events" style="width: 100%">
              <el-table-column prop="date" label="日期" width="120" />
              <el-table-column prop="type" label="类型" width="100">
                <template #default="scope">
                  <el-tag :type="scope.row.type === '利好' ? 'success' : scope.row.type === '利空' ? 'danger' : 'info'" size="small">
                    {{ scope.row.type }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="title" label="事件标题" show-overflow-tooltip />
              <el-table-column label="内容摘要" width="200" show-overflow-tooltip>
                <template #default="scope">
                  {{ scope.row.summary || scope.row.title || '-' }}
                </template>
              </el-table-column>
              <el-table-column prop="score_impact" label="得分影响" width="100">
                <template #default="scope">
                  <span :class="scope.row.score_impact > 0 ? 'text-success' : scope.row.score_impact < 0 ? 'text-danger' : ''">
                    {{ scope.row.score_impact > 0 ? '+' : '' }}{{ scope.row.score_impact }}
                  </span>
                </template>
              </el-table-column>
              <el-table-column label="操作" width="100">
                <template #default="scope">
                  <el-button 
                    v-if="scope.row.url && scope.row.url !== '' && scope.row.url !== 'None'" 
                    type="primary" 
                    size="small" 
                    link
                    @click="openUrl(scope.row.url)"
                  >
                    查看详情
                  </el-button>
                  <span v-else class="text-muted">-</span>
                </template>
              </el-table-column>
            </el-table>
          </div>
          <el-empty v-else description="暂无消息面事件数据" />
        </el-tab-pane>
        
        <!-- 政策面明细 -->
        <el-tab-pane label="政策面明细" name="policy">
          <el-alert type="info" :closable="false" style="margin-bottom: 16px;">
            <template #title>
              <span style="font-weight: 600;">政策面评分规则</span>
            </template>
            <div style="font-size: 13px; line-height: 2;">
              <div>未来产业（数字经济、人工智能、核聚变、6G）：+10分</div>
              <div>战略性新兴产业（新能源、新材料、高端制造、半导体、生物医药）：+8分</div>
              <div>民生消费（消费升级）：+5分</div>
              <div>其他行业：+3分</div>
              <div style="color: #909399; margin-top: 4px;">注：根据行业类型和政策支持力度评分</div>
            </div>
          </el-alert>
          <div class="detail-section" v-if="policyDetail && policyDetail.policies && policyDetail.policies.length > 0">
            <el-table :data="policyDetail.policies" style="width: 100%">
              <el-table-column prop="date" label="日期" width="120" />
              <el-table-column prop="level" label="政策级别" width="100">
                <template #default="scope">
                  <el-tag :type="getPolicyLevelType(scope.row.level)" size="small">
                    {{ scope.row.level }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="title" label="政策名称" show-overflow-tooltip />
              <el-table-column label="政策内容" show-overflow-tooltip>
                <template #default="scope">
                  {{ scope.row.content || scope.row.title || '-' }}
                </template>
              </el-table-column>
              <el-table-column prop="score_impact" label="得分影响" width="100">
                <template #default="scope">
                  <span :class="scope.row.score_impact > 0 ? 'text-success' : ''">
                    {{ scope.row.score_impact > 0 ? '+' : '' }}{{ scope.row.score_impact }}
                  </span>
                </template>
              </el-table-column>
              <el-table-column label="操作" width="100">
                <template #default="scope">
                  <el-button 
                    v-if="scope.row.url && scope.row.url !== '' && scope.row.url !== 'None'" 
                    type="primary" 
                    size="small" 
                    link
                    @click="openUrl(scope.row.url)"
                  >
                    查看详情
                  </el-button>
                  <span v-else class="text-muted">-</span>
                </template>
              </el-table-column>
            </el-table>
          </div>
          <el-empty v-else description="暂无政策面数据" />
        </el-tab-pane>
        
        <!-- 减项明细 -->
        <el-tab-pane label="减项扣分明细" name="deduction">
          <el-alert type="warning" :closable="false" style="margin-bottom: 16px;">
            <template #title>
              <span style="font-weight: 600;">减项扣分规则（负分制）</span>
            </template>
            <div style="font-size: 13px; line-height: 1.8;">
              高质押率：-10分 | 减持公告：-15分 | 诉讼风险：-20分 | 财务异常：-15分 | 限售解禁：-10分 | 负面新闻：-10分
            </div>
          </el-alert>
          <div class="detail-section" v-if="deductionDetail && deductionDetail.items && deductionDetail.items.length > 0">
            <el-table :data="deductionDetail.items" style="width: 100%">
              <el-table-column prop="type" label="扣分类型" width="150">
                <template #default="scope">
                  <el-tag type="danger" size="small">{{ scope.row.type }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="detail" label="详情说明" show-overflow-tooltip />
              <el-table-column prop="deduction" label="扣分" width="100">
                <template #default="scope">
                  <span class="text-danger">-{{ scope.row.deduction }}</span>
                </template>
              </el-table-column>
            </el-table>
          </div>
          <el-empty v-else description="暂无减项扣分数据" :image-size="80">
            <template #description>
              <span class="text-success">该股票暂无明显风险项</span>
            </template>
          </el-empty>
        </el-tab-pane>
      </el-tabs>
    </el-card>

    <el-card style="margin-top: 20px;">
      <template #header>
        <span>各指标得分变化趋势</span>
      </template>
      <div ref="indicatorChart" class="chart-container"></div>
    </el-card>

    <el-card style="margin-top: 20px;">
      <template #header>
        <span>历史评分记录</span>
      </template>
      <el-table :data="scoreHistory" style="width: 100%" v-loading="loading">
        <el-table-column prop="create_time" label="评分时间" width="160">
          <template #default="scope">
            {{ scope.row.create_time || scope.row.score_date }}
          </template>
        </el-table-column>
        <el-table-column prop="composite_score" label="综合" width="70">
          <template #default="scope">
            <el-tag :type="getScoreType(scope.row.composite_score || scope.row.total_score)" size="small">
              {{ (scope.row.composite_score || scope.row.total_score)?.toFixed(0) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="rating" label="评级" width="70">
          <template #default="scope">
            <el-tag :type="getRatingType(scope.row.rating)" size="small">
              {{ scope.row.rating }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="technical_score" label="技术面" width="70">
          <template #default="scope">
            <span :class="getScoreTextClass(scope.row.technical_score)">
              {{ scope.row.technical_score?.toFixed(0) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="fundamental_score" label="基本面" width="70">
          <template #default="scope">
            <span :class="getScoreTextClass(scope.row.fundamental_score)">
              {{ scope.row.fundamental_score?.toFixed(0) || 0 }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="news_score" label="消息面" width="70">
          <template #default="scope">
            <span :class="getAdjustmentTextClass(scope.row.news_score)">
              {{ formatAdjustmentScore(scope.row.news_score || 0) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="policy_score" label="政策面" width="70">
          <template #default="scope">
            <span :class="getAdjustmentTextClass(scope.row.policy_score)">
              {{ formatAdjustmentScore(scope.row.policy_score || 0) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="deduction_score" label="扣分" width="60">
          <template #default="scope">
            <span :class="scope.row.deduction_score > 0 ? 'text-danger' : 'text-success'">
              -{{ scope.row.deduction_score || 0 }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="close_price" label="收盘价" width="80">
          <template #default="scope">
            {{ scope.row.close_price?.toFixed(2) }}
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { scoreApi } from '../api'
import api from '../api'
import * as echarts from 'echarts'

const route = useRoute()
const router = useRouter()

const stockCode = ref(route.query.stock_code || '')
const stockName = ref(route.query.stock_name || '')
const scoreHistory = ref([])
const stockInfo = ref(null)
const loading = ref(false)
const indicatorChart = ref(null)
const activeTab = ref('technical')
const tradePlans = ref([])

const latestRecord = computed(() => scoreHistory.value[0])
const latestCompositeScore = computed(() => scoreHistory.value[0]?.composite_score || scoreHistory.value[0]?.total_score || 0)
const latestTechnicalScore = computed(() => scoreHistory.value[0]?.technical_score || 0)
const latestFundamentalScore = computed(() => scoreHistory.value[0]?.fundamental_score || 0)
const latestNewsScore = computed(() => scoreHistory.value[0]?.news_score || 0)
const latestPolicyScore = computed(() => scoreHistory.value[0]?.policy_score || 0)
const latestRating = computed(() => scoreHistory.value[0]?.rating || '-')
const latestSummary = computed(() => scoreHistory.value[0]?.summary || '')

const technicalDetail = computed(() => {
  const detail = scoreHistory.value[0]?.technical_detail
  if (detail) {
    try {
      return typeof detail === 'string' ? JSON.parse(detail) : detail
    } catch (e) {
      return null
    }
  }
  return null
})

const fundamentalDetail = computed(() => {
  const detail = scoreHistory.value[0]?.fundamental_detail
  if (detail) {
    try {
      return typeof detail === 'string' ? JSON.parse(detail) : detail
    } catch (e) {
      return null
    }
  }
  return null
})

const newsDetail = computed(() => {
  const detail = scoreHistory.value[0]?.news_detail
  if (detail) {
    try {
      return typeof detail === 'string' ? JSON.parse(detail) : detail
    } catch (e) {
      return null
    }
  }
  return null
})

const policyDetail = computed(() => {
  const detail = scoreHistory.value[0]?.policy_detail
  if (detail) {
    try {
      return typeof detail === 'string' ? JSON.parse(detail) : detail
    } catch (e) {
      return null
    }
  }
  return null
})

const deductionDetail = computed(() => {
  const detail = scoreHistory.value[0]?.deduction_detail
  if (detail) {
    try {
      return typeof detail === 'string' ? JSON.parse(detail) : detail
    } catch (e) {
      return null
    }
  }
  return null
})

const getTechnicalLabel = (key) => {
  const labels = {
    'ma': '均线系统',
    'volume': '成交量',
    'trend': '趋势指标',
    'fund': '资金指标',
    'bollinger': '布林线'
  }
  return labels[key] || key
}

const getFundamentalLabel = (key) => {
  const labels = {
    'roe': 'ROE（盈利能力）',
    'net_margin': '净利率（盈利能力）',
    'net_profit_growth': '净利润增长率（成长能力）',
    'revenue_growth': '营收增长率（成长能力）',
    'pe': '市盈率PE（估值）',
    'pb': '市净率PB（估值）',
    'debt_ratio': '负债率（财务健康）',
    'current_ratio': '流动比率（财务健康）',
    'asset_turnover': '资产周转率（现金流&运营）',
    'cash_flow_ratio': '现金流动比率（现金流&运营）'
  }
  return labels[key] || key
}

const getPolicyLevelType = (level) => {
  const types = {
    '国家政策': 'danger',
    '地方政策': 'warning',
    '行业规划': 'primary',
    '监管环境': 'info'
  }
  return types[level] || 'info'
}

const scrollToTab = (tabName) => {
  activeTab.value = tabName
  setTimeout(() => {
    const tabsElement = document.querySelector('.el-tabs')
    if (tabsElement) {
      tabsElement.scrollIntoView({ behavior: 'smooth', block: 'start' })
    }
  }, 100)
}

const openUrl = (url) => {
  if (url) {
    window.open(url, '_blank')
  }
}

const getScoreClass = (score) => {
  if (score >= 70) return 'profit'
  if (score >= 50) return ''
  return 'loss'
}

const getAdjustmentScoreClass = (score) => {
  if (score > 0) return 'profit'
  if (score < 0) return 'loss'
  return ''
}

const formatAdjustmentScore = (score) => {
  if (score > 0) return `+${score.toFixed(0)}`
  if (score < 0) return score.toFixed(0)
  return '0'
}

const getScoreTextClass = (score) => {
  if (score >= 70) return 'text-success'
  if (score >= 50) return 'text-warning'
  return 'text-danger'
}

const getAdjustmentTextClass = (score) => {
  if (score > 0) return 'text-success'
  if (score < 0) return 'text-danger'
  return 'text-warning'
}

const getScoreType = (score) => {
  if (score >= 90) return 'success'
  if (score >= 70) return 'primary'
  if (score >= 50) return 'warning'
  return 'info'
}

const getRatingType = (rating) => {
  const types = {
    '强烈推荐': 'success',
    '推荐': 'primary',
    '中性': 'warning',
    '观望': 'info',
    '不推荐': 'danger'
  }
  return types[rating] || 'info'
}

const goBack = () => {
  router.push('/stock-selection')
}

const loadScoreHistory = async () => {
  loading.value = true
  try {
    const data = await scoreApi.getScoreByCode(stockCode.value)
    scoreHistory.value = data.history || []
    stockInfo.value = data.stock_info || null
    
    await loadTradePlans()
    
    if (scoreHistory.value.length > 0) {
      setTimeout(() => {
        renderIndicatorChart()
      }, 100)
    }
  } catch (error) {
    console.error('加载评分历史失败:', error)
  } finally {
    loading.value = false
  }
}

const loadTradePlans = async () => {
  try {
    const response = await api.get(`/stocks/${stockCode.value}/trade-plans`)
    tradePlans.value = response.plans || []
  } catch (error) {
    console.error('加载交易计划失败:', error)
    tradePlans.value = []
  }
}

const renderIndicatorChart = () => {
  if (!indicatorChart.value) return
  
  const chart = echarts.init(indicatorChart.value)
  const sortedHistory = [...scoreHistory.value].sort((a, b) => {
    const timeA = a.create_time || a.score_date
    const timeB = b.create_time || b.score_date
    return timeA.localeCompare(timeB)
  })
  const times = sortedHistory.map(s => s.create_time || s.score_date)
  
  const buyPoints = []
  const sellPoints = []
  
  tradePlans.value.forEach(plan => {
    if (plan.records) {
      plan.records.forEach(record => {
        const tradeDate = record.trade_date
        const dateIndex = times.findIndex(t => t && t.startsWith(tradeDate))
        
        console.log('交易记录:', record.trade_date, record.trade_type, '价格:', record.trade_price, '匹配索引:', dateIndex)
        
        if (dateIndex !== -1) {
          const point = {
            name: record.trade_type,
            value: [dateIndex, record.trade_price],
            trade_price: record.trade_price,
            trade_quantity: record.trade_quantity,
            trade_amount: record.trade_amount,
            plan_name: plan.plan_name
          }
          if (record.trade_type === '买入') {
            buyPoints.push(point)
          } else if (record.trade_type === '卖出') {
            sellPoints.push(point)
          }
        }
      })
    }
  })
  
  const legendData = ['技术面', '基本面', '消息面', '政策面', '综合评分', '股票价格', '买入点', '卖出点']
  const series = [
    {
      name: '技术面',
      type: 'line',
      data: sortedHistory.map(s => s.technical_score),
      smooth: true,
      itemStyle: { color: '#409EFF' }
    },
    {
      name: '基本面',
      type: 'line',
      data: sortedHistory.map(s => s.fundamental_score || 0),
      smooth: true,
      itemStyle: { color: '#67C23A' }
    },
    {
      name: '消息面',
      type: 'line',
      data: sortedHistory.map(s => s.news_score || 0),
      smooth: true,
      itemStyle: { color: '#E6A23C' }
    },
    {
      name: '政策面',
      type: 'line',
      data: sortedHistory.map(s => s.policy_score || 0),
      smooth: true,
      itemStyle: { color: '#909399' }
    },
    {
      name: '综合评分',
      type: 'line',
      data: sortedHistory.map(s => s.composite_score || s.total_score),
      smooth: true,
      lineStyle: { width: 3 },
      itemStyle: { color: '#9B59B6' }
    }
  ]
  
  const stockPriceSeries = {
    name: '股票价格',
    type: 'line',
    yAxisIndex: 1,
    data: sortedHistory.map(s => s.close_price),
    smooth: true,
    itemStyle: { color: '#F56C6C' },
    lineStyle: { type: 'dashed' }
  }
  
  series.push(stockPriceSeries)
  
  series.push({
    name: '买入点',
    type: 'scatter',
    yAxisIndex: 1,
    data: buyPoints.map(p => [p.value[0], p.value[1]]),
    symbol: 'triangle',
    symbolSize: 15,
    itemStyle: { color: '#67C23A' },
    tooltip: {
      formatter: (params) => {
        const point = buyPoints[params.dataIndex]
        return `买入: ${point.trade_price}元<br>数量: ${point.trade_quantity}<br>金额: ${point.trade_amount}`
      }
    }
  })
  
  series.push({
    name: '卖出点',
    type: 'scatter',
    yAxisIndex: 1,
    data: sellPoints.map(p => [p.value[0], p.value[1]]),
    symbol: 'triangle',
    symbolRotate: 180,
    symbolSize: 15,
    itemStyle: { color: '#F56C6C' },
    tooltip: {
      formatter: (params) => {
        const point = sellPoints[params.dataIndex]
        return `卖出: ${point.trade_price}元<br>数量: ${point.trade_quantity}<br>金额: ${point.trade_amount}`
      }
    }
  })
  
  if (tradePlans.value.length > 0) {
    const plan = tradePlans.value[0]
    const stopLossPrice = plan.stop_loss_price
    const takeProfitPrice = plan.take_profit_price
    const avgCostPrice = plan.avg_cost_price || (plan.records && plan.records.find(r => r.trade_type === '买入')?.trade_price)
    
    if (stopLossPrice || takeProfitPrice) {
      if (stopLossPrice) {
        legendData.push('止损线')
        series.push({
          name: '止损线',
          type: 'line',
          yAxisIndex: 1,
          data: Array(times.length).fill(stopLossPrice),
          lineStyle: { type: 'dashed', color: '#F56C6C', width: 2 },
          itemStyle: { color: '#F56C6C' },
          symbol: 'none',
          tooltip: { show: false }
        })
      }
      
      if (takeProfitPrice) {
        legendData.push('止盈线')
        series.push({
          name: '止盈线',
          type: 'line',
          yAxisIndex: 1,
          data: Array(times.length).fill(takeProfitPrice),
          lineStyle: { type: 'dashed', color: '#67C23A', width: 2 },
          itemStyle: { color: '#67C23A' },
          symbol: 'none',
          tooltip: { show: false }
        })
      }
      
      if (avgCostPrice) {
        legendData.push('成本线')
        series.push({
          name: '成本线',
          type: 'line',
          yAxisIndex: 1,
          data: Array(times.length).fill(avgCostPrice),
          lineStyle: { type: 'dashed', color: '#409EFF', width: 2 },
          itemStyle: { color: '#409EFF' },
          symbol: 'none',
          tooltip: { show: false }
        })
      }
      
      if (avgCostPrice && (stopLossPrice || takeProfitPrice)) {
        const markAreaData = []
        
        if (takeProfitPrice && avgCostPrice < takeProfitPrice) {
          markAreaData.push([
            { yAxis: avgCostPrice, name: '成本' },
            { yAxis: takeProfitPrice, name: '盈利区', itemStyle: { color: 'rgba(103,194,58,0.15)' } }
          ])
        }
        
        if (stopLossPrice && avgCostPrice > stopLossPrice) {
          markAreaData.push([
            { yAxis: stopLossPrice, name: '止损' },
            { yAxis: avgCostPrice, name: '亏损区', itemStyle: { color: 'rgba(245,108,108,0.15)' } }
          ])
        }
        
        if (markAreaData.length > 0) {
          stockPriceSeries.markArea = {
            silent: true,
            data: markAreaData
          }
        }
      }
    }
  }
  
  chart.setOption({
    tooltip: {
      trigger: 'axis'
    },
    legend: {
      data: legendData
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: times,
      axisLabel: {
        rotate: 45,
        interval: 0
      }
    },
    yAxis: [
      {
        type: 'value',
        name: '得分',
        min: 0,
        max: 100
      },
      {
        type: 'value',
        name: '价格',
        position: 'right'
      }
    ],
    series: series
  })
}

onMounted(() => {
  loadScoreHistory()
})
</script>

<style scoped>
.page-title {
  font-size: 18px;
  font-weight: bold;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.stat-card {
  text-align: center;
  padding: 10px;
}

.stat-card.clickable {
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
}

.stat-card.clickable:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
}

.stat-title {
  font-size: 13px;
  color: #909399;
}

.stat-value {
  font-size: 24px;
  font-weight: bold;
  margin: 8px 0;
}

.stat-desc {
  font-size: 12px;
  color: #909399;
}

.profit {
  color: #67C23A;
}

.loss {
  color: #F56C6C;
}

.text-success {
  color: #67C23A;
}

.text-warning {
  color: #E6A23C;
}

.text-danger {
  color: #F56C6C;
}

.chart-container {
  height: 350px;
}

.detail-section {
  padding: 10px 0;
}

.indicator-card {
  background: #f5f7fa;
  border-radius: 8px;
  padding: 15px;
  margin-bottom: 15px;
}

.indicator-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.indicator-name {
  font-weight: bold;
  font-size: 14px;
  color: #303133;
}

.indicator-value {
  font-size: 13px;
  color: #606266;
  margin-bottom: 5px;
}

.indicator-detail {
  font-size: 12px;
  color: #909399;
  line-height: 1.5;
  white-space: pre-line;
}

.summary-content {
  font-size: 14px;
  color: #303133;
  line-height: 1.8;
  padding: 10px 0;
}

.info-item {
  display: flex;
  align-items: center;
  padding: 8px 0;
}

.info-label {
  font-size: 13px;
  color: #909399;
  min-width: 80px;
}

.info-value {
  font-size: 14px;
  color: #303133;
  font-weight: 500;
}
</style>
