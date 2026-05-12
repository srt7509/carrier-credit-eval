<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { Bell, Warning, Search, Van, Document } from '@element-plus/icons-vue'
import { getAlerts, getAlertStats, updateAlert } from '../api'

const router = useRouter()
const alerts = ref([])
const stats = ref({})
const loading = ref(false)

const filterType = ref('')
const filterSeverity = ref('')
const filterStatus = ref('')
const filterDays = ref(90)

const alertTypes = ['评分快速下滑', '一票否决触发', '许可证即将过期', '连续多单投诉']
const severities = ['高', '中', '低']
const statuses = ['未处理', '处理中', '已处理']

async function loadAlerts() {
  loading.value = true
  try {
    const params = { days: filterDays.value }
    if (filterType.value) params.alert_type = filterType.value
    if (filterSeverity.value) params.severity = filterSeverity.value
    if (filterStatus.value) params.status = filterStatus.value
    const [a, s] = await Promise.all([getAlerts(params), getAlertStats()])
    alerts.value = a
    stats.value = s
  } catch (e) { console.error(e) }
  loading.value = false
}

onMounted(loadAlerts)

function goToProfile(entityId) { router.push(`/profile/${entityId}`) }

async function handleStatusChange(alertId, status) {
  try {
    await updateAlert(alertId, { status, handler_note: status === '已处理' ? '已处理完毕' : '' })
    ElMessage.success('状态已更新')
    await loadAlerts()
  } catch (e) { ElMessage.error('更新失败') }
}

function severityColor(s) {
  return { '高': 'danger', '中': 'warning', '低': 'info' }[s] || 'info'
}

function statusTag(s) {
  return { '未处理': 'danger', '处理中': 'warning', '已处理': 'success' }[s] || 'info'
}

function alertTypeIcon(t) {
  if (t === '一票否决触发') return 'error'
  if (t === '评分快速下滑') return 'warning'
  return 'info'
}
</script>

<template>
  <div class="page-header">
    <div class="page-breadcrumb">
      <el-breadcrumb separator="/">
        <el-breadcrumb-item :to="{ path: '/' }">首页</el-breadcrumb-item>
        <el-breadcrumb-item>风险预警</el-breadcrumb-item>
      </el-breadcrumb>
    </div>
    <h1 class="page-title"><el-icon size="22" color="#D4A017"><Bell /></el-icon>风险预警看板</h1>
    <p class="page-desc">集中展示需要关注的车辆风险信号</p>
  </div>

  <!-- KPI -->
  <div class="kpi-row">
    <div class="kpi-card">
      <div class="kpi-icon"><el-icon size="20"><Bell /></el-icon></div>
      <div class="kpi-label">总预警</div>
      <div class="kpi-value">{{ stats.total || 0 }}</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-icon"><el-icon size="20" color="#C62828"><Warning /></el-icon></div>
      <div class="kpi-label">未处理</div>
      <div class="kpi-value" style="color:#C62828;">{{ stats.unprocessed || 0 }}</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-icon"><el-icon size="20" color="#EF4444"><Warning /></el-icon></div>
      <div class="kpi-label">高危预警</div>
      <div class="kpi-value" style="color:#EF4444;">{{ stats.high_severity || 0 }}</div>
    </div>
  </div>

  <!-- Filter -->
  <div class="filter-card">
    <el-row :gutter="12" align="middle">
      <el-col :xs="12" :sm="6" :md="4">
        <el-select v-model="filterType" placeholder="预警类型" clearable style="width:100%" @change="loadAlerts">
          <el-option v-for="t in alertTypes" :key="t" :label="t" :value="t" />
        </el-select>
      </el-col>
      <el-col :xs="12" :sm="6" :md="4">
        <el-select v-model="filterSeverity" placeholder="严重程度" clearable style="width:100%" @change="loadAlerts">
          <el-option v-for="s in severities" :key="s" :label="s" :value="s" />
        </el-select>
      </el-col>
      <el-col :xs="12" :sm="6" :md="4">
        <el-select v-model="filterStatus" placeholder="处理状态" clearable style="width:100%" @change="loadAlerts">
          <el-option v-for="s in statuses" :key="s" :label="s" :value="s" />
        </el-select>
      </el-col>
      <el-col :xs="12" :sm="6" :md="4">
        <el-select v-model="filterDays" style="width:100%" @change="loadAlerts">
          <el-option :label="'近7天'" :value="7" />
          <el-option :label="'近30天'" :value="30" />
          <el-option :label="'近90天'" :value="90" />
        </el-select>
      </el-col>
    </el-row>
  </div>

  <!-- Alert Table -->
  <el-card>
    <template #header>预警记录</template>
    <el-table :data="alerts" v-loading="loading" stripe style="width:100%;">
      <el-table-column label="预警类型" min-width="140">
        <template #default="{ row }">
          <el-alert :type="alertTypeIcon(row.alert_type)" :title="row.alert_type" :closable="false" show-icon style="padding:0;" />
        </template>
      </el-table-column>
      <el-table-column label="车辆/企业" min-width="140">
        <template #default="{ row }">
          <el-button link type="primary" @click="goToProfile(row.entity_id)">
            <el-icon><Van /></el-icon> {{ row.entity_name }}
          </el-button>
        </template>
      </el-table-column>
      <el-table-column label="严重程度" width="90">
        <template #default="{ row }"><el-tag :type="severityColor(row.severity)" size="small">{{ row.severity }}</el-tag></template>
      </el-table-column>
      <el-table-column prop="trigger_time" label="触发时间" width="160" />
      <el-table-column label="当前评分" width="100">
        <template #default="{ row }">
          <span :style="{ color: row.current_score >= 80 ? '#0B8A5E' : row.current_score >= 60 ? '#C47D0B' : '#C62828', fontWeight:700 }">
            {{ row.current_score.toFixed(1) }}
          </span>
        </template>
      </el-table-column>
      <el-table-column label="处理状态" width="120">
        <template #default="{ row }">
          <el-select v-model="row.status" size="small" @change="(v) => handleStatusChange(row.alert_id, v)">
            <el-option v-for="s in statuses" :key="s" :label="s" :value="s" />
          </el-select>
        </template>
      </el-table-column>
      <el-table-column prop="handler_note" label="处理备注" min-width="120" />
    </el-table>
  </el-card>
</template>
