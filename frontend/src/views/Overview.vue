<script setup>
import { ref, onMounted, computed, watch, nextTick, onUnmounted } from 'vue'
import { DataAnalysis, Search, Download, Box, Star, Trophy, Warning, Van } from '@element-plus/icons-vue'
import { getScores, exportCsv } from '../api'

let echarts = null

async function loadEcharts() {
  if (echarts) return echarts
  const [{ BarChart, PieChart }, { TooltipComponent, GridComponent, LegendComponent, DataZoomComponent, GraphicComponent }, core, { CanvasRenderer }] = await Promise.all([
    import('echarts/charts'),
    import('echarts/components'),
    import('echarts/core'),
    import('echarts/renderers'),
  ])
  core.use([BarChart, PieChart, TooltipComponent, GridComponent, LegendComponent, DataZoomComponent, GraphicComponent, CanvasRenderer])
  echarts = core
  return core
}

const scores = ref([])
const filterType = ref('all')
const searchQuery = ref('')
const tableLoading = ref(false)
const dataReady = ref(false)

const totalAnim = ref(0)
const avgAnim = ref(0)
const aaaAnim = ref(0)
const highRiskAnim = ref(0)
const carriersAnim = ref(0)

function animateCounter(refObj, target, duration = 1200) {
  const start = performance.now()
  const from = refObj.value
  function tick(now) {
    const progress = Math.min((now - start) / duration, 1)
    const eased = 1 - Math.pow(1 - progress, 3)
    refObj.value = Math.round(from + (target - from) * eased)
    if (progress < 1) requestAnimationFrame(tick)
  }
  requestAnimationFrame(tick)
}

const filteredScores = computed(() => {
  let result = scores.value
  if (filterType.value !== 'all') result = result.filter(s => s.entity_type === filterType.value)
  if (searchQuery.value) result = result.filter(s => s.entity_id.toLowerCase().includes(searchQuery.value.toLowerCase()))
  return result
})

const kpiData = computed(() => {
  const data = filteredScores.value
  if (!data.length) return { total: 0, avg: 0, aaa: 0, highRisk: 0, carriers: 0 }
  return {
    total: data.length,
    avg: (data.reduce((sum, s) => sum + s.score_value, 0) / data.length).toFixed(1),
    aaa: data.filter(s => s.grade === 'AAA').length,
    highRisk: data.filter(s => s.grade === 'C').length,
    carriers: data.filter(s => s.entity_type === 'carrier').length,
  }
})

let histChart = null
let pieChart = null

onMounted(() => {
  tableLoading.value = true
  getScores().then(data => {
    scores.value = data
    tableLoading.value = false
    dataReady.value = true
    nextTick(() => { initCharts(); animateCounters() })
  }).catch(() => {
    tableLoading.value = false
    dataReady.value = true
  })
})

onUnmounted(() => { histChart?.dispose(); pieChart?.dispose() })

function animateCounters() {
  const d = kpiData.value
  animateCounter(totalAnim, d.total)
  animateCounter(avgAnim, parseFloat(d.avg))
  animateCounter(aaaAnim, d.aaa)
  animateCounter(highRiskAnim, d.highRisk)
  animateCounter(carriersAnim, d.carriers)
}

watch(filteredScores, async () => {
  await nextTick()
  if (dataReady.value) { initCharts(); animateCounters() }
})

async function initCharts() {
  const histDom = document.getElementById('histChart')
  const pieDom = document.getElementById('pieChart')
  if (!histDom || !pieDom) return
  const ec = await loadEcharts()
  histChart?.dispose(); pieChart?.dispose()
  histChart = ec.init(histDom); pieChart = ec.init(pieDom)
  const data = filteredScores.value

  histChart.setOption({
    tooltip: { trigger: 'item', formatter: (p) => `<strong>评分</strong>: ${p.value.toFixed(1)}`, backgroundColor: 'rgba(10,22,40,0.92)', borderColor: 'rgba(212,160,23,0.3)', textStyle: { color: '#FFF', fontSize: 13 } },
    color: [{ type: 'linear', x: 0, y: 0, x2: 0, y2: 1, colorStops: [{ offset: 0, color: '#1A365D' }, { offset: 1, color: '#3B6B9E' }] }],
    grid: { left: 55, right: 25, top: 40, bottom: 55 },
    dataZoom: data.length > 20 ? [{ type: 'slider', bottom: 10, height: 15 }] : [],
    xAxis: { type: 'value', name: '评分', nameTextStyle: { color: '#94A3B8', fontSize: 12 }, axisLabel: { color: '#64748B', fontSize: 11 }, axisLine: { lineStyle: { color: '#E2E8F0' } }, splitLine: { lineStyle: { color: '#F1F5F9', type: 'dashed' } } },
    yAxis: { type: 'value', name: '数量', nameTextStyle: { color: '#94A3B8', fontSize: 12 }, axisLabel: { color: '#64748B', fontSize: 11 }, axisLine: { show: false }, splitLine: { lineStyle: { color: '#F1F5F9', type: 'dashed' } } },
    series: [{ type: 'bar', data: data.map((s) => ({ value: s.score_value, itemStyle: { borderRadius: [6, 6, 0, 0], color: s.grade === 'AAA' ? '#0B8A5E' : s.grade === 'C' ? '#C62828' : undefined } })), barWidth: '60%', emphasis: { itemStyle: { color: '#D4A017' } }, animationDuration: 800, animationEasing: 'cubicOut' }],
  })

  const gradeCounts = {}; data.forEach(s => { gradeCounts[s.grade] = (gradeCounts[s.grade] || 0) + 1 })
  pieChart.setOption({
    tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)', backgroundColor: 'rgba(10,22,40,0.92)', borderColor: 'rgba(212,160,23,0.3)', textStyle: { color: '#FFF', fontSize: 13 } },
    series: [{ type: 'pie', roseType: 'area', radius: ['40%', '72%'], center: ['50%', '52%'], data: Object.entries(gradeCounts).map(([g, c]) => ({ name: g, value: c, itemStyle: { color: { AAA: '#0B8A5E', AA: '#2563EB', A: '#3B82F6', B: '#C47D0B', C: '#C62828' }[g] || '#94A3B8', borderRadius: 3, borderColor: '#FFFFFF', borderWidth: 2 } })), label: { show: true, formatter: '{b}: {c}', color: '#64748B', fontSize: 12, fontWeight: 500 }, emphasis: { scaleSize: 8, itemStyle: { shadowBlur: 20, shadowColor: 'rgba(0,0,0,0.12)' } }, animationType: 'scale', animationEasing: 'elasticOut' }],
    graphic: [{ type: 'text', left: 'center', top: 'center', style: { text: `总计\n${data.length}`, fill: '#0F172A', fontSize: 16, fontWeight: 700, textAlign: 'center', lineHeight: 22 } }],
  })
}

function gradeClass(grade) { return { 'grade-badge': true, [`grade-${grade}`]: true } }

async function handleExport() {
  try {
    const type = filterType.value === 'all' ? null : filterType.value
    const blob = await exportCsv(type)
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a'); a.href = url; a.download = 'credit_scores.csv'; a.click()
    ElMessage.success('CSV 导出成功')
  } catch { ElMessage.error('导出失败') }
}
</script>

<template>
  <!-- Page header -->
  <div class="page-header">
    <div class="page-breadcrumb">
      <el-breadcrumb separator="/">
        <el-breadcrumb-item :to="{ path: '/' }">首页</el-breadcrumb-item>
        <el-breadcrumb-item>评分概览</el-breadcrumb-item>
      </el-breadcrumb>
    </div>
    <h1 class="page-title">
      <el-icon size="22" color="#D4A017"><DataAnalysis /></el-icon>
      评分概览
    </h1>
    <p class="page-desc">实时监控承运商与货主信用评分状况 · 共 {{ scores.length }} 条记录</p>
  </div>

  <!-- Filter -->
  <div class="filter-card">
    <el-row :gutter="15" align="middle" style="flex-wrap: wrap;">
      <el-col :xs="24" :sm="12" :md="6">
        <el-select v-model="filterType" placeholder="评价对象" style="width: 100%;">
          <el-option label="全部" value="all" />
          <el-option label="承运商" value="carrier" />
          <el-option label="货主" value="shipper" />
        </el-select>
      </el-col>
      <el-col :xs="24" :sm="12" :md="6">
        <el-input v-model="searchQuery" placeholder="搜索 ID..." clearable>
          <template #prefix><el-icon><Search /></el-icon></template>
        </el-input>
      </el-col>
      <el-col :xs="24" :sm="24" :md="12" style="text-align: right;">
        <el-button type="primary" @click="handleExport">
          <el-icon><Download /></el-icon> 导出 CSV
        </el-button>
      </el-col>
    </el-row>
  </div>

  <!-- KPI -->
  <div class="kpi-row">
    <div class="kpi-card">
      <div class="kpi-icon"><el-icon size="20"><Box /></el-icon></div>
      <div class="kpi-label">评分数</div>
      <div class="kpi-value">{{ totalAnim }}</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-icon"><el-icon size="20"><Star /></el-icon></div>
      <div class="kpi-label">平均分</div>
      <div class="kpi-value">{{ avgAnim }}</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-icon"><el-icon size="20" color="#0B8A5E"><Trophy /></el-icon></div>
      <div class="kpi-label">AAA</div>
      <div class="kpi-value">{{ aaaAnim }}</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-icon"><el-icon size="20" color="#C62828"><Warning /></el-icon></div>
      <div class="kpi-label">高风险</div>
      <div class="kpi-value" style="color: #C62828;">{{ highRiskAnim }}</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-icon"><el-icon size="20"><Van /></el-icon></div>
      <div class="kpi-label">承运商</div>
      <div class="kpi-value">{{ carriersAnim }}</div>
    </div>
  </div>

  <!-- Charts -->
  <div class="two-col" style="margin-bottom: 15px;">
    <div class="col-left">
      <el-card><template #header>评分分布</template><div id="histChart" style="height: 300px;"></div></el-card>
    </div>
    <div class="col-right">
      <el-card><template #header>等级占比</template><div id="pieChart" style="height: 300px;"></div></el-card>
    </div>
  </div>

  <!-- Table -->
  <el-card>
    <template #header>评分列表</template>
    <template v-if="filteredScores.length">
      <el-table :data="filteredScores" v-loading="tableLoading" stripe style="width: 100%;">
        <el-table-column prop="entity_id" label="ID" width="120" />
        <el-table-column label="类型" width="100">
          <template #default="{ row }">
            <el-tag :type="row.entity_type === 'carrier' ? '' : 'info'" size="small">{{ row.entity_type === 'carrier' ? '承运商' : '货主' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="score_value" label="评分" width="120" sortable>
          <template #default="{ row }">
            <el-tag :type="row.score_value >= 80 ? 'success' : row.score_value >= 60 ? 'warning' : 'danger'" effect="plain">{{ row.score_value.toFixed(1) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="等级" width="100">
          <template #default="{ row }"><span :class="gradeClass(row.grade)">{{ row.grade }}</span></template>
        </el-table-column>
        <el-table-column prop="eval_time" label="评估时间" />
      </el-table>
    </template>
    <div v-else class="empty-state">
      <div class="empty-state-icon"><el-icon size="28"><Search /></el-icon></div>
      <div class="empty-state-title">暂无评分数据</div>
      <div class="empty-state-desc">请确认后端服务已启动（localhost:5001）</div>
    </div>
  </el-card>
</template>
