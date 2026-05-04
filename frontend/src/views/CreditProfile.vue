<script setup>
import { ref, onMounted, watch, computed, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft, Star, Trophy, TrendCharts, Warning, Download, Refresh } from '@element-plus/icons-vue'
import { getCarrierDetail, getDimensionAverages, exportPdf, recalculateScores } from '../api'

const route = useRoute()
const router = useRouter()
const carrier = ref(null)
const averages = ref({})
const error = ref('')
const loading = ref(false)

// 各维度权重（与 config.yaml 保持一致）
const DIM_WEIGHTS = {
  '企业资质': 0.15, '履约能力': 0.25, '服务质量': 0.20,
  '行为合规': 0.15, '经营信用': 0.15, '生态协同': 0.10,
}

function normalizeScore(score, dim) {
  const w = DIM_WEIGHTS[dim] || 0.15
  return Math.min(100, score / w)
}

let echartsInstalled = false

async function ensureEcharts() {
  if (echartsInstalled) return
  const echarts = await import('echarts')
  echartsInstalled = true
  window._echarts = echarts
}

async function loadData() {
  loading.value = true
  error.value = ''
  try {
    const id = route.params.id
    const [c, a] = await Promise.all([
      getCarrierDetail(id),
      getDimensionAverages(),
    ])
    carrier.value = c
    averages.value = a
  } catch (e) {
    error.value = '加载失败: ' + (e.message || e)
  }
  loading.value = false
  await nextTick()
  initRadar()
  initTrend()
}

onMounted(async () => {
  try { await ensureEcharts() } catch (e) { console.error('echarts failed:', e) }
  await loadData()
})
watch(() => route.params.id, loadData)

function initRadar() {
  const dom = document.getElementById('radarChart')
  const dims = carrier.value?.current_score?.dimension_scores
  const ec = window._echarts
  if (!dom || !dims || !ec) return

  const chart = ec.init(dom)
  const dimNames = Object.keys(dims)
  const myValues = dimNames.map(k => normalizeScore(dims[k], k))
  const avgValues = dimNames.map(k => normalizeScore(averages.value[k] || 0, k))

  chart.setOption({
    tooltip: {},
    legend: { data: ['当前得分', '平台均值'], bottom: 0 },
    radar: {
      center: ['50%', '45%'], radius: '60%',
      indicator: dimNames.map(k => ({ name: k, max: 100 })),
    },
    series: [
      { type: 'radar', data: [{ value: myValues, name: '当前得分' }] },
      { type: 'radar', data: [{ value: avgValues, name: '平台均值' }] },
    ],
  })
}

function initTrend() {
  const dom = document.getElementById('trendChart')
  const history = carrier.value?.score_history
  const ec = window._echarts
  if (!dom || !history?.length || !ec) return

  const chart = ec.init(dom)
  chart.setOption({
    tooltip: { trigger: 'axis' },
    grid: { left: 50, right: 20, top: 20, bottom: 30 },
    xAxis: { type: 'category', data: history.map(h => h.eval_period) },
    yAxis: { type: 'value', name: '评分', min: 0, max: 100 },
    series: [{
      type: 'line', data: history.map(h => h.score_value),
      smooth: true, areaStyle: { color: 'rgba(26,54,93,0.15)' },
      markLine: { silent: true, data: [{ yAxis: 90 }, { yAxis: 60 }] },
    }],
  })
}

function goBack() { window.location.href = '/' }

function scoreColor(v) {
  return v >= 80 ? '#0B8A5E' : v >= 60 ? '#C47D0B' : '#C62828'
}

function gradeClass(g) { return { 'grade-badge': true, [`grade-${g}`]: !!g } }
function eventColor(t) { return t === 'addition' ? 'success' : t === 'one_vote_veto' ? 'danger' : 'warning' }

const showExplanation = ref(false)
const dimensionContributions = computed(() => {
  const dims = carrier.value?.current_score?.dimension_scores
  if (!dims) return []
  const total = carrier.value.current_score.score_value || 1
  return Object.entries(dims).map(([name, val]) => ({ name, value: val, pct: ((val / total) * 100).toFixed(1) }))
})
</script>

<template>
  <div>
    <div class="page-header">
      <el-breadcrumb separator="/">
        <el-breadcrumb-item><a href="/" @click.prevent="goBack">承运商列表</a></el-breadcrumb-item>
        <el-breadcrumb-item>信用画像</el-breadcrumb-item>
      </el-breadcrumb>
      <div style="display:flex; justify-content:space-between; align-items:flex-start;">
        <h1 class="page-title">
          <el-button link @click="goBack"><el-icon size="18"><ArrowLeft /></el-icon></el-button>
          {{ carrier?.name || '加载中...' }}
        </h1>
      </div>
      <p v-if="carrier" class="page-desc">
        {{ carrier.unified_credit_code }} · {{ carrier.transport_category }} · 合作起始: {{ carrier.cooperation_start_date }}
      </p>
      <p v-if="error" style="color:#C62828;">{{ error }}</p>
    </div>

    <div v-if="carrier?.current_score && !loading">
      <div class="kpi-row">
        <div class="kpi-card">
          <div class="kpi-label">信用总分</div>
          <div class="kpi-value" :style="{ color: scoreColor(carrier.current_score.score_value) }">
            {{ carrier.current_score.score_value.toFixed(1) }}
          </div>
        </div>
        <div class="kpi-card">
          <div class="kpi-label">信用等级</div>
          <span :class="gradeClass(carrier.current_score.grade)" style="font-size:20px;font-weight:800;">{{ carrier.current_score.grade }}</span>
        </div>
        <div class="kpi-card">
          <div class="kpi-label">较上月变动</div>
          <div class="kpi-value" :style="{ color: (carrier.score_change || 0) >= 0 ? '#0B8A5E' : '#C62828' }">
            {{ (carrier.score_change || 0) >= 0 ? '+' : '' }}{{ (carrier.score_change || 0).toFixed(1) }}
          </div>
        </div>
        <div class="kpi-card">
          <div class="kpi-label">风险标签</div>
          <el-tag :type="carrier.risk_label === '预警' ? 'danger' : carrier.risk_label === '关注' ? 'warning' : 'success'" size="large">{{ carrier.risk_label }}</el-tag>
        </div>
      </div>

      <div class="two-col">
        <div class="col-left">
          <el-card><template #header>六维雷达图</template><div id="radarChart" style="height:340px;"></div></el-card>
        </div>
        <div class="col-right">
          <el-card>
            <template #header>
              <span>维度得分</span>
              <el-button link type="primary" size="small" style="float:right;" @click="showExplanation = true">评分解释</el-button>
            </template>
            <div v-for="(val, dim) in carrier.current_score.dimension_scores" :key="dim" style="margin-bottom:14px;">
              <div style="display:flex;justify-content:space-between;margin-bottom:4px;">
                <span style="font-weight:500;">{{ dim }}</span>
                <span style="font-weight:700;" :style="{ color: scoreColor(val) }">{{ val.toFixed(1) }}</span>
              </div>
              <el-progress :percentage="Math.round(val)" :color="val >= 80 ? '#0B8A5E' : val >= 60 ? '#C47D0B' : '#C62828'" :show-text="false" :stroke-width="8" />
            </div>
          </el-card>
        </div>
      </div>

      <div class="two-col">
        <div class="col-left">
          <el-card><template #header>近12月评分趋势</template><div id="trendChart" style="height:280px;"></div></el-card>
        </div>
        <div class="col-right">
          <el-card>
            <template #header>扣分/加分事件</template>
            <el-timeline v-if="carrier.events?.length">
              <el-timeline-item v-for="e in carrier.events.slice(0, 8)" :key="e.event_id" :timestamp="e.event_time" :type="eventColor(e.event_type)">
                <p style="font-weight:600;margin:0;">{{ e.event_desc }}</p>
                <p style="font-size:12px;color:var(--text-muted);">
                  分值: <span :style="{ color: e.score_change >= 0 ? '#0B8A5E' : '#C62828', fontWeight:700 }">{{ e.score_change >= 0 ? '+' : '' }}{{ e.score_change }}</span>
                </p>
              </el-timeline-item>
            </el-timeline>
            <el-empty v-else description="暂无评分事件" />
          </el-card>
        </div>
      </div>

      <el-card>
        <template #header>基本信息</template>
        <el-descriptions :column="3" border size="small">
          <el-descriptions-item label="企业名称">{{ carrier.name }}</el-descriptions-item>
          <el-descriptions-item label="ID">{{ carrier.carrier_id }}</el-descriptions-item>
          <el-descriptions-item label="信用代码">{{ carrier.unified_credit_code }}</el-descriptions-item>
          <el-descriptions-item label="类型">{{ carrier.carrier_type }}</el-descriptions-item>
          <el-descriptions-item label="运输品类">{{ carrier.transport_category }}</el-descriptions-item>
          <el-descriptions-item label="合作起始">{{ carrier.cooperation_start_date }}</el-descriptions-item>
          <el-descriptions-item label="总订单">{{ carrier.total_orders }}</el-descriptions-item>
          <el-descriptions-item label="完成订单">{{ carrier.completed_orders }}</el-descriptions-item>
          <el-descriptions-item label="近三月订单">{{ carrier.recent_3m_orders }}</el-descriptions-item>
          <el-descriptions-item label="证照">
            <el-tag :type="carrier.license_valid ? 'success' : 'danger'" size="small">{{ carrier.license_valid ? '有效' : '无效' }}</el-tag>
          </el-descriptions-item>
        </el-descriptions>
      </el-card>

      <el-dialog v-model="showExplanation" title="评分构成解释" width="500px">
        <p style="color:var(--text-muted);margin-bottom:16px;">各维度对总分 {{ carrier.current_score.score_value.toFixed(1) }} 的贡献占比</p>
        <div v-for="d in dimensionContributions" :key="d.name" style="margin-bottom:14px;">
          <div style="display:flex;justify-content:space-between;">
            <span>{{ d.name }}</span>
            <span style="font-weight:700;">{{ d.value.toFixed(1) }} ({{ d.pct }}%)</span>
          </div>
          <el-progress :percentage="Number(d.pct)" :stroke-width="10" />
        </div>
      </el-dialog>
    </div>

    <div v-if="!carrier && !loading && !error" style="text-align:center;padding:60px;color:#999;">暂无数据</div>
  </div>
</template>
