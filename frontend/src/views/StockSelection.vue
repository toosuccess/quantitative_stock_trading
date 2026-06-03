<template>
  <div class="stock-pool-page">
    <!-- 统计概览卡片 -->
    <el-row :gutter="20" style="margin-bottom: 20px;">
      <el-col :span="4">
        <el-card class="stat-card">
          <div class="stat-title">股票总数</div>
          <div class="stat-value">{{ stockPool.length }}</div>
        </el-card>
      </el-col>
      <el-col :span="4">
        <el-card class="stat-card stat-success clickable" :class="{ active: ratingFilter === '强烈推荐' }" @click="filterByRating('强烈推荐')">
          <div class="stat-title">强烈推荐</div>
          <div class="stat-value">{{ ratingStats.strongRecommended }}</div>
        </el-card>
      </el-col>
      <el-col :span="4">
        <el-card class="stat-card stat-primary clickable" :class="{ active: ratingFilter === '推荐' }" @click="filterByRating('推荐')">
          <div class="stat-title">推荐</div>
          <div class="stat-value">{{ ratingStats.recommended }}</div>
        </el-card>
      </el-col>
      <el-col :span="4">
        <el-card class="stat-card stat-warning clickable" :class="{ active: ratingFilter === '中性' }" @click="filterByRating('中性')">
          <div class="stat-title">中性</div>
          <div class="stat-value">{{ ratingStats.neutral }}</div>
        </el-card>
      </el-col>
      <el-col :span="4">
        <el-card class="stat-card stat-info clickable" :class="{ active: ratingFilter === '观望' }" @click="filterByRating('观望')">
          <div class="stat-title">观望</div>
          <div class="stat-value">{{ ratingStats.watch }}</div>
        </el-card>
      </el-col>
      <el-col :span="4">
        <el-card class="stat-card stat-danger clickable" :class="{ active: ratingFilter === '不推荐' }" @click="filterByRating('不推荐')">
          <div class="stat-title">不推荐</div>
          <div class="stat-value">{{ ratingStats.notRecommended }}</div>
        </el-card>
      </el-col>
    </el-row>

    <el-card>
      <template #header>
        <div class="card-header">
          <div class="search-bar">
            <el-input
              v-model="searchText"
              placeholder="搜索股票代码/名称"
              clearable
              style="width: 200px; margin-right: 10px;"
            />
            <el-select v-model="ratingFilter" placeholder="评级筛选" clearable style="width: 120px;">
              <el-option label="强烈推荐" value="强烈推荐" />
              <el-option label="推荐" value="推荐" />
              <el-option label="中性" value="中性" />
              <el-option label="观望" value="观望" />
              <el-option label="不推荐" value="不推荐" />
            </el-select>
            <el-button 
              :type="showOnlyFavorite ? 'warning' : 'default'"
              @click="toggleFavoriteFilter"
              style="margin-left: 10px;"
            >
              <el-icon><Star /></el-icon>
              只看收藏 ({{ favoriteCount }})
            </el-button>
          </div>
          <div class="button-group">
            <el-button 
              type="default" 
              @click="backToTradePlan"
              title="返回交易计划列表"
            >
              <el-icon><ArrowLeft /></el-icon>
              返回交易计划
            </el-button>
            <el-button 
              type="info" 
              @click="selectExecutingStocks"
              title="一键勾选正在执行的股票"
            >
              <el-icon><Select /></el-icon>
              勾选执行中
            </el-button>
            <el-button 
              type="warning" 
              :disabled="selectedStocks.length === 0"
              @click="batchEvaluate"
              :loading="batchEvaluating"
            >
              <el-icon><Check /></el-icon>
              批量评价 ({{ selectedStocks.length }})
            </el-button>
            <el-button
              type="primary"
              @click="batchEvaluateAll"
              :disabled="evaluating"
              title="一键评价所有股票"
              :style="{ opacity: evaluating ? 0.7 : 1 }"
            >
              <el-icon><Refresh /></el-icon>
              <span v-if="evaluating && evaluateProgress.percentage > 0">
                {{ evaluateProgress.percentage }}% ({{ evaluateProgress.current }}/{{ evaluateProgress.total }})
                <template v-if="evaluateProgress.currentStock">
                  - {{ evaluateProgress.currentStock }}
                </template>
              </span>
              <span v-else-if="evaluating">
                启动中...
              </span>
              <span v-else>
                一键评价
              </span>
            </el-button>
            <el-button
              type="success"
              @click="batchReviewAll"
              :disabled="reviewing"
              title="一键复审所有未复审股票"
              :style="{ opacity: reviewing ? 0.7 : 1 }"
            >
              <el-icon><DataAnalysis /></el-icon>
              <span v-if="reviewing && reviewProgress.percentage > 0">
                {{ reviewProgress.percentage }}% ({{ reviewProgress.current }}/{{ reviewProgress.total }})
                <template v-if="reviewProgress.currentStock">
                  - {{ reviewProgress.currentStock }}
                </template>
              </span>
              <span v-else-if="reviewing">
                启动中...
              </span>
              <span v-else>
                一键复审
              </span>
            </el-button>
            <el-button 
              type="danger" 
              @click="cleanupData"
              :loading="cleaning"
              title="清理垃圾数据"
            >
              <el-icon><Delete /></el-icon>
              数据清理
            </el-button>
          </div>
        </div>
      </template>
      
      <el-table 
        ref="stockTableRef"
        :data="paginatedData" 
        row-key="stock_code"
        style="width: 100%" 
        v-loading="loading"
        @sort-change="handleSortChange"
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="55" />
        <el-table-column prop="stock_code" label="股票代码" width="100" />
        <el-table-column prop="stock_name" label="股票名称" width="200">
          <template #default="scope">
            <div style="display: flex; align-items: center; gap: 4px; flex-wrap: wrap;">
              <el-icon 
                class="favorite-icon" 
                :class="{ 'is-favorite': scope.row.is_favorite }"
                @click.stop="toggleFavorite(scope.row)"
                :title="scope.row.is_favorite ? '点击取消收藏' : '点击收藏'"
              >
                <Star />
              </el-icon>
              <el-tag v-if="scope.row.is_leader" type="danger" size="small">龙头</el-tag>
              <span>{{ scope.row.stock_name }}</span>
              <el-tag v-if="getPredictionStats(scope.row.stock_code)" type="warning" size="small" effect="plain" class="prediction-stats-tag">
                预判{{ getPredictionStats(scope.row.stock_code).total_count }}次 {{ getPredictionStats(scope.row.stock_code).success_rate }}%
              </el-tag>
              <el-tag v-if="scope.row.sector" type="info" size="small" effect="plain">{{ scope.row.sector }}</el-tag>
              <el-tag v-else-if="scope.row.industry" type="info" size="small" effect="plain">{{ scope.row.industry }}</el-tag>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="close_price" label="收盘价" width="80">
          <template #default="scope">
            {{ scope.row.close_price?.toFixed(2) }}
          </template>
        </el-table-column>
        <el-table-column prop="composite_score" width="160" sortable="custom">
          <template #header>
            <div class="score-header">
              <span>综合评分</span>
              <div class="trend-legend">
                <span class="legend-item"><span class="legend-line price"></span>股价</span>
                <span class="legend-item"><span class="legend-line score"></span>综合</span>
              </div>
            </div>
          </template>
          <template #default="scope">
            <div class="score-cell">
              <el-tag :type="getScoreType(scope.row.composite_score || scope.row.latest_score)">
                {{ (scope.row.composite_score || scope.row.latest_score || 0).toFixed(0) }}
              </el-tag>
              <el-tooltip 
                v-if="(scope.row.score_history && scope.row.score_history.length >= 1) || (scope.row.price_history && scope.row.price_history.length >= 1)"
                placement="top"
                effect="light"
                :show-after="200"
              >
                <template #content>
                  <div class="trend-tooltip">
                    <!-- 综合得分和股价走势（按日期整合） -->
                    <div v-if="scope.row.score_history && scope.row.score_history.length > 0">
                      <div class="tooltip-title">综合得分与股价走势</div>
                      <div v-for="(item, idx) in scope.row.score_history.slice(-5)" :key="idx" class="tooltip-row">
                        <span class="tooltip-date">{{ item.date }}</span>
                        <span class="tooltip-score">{{ item.score?.toFixed(1) }}分</span>
                        <span class="tooltip-price">¥{{ getPriceByDate(scope.row.price_history, item.date)?.toFixed(2) || 'N/A' }}</span>
                      </div>
                    </div>
                  </div>
                </template>
                <svg class="trend-chart" viewBox="0 0 60 20">
                  <polyline
                    v-if="scope.row.price_history && scope.row.price_history.length >= 1"
                    :points="getPriceTrendPoints(scope.row.price_history)"
                    fill="none"
                    stroke="#409eff"
                    stroke-width="1.5"
                    stroke-dasharray="4,2"
                  />
                  <g v-if="scope.row.price_history && scope.row.price_history.length >= 1">
                    <circle
                      v-for="(point, idx) in getPriceCirclePoints(scope.row.price_history)"
                      :key="'p'+idx"
                      :cx="point.x"
                      :cy="point.y"
                      r="2"
                      fill="#409eff"
                      class="trend-point"
                    />
                  </g>
                  <polyline
                    v-if="scope.row.score_history && scope.row.score_history.length >= 1"
                    :points="getTrendPoints(scope.row.score_history)"
                    fill="none"
                    stroke="#e6a23c"
                    stroke-width="1.5"
                  />
                  <g v-if="scope.row.score_history && scope.row.score_history.length >= 1">
                    <circle
                      v-for="(point, idx) in getScoreCirclePoints(scope.row.score_history)"
                      :key="'s'+idx"
                      :cx="point.x"
                      :cy="point.y"
                      r="2"
                      fill="#e6a23c"
                      class="trend-point"
                    />
                  </g>
                </svg>
              </el-tooltip>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="执行" width="130" align="center" prop="plan_profit_rate" sortable="custom">
          <template #default="scope">
            <div v-if="scope.row.plan_status" class="plan-status-cell" :class="scope.row.plan_status">
              <div class="plan-price">执行中</div>
              <div class="plan-profit">{{ scope.row.plan_profit >= 0 ? '+' : '' }}{{ scope.row.plan_profit?.toFixed(0) }}元</div>
              <div class="plan-rate">{{ scope.row.plan_profit_rate >= 0 ? '+' : '' }}{{ scope.row.plan_profit_rate?.toFixed(1) }}%</div>
            </div>
            <span v-else class="no-plan">待执行</span>
          </template>
        </el-table-column>
        <el-table-column prop="latest_rating" label="评级" width="80">
          <template #default="scope">
            <el-tag :type="getRatingType(scope.row.latest_rating)" size="small">
              {{ scope.row.latest_rating }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="review_score" label="复审得分" width="100" sortable="custom" align="center">
          <template #default="scope">
            <div v-if="scope.row.reviewData && scope.row.reviewData.reviewed">
              <el-tag 
                :type="getReviewScoreType(scope.row.reviewData.review_score)" 
                size="small"
                effect="dark"
                class="review-score-tag"
              >
                {{ scope.row.reviewData.review_score?.toFixed(1) }}
              </el-tag>
            </div>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column label="查看" width="80" align="center">
          <template #default="scope">
            <div v-if="scope.row.reviewData && scope.row.reviewData.reviewed">
              <el-button size="small" type="primary" link @click="showReviewDetail(scope.row)">
                <el-icon><View /></el-icon> 查看
              </el-button>
            </div>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column prop="review_time" label="复审日期" width="170" align="center">
          <template #default="scope">
            <span v-if="scope.row.reviewData && scope.row.reviewData.reviewed">{{ formatReviewTime(scope.row.reviewData.review_time) }}</span>
            <span v-else>-</span>
          </template>
        </el-table-column>

        <el-table-column label="各维度评分" width="180">
          <el-table-column prop="technical_score" label="技术面" width="60" sortable="custom">
            <template #default="scope">
              <el-tooltip placement="top" :disabled="!getTechnicalDetail(scope.row)">
                <template #content>
                  <div class="tooltip-content" v-if="getTechnicalDetail(scope.row)">
                    <div v-for="(item, key) in getTechnicalDetail(scope.row)" :key="key" class="tooltip-item">
                      <strong>{{ getTechnicalLabel(key) }}:</strong> {{ item.score }}分 - {{ item.detail }}
                    </div>
                  </div>
                </template>
                <span :class="getScoreClass(scope.row.technical_score)">
                  {{ (scope.row.technical_score || 0).toFixed(0) }}
                </span>
              </el-tooltip>
            </template>
          </el-table-column>
          <el-table-column prop="fundamental_score" label="基本面" width="60" sortable="custom">
            <template #default="scope">
              <el-tooltip placement="top" :disabled="!getFundamentalDetail(scope.row)">
                <template #content>
                  <div class="tooltip-content" v-if="getFundamentalDetail(scope.row)">
                    <div v-for="(item, key) in getFundamentalDetail(scope.row)" :key="key" class="tooltip-item">
                      <strong>{{ getFundamentalLabel(key) }}:</strong> {{ item.score }}分 ({{ item.value }}) - {{ item.detail }}
                    </div>
                  </div>
                </template>
                <span :class="getScoreClass(scope.row.fundamental_score)">
                  {{ (scope.row.fundamental_score || 0).toFixed(0) }}
                </span>
              </el-tooltip>
            </template>
          </el-table-column>
          <el-table-column prop="news_score" label="消息面" width="60" sortable="custom">
            <template #default="scope">
              <el-tooltip placement="top" :disabled="!getNewsDetail(scope.row)">
                <template #content>
                  <div class="tooltip-content" v-if="getNewsDetail(scope.row)">
                    <div class="tooltip-item"><strong>消息面得分:</strong> {{ formatAdjustmentScore(scope.row.news_score || 0) }}</div>
                    <div v-for="(event, idx) in (getNewsDetail(scope.row).events || [])" :key="idx" class="tooltip-item">
                      [{{ event.date }}] {{ event.type }}: {{ event.title }} ({{ event.score_impact > 0 ? '+' : '' }}{{ event.score_impact }})
                    </div>
                  </div>
                </template>
                <span :class="getAdjustmentScoreClass(scope.row.news_score)">
                  {{ formatAdjustmentScore(scope.row.news_score || 0) }}
                </span>
              </el-tooltip>
            </template>
          </el-table-column>
          <el-table-column prop="policy_score" label="政策面" width="60" sortable="custom">
            <template #default="scope">
              <el-tooltip placement="top" :disabled="!getPolicyDetail(scope.row)">
                <template #content>
                  <div class="tooltip-content" v-if="getPolicyDetail(scope.row)">
                    <div class="tooltip-item"><strong>政策面得分:</strong> {{ formatAdjustmentScore(scope.row.policy_score || 0) }}</div>
                    <div v-for="(policy, idx) in (getPolicyDetail(scope.row).policies || [])" :key="idx" class="tooltip-item">
                      [{{ policy.level }}] {{ policy.title }} ({{ policy.score_impact > 0 ? '+' : '' }}{{ policy.score_impact }})
                    </div>
                  </div>
                </template>
                <span :class="getAdjustmentScoreClass(scope.row.policy_score)">
                  {{ formatAdjustmentScore(scope.row.policy_score || 0) }}
                </span>
              </el-tooltip>
            </template>
          </el-table-column>
          <el-table-column prop="deduction_score" label="扣分" width="50" sortable="custom">
            <template #default="scope">
              <el-tooltip placement="top" :disabled="!getDeductionDetail(scope.row)">
                <template #content>
                  <div class="tooltip-content" v-if="getDeductionDetail(scope.row)">
                    <div v-for="(item, idx) in (getDeductionDetail(scope.row).items || [])" :key="idx" class="tooltip-item">
                      <strong>{{ item.type }}:</strong> -{{ item.deduction }}分 - {{ item.detail }}
                    </div>
                    <div v-if="!(getDeductionDetail(scope.row).items || []).length" class="tooltip-item">
                      暂无明显风险项
                    </div>
                  </div>
                </template>
                <span :class="scope.row.deduction_score > 0 ? 'score-bad' : 'score-good'">
                  {{ (scope.row.deduction_score || 0).toFixed(0) }}
                </span>
              </el-tooltip>
            </template>
          </el-table-column>
        </el-table-column>
        <el-table-column prop="create_time" label="最近打分时间" width="180" sortable="custom">
          <template #default="scope">
            <span>{{ scope.row.create_time || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="230" fixed="right">
          <template #default="scope">
            <div class="operation-buttons">
              <el-button size="small" type="primary" @click="viewStockIndicator(scope.row.stock_code)">
                指标
              </el-button>
              <el-button size="small" type="primary" @click="viewDetail(scope.row)">
                详情
              </el-button>
              <el-button size="small" type="success" @click="createPlan(scope.row)">
                计划
              </el-button>
              <el-button size="small" type="warning" @click="openPredictionDialog(scope.row)">
                预判
              </el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>
      
      <!-- 分页 -->
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50, 100]"
          :total="filteredData.length"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>

    <!-- 批量评价进度对话框 -->
    <el-dialog 
      v-model="showProgressDialog" 
      title="批量评价进度" 
      width="500px" 
      :close-on-click-modal="false"
      :close-on-press-escape="false"
      :show-close="false"
    >
      <div style="text-align: center; padding: 20px;">
        <el-progress 
          :percentage="evaluateProgress.percentage" 
          :format="progressFormat"
          :stroke-width="20"
        />
        <p style="margin-top: 20px; font-size: 16px; color: #606266;">
          {{ evaluateProgress.current }} / {{ evaluateProgress.total }}
        </p>
        <p style="margin-top: 10px; font-size: 14px; color: #909399;">
          正在评价: {{ evaluateProgress.currentStock }}
        </p>
      </div>
    </el-dialog>

    <!-- 复审意见详情弹窗 -->
    <el-dialog 
      v-model="showReviewDetailDialog" 
      title="技术面复审报告" 
      width="700px"
      :close-on-click-modal="true"
      class="review-detail-dialog"
    >
      <div v-if="currentReviewData" class="review-detail-content">
        <div class="detail-header">
          <div class="detail-stock-info">
            <h3>{{ currentReviewData.stock_name }} ({{ currentReviewData.stock_code }})</h3>
            <div class="detail-rating-badge">
              <el-tag :type="getReviewScoreType(currentReviewData.review_score)" size="large" effect="dark">
                {{ currentReviewData.review_score?.toFixed(1) }}分
              </el-tag>
              <el-tag :type="getReviewRatingType(currentReviewData.review_rating)" size="large">
                {{ currentReviewData.review_rating }}
              </el-tag>
            </div>
          </div>
          <div class="detail-meta">
            <span>📅 复审时间：{{ currentReviewData.review_time }}</span>
            <span>🏢 所属板块：{{ currentReviewData.industry || '未知' }}</span>
          </div>
        </div>

        <el-divider />

        <div class="detail-body">
          <pre class="review-opinion-full">{{ currentReviewData.review_opinion }}</pre>
        </div>
      </div>
    </el-dialog>

    <!-- 预判记录弹窗 -->
    <el-dialog
      v-model="showPredictionDialog"
      :title="`预判 - ${predictionStock?.stock_name || ''}(${predictionStock?.stock_code || ''})`"
      width="95%"
      :close-on-click-modal="true"
      class="prediction-dialog"
    >
      <div class="prediction-dialog-content">
        <!-- 新建预判表单 -->
        <el-card class="prediction-form-card" shadow="never">
          <template #header>
            <div class="prediction-form-header">
              <span>新建预判</span>
              <span class="prediction-price-info" v-if="predictionStock">
                当前价格: <strong>{{ predictionStock.close_price?.toFixed(2) || '-' }}</strong>
              </span>
            </div>
          </template>
          <el-form :model="predictionForm" label-width="100px" size="default">
            <el-row :gutter="20">
              <el-col :span="8">
                <el-form-item label="预测方向">
                  <el-radio-group v-model="predictionForm.prediction_direction">
                    <el-radio-button label="看涨">
                      <span style="color: #f56c6c; font-weight: bold;">看涨 ↑</span>
                    </el-radio-button>
                    <el-radio-button label="看跌">
                      <span style="color: #67c23a; font-weight: bold;">看跌 ↓</span>
                    </el-radio-button>
                  </el-radio-group>
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="预测周期">
                  <el-select v-model="predictionForm.prediction_period" placeholder="选择预测周期">
                    <el-option label="3天" :value="3" />
                    <el-option label="5天" :value="5" />
                    <el-option label="7天（1周）" :value="7" />
                    <el-option label="10天" :value="10" />
                    <el-option label="14天（2周）" :value="14" />
                    <el-option label="20天（1月）" :value="20" />
                    <el-option label="30天" :value="30" />
                    <el-option label="60天（2月）" :value="60" />
                    <el-option label="90天（3月）" :value="90" />
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item>
                  <el-button type="primary" @click="submitPrediction" :loading="submittingPrediction">
                    提交预判
                  </el-button>
                </el-form-item>
              </el-col>
            </el-row>
            <el-form-item label="复审意见" v-if="predictionReviewInfo">
              <el-input
                v-model="predictionReviewInfo"
                type="textarea"
                :autosize="{ minRows: 6, maxRows: 20 }"
                readonly
                resize="none"
                class="review-info-readonly"
              />
            </el-form-item>
            <el-form-item label="分析理由">
              <el-input
                v-model="predictionForm.review_info"
                type="textarea"
                :rows="3"
                placeholder="请输入你的分析理由和预判依据..."
              />
            </el-form-item>
          </el-form>
        </el-card>

        <!-- 预判历史记录 -->
        <el-card class="prediction-history-card" shadow="never">
          <template #header>
            <div class="prediction-form-header">
              <span>预判记录</span>
              <span v-if="predictionStats" class="prediction-stats-info">
                共{{ predictionStats.total_count }}次 | 成功{{ predictionStats.correct_count }}次 | 成功率{{ predictionStats.success_rate }}%
              </span>
            </div>
          </template>
          <el-table :data="predictionList" style="width: 100%" size="small" max-height="400" v-loading="loadingPredictions">
            <el-table-column prop="prediction_time" label="预判时间" width="170">
              <template #default="scope">
                {{ formatPredictionTime(scope.row.prediction_time) }}
              </template>
            </el-table-column>
            <el-table-column prop="current_price" label="对标价格" width="100" align="right">
              <template #default="scope">
                {{ scope.row.current_price?.toFixed(2) || '-' }}
              </template>
            </el-table-column>
            <el-table-column prop="prediction_direction" label="方向" width="80" align="center">
              <template #default="scope">
                <el-tag :type="scope.row.prediction_direction === '看涨' ? 'danger' : 'success'" size="small" effect="dark">
                  {{ scope.row.prediction_direction }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="prediction_period" label="周期" width="70" align="center">
              <template #default="scope">
                {{ scope.row.prediction_period }}天
              </template>
            </el-table-column>
            <el-table-column prop="target_date" label="到期日" width="110" align="center" />
            <el-table-column prop="actual_direction" label="实际" width="80" align="center">
              <template #default="scope">
                <el-tag v-if="scope.row.actual_direction" :type="scope.row.actual_direction === '看涨' ? 'danger' : scope.row.actual_direction === '看跌' ? 'success' : 'info'" size="small">
                  {{ scope.row.actual_direction }}
                </el-tag>
                <span v-else class="pending-text">待定</span>
              </template>
            </el-table-column>
            <el-table-column prop="is_correct" label="结果" width="80" align="center">
              <template #default="scope">
                <el-tag v-if="scope.row.is_correct === 1" type="success" size="small" effect="dark">正确</el-tag>
                <el-tag v-else-if="scope.row.is_correct === -1" type="warning" size="small" effect="dark">持平</el-tag>
                <el-tag v-else-if="scope.row.is_correct === 0 && scope.row.status === 'settled'" type="danger" size="small" effect="dark">错误</el-tag>
                <el-tag v-else type="info" size="small">待验证</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="review_info" label="分析理由" min-width="200">
              <template #default="scope">
                <el-tooltip v-if="scope.row.review_info" placement="top" :show-after="300">
                  <template #content>
                    <div class="prediction-review-tooltip">{{ scope.row.review_info }}</div>
                  </template>
                  <span class="review-info-preview">{{ scope.row.review_info }}</span>
                </el-tooltip>
                <span v-else class="no-review">-</span>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="140" align="center">
              <template #default="scope">
                <el-button v-if="scope.row.status === 'pending'" size="small" type="warning" link @click="settleSinglePrediction(scope.row)">
                  判定
                </el-button>
                <el-button size="small" type="danger" link @click="deletePredictionRecord(scope.row)">
                  删除
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Refresh, Check, Delete, Select, Star, ArrowLeft, Search, View, DataAnalysis } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox, ElNotification } from 'element-plus'
import { scoreApi, stockApi } from '../api'
import api from '../api'

const router = useRouter()

const EVALUATE_STORAGE_KEY = 'stock_evaluate_status'

const stockTableRef = ref(null)
const stockPool = ref([])
const loading = ref(false)
const searchText = ref('')
const ratingFilter = ref('')
const showOnlyFavorite = ref(false)
const currentPage = ref(1)
const pageSize = ref(20)
const sortProp = ref('composite_score')
const sortOrder = ref('descending')
const selectedStocks = ref([])
const batchEvaluating = ref(false)
const evaluating = ref(false)
const cleaning = ref(false)
const reviewing = ref(false)
const showProgressDialog = ref(false)
const evaluateProgress = ref({
  current: 0,
  total: 0,
  percentage: 0,
  currentStock: ''
})
const reviewProgress = ref({
  current: 0,
  total: 0,
  percentage: 0,
  currentStock: ''
})

const showReviewDetailDialog = ref(false)
const currentReviewData = ref(null)

const showPredictionDialog = ref(false)
const predictionStock = ref(null)
const predictionList = ref([])
const predictionStats = ref(null)
const loadingPredictions = ref(false)
const submittingPrediction = ref(false)
const predictionReviewInfo = ref('')
const predictionStatsMap = ref({})
const predictionForm = ref({
  prediction_direction: '看涨',
  prediction_period: 7,
  review_info: ''
})

const filteredData = computed(() => {
  let data = [...stockPool.value]
  
  if (searchText.value) {
    const search = searchText.value.toLowerCase()
    data = data.filter(item => 
      item.stock_code?.toLowerCase().includes(search) ||
      item.stock_name?.toLowerCase().includes(search)
    )
  }
  
  if (ratingFilter.value) {
    data = data.filter(item => item.latest_rating === ratingFilter.value)
  }
  
  if (showOnlyFavorite.value) {
    data = data.filter(item => item.is_favorite === 1)
  }
  
  if (sortProp.value && sortOrder.value) {
    data.sort((a, b) => {
      if (sortProp.value === 'review_score') {
        const aScore = a.reviewData?.review_score ?? -1
        const bScore = b.reviewData?.review_score ?? -1
        return sortOrder.value === 'ascending' ? aScore - bScore : bScore - aScore
      }

      const aVal = a[sortProp.value]
      const bVal = b[sortProp.value]

      if (sortProp.value === 'plan_profit_rate') {
        const getStatusPriority = (item) => {
          if (!item.plan_status) return 4
          if (item.plan_status === 'profit') return 1
          if (item.plan_status === 'neutral') return 2
          if (item.plan_status === 'loss') return 3
          return 4
        }

        const aPriority = getStatusPriority(a)
        const bPriority = getStatusPriority(b)

        if (aPriority === bPriority && aPriority !== 4) {
          const aRate = a.plan_profit_rate || 0
          const bRate = b.plan_profit_rate || 0
          return sortOrder.value === 'ascending' ? aRate - bRate : bRate - aRate
        }

        return sortOrder.value === 'ascending' ? aPriority - bPriority : bPriority - aPriority
      }

      if (sortProp.value === 'create_time') {
        const aTime = aVal ? new Date(aVal).getTime() : 0
        const bTime = bVal ? new Date(bVal).getTime() : 0
        return sortOrder.value === 'ascending' ? aTime - bTime : bTime - aTime
      }

      const aNum = aVal || 0
      const bNum = bVal || 0
      return sortOrder.value === 'ascending' ? aNum - bNum : bNum - aNum
    })
  }
  
  return data
})

const paginatedData = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return filteredData.value.slice(start, end)
})

const ratingStats = computed(() => {
  /**
   * 统计各评级的股票数量
   * 用于统计卡片显示
   */
  const stats = {
    strongRecommended: 0,
    recommended: 0,
    neutral: 0,
    watch: 0,
    notRecommended: 0
  }
  stockPool.value.forEach(item => {
    if (item.latest_rating === '强烈推荐') {
      stats.strongRecommended++
    } else if (item.latest_rating === '推荐') {
      stats.recommended++
    } else if (item.latest_rating === '中性') {
      stats.neutral++
    } else if (item.latest_rating === '观望') {
      stats.watch++
    } else if (item.latest_rating === '不推荐') {
      stats.notRecommended++
    }
  })
  return stats
})

const favoriteCount = computed(() => {
  return stockPool.value.filter(item => item.is_favorite === 1).length
})

const getScoreType = (score) => {
  /**
   * 根据评分返回标签类型
   * @param {number} score - 评分值
   * @returns {string} Element Plus标签类型
   */
  if (score >= 90) return 'success'
  if (score >= 70) return 'primary'
  if (score >= 50) return 'warning'
  return 'info'
}

const getTrendPoints = (history) => {
  /**
   * 计算评分趋势图的SVG折线点坐标
   * @param {Array} history - 评分历史数组
   * @returns {string} SVG折线点坐标字符串
   */
  if (!history || history.length < 1) return ''

  const scores = history.map(h => h.score || 0)
  const minScore = Math.min(...scores)
  const maxScore = Math.max(...scores)
  const range = maxScore - minScore || 1

  const width = 60
  const height = 20
  const padding = 2

  const points = scores.map((score, index) => {
    const x = padding + (index / Math.max(scores.length - 1, 1)) * (width - 2 * padding)
    const y = height - padding - ((score - minScore) / range) * (height - 2 * padding)
    return `${x.toFixed(1)},${y.toFixed(1)}`
  })

  return points.join(' ')
}

const getTrendColor = (history) => {
  /**
   * 根据评分变化趋势返回颜色
   * @param {Array} history - 评分历史数组
   * @returns {string} 颜色值（绿色上涨/红色下跌/灰色持平）
   */
  if (!history || history.length < 2) return '#909399'
  
  const firstScore = history[0].score || 0
  const lastScore = history[history.length - 1].score || 0
  
  if (lastScore > firstScore) return '#67c23a'
  if (lastScore < firstScore) return '#f56c6c'
  return '#909399'
}

const getPriceTrendPoints = (history) => {
  /**
   * 计算股价趋势图的SVG折线点坐标
   * @param {Array} history - 股价历史数组
   * @returns {string} SVG折线点坐标字符串
   */
  if (!history || history.length < 1) return ''

  const prices = history.map(h => h.price || 0)

  const width = 60
  const height = 20
  const padding = 2

  if (prices.length === 1) {
    return `${padding},${height/2}`
  }

  const minPrice = Math.min(...prices)
  const maxPrice = Math.max(...prices)
  let range = maxPrice - minPrice

  const minRange = maxPrice * 0.005
  if (range < minRange && range > 0) {
    range = minRange
  } else if (range === 0) {
    return `${padding},${height/2} ${width-padding},${height/2}`
  }

  const points = prices.map((price, index) => {
    const x = padding + (index / Math.max(prices.length - 1, 1)) * (width - 2 * padding)
    const y = height - padding - ((price - minPrice) / range) * (height - 2 * padding)
    return `${x.toFixed(1)},${y.toFixed(1)}`
  })

  return points.join(' ')
}

const getPriceCirclePoints = (history) => {
  if (!history || history.length < 1) return []

  const prices = history.map(h => h.price || 0)

  const width = 60
  const height = 20
  const padding = 2

  if (prices.length === 1) {
    return [{
      x: padding,
      y: height / 2,
      price: prices[0],
      date: history[0].date
    }]
  }

  const minPrice = Math.min(...prices)
  const maxPrice = Math.max(...prices)
  let range = maxPrice - minPrice

  const minRange = maxPrice * 0.005
  if (range < minRange && range > 0) {
    range = minRange
  } else if (range === 0) {
    return prices.map((price, index) => ({
      x: padding + (index / Math.max(prices.length - 1, 1)) * (width - 2 * padding),
      y: height / 2,
      price: price,
      date: history[index].date
    }))
  }

  return prices.map((price, index) => ({
    x: padding + (index / Math.max(prices.length - 1, 1)) * (width - 2 * padding),
    y: height - padding - ((price - minPrice) / range) * (height - 2 * padding),
    price: price,
    date: history[index].date
  }))
}

const getPriceByDate = (priceHistory, date) => {
  if (!priceHistory || !date) return null
  const record = priceHistory.find(item => item.date === date)
  return record ? record.price : null
}

const getScoreCirclePoints = (history) => {
  if (!history || history.length < 1) return []

  const scores = history.map(h => h.score || 0)
  const minScore = Math.min(...scores)
  const maxScore = Math.max(...scores)
  const range = maxScore - minScore || 1

  const width = 60
  const height = 20
  const padding = 2

  return scores.map((score, index) => ({
    x: padding + (index / Math.max(scores.length - 1, 1)) * (width - 2 * padding),
    y: height - padding - ((score - minScore) / range) * (height - 2 * padding),
    score: score,
    date: history[index].date
  }))
}

const getTechTrendPoints = (history) => {
  if (!history || history.length < 1) return ''

  const scores = history.map(h => h.score || 0)
  const minScore = Math.min(...scores)
  const maxScore = Math.max(...scores)
  const range = maxScore - minScore || 1

  const width = 60
  const height = 20
  const padding = 2

  const points = scores.map((score, index) => {
    const x = padding + (index / Math.max(scores.length - 1, 1)) * (width - 2 * padding)
    const y = height - padding - ((score - minScore) / range) * (height - 2 * padding)
    return `${x.toFixed(1)},${y.toFixed(1)}`
  })

  return points.join(' ')
}

const getTechCirclePoints = (history) => {
  if (!history || history.length < 1) return []

  const scores = history.map(h => h.score || 0)
  const minScore = Math.min(...scores)
  const maxScore = Math.max(...scores)
  const range = maxScore - minScore || 1

  const width = 60
  const height = 20
  const padding = 2

  return scores.map((score, index) => ({
    x: padding + (index / Math.max(scores.length - 1, 1)) * (width - 2 * padding),
    y: height - padding - ((score - minScore) / range) * (height - 2 * padding),
    score: score,
    date: history[index].date
  }))
}

const getScoreClass = (score) => {
  /**
   * 根据评分返回CSS类名
   * @param {number} score - 评分值
   * @returns {string} CSS类名
   */
  if (score >= 70) return 'score-good'
  if (score >= 50) return 'score-normal'
  return 'score-bad'
}

const getAdjustmentScoreClass = (score) => {
  if (score > 0) return 'score-good'
  if (score < 0) return 'score-bad'
  return 'score-normal'
}

const formatAdjustmentScore = (score) => {
  if (score > 0) return `+${score.toFixed(0)}`
  if (score < 0) return score.toFixed(0)
  return '0'
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

const parseDetail = (detail) => {
  if (!detail) return null
  try {
    return typeof detail === 'string' ? JSON.parse(detail) : detail
  } catch (e) {
    return null
  }
}

const getTechnicalDetail = (row) => parseDetail(row.technical_detail)
const getFundamentalDetail = (row) => parseDetail(row.fundamental_detail)
const getNewsDetail = (row) => parseDetail(row.news_detail)
const getPolicyDetail = (row) => parseDetail(row.policy_detail)
const getDeductionDetail = (row) => parseDetail(row.deduction_detail)

const loadReviewData = async (row) => {
  if (row._reviewLoading) return
  
  row._reviewLoading = true
  
  try {
    const reviewData = await stockApi.getReviewInfo(row.stock_code)
    row.reviewData = reviewData
    row._reviewLoading = false
    
    if (!reviewData.reviewed) {
      ElMessage.info(`${row.stock_name}(${row.stock_code}) 尚未进行复审`)
    }
  } catch (error) {
    console.error('获取复审信息失败:', error)
    row.reviewData = { reviewed: false }
    row._reviewLoading = false
    ElMessage.error(`获取${row.stock_name}复审信息失败`)
  }
}

const getReviewScoreType = (score) => {
  if (score >= 85) return 'success'
  if (score >= 70) return 'primary'
  if (score >= 55) return 'warning'
  if (score >= 40) return 'info'
  return 'danger'
}

const getReviewRatingType = (rating) => {
  const types = {
    '强烈推荐': 'success',
    '推荐': 'primary',
    '中性': 'warning',
    '谨慎': 'info',
    '回避': 'danger'
  }
  return types[rating] || 'info'
}

const getReviewOpinionPreview = (opinion) => {
  if (!opinion) return '-'
  
  const lines = opinion.split('\n')
  const suggestionLine = lines.find(line => line.includes('操作建议：'))
  
  if (suggestionLine) {
    return suggestionLine.replace(/.*操作建议：/, '').trim()
  }
  
  return lines.slice(2, 6).join('\n') || opinion.substring(0, 100) + '...'
}

const showReviewDetail = (row) => {
  if (row.reviewData && row.reviewData.reviewed) {
    currentReviewData.value = row.reviewData
    showReviewDetailDialog.value = true
  }
}

const getReviewOpinionSummary = (reviewData) => {
  if (!reviewData || !reviewData.reviewed) {
    return '暂无'
  }
  
  // 优先显示提取的建议
  if (reviewData.suggestion) {
    const maxLen = 15
    if (reviewData.suggestion.length > maxLen) {
      return reviewData.suggestion.substring(0, maxLen) + '...'
    }
    return reviewData.suggestion
  }
  
  return '点击查看详情'
}

const formatReviewTime = (timeStr) => {
  if (!timeStr) return '-'
  
  try {
    const date = new Date(timeStr)
    const year = date.getFullYear()
    const month = String(date.getMonth() + 1).padStart(2, '0')
    const day = String(date.getDate()).padStart(2, '0')
    const hours = String(date.getHours()).padStart(2, '0')
    const minutes = String(date.getMinutes()).padStart(2, '0')
    const seconds = String(date.getSeconds()).padStart(2, '0')
    return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`
  } catch (e) {
    return timeStr
  }
}

const getPlanStatusText = (row) => {
  /**
   * 根据计划状态返回提示文本
   * @param {Object} row - 股票数据行
   * @returns {string} 提示文本
   */
  const status = row.plan_status
  const profit = row.plan_profit || 0
  const profitRate = row.plan_profit_rate || 0
  
  const statusTexts = {
    'profit': '执行中',
    'loss': '执行中',
    'neutral': '执行中'
  }
  
  const profitStr = profit >= 0 ? `+${profit.toFixed(2)}` : profit.toFixed(2)
  const profitRateStr = profitRate >= 0 ? `+${profitRate.toFixed(2)}%` : `${profitRate.toFixed(2)}%`
  
  return `有未完成计划 - ${statusTexts[status] || '待执行'}\n盈亏: ${profitStr}元 (${profitRateStr})`
}

const handleSortChange = ({ prop, order }) => {
  sortProp.value = prop
  sortOrder.value = order
}

const filterByRating = (rating) => {
  if (ratingFilter.value === rating) {
    ratingFilter.value = ''
  } else {
    ratingFilter.value = rating
  }
}

const toggleFavoriteFilter = () => {
  showOnlyFavorite.value = !showOnlyFavorite.value
  currentPage.value = 1
}

const toggleFavorite = async (row) => {
  try {
    const response = await api.post('/stocks/favorite', {
      stock_code: row.stock_code
    })
    if (response.success) {
      row.is_favorite = response.is_favorite
      ElMessage.success(response.message)
    }
  } catch (error) {
    console.error('收藏操作失败:', error)
    ElMessage.error('收藏操作失败')
  }
}

const handleSizeChange = (val) => {
  pageSize.value = val
  currentPage.value = 1
}

const handleCurrentChange = (val) => {
  currentPage.value = val
}

const loadStockPool = async () => {
  loading.value = true
  try {
    const data = await scoreApi.getStockPoolScores()
    stockPool.value = data.stocks || []
    
    // 批量加载所有股票的复审信息
    await batchLoadReviewData()
  } catch (error) {
    console.error('加载股票池失败:', error)
    ElMessage.error('加载股票池失败')
  } finally {
    loading.value = false
  }
}

const batchLoadReviewData = async () => {
  try {
    const reviewList = await stockApi.getReviewList({ limit: 500 })
    
    if (reviewList.success && reviewList.reviews) {
      const reviewMap = {}
      reviewList.reviews.forEach(review => {
        // 使用多种格式作为 key 进行匹配
        reviewMap[review.stock_code] = review
        const pureCode = review.stock_code.replace(/^sh|^sz|^bj/, '')
        reviewMap[pureCode] = review
        reviewMap[`sh${pureCode}`] = review
        reviewMap[`sz${pureCode}`] = review
        reviewMap[`bj${pureCode}`] = review
      })
      
      // 将复审数据映射到对应的股票行
      stockPool.value.forEach(stock => {
        // 尝试多种格式匹配
        let matchedReview = reviewMap[stock.stock_code]
        
        if (!matchedReview) {
          const pureCode = stock.stock_code.replace(/^sh|^sz|^bj/, '')
          matchedReview = reviewMap[pureCode] || 
                         reviewMap[`sh${pureCode}`] || 
                         reviewMap[`sz${pureCode}`] || 
                         reviewMap[`bj${pureCode}`]
        }
        
        if (matchedReview) {
          stock.reviewData = {
            ...matchedReview,
            reviewed: true,
            suggestion: extractSuggestion(matchedReview.review_opinion)
          }
        } else {
          stock.reviewData = { reviewed: false }
        }
      })
    }
  } catch (error) {
    console.warn('批量加载复审信息失败:', error)
    // 失败时为所有股票设置默认值
    stockPool.value.forEach(stock => {
      stock.reviewData = { reviewed: false }
    })
  }
}

const extractSuggestion = (opinion) => {
  if (!opinion) return ''
  
  const lines = opinion.split('\n')
  const suggestionLine = lines.find(line => line.includes('操作建议：'))
  
  if (suggestionLine) {
    return suggestionLine.replace(/.*操作建议：/, '').trim()
  }
  
  return ''
}

const refreshPool = () => {
  ElMessage.success('正在刷新股票池...')
  loadStockPool()
}

const handleSelectionChange = (selection) => {
  selectedStocks.value = selection
}

const selectExecutingStocks = () => {
  if (!stockTableRef.value) return
  
  stockTableRef.value.clearSelection()
  
  let count = 0
  paginatedData.value.forEach(row => {
    if (row.plan_status && ['profit', 'loss', 'neutral'].includes(row.plan_status)) {
      stockTableRef.value.toggleRowSelection(row, true)
      count++
    }
  })
  
  ElMessage.success(`已选中 ${count} 只有执行计划的股票`)
}

const batchEvaluate = async () => {
  if (selectedStocks.value.length === 0) {
    ElMessage.warning('请先选择要评价的股票')
    return
  }
  
  batchEvaluating.value = true
  showProgressDialog.value = true
  const stocks = selectedStocks.value
  const total = stocks.length
  
  evaluateProgress.value = {
    current: 0,
    total: total,
    percentage: 0,
    currentStock: ''
  }
  
  let successCount = 0
  let failCount = 0
  
  for (let i = 0; i < stocks.length; i++) {
    const stock = stocks[i]
    evaluateProgress.value.current = i + 1
    evaluateProgress.value.percentage = Math.round(((i + 1) / total) * 100)
    evaluateProgress.value.currentStock = `${stock.stock_name} (${stock.stock_code})`
    
    try {
      await api.post('/stocks/evaluate', {
        stock_code: stock.stock_code
      }, { timeout: 120000 })
      successCount++
    } catch (error) {
      console.error(`评价 ${stock.stock_code} 失败:`, error)
      failCount++
    }
  }
  
  showProgressDialog.value = false
  batchEvaluating.value = false
  
  if (successCount > 0) {
    ElMessage.success(`批量评价完成！成功: ${successCount}, 失败: ${failCount}`)
  } else {
    ElMessage.error(`批量评价失败，请检查后端服务`)
  }
  selectedStocks.value = []
  loadStockPool()
}

const batchEvaluateAll = async () => {
  try {
    await ElMessageBox.confirm('确定要评价所有股票吗？评价将在后台运行，可以继续其他操作。', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
  } catch {
    return
  }

  evaluating.value = true

  try {
    // 调用异步评价API
    const result = await stockApi.batchEvaluateAsync()

    if (!result.success) {
      ElNotification.error({
        title: '启动失败',
        message: result.message || '无法启动评价任务'
      })
      evaluating.value = false
      return
    }

    const taskId = result.taskId
    evaluateProgress.value.total = result.total

    // 保存评价状态到localStorage
    saveEvaluateStatus({
      taskId,
      evaluating: true,
      progress: {
        current: 0,
        total: result.total,
        percentage: 0,
        currentStock: ''
      },
      startTime: Date.now()
    })

    ElNotification.info({
      title: '任务已启动',
      message: `正在后台评价${result.total}只股票...`,
      duration: 3000
    })

    // 开始轮询进度
    pollEvaluateProgress(taskId)

  } catch (error) {
    console.error('一键评价启动失败:', error)
    ElNotification.error({
      title: '启动失败',
      message: error.message || '网络错误，请重试'
    })
    evaluating.value = false
  }
}

let progressTimer = null

const saveEvaluateStatus = (status) => {
  try {
    localStorage.setItem(EVALUATE_STORAGE_KEY, JSON.stringify(status))
  } catch (error) {
    console.error('保存评价状态失败:', error)
  }
}

const clearEvaluateStatus = () => {
  try {
    localStorage.removeItem(EVALUATE_STORAGE_KEY)
  } catch (error) {
    console.error('清除评价状态失败:', error)
  }
}

const restoreEvaluateStatus = () => {
  try {
    const saved = localStorage.getItem(EVALUATE_STORAGE_KEY)
    if (saved) {
      const status = JSON.parse(saved)
      // 检查状态是否过期（超过30分钟则清除）
      if (Date.now() - status.startTime > 30 * 60 * 1000) {
        clearEvaluateStatus()
        return null
      }
      return status
    }
  } catch (error) {
    console.error('读取评价状态失败:', error)
  }
  return null
}

const pollEvaluateProgress = async (taskId) => {
  if (progressTimer) {
    clearInterval(progressTimer)
  }

  // 每2秒查询一次进度
  progressTimer = setInterval(async () => {
    try {
      const progress = await stockApi.getEvaluateProgress(taskId)

      // 更新进度显示
      evaluateProgress.value = {
        current: progress.current || 0,
        total: progress.total || 0,
        percentage: progress.percentage || 0,
        currentStock: progress.currentStock || ''
      }

      // 检查是否完成或失败
      if (progress.status === 'completed') {
        clearInterval(progressTimer)
        progressTimer = null
        evaluating.value = false

        // 清除保存的评价状态
        clearEvaluateStatus()

        ElNotification.success({
          title: '评价完成',
          message: progress.message || `成功${progress.successCount}只，失败${progress.failedCount}只`,
          duration: 5000
        })

        // 刷新股票池数据
        await loadStockPool()
      } else if (progress.status === 'failed') {
        clearInterval(progressTimer)
        progressTimer = null
        evaluating.value = false

        // 清除保存的评价状态
        clearEvaluateStatus()

        ElNotification.error({
          title: '评价失败',
          message: progress.message || '任务执行失败'
        })
      }

    } catch (error) {
      console.error('查询进度失败:', error)
      // 如果查询失败3次，停止轮询
      // 这里简单处理：继续轮询直到手动刷新页面
    }
  }, 2000)  // 2秒轮询一次
}

const REVIEW_STORAGE_KEY = 'stock_review_status'
let reviewTimer = null

const batchReviewAll = async () => {
  try {
    await ElMessageBox.confirm('确定要复审所有未复审的股票吗？复审将在后台运行，可以继续其他操作。', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
  } catch {
    return
  }

  reviewing.value = true

  try {
    const result = await stockApi.batchReviewAsync()

    if (!result.success) {
      ElNotification.error({
        title: '启动失败',
        message: result.message || '无法启动复审任务'
      })
      reviewing.value = false
      return
    }

    const taskId = result.taskId
    reviewProgress.value.total = result.total

    try {
      localStorage.setItem(REVIEW_STORAGE_KEY, JSON.stringify({
        taskId,
        reviewing: true,
        progress: { current: 0, total: result.total, percentage: 0, currentStock: '' },
        startTime: Date.now()
      }))
    } catch (e) {}

    ElNotification.info({
      title: '复审任务已启动',
      message: `正在后台复审${result.total}只股票...`,
      duration: 3000
    })

    pollReviewProgress(taskId)

  } catch (error) {
    console.error('一键复审启动失败:', error)
    ElNotification.error({
      title: '启动失败',
      message: error.message || '网络错误，请重试'
    })
    reviewing.value = false
  }
}

const pollReviewProgress = async (taskId) => {
  if (reviewTimer) clearInterval(reviewTimer)

  reviewTimer = setInterval(async () => {
    try {
      const progress = await stockApi.getReviewProgress(taskId)

      reviewProgress.value = {
        current: progress.current || 0,
        total: progress.total || 0,
        percentage: progress.percentage || 0,
        currentStock: progress.currentStock || ''
      }

      if (progress.status === 'completed') {
        clearInterval(reviewTimer)
        reviewTimer = null
        reviewing.value = false

        try { localStorage.removeItem(REVIEW_STORAGE_KEY) } catch (e) {}

        ElNotification.success({
          title: '复审完成',
          message: progress.message || `成功${progress.successCount}只，失败${progress.failedCount}只`,
          duration: 5000
        })

        loadStockPool()
        batchLoadReviewData()

      } else if (progress.status === 'failed') {
        clearInterval(reviewTimer)
        reviewTimer = null
        reviewing.value = false

        try { localStorage.removeItem(REVIEW_STORAGE_KEY) } catch (e) {}

        ElNotification.error({
          title: '复审失败',
          message: progress.message || '任务执行失败'
        })
      }
    } catch (error) {
      console.error('查询复审进度失败:', error)
    }
  }, 2000)
}

onMounted(async () => {
  const savedReviewStatus = (() => {
    try {
      const s = localStorage.getItem(REVIEW_STORAGE_KEY)
      if (s) {
        const status = JSON.parse(s)
        if (Date.now() - status.startTime > 60 * 60 * 1000) {
          localStorage.removeItem(REVIEW_STORAGE_KEY)
          return null
        }
        return status
      }
    } catch (e) {}
    return null
  })()

  if (savedReviewStatus && savedReviewStatus.reviewing && savedReviewStatus.taskId) {
    reviewing.value = true
    reviewProgress.value = savedReviewStatus.progress || { current: 0, total: 0, percentage: 0, currentStock: '' }
    pollReviewProgress(savedReviewStatus.taskId)
  }

  loadStockPool()
  loadPredictionStats()

  const savedStatus = restoreEvaluateStatus()
  if (savedStatus && savedStatus.evaluating && savedStatus.taskId) {
    evaluating.value = true
    evaluateProgress.value = savedStatus.progress

    ElNotification.info({
      title: '恢复评价任务',
      message: '检测到有正在进行的评价任务，已自动恢复...',
      duration: 3000
    })

    pollEvaluateProgress(savedStatus.taskId)
  }
})

const cleanupData = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要清理垃圾数据吗？此操作将删除：\n1. 股价为 0 的评价记录\n2. 同一天内的重复评价记录\n\n此操作不可恢复，请谨慎操作！',
      '警告',
      {
        confirmButtonText: '确定清理',
        cancelButtonText: '取消',
        type: 'warning',
        distinguishCancelAndClose: true
      }
    )
  } catch (action) {
    return
  }
  
  cleaning.value = true
  
  try {
    const result = await scoreApi.cleanup()
    
    ElNotification.success({
      title: '清理完成',
      message: `共删除 ${result.total_deleted} 条记录\n- 股价为 0: ${result.deleted_zero_price} 条\n- 重复评价：${result.deleted_duplicates} 条`,
      duration: 5000
    })
    
    await loadStockPool()
  } catch (error) {
    console.error('数据清理失败:', error)
    ElNotification.error({
      title: '清理失败',
      message: error.message || '网络错误，请重试'
    })
  } finally {
    cleaning.value = false
  }
}

const progressFormat = (percentage) => {
  return `${percentage}%`
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

const viewDetail = (row) => {
  router.push({
    path: '/score-detail',
    query: { stock_code: row.stock_code, stock_name: row.stock_name }
  })
}

const createPlan = (row) => {
  const reviewOpinion = row.reviewData?.review_opinion || row.reviewData?.suggestion || ''
  router.push({
    path: '/trade-plan',
    query: { 
      stock_code: row.stock_code, 
      stock_name: row.stock_name,
      close_price: row.close_price,
      review_opinion: reviewOpinion
    }
  })
}

const backToTradePlan = () => {
  router.push({
    path: '/trade-plan'
  })
}

const getPredictionStats = (stockCode) => {
  const pureCode = stockCode.replace(/^sh|^sz|^bj/, '')
  return predictionStatsMap.value[pureCode] || predictionStatsMap.value[stockCode] || null
}

const loadPredictionStats = async () => {
  try {
    const result = await stockApi.getPredictionStats()
    if (result.success && result.stats) {
      predictionStatsMap.value = result.stats
    }
  } catch (error) {
    console.warn('加载预判统计失败:', error)
  }
}

const openPredictionDialog = async (row) => {
  predictionStock.value = row
  showPredictionDialog.value = true
  predictionForm.value = {
    prediction_direction: '看涨',
    prediction_period: 7,
    review_info: ''
  }
  predictionReviewInfo.value = ''
  try {
    const reviewResult = await stockApi.getReviewInfo(row.stock_code)
    if (reviewResult.success && reviewResult.reviewed && reviewResult.review_opinion) {
      predictionReviewInfo.value = reviewResult.review_opinion
    }
  } catch (e) {
    console.warn('加载复审信息失败:', e)
  }
  await loadPredictionList(row.stock_code)
}

const loadPredictionList = async (stockCode) => {
  loadingPredictions.value = true
  try {
    const result = await stockApi.getPredictions(stockCode)
    if (result.success) {
      predictionList.value = result.predictions || []
      const pureCode = stockCode.replace(/^sh|^sz|^bj/, '')
      predictionStats.value = predictionStatsMap.value[pureCode] || predictionStatsMap.value[stockCode] || null
    }
  } catch (error) {
    console.error('加载预判记录失败:', error)
    ElMessage.error('加载预判记录失败')
  } finally {
    loadingPredictions.value = false
  }
}

const submitPrediction = async () => {
  if (!predictionStock.value) return
  if (!predictionForm.value.prediction_direction) {
    ElMessage.warning('请选择预测方向')
    return
  }
  if (!predictionForm.value.prediction_period) {
    ElMessage.warning('请选择预测周期')
    return
  }

  submittingPrediction.value = true
  try {
    const result = await stockApi.createPrediction({
      stock_code: predictionStock.value.stock_code,
      stock_name: predictionStock.value.stock_name,
      current_price: predictionStock.value.close_price,
      review_info: predictionForm.value.review_info,
      prediction_period: predictionForm.value.prediction_period,
      prediction_direction: predictionForm.value.prediction_direction
    })

    if (result.success) {
      ElMessage.success(`预判创建成功！到期日: ${result.target_date}`)
      predictionForm.value = {
        prediction_direction: '看涨',
        prediction_period: 7,
        review_info: ''
      }
      await loadPredictionList(predictionStock.value.stock_code)
      await loadPredictionStats()
    }
  } catch (error) {
    console.error('提交预判失败:', error)
    ElMessage.error('提交预判失败')
  } finally {
    submittingPrediction.value = false
  }
}

const settleSinglePrediction = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确定要判定该预判吗？将获取当前股价与对标价格对比进行判定。`,
      '预判判定',
      {
        confirmButtonText: '确定判定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
  } catch {
    return
  }

  try {
    const result = await stockApi.settlePredictions(row.id)
    if (result.success) {
      if (result.skipped_not_due > 0) {
        ElMessage.warning(result.message || '该预判尚未到期，无法判定')
      } else if (result.settled_count > 0) {
        ElMessage.success('判定完成，预测结果已更新')
      } else {
        ElMessage.info(result.message || '未能获取最新股价，请稍后再试')
      }
      if (predictionStock.value) {
        await loadPredictionList(predictionStock.value.stock_code)
      }
      await loadPredictionStats()
    }
  } catch (error) {
    console.error('判定预判失败:', error)
    ElMessage.error('判定预判失败')
  }
}

const deletePredictionRecord = async (row) => {
  try {
    await ElMessageBox.confirm('确定要删除这条预判记录吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
  } catch {
    return
  }

  try {
    const result = await stockApi.deletePrediction(row.id)
    if (result.success) {
      ElMessage.success('预判记录已删除')
      if (predictionStock.value) {
        await loadPredictionList(predictionStock.value.stock_code)
      }
      await loadPredictionStats()
    }
  } catch (error) {
    console.error('删除预判记录失败:', error)
    ElMessage.error('删除预判记录失败')
  }
}

const formatPredictionTime = (timeStr) => {
  if (!timeStr) return '-'
  try {
    const date = new Date(timeStr)
    const year = date.getFullYear()
    const month = String(date.getMonth() + 1).padStart(2, '0')
    const day = String(date.getDate()).padStart(2, '0')
    const hours = String(date.getHours()).padStart(2, '0')
    const minutes = String(date.getMinutes()).padStart(2, '0')
    return `${year}-${month}-${day} ${hours}:${minutes}`
  } catch (e) {
    return timeStr
  }
}
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.search-bar {
  display: flex;
  align-items: center;
  gap: 10px;
}

.search-bar .el-input {
  margin-right: 0;
}

.button-group {
  display: flex;
  gap: 8px;
}

.stat-card {
  text-align: center;
  padding: 10px;
}

.stat-card .stat-title {
  font-size: 12px;
  color: #909399;
  margin-bottom: 5px;
}

.stat-card .stat-value {
  font-size: 24px;
  font-weight: bold;
  color: #303133;
}

.stat-card.stat-success .stat-value {
  color: #67c23a;
}

.stat-card.stat-primary .stat-value {
  color: #409eff;
}

.stat-card.stat-warning .stat-value {
  color: #e6a23c;
}

.stat-card.stat-info .stat-value {
  color: #909399;
}

.stat-card.stat-danger .stat-value {
  color: #f56c6c;
}

.stat-card.clickable {
  cursor: pointer;
  transition: all 0.3s ease;
}

.stat-card.clickable:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.stat-card.clickable.active {
  box-shadow: 0 0 0 2px #409eff;
}

.score-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}

.trend-chart {
  width: 60px;
  height: 20px;
  flex-shrink: 0;
  cursor: pointer;
}

.trend-point {
  cursor: pointer;
  transition: r 0.2s;
}

.trend-point:hover {
  r: 4;
}

.trend-tooltip {
  padding: 8px;
  min-width: 120px;
}

.trend-tooltip .tooltip-title {
  font-weight: 600;
  margin-bottom: 8px;
  padding-bottom: 4px;
  border-bottom: 1px solid #ebeef5;
  color: #303133;
}

.trend-tooltip .tooltip-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
  font-size: 11px;
  margin-bottom: 4px;
}

.trend-tooltip .tooltip-date {
  color: #909399;
  min-width: 70px;
}

.trend-tooltip .tooltip-score {
  color: #e6a23c;
  font-weight: 600;
  min-width: 50px;
  text-align: right;
}

.trend-tooltip .tooltip-price {
  color: #409eff;
  font-weight: 500;
  min-width: 50px;
  text-align: right;
}

.score-header {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 4px;
}

.trend-legend {
  display: flex;
  gap: 12px;
  font-size: 11px;
  font-weight: normal;
}

.trend-legend .legend-item {
  display: flex;
  align-items: center;
  gap: 4px;
  color: #909399;
}

.trend-legend .legend-line {
  display: inline-block;
  width: 16px;
  height: 2px;
  border-radius: 1px;
}

.trend-legend .legend-line.price {
  background-color: #409eff;
}

.trend-legend .legend-line.score {
  background-color: #e6a23c;
}

.trend-legend .legend-line.tech {
  background-color: #67c23a;
}

.plan-status-cell {
  text-align: center;
  line-height: 1.4;
}

.plan-status-cell .plan-price {
  font-size: 11px;
  opacity: 0.75;
  margin-bottom: 2px;
}

.plan-status-cell .plan-profit {
  font-size: 12px;
  font-weight: 600;
}

.plan-status-cell .plan-rate {
  font-size: 11px;
  opacity: 0.85;
}

.plan-status-cell.profit {
  color: #f56c6c; /* 盈利红色 */
}

.plan-status-cell.loss {
  color: #67c23a; /* 亏损绿色 */
}

.plan-status-cell.neutral {
  color: #909399;
}

.no-plan {
  color: #c0c4cc;
}

.plan-status-dot {
  display: inline-block;
  width: 12px;
  height: 12px;
  border-radius: 50%;
  cursor: pointer;
}

.plan-status-dot.profit {
  background-color: #f56c6c; /* 盈利红色 */
}

.plan-status-dot.loss {
  background-color: #67c23a; /* 亏损绿色 */
}

.plan-status-dot.neutral {
  background-color: #909399;
}

.score-dimensions {
  display: flex;
  gap: 6px;
}

.score-dimensions span {
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 11px;
  cursor: pointer;
}

.score-good {
  background-color: #f0f9eb;
  color: #67c23a;
}

.score-normal {
  background-color: #fdf6ec;
  color: #e6a23c;
}

.score-bad {
  background-color: #fef0f0;
  color: #f56c6c;
}

.tooltip-content {
  max-width: 400px;
  white-space: pre-line;
}

.tooltip-item {
  padding: 4px 0;
  border-bottom: 1px dashed #e4e7ed;
  font-size: 12px;
  line-height: 1.5;
}

.tooltip-item:last-child {
  border-bottom: none;
}

.summary-text {
  font-size: 12px;
  color: #606266;
  line-height: 1.5;
  white-space: normal;
  word-break: break-all;
}

.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

.operation-buttons {
  display: flex;
  flex-wrap: nowrap;
  gap: 4px;
}

.operation-buttons .el-button {
  white-space: nowrap;
  padding: 4px 8px;
  font-size: 11px;
  min-width: auto;
}

.favorite-icon {
  cursor: pointer;
  font-size: 16px;
  color: #c0c4cc;
  transition: all 0.3s ease;
}

.favorite-icon:hover {
  color: #e6a23c;
  transform: scale(1.2);
}

.favorite-icon.is-favorite {
  color: #e6a23c;
}

/* 复审信息列 - 三行布局 */
.review-info-cell {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 4px 0;
}

.review-row {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  line-height: 1.4;
}

.review-label {
  font-weight: 600;
  color: #909399;
  min-width: 28px;
  flex-shrink: 0;
}

/* 得分行 */
.review-score-row {
  justify-content: flex-start;
}

.review-score-tag {
  font-weight: 600;
  min-width: 36px;
  text-align: center;
}

.review-rating-tag {
  font-weight: 500;
}

/* 意见行 - 可点击 */
.review-opinion-row {
  cursor: pointer;
  transition: all 0.2s ease;
  padding: 2px 4px;
  border-radius: 3px;
}

.review-opinion-row:hover {
  background-color: #f0f9ff;
}

.review-opinion-text {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: #606266;
  font-size: 10px;
  display: flex;
  align-items: center;
  gap: 2px;
}

.view-detail-icon {
  font-size: 12px;
  color: #409eff;
  flex-shrink: 0;
  opacity: 0.7;
  transition: opacity 0.2s ease;
}

.review-opinion-row:hover .view-detail-icon {
  opacity: 1;
}

/* 时间行 */
.review-time-row {
  color: #909399;
  font-size: 10px;
}

.review-time-text {
  color: #c0c4cc;
}

/* 未复审状态 */
.no-review-cell {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 60px;
}

.no-review-text {
  color: #c0c4cc;
  font-size: 12px;
  opacity: 0.7;
}

/* 复审详情弹窗 */
.review-detail-dialog .el-dialog__body {
  padding-top: 10px;
}

.review-detail-content {
  max-height: 70vh;
  overflow-y: auto;
}

.detail-header {
  margin-bottom: 16px;
}

.detail-stock-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.detail-stock-info h3 {
  margin: 0;
  font-size: 18px;
  color: #303133;
}

.detail-rating-badge {
  display: flex;
  gap: 8px;
}

.detail-meta {
  display: flex;
  gap: 20px;
  font-size: 13px;
  color: #909399;
}

.detail-body {
  background-color: #f5f7fa;
  border-radius: 6px;
  padding: 16px;
}

.review-opinion-full {
  margin: 0;
  font-family: 'Courier New', monospace;
  font-size: 12px;
  line-height: 1.6;
  color: #303133;
  white-space: pre-wrap;
  word-break: break-all;
  max-height: 50vh;
  overflow-y: auto;
}

.prediction-stats-tag {
  font-size: 10px;
  padding: 0 4px;
  height: 18px;
  line-height: 18px;
}

.prediction-dialog .el-dialog__body {
  padding-top: 10px;
  max-height: 75vh;
  overflow-y: auto;
}

.prediction-form-card {
  margin-bottom: 16px;
}

.prediction-form-card .el-card__header {
  padding: 12px 20px;
  background-color: #fdf6ec;
}

.prediction-form-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 600;
  font-size: 14px;
}

.prediction-price-info {
  font-weight: normal;
  font-size: 13px;
  color: #606266;
}

.prediction-price-info strong {
  color: #f56c6c;
  font-size: 16px;
}

.prediction-stats-info {
  font-weight: normal;
  font-size: 12px;
  color: #909399;
}

.prediction-history-card .el-card__header {
  padding: 12px 20px;
  background-color: #f0f9eb;
}

.pending-text {
  color: #c0c4cc;
  font-size: 12px;
}

.review-info-preview {
  display: inline-block;
  max-width: 150px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 12px;
  color: #606266;
  cursor: pointer;
}

.no-review {
  color: #c0c4cc;
}

.prediction-review-tooltip {
  max-width: 300px;
  white-space: pre-wrap;
  word-break: break-all;
  font-size: 12px;
  line-height: 1.5;
}

.review-info-readonly .el-textarea__inner {
  background-color: #f5f7fa;
  color: #606266;
  cursor: default;
  font-size: 12px;
  line-height: 1.6;
  overflow-y: hidden !important;
  scrollbar-width: none;
}
.review-info-readonly .el-textarea__inner::-webkit-scrollbar {
  display: none;
}
</style>
