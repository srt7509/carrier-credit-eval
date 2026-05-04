<script setup>
import { ref, onMounted, computed, watch, nextTick, onUnmounted } from 'vue'
import { Search, ArrowLeft, ArrowRight, OfficeBuilding, Star, Trophy, Folder, CopyDocument, Lock, Connection, CircleCheck } from '@element-plus/icons-vue'
import { getScores, getScoreDetail } from '../api'

let echarts = null

async function loadEcharts() {
  if (echarts) return echarts
  const [{ RadarChart }, { TooltipComponent, LegendComponent }, core, { CanvasRenderer }] = await Promise.all([
    import('echarts/charts'),
    import('echarts/components'),
    import('echarts/core'),
    import('echarts/renderers'),
  ])
  core.use([RadarChart, TooltipComponent, LegendComponent, CanvasRenderer])
  echarts = core
  return core
}

const scores = ref([])
const selectedId = ref('')
const detail = ref(null)
const activeType = ref('all')
const detailLoading = ref(false)

const filteredEntities = computed(() => {
  if (activeType.value === 'all') return scores.value
  return scores.value.filter(s => s.entity_type === activeType.value)
})
const currentIndex = computed(() => filteredEntities.value.findIndex(s => s.entity_id === selectedId.value))

function goToPrev() { const idx = currentIndex.value; if (idx > 0) selectedId.value = filteredEntities.value[idx - 1].entity_id }
function goToNext() { const idx = currentIndex.value; if (idx < filteredEntities.value.length - 1) selectedId.value = filteredEntities.value[idx + 1].entity_id }

async function copyToClipboard(text) {
  try { await navigator.clipboard.writeText(text); ElMessage.success('已复制到剪贴板') } catch { ElMessage.error('复制失败') }
}

onMounted(() => {
  getScores().then(data => {
    scores.value = data
    if (data.length && !selectedId.value) { selectedId.value = data[0].entity_id; loadDetail() }
  }).catch(() => {})
})

watch(selectedId, loadDetail)

async function loadDetail() {
  if (!selectedId.value) return
  detailLoading.value = true
  try {
    detail.value = await getScoreDetail(selectedId.value)
    await nextTick(); initRadar()
  } catch (e) { console.error(e) }
  detailLoading.value = false
}

let radarChart = null
onUnmounted(() => { radarChart?.dispose() })

async function initRadar() {
  const dom = document.getElementById('radarChart')
  if (!dom || !detail.value?.dimension_scores) return
  const ec = await loadEcharts()
  radarChart?.dispose(); radarChart = ec.init(dom)
  const dims = detail.value.dimension_scores
  const weights = { '履约能力': 0.30, '合规记录': 0.20, '财务信用': 0.15, '服务质量': 0.15, '历史信用': 0.20 }
  const rawScores = Object.entries(dims).map(([dim, score]) => { const w = weights[dim] || 0.2; return Math.round((score / w) * 10) / 10 })

  radarChart.setOption({
    tooltip: { trigger: 'item', backgroundColor: 'rgba(10,22,40,0.92)', borderColor: 'rgba(212,160,23,0.3)', textStyle: { color: '#FFF', fontSize: 13 } },
    radar: { center: ['50%', '52%'], radius: '62%', indicator: Object.keys(dims).map(k => ({ name: k, max: 100 })), axisName: { color: '#475569', fontSize: 11, fontWeight: 500, padding: [3, 5] }, splitLine: { lineStyle: { color: '#E2E8F0' } }, splitArea: { areaStyle: { color: ['#F8FAFC', '#FFFFFF'] } }, axisLine: { lineStyle: { color: '#CBD5E1' } } },
    series: [{ type: 'radar', data: [{ value: rawScores, name: '评分', areaStyle: { color: 'rgba(26, 54, 93, 0.12)' }, lineStyle: { color: '#1A365D', width: 2.5 }, itemStyle: { color: '#1A365D', borderColor: '#FFFFFF', borderWidth: 2 } }], symbol: 'circle', symbolSize: 6, emphasis: { lineStyle: { width: 3 }, areaStyle: { color: 'rgba(26, 54, 93, 0.2)' } }, animationDuration: 600 }],
  })
}

function gradeClass(g) { return { 'grade-badge': true, [`grade-${g}`]: true } }
function progressColor(v) { return v >= 80 ? { '0%': '#0B8A5E', '100%': '#10B981' } : v >= 60 ? { '0%': '#C47D0B', '100%': '#F59E0B' } : { '0%': '#C62828', '100%': '#EF4444' } }
function riskType(f) { return (f.includes('投诉') || f.includes('事故')) ? 'danger' : f.includes('偏低') ? 'warning' : 'info' }
</script>

<template>
  <div class="page-header">
    <div class="page-breadcrumb">
      <el-breadcrumb separator="/">
        <el-breadcrumb-item :to="{ path: '/' }">首页</el-breadcrumb-item>
        <el-breadcrumb-item>评分详情</el-breadcrumb-item>
      </el-breadcrumb>
    </div>
    <h1 class="page-title"><el-icon size="22" color="#D4A017"><Search /></el-icon>评分详情</h1>
    <p class="page-desc">查看单个实体的信用评分明细与风险预警</p>
  </div>

  <div class="filter-card">
    <el-row :gutter="15" align="middle">
      <el-col :span="6">
        <el-radio-group v-model="activeType" size="small">
          <el-radio-button value="all">全部</el-radio-button>
          <el-radio-button value="carrier">承运商</el-radio-button>
          <el-radio-button value="shipper">货主</el-radio-button>
        </el-radio-group>
      </el-col>
      <el-col :span="12">
        <el-select v-model="selectedId" placeholder="选择实体" style="width: 100%;" filterable>
          <el-option v-for="s in filteredEntities" :key="s.entity_id" :label="`${s.entity_id} - ${s.entity_type === 'carrier' ? '承运商' : '货主'}`" :value="s.entity_id" />
        </el-select>
      </el-col>
      <el-col :span="6" style="text-align: right;">
        <el-button-group>
          <el-button :disabled="currentIndex <= 0" @click="goToPrev"><el-icon><ArrowLeft /></el-icon></el-button>
          <el-button :disabled="currentIndex >= filteredEntities.length - 1" @click="goToNext"><el-icon><ArrowRight /></el-icon></el-button>
        </el-button-group>
        <span style="margin-left: 8px; font-size: 12px; color: var(--text-muted);">{{ currentIndex + 1 }} / {{ filteredEntities.length }}</span>
      </el-col>
    </el-row>
  </div>

  <template v-if="detail">
    <div class="kpi-row">
      <div class="kpi-card">
        <div class="kpi-icon"><el-icon size="20"><OfficeBuilding /></el-icon></div>
        <div class="kpi-label">类型</div>
        <div style="font-size: 15px; font-weight: 700; color: var(--text-primary); margin-top: 2px;">{{ detail.entity_type === 'carrier' ? '承运商' : '货主' }}</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-icon" :style="{ background: detail.score_value >= 80 ? 'rgba(11,138,94,0.1)' : detail.score_value >= 60 ? 'rgba(196,125,11,0.1)' : 'rgba(198,40,40,0.1)' }">
          <el-icon size="20" :color="detail.score_value >= 80 ? '#0B8A5E' : detail.score_value >= 60 ? '#C47D0B' : '#C62828'"><Star /></el-icon>
        </div>
        <div class="kpi-label">评分</div>
        <div class="kpi-value" :style="{ color: detail.score_value >= 80 ? '#0B8A5E' : detail.score_value >= 60 ? '#C47D0B' : '#C62828' }">{{ detail.score_value.toFixed(1) }}</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-icon"><el-icon size="20" color="#D4A017"><Trophy /></el-icon></div>
        <div class="kpi-label">等级</div>
        <span :class="gradeClass(detail.grade)" style="margin-top: 2px;">{{ detail.grade }}</span>
      </div>
      <div class="kpi-card">
        <div class="kpi-icon"><el-icon size="20"><Folder /></el-icon></div>
        <div class="kpi-label">名称</div>
        <div style="font-size: 14px; font-weight: 700; color: var(--text-primary); margin-top: 2px;">{{ detail.entity?.name || '-' }}</div>
      </div>
    </div>

    <div class="two-col">
      <div class="col-equal">
        <el-card><template #header>雷达图</template><div id="radarChart" style="height: 280px;"></div></el-card>
        <el-card>
          <template #header>维度得分</template>
          <div v-for="(val, dim) in detail.dimension_scores" :key="dim" style="margin-bottom: 12px;">
            <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
              <span style="font-weight: 500; font-size: 13px;">{{ dim }}</span>
              <span style="font-weight: 700; font-size: 13px;" :style="{ color: val >= 80 ? '#0B8A5E' : val >= 60 ? '#C47D0B' : '#C62828' }">{{ val.toFixed(1) }}</span>
            </div>
            <el-progress :percentage="Math.round(val)" :color="progressColor(val)" :show-text="false" :stroke-width="8" />
          </div>
        </el-card>
      </div>
      <div class="col-equal">
        <el-card>
          <template #header>基本信息</template>
          <el-descriptions v-if="detail.entity" :column="1" size="small" border>
            <el-descriptions-item label="ID">
              <span style="font-family: monospace;">{{ detail.entity.id }}</span>
              <el-button link type="primary" size="small" style="margin-left: 6px;" @click="copyToClipboard(detail.entity.id)"><el-icon><CopyDocument /></el-icon></el-button>
            </el-descriptions-item>
            <el-descriptions-item label="名称">{{ detail.entity.name }}</el-descriptions-item>
            <el-descriptions-item label="类型">{{ detail.entity.type }}</el-descriptions-item>
            <el-descriptions-item label="订单">{{ detail.entity.total_orders }}</el-descriptions-item>
            <template v-if="detail.entity_type === 'carrier'">
              <el-descriptions-item label="准时率">{{ (detail.entity.on_time_orders / (detail.entity.completed_orders || 1) * 100).toFixed(1) }}%</el-descriptions-item>
              <el-descriptions-item label="投诉">{{ detail.entity.complaint_count }}</el-descriptions-item>
              <el-descriptions-item label="证照"><el-tag :type="detail.entity.license_valid ? 'success' : 'danger'" size="small">{{ detail.entity.license_valid ? '有效' : '无效' }}</el-tag></el-descriptions-item>
            </template>
            <template v-else>
              <el-descriptions-item label="及时率">{{ (detail.entity.on_time_payment_rate * 100).toFixed(1) }}%</el-descriptions-item>
              <el-descriptions-item label="逾期">{{ detail.entity.overdue_count }}</el-descriptions-item>
            </template>
          </el-descriptions>
        </el-card>
        <el-card>
          <template #header>
            <span>风险预警</span>
            <el-badge v-if="detail.risk_flags?.length" :value="detail.risk_flags.length" type="danger" style="margin-left: 8px;" />
          </template>
          <template v-if="detail.risk_flags?.length">
            <el-alert v-for="(flag, i) in detail.risk_flags" :key="i" :title="flag" :type="riskType(flag)" :closable="false" style="margin-bottom: 6px;" show-icon />
          </template>
          <el-result v-else icon="success" title="无风险预警" sub-title="信用良好" />
        </el-card>
      </div>
    </div>

    <h2 class="section-divider">存证信息</h2>
    <div class="two-col">
      <div class="col-equal">
        <div class="data-card">
          <div class="data-card-header">
            <span class="data-card-label"><el-icon><Lock /></el-icon> 数字签名</span>
            <el-button link type="primary" size="small" @click="copyToClipboard(detail.signature || '')"><el-icon><CopyDocument /></el-icon></el-button>
          </div>
          <div class="code-block" style="font-size: 10px;">{{ detail.signature?.slice(0, 28) || '无' }}<br />{{ detail.signature?.slice(28, 56) || '' }}</div>
          <el-tag type="success" size="small" style="margin-top: 8px;"><el-icon><CircleCheck /></el-icon> 有效</el-tag>
        </div>
      </div>
      <div class="col-equal">
        <div class="data-card">
          <div class="data-card-header">
            <span class="data-card-label"><el-icon><Connection /></el-icon> 区块链存证</span>
            <el-button v-if="detail.tx_hash" link type="primary" size="small" @click="copyToClipboard(detail.tx_hash)"><el-icon><CopyDocument /></el-icon></el-button>
          </div>
          <div class="code-block" style="font-size: 10px;">{{ detail.tx_hash?.slice(0, 28) || '无' }}<br />{{ detail.tx_hash?.slice(28, 56) || '' }}</div>
          <el-tag v-if="detail.tx_hash" type="success" size="small" style="margin-top: 8px;"><el-icon><CircleCheck /></el-icon> 已上链</el-tag>
          <el-tag v-else type="warning" size="small" style="margin-top: 8px;">未上链</el-tag>
        </div>
      </div>
    </div>
  </template>

  <div v-else class="empty-state">
    <div class="empty-state-icon"><el-icon size="28"><Search /></el-icon></div>
    <div class="empty-state-title">请选择一个实体</div>
    <div class="empty-state-desc">在上方选择器中选取一个实体以查看评分详情，请确认后端服务已启动</div>
  </div>
</template>
