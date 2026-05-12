<script setup>
import { ref, onMounted, computed, watch, nextTick, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { Search, Download, Van, Star, Warning, Filter, Refresh } from '@element-plus/icons-vue'
import { getCarriers, exportCsv } from '../api'

const router = useRouter()
const carriers = ref([])
const loading = ref(false)

// 筛选条件
const filterGrade = ref('')
const filterCategory = ref('')
const filterRisk = ref('')
const filterScoreMin = ref(null)
const filterScoreMax = ref(null)
const filterSearch = ref('')
const sortBy = ref('score_value')
const sortOrder = ref('desc')

const gradeOptions = ['AAA', 'AA', 'A', 'B', 'C']
const categoryOptions = ['普运', '危化品']
const riskOptions = ['正常', '关注', '预警']

const filteredCarriers = computed(() => carriers.value)

function buildParams() {
  const p = { sort_by: sortBy.value, sort_order: sortOrder.value }
  if (filterGrade.value) p.grade = filterGrade.value
  if (filterCategory.value) p.transport_category = filterCategory.value
  if (filterRisk.value) p.risk_label = filterRisk.value
  if (filterScoreMin.value !== null) p.score_min = filterScoreMin.value
  if (filterScoreMax.value !== null) p.score_max = filterScoreMax.value
  if (filterSearch.value) p.search = filterSearch.value
  return p
}

async function loadCarriers() {
  loading.value = true
  try {
    carriers.value = await getCarriers(buildParams())
  } catch (e) { console.error(e) }
  loading.value = false
}

onMounted(loadCarriers)

let animFrame = null
const totalAnim = ref(0)
const avgAnim = ref(0)
const aaaAnim = ref(0)
const warningAnim = ref(0)

function animateCounters() {
  const d = carriers.value
  const targets = {
    total: d.length,
    avg: d.length ? (d.reduce((s, c) => s + (c.score_value || 0), 0) / d.length) : 0,
    aaa: d.filter(c => c.grade === 'AAA').length,
    warning: d.filter(c => c.risk_label === '预警').length,
  }
  const start = performance.now()
  const from = { total: totalAnim.value, avg: avgAnim.value, aaa: aaaAnim.value, warning: warningAnim.value }
  function tick(now) {
    const progress = Math.min((now - start) / 1000, 1)
    const eased = 1 - Math.pow(1 - progress, 3)
    totalAnim.value = Math.round(from.total + (targets.total - from.total) * eased)
    avgAnim.value = (from.avg + (targets.avg - from.avg) * eased).toFixed(1)
    aaaAnim.value = Math.round(from.aaa + (targets.aaa - from.aaa) * eased)
    warningAnim.value = Math.round(from.warning + (targets.warning - from.warning) * eased)
    if (progress < 1) animFrame = requestAnimationFrame(tick)
  }
  animFrame = requestAnimationFrame(tick)
}

watch(carriers, () => { nextTick(animateCounters) })

onUnmounted(() => { if (animFrame) cancelAnimationFrame(animFrame) })

function openProfile(row) {
  if (!row || !row.carrier_id) return
  window.location.href = `/profile/${row.carrier_id}`
}

function gradeColor(g) {
  const m = { AAA: '#0B8A5E', AA: '#2563EB', A: '#3B82F6', B: '#C47D0B', C: '#C62828' }
  return m[g] || '#94A3B8'
}

function riskColor(r) {
  const m = { '正常': 'success', '关注': 'warning', '预警': 'danger' }
  return m[r] || 'info'
}

async function handleExport() {
  try {
    const blob = await exportCsv('carrier')
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a'); a.href = url; a.download = 'carriers.csv'; a.click()
    ElMessage.success('导出成功')
  } catch { ElMessage.error('导出失败') }
}
</script>

<template>
  <div class="page-header">
    <div class="page-breadcrumb">
      <el-breadcrumb separator="/">
        <el-breadcrumb-item :to="{ path: '/' }">首页</el-breadcrumb-item>
        <el-breadcrumb-item>承运商列表</el-breadcrumb-item>
      </el-breadcrumb>
    </div>
    <h1 class="page-title">
      <el-icon size="22" color="#D4A017"><Van /></el-icon>
      承运商列表
    </h1>
    <p class="page-desc">承运商日常管理统一入口 · 共 {{ carriers.length }} 家在册</p>
  </div>

  <!-- KPI -->
  <div class="kpi-row">
    <div class="kpi-card">
      <div class="kpi-icon"><el-icon size="20"><Van /></el-icon></div>
      <div class="kpi-label">在册承运商</div>
      <div class="kpi-value">{{ totalAnim }}</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-icon"><el-icon size="20"><Star /></el-icon></div>
      <div class="kpi-label">平均信用分</div>
      <div class="kpi-value">{{ avgAnim }}</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-icon"><el-icon size="20" color="#0B8A5E"><Star /></el-icon></div>
      <div class="kpi-label">AAA 级</div>
      <div class="kpi-value">{{ aaaAnim }}</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-icon"><el-icon size="20" color="#C62828"><Warning /></el-icon></div>
      <div class="kpi-label">预警状态</div>
      <div class="kpi-value" style="color: #C62828;">{{ warningAnim }}</div>
    </div>
  </div>

  <!-- Filter -->
  <div class="filter-card">
    <el-row :gutter="12" align="middle">
      <el-col :xs="12" :sm="6" :md="3">
        <el-select v-model="filterGrade" placeholder="信用等级" clearable style="width:100%" @change="loadCarriers">
          <el-option v-for="g in gradeOptions" :key="g" :label="g" :value="g" />
        </el-select>
      </el-col>
      <el-col :xs="12" :sm="6" :md="3">
        <el-select v-model="filterCategory" placeholder="运输品类" clearable style="width:100%" @change="loadCarriers">
          <el-option v-for="c in categoryOptions" :key="c" :label="c" :value="c" />
        </el-select>
      </el-col>
      <el-col :xs="12" :sm="6" :md="3">
        <el-select v-model="filterRisk" placeholder="风险标签" clearable style="width:100%" @change="loadCarriers">
          <el-option v-for="r in riskOptions" :key="r" :label="r" :value="r" />
        </el-select>
      </el-col>
      <el-col :xs="12" :sm="6" :md="2">
        <el-input-number v-model="filterScoreMin" placeholder="最低分" :min="0" :max="100" controls-position="right" style="width:100%" @change="loadCarriers" />
      </el-col>
      <el-col :xs="12" :sm="6" :md="2">
        <el-input-number v-model="filterScoreMax" placeholder="最高分" :min="0" :max="100" controls-position="right" style="width:100%" @change="loadCarriers" />
      </el-col>
      <el-col :xs="12" :sm="6" :md="4">
        <el-input v-model="filterSearch" placeholder="搜索名称/ID..." clearable @change="loadCarriers">
          <template #prefix><el-icon><Search /></el-icon></template>
        </el-input>
      </el-col>
      <el-col :xs="24" :sm="12" :md="7" style="text-align:right;">
        <el-button @click="loadCarriers"><el-icon><Refresh /></el-icon> 刷新</el-button>
        <el-button type="primary" @click="handleExport"><el-icon><Download /></el-icon> 导出</el-button>
      </el-col>
    </el-row>
  </div>

  <!-- Table -->
  <el-card>
    <template #header>承运商列表</template>
    <el-table :data="filteredCarriers" v-loading="loading" stripe @row-click="openProfile" style="width:100%; cursor:pointer;">
      <el-table-column prop="name" label="企业名称" min-width="150" />
      <el-table-column prop="carrier_id" label="ID" width="80" />
      <el-table-column label="信用分" width="100" sortable>
        <template #default="{ row }">
          <el-tag :type="row.score_value >= 80 ? 'success' : row.score_value >= 60 ? 'warning' : 'danger'" effect="plain">
            {{ (row.score_value || 0).toFixed(1) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="等级" width="80">
        <template #default="{ row }">
          <span class="grade-badge" :class="`grade-${row.grade}`">{{ row.grade || 'C' }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="transport_category" label="运输品类" width="90">
        <template #default="{ row }"><el-tag :type="row.transport_category === '危化品' ? 'danger' : ''" size="small">{{ row.transport_category }}</el-tag></template>
      </el-table-column>
      <el-table-column prop="recent_3m_orders" label="近三月订单" width="110" sortable />
      <el-table-column label="风险标签" width="90">
        <template #default="{ row }"><el-tag :type="riskColor(row.risk_label)" size="small">{{ row.risk_label }}</el-tag></template>
      </el-table-column>
      <el-table-column label="操作" width="80" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" size="small" @click.stop="openProfile(row)">查看</el-button>
        </template>
      </el-table-column>
    </el-table>
  </el-card>
</template>
