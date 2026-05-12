<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { Monitor, Clock, Van, OfficeBuilding, DataAnalysis, Connection, Search, Setting } from '@element-plus/icons-vue'
import { getStats, getBlockchainStatus } from '../api'

const router = useRouter()
const stats = ref({})
const blockchain = ref({})
const statsLoading = ref(false)
const uptime = ref('')
let uptimeInterval = null

const techStack = [
  { name: 'Flask', desc: '后端框架', color: '#2563EB' },
  { name: 'Vue 3', desc: '前端框架', color: '#10B981' },
  { name: 'SQLite', desc: '数据存储', color: '#C47D0B' },
  { name: 'Web3.py', desc: '区块链', color: '#8B5CF6' },
]

const apiEndpoints = [
  { method: 'GET', path: '/api/scores', desc: '获取评分列表' },
  { method: 'GET', path: '/api/scores/:id', desc: '获取评分详情' },
  { method: 'GET', path: '/api/stats', desc: '获取统计数据' },
  { method: 'POST', path: '/api/signature/verify', desc: '验证数字签名' },
  { method: 'GET', path: '/api/blockchain/status', desc: '区块链状态' },
  { method: 'GET', path: '/api/blockchain/records', desc: '存证记录' },
  { method: 'GET', path: '/api/config', desc: '获取评分配置' },
  { method: 'PUT', path: '/api/config', desc: '更新评分配置' },
  { method: 'GET', path: '/api/export', desc: '导出 CSV' },
]

onMounted(() => {
  statsLoading.value = true
  Promise.all([getStats(), getBlockchainStatus()]).then(([s, b]) => {
    stats.value = s; blockchain.value = b
  }).catch(() => {}).finally(() => { statsLoading.value = false })

  const startTime = Date.now()
  uptimeInterval = setInterval(() => {
    const elapsed = Math.floor((Date.now() - startTime) / 1000)
    const h = Math.floor(elapsed / 3600); const m = Math.floor((elapsed % 3600) / 60); const s = elapsed % 60
    uptime.value = `${h}h ${m}m ${s}s`
  }, 1000)
})

onUnmounted(() => { clearInterval(uptimeInterval) })
</script>

<template>
  <div class="page-header">
    <div class="page-breadcrumb">
      <el-breadcrumb separator="/">
        <el-breadcrumb-item :to="{ path: '/' }">首页</el-breadcrumb-item>
        <el-breadcrumb-item>系统状态</el-breadcrumb-item>
      </el-breadcrumb>
    </div>
    <h1 class="page-title"><el-icon size="22" color="#D4A017"><Monitor /></el-icon>系统状态</h1>
    <p class="page-desc">
      查看系统运行状态与数据统计
      <span style="margin-left: 12px; font-size: 11px; color: var(--text-muted);"><el-icon size="12"><Clock /></el-icon> 运行时间: {{ uptime }}</span>
    </p>
  </div>

  <div class="kpi-row">
    <div class="kpi-card">
      <div class="kpi-icon"><el-icon size="20" color="#1A365D"><Van /></el-icon></div>
      <div class="kpi-label">车辆</div>
      <div class="kpi-value">{{ stats.vehicle_count || 0 }}</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-icon"><el-icon size="20" color="#3D5A80"><OfficeBuilding /></el-icon></div>
      <div class="kpi-label">货主</div>
      <div class="kpi-value">{{ stats.shipper_count || 0 }}</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-icon"><el-icon size="20" color="#0A1628"><DataAnalysis /></el-icon></div>
      <div class="kpi-label">总评分</div>
      <div class="kpi-value">{{ stats.score_count || 0 }}</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-icon"><el-icon size="20" color="#D4A017"><Connection /></el-icon></div>
      <div class="kpi-label">存证数</div>
      <div class="kpi-value">{{ stats.record_count || 0 }}</div>
    </div>
  </div>

  <el-card>
    <template #header>区块链状态</template>
    <el-descriptions :column="3" border v-loading="statsLoading">
      <el-descriptions-item label="连接状态"><el-tag :type="blockchain.connected ? 'success' : 'danger'">{{ blockchain.connected ? '已连接' : '未连接' }}</el-tag></el-descriptions-item>
      <el-descriptions-item label="区块高度">{{ blockchain.block_number }}</el-descriptions-item>
      <el-descriptions-item label="测试账户">{{ blockchain.accounts_count }}</el-descriptions-item>
    </el-descriptions>
  </el-card>

  <el-card>
    <template #header>API 端点</template>
    <el-table :data="apiEndpoints" size="small" stripe>
      <el-table-column label="方法" width="80">
        <template #default="{ row }"><el-tag :type="row.method === 'GET' ? 'success' : row.method === 'POST' ? 'warning' : 'info'" size="small" style="font-family: monospace; font-weight: 700;">{{ row.method }}</el-tag></template>
      </el-table-column>
      <el-table-column prop="path" label="路径">
        <template #default="{ row }"><span style="font-family: monospace; font-size: 13px;">{{ row.path }}</span></template>
      </el-table-column>
      <el-table-column prop="desc" label="说明" />
    </el-table>
  </el-card>

  <el-card>
    <template #header>技术栈</template>
    <div class="tech-stack-grid">
      <div class="tech-stack-card" v-for="(item, i) in techStack" :key="i">
        <div class="tech-stack-dot" :style="{ background: item.color }"></div>
        <div class="tech-stack-name">{{ item.name }}</div>
        <div class="tech-stack-desc">{{ item.desc }}</div>
      </div>
    </div>
  </el-card>

  <el-card>
    <template #header>快捷操作</template>
    <el-row :gutter="12">
      <el-col :span="6"><el-button style="width: 100%;" @click="router.push('/')"><el-icon><DataAnalysis /></el-icon> 车辆管理</el-button></el-col>
      <el-col :span="6"><el-button style="width: 100%;" @click="router.push('/monitor')"><el-icon><DataAnalysis /></el-icon> 模型监控</el-button></el-col>
      <el-col :span="6"><el-button style="width: 100%;" @click="router.push('/alerts')"><el-icon><Search /></el-icon> 风险预警</el-button></el-col>
      <el-col :span="6"><el-button style="width: 100%;" @click="router.push('/config')"><el-icon><Setting /></el-icon> 评分配置</el-button></el-col>
    </el-row>
  </el-card>
</template>
