<script setup>
import { ref, onMounted, nextTick, onUnmounted } from 'vue'
import { Monitor, DataAnalysis, TrendCharts, CircleCheck, CircleClose, Warning, Switch } from '@element-plus/icons-vue'
import { getModelPerformance, getModelRegistry, getModelSwitchStatus } from '../api'

let echarts = null
async function loadEcharts() {
  if (echarts) return echarts
  const [{ LineChart, GaugeChart }, { TooltipComponent, LegendComponent, GridComponent }, core, { CanvasRenderer }] = await Promise.all([
    import('echarts/charts'),
    import('echarts/components'),
    import('echarts/core'),
    import('echarts/renderers'),
  ])
  core.use([LineChart, GaugeChart, TooltipComponent, LegendComponent, GridComponent, CanvasRenderer])
  echarts = core
  return core
}

const performance = ref({ champion: [], challenger: [] })
const registry = ref([])
const switchStatus = ref(null)
const loading = ref(true)

let ksChart = null
let aucChart = null
let psiChart = null
let spearmanChart = null
let gaugeChart = null

onMounted(async () => {
  loading.value = true
  try {
    const [perf, reg, sw] = await Promise.all([
      getModelPerformance(), getModelRegistry(), getModelSwitchStatus(),
    ])
    performance.value = perf
    registry.value = reg
    switchStatus.value = sw
    await loadEcharts()
    await nextTick()
    initCharts()
  } catch (e) { console.error(e) }
  loading.value = false
})

onUnmounted(() => {
  ksChart?.dispose(); aucChart?.dispose(); psiChart?.dispose()
  spearmanChart?.dispose(); gaugeChart?.dispose()
})

function makeLineChart(domId, chartRef, title, champData, challData, yName) {
  const dom = document.getElementById(domId)
  if (!dom) return
  chartRef?.dispose()
  const chart = echarts.init(dom)
  const periods = champData.map(d => d.period)
  chart.setOption({
    tooltip: { trigger: 'axis', backgroundColor: 'rgba(10,22,40,0.92)', borderColor: 'rgba(212,160,23,0.3)', textStyle: { color: '#FFF', fontSize: 12 } },
    legend: { data: ['冠军模型', '挑战者模型'], bottom: 0, textStyle: { color: '#64748B', fontSize: 10 } },
    grid: { left: 50, right: 15, top: 15, bottom: 35 },
    xAxis: { type: 'category', data: periods, axisLabel: { color: '#64748B', fontSize: 9, rotate: 30 } },
    yAxis: { type: 'value', name: yName, nameTextStyle: { color: '#94A3B8', fontSize: 10 }, axisLabel: { color: '#64748B', fontSize: 10 } },
    series: [
      { name: '冠军模型', type: 'line', data: champData.map(d => d[yName.toLowerCase()]), smooth: true, lineStyle: { color: '#1A365D', width: 2.5 }, itemStyle: { color: '#1A365D' }, symbol: 'circle', symbolSize: 5 },
      { name: '挑战者模型', type: 'line', data: challData.map(d => d[yName.toLowerCase()]), smooth: true, lineStyle: { color: '#D4A017', width: 2.5 }, itemStyle: { color: '#D4A017' }, symbol: 'diamond', symbolSize: 5 },
    ],
    animationDuration: 600,
  })
  return chart
}

function initCharts() {
  const c = performance.value.champion
  const h = performance.value.challenger
  if (!c.length || !h.length) return

  ksChart = makeLineChart('ksChart', ksChart, 'KS', c, h, 'Ks')
  aucChart = makeLineChart('aucChart', aucChart, 'AUC', c, h, 'Auc')
  psiChart = makeLineChart('psiChart', psiChart, 'PSI', c, h, 'Psi')

  // Spearman
  const dom = document.getElementById('spearmanChart')
  if (dom) {
    spearmanChart?.dispose()
    spearmanChart = echarts.init(dom)
    const spearmanData = h.map(d => d.spearman || 0)
    spearmanChart.setOption({
      tooltip: { trigger: 'axis', backgroundColor: 'rgba(10,22,40,0.92)', borderColor: 'rgba(212,160,23,0.3)', textStyle: { color: '#FFF', fontSize: 12 } },
      grid: { left: 50, right: 15, top: 15, bottom: 35 },
      xAxis: { type: 'category', data: h.map(d => d.period), axisLabel: { color: '#64748B', fontSize: 9, rotate: 30 } },
      yAxis: { type: 'value', name: 'Spearman', min: 0.5, max: 1, nameTextStyle: { color: '#94A3B8', fontSize: 10 }, axisLabel: { color: '#64748B', fontSize: 10 } },
      series: [{
        type: 'line', data: spearmanData, smooth: true,
        lineStyle: { color: '#8B5CF6', width: 2.5 }, itemStyle: { color: '#8B5CF6' },
        symbol: 'circle', symbolSize: 5,
        markLine: { silent: true, data: [{ yAxis: 0.75, label: { formatter: '阈值 0.75', fontSize: 9 }, lineStyle: { color: '#C62828', type: 'dashed' } }] },
      }],
      animationDuration: 600,
    })
  }

  // Switch gauge
  const gaugeDom = document.getElementById('gaugeChart')
  if (gaugeDom && switchStatus.value) {
    gaugeChart?.dispose()
    gaugeChart = echarts.init(gaugeDom)
    const passed = [
      switchStatus.value.conditions.epv_satisfied ? 1 : 0,
      switchStatus.value.conditions.ks_not_lower ? 1 : 0,
      switchStatus.value.conditions.psi_ok ? 1 : 0,
      switchStatus.value.conditions.spearman_ok ? 1 : 0,
    ].reduce((a, b) => a + b, 0)
    gaugeChart.setOption({
      series: [{
        type: 'gauge',
        startAngle: 210, endAngle: -30,
        min: 0, max: 4,
        axisLine: { lineStyle: { width: 20, color: [[0.25, '#C62828'], [0.5, '#C47D0B'], [0.75, '#2563EB'], [1, '#0B8A5E']] } },
        pointer: { length: '70%', width: 6, itemStyle: { color: '#1A365D' } },
        axisTick: { distance: -20, length: 6 },
        splitLine: { distance: -24, length: 14 },
        axisLabel: { distance: 30, fontSize: 11, color: '#64748B' },
        detail: { valueAnimation: true, fontSize: 32, fontWeight: 700, color: '#1A365D', formatter: '{value}/4' },
        data: [{ value: passed, name: '达标项' }],
      }],
    })
  }
}

function modelStatusTag(status) {
  const m = { '运行中': 'success', '影子运行中': 'warning', '达标待切换': '', '已切换': 'info', '已归档': 'info' }
  return m[status] || 'info'
}
</script>

<template>
  <div class="page-header">
    <div class="page-breadcrumb">
      <el-breadcrumb separator="/">
        <el-breadcrumb-item :to="{ path: '/' }">首页</el-breadcrumb-item>
        <el-breadcrumb-item>模型监控</el-breadcrumb-item>
      </el-breadcrumb>
    </div>
    <h1 class="page-title"><el-icon size="22" color="#D4A017"><Monitor /></el-icon>评分模型监控看板</h1>
    <p class="page-desc">实时掌握冠军与挑战者模型的运行状态</p>
  </div>

  <!-- 模型状态区 -->
  <el-card style="margin-bottom:15px;" v-loading="loading">
    <template #header>模型状态</template>
    <el-row :gutter="15">
      <el-col :span="12" v-for="m in registry" :key="m.model_version">
        <div class="data-card">
          <div class="data-card-header">
            <span class="data-card-label">
              <el-tag :type="m.model_role === 'champion' ? 'success' : 'warning'" size="small" style="margin-right:8px;">{{ m.model_role === 'champion' ? '冠军模型' : '挑战者模型' }}</el-tag>
              {{ m.model_version }}
            </span>
            <el-tag :type="modelStatusTag(m.status)" size="small">{{ m.status }}</el-tag>
          </div>
          <el-descriptions :column="3" size="small" style="margin-top:8px;">
            <el-descriptions-item label="上线日期">{{ m.online_date }}</el-descriptions-item>
            <el-descriptions-item label="更新周期">{{ m.update_cycle }}</el-descriptions-item>
            <el-descriptions-item label="维度数">{{ m.dimension_count }}</el-descriptions-item>
            <el-descriptions-item v-if="m.model_role === 'challenger'" label="连续达标月数">
              <span :style="{ color: m.consecutive_pass_months >= 6 ? '#0B8A5E' : '#C47D0B', fontWeight:700 }">{{ m.consecutive_pass_months }}</span>
            </el-descriptions-item>
          </el-descriptions>
        </div>
      </el-col>
    </el-row>
  </el-card>

  <!-- 性能监控图 -->
  <div class="two-col" style="margin-bottom:15px;">
    <div class="col-equal"><el-card><template #header>KS 趋势</template><div id="ksChart" style="height:250px;" /></el-card></div>
    <div class="col-equal"><el-card><template #header>AUC 趋势</template><div id="aucChart" style="height:250px;" /></el-card></div>
  </div>
  <div class="two-col" style="margin-bottom:15px;">
    <div class="col-equal"><el-card><template #header>PSI 趋势</template><div id="psiChart" style="height:250px;" /></el-card></div>
    <div class="col-equal"><el-card><template #header>Spearman 相关系数</template><div id="spearmanChart" style="height:250px;" /></el-card></div>
  </div>

  <!-- 切换判定仪表盘 -->
  <el-card v-if="switchStatus" style="margin-bottom:15px;">
    <template #header>切换判定</template>
    <el-row :gutter="15">
      <el-col :span="14">
        <div style="display:grid; grid-template-columns: 1fr 1fr; gap:12px;">
          <div class="data-card" v-for="(val, key) in {
            'EPV 达标': switchStatus.conditions.epv_satisfied,
            'KS ≥ 冠军': switchStatus.conditions.ks_not_lower,
            'PSI < 0.1': switchStatus.conditions.psi_ok,
            'Spearman > 0.75': switchStatus.conditions.spearman_ok,
          }" :key="key">
            <div style="display:flex; align-items:center; gap:8px;">
              <el-icon :size="20" :color="val ? '#0B8A5E' : '#C62828'">
                <CircleCheck v-if="val" /><CircleClose v-else />
              </el-icon>
              <div>
                <div style="font-weight:600; font-size:14px;">{{ key }}</div>
                <div style="font-size:12px; color:var(--text-muted);">{{ val ? '已达标' : '未达标' }}</div>
              </div>
            </div>
          </div>
          <div class="data-card">
            <div style="display:flex; align-items:center; gap:8px;">
              <el-icon :size="20" :color="switchStatus.conditions.consecutive_months >= switchStatus.conditions.required_months ? '#0B8A5E' : '#C47D0B'">
                <DataAnalysis />
              </el-icon>
              <div>
                <div style="font-weight:600; font-size:14px;">连续达标月数</div>
                <div style="font-size:12px; color:var(--text-muted);">
                  {{ switchStatus.conditions.consecutive_months }} / {{ switchStatus.conditions.required_months }} 月
                </div>
              </div>
            </div>
          </div>
        </div>
      </el-col>
      <el-col :span="10">
        <div id="gaugeChart" style="height:200px;" />
      </el-col>
    </el-row>
    <div v-if="switchStatus.suggest_switch" style="text-align:center; margin-top:16px;">
      <el-alert type="success" title="建议切换" description="挑战者模型已满足全部切换条件，可在业务低峰期执行模型切换" show-icon :closable="false">
        <template #default>
          <el-button type="primary" size="small" style="margin-top:8px;"><el-icon><Switch /></el-icon> 发起切换审批</el-button>
        </template>
      </el-alert>
    </div>
  </el-card>
</template>
