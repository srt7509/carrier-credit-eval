<script setup>
import { ref, onMounted, computed } from 'vue'
import { Connection, Histogram, Avatar, CreditCard, Search, Checked } from '@element-plus/icons-vue'
import { getBlockchainStatus, getBlockchainRecords, verifyBlockchain } from '../api'

const status = ref({})
const records = ref([])
const txInput = ref('')
const verifyResult = ref(null)
const verifying = ref(false)
const dataLoading = ref(false)

const recordCount = computed(() => records.value.length)
const connectionClass = computed(() => ({ 'status-dot': true, 'status-dot--connected': status.value.connected, 'status-dot--disconnected': !status.value.connected }))

onMounted(() => {
  dataLoading.value = true
  Promise.all([getBlockchainStatus(), getBlockchainRecords()]).then(([s, r]) => {
    status.value = s; records.value = r
  }).catch(() => {}).finally(() => { dataLoading.value = false })
})

async function handleVerify() {
  if (!txInput.value) return
  verifying.value = true; verifyResult.value = null
  try {
    verifyResult.value = await verifyBlockchain(txInput.value)
    if (verifyResult.value?.result?.is_valid) ElMessage.success('存证验证通过')
  } catch (e) { verifyResult.value = { error: e.message }; ElMessage.error('验证失败: ' + e.message) }
  verifying.value = false
}
</script>

<template>
  <div class="page-header">
    <div class="page-breadcrumb">
      <el-breadcrumb separator="/">
        <el-breadcrumb-item :to="{ path: '/' }">首页</el-breadcrumb-item>
        <el-breadcrumb-item>区块链验证</el-breadcrumb-item>
      </el-breadcrumb>
    </div>
    <h1 class="page-title"><el-icon size="22" color="#D4A017"><Connection /></el-icon>区块链验证<span :class="connectionClass" style="margin-left: 6px;" /></h1>
    <p class="page-desc">查看区块链存证状态并验证数据完整性</p>
  </div>

  <div class="kpi-row">
    <div class="kpi-card">
      <div class="kpi-icon"><el-icon size="20" :color="status.connected ? '#10B981' : '#EF4444'"><Connection /></el-icon></div>
      <div class="kpi-label">连接状态</div>
      <div style="font-size: 16px; font-weight: 700; color: var(--text-primary); margin-top: 2px;">{{ status.connected ? '已连接' : '未连接' }}</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-icon"><el-icon size="20"><Histogram /></el-icon></div>
      <div class="kpi-label">当前区块</div>
      <div class="kpi-value">{{ status.block_number || 0 }}</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-icon"><el-icon size="20"><Avatar /></el-icon></div>
      <div class="kpi-label">测试账户</div>
      <div class="kpi-value">{{ status.accounts_count || 0 }}</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-icon"><el-icon size="20"><CreditCard /></el-icon></div>
      <div class="kpi-label">链 ID</div>
      <div style="font-size: 24px; font-weight: 800; color: var(--text-primary); margin-top: 2px;">{{ status.chain_id }}</div>
    </div>
  </div>

  <el-card>
    <template #header><span>存证记录</span><el-tag size="small" type="info" style="margin-left: 8px;">最近 {{ recordCount }} 条</el-tag></template>
    <el-table :data="records" v-loading="dataLoading" stripe>
      <el-table-column prop="entity_id" label="实体ID" width="100" />
      <el-table-column label="交易哈希" min-width="200">
        <template #default="{ row }"><span style="font-family: monospace; font-size: 12px;">{{ row.tx_hash?.slice(0, 24) }}...</span></template>
      </el-table-column>
      <el-table-column prop="block_number" label="区块号" width="100">
        <template #default="{ row }"><el-tag size="small">{{ row.block_number }}</el-tag></template>
      </el-table-column>
      <el-table-column prop="on_chain_time" label="上链时间" width="180" />
      <el-table-column label="状态" width="100">
        <template #default="{ row }"><el-tag :type="row.verified ? 'success' : 'warning'" size="small">{{ row.verified ? '已验证' : '未验证' }}</el-tag></template>
      </el-table-column>
    </el-table>
  </el-card>

  <el-card>
    <template #header>验证存证</template>
    <el-row :gutter="15">
      <el-col :span="18"><el-input v-model="txInput" placeholder="输入交易哈希 (0x...)"><template #prefix><el-icon><Search /></el-icon></template></el-input></el-col>
      <el-col :span="6"><el-button type="primary" @click="handleVerify" :loading="verifying" style="width: 100%;"><el-icon><Checked /></el-icon> 验证</el-button></el-col>
    </el-row>
  </el-card>

  <Transition name="page-fade">
    <div v-if="verifyResult?.result?.is_valid" class="glass-card" style="margin-top: 15px; padding: 24px; text-align: center;">
      <el-result icon="success" title="存证验证通过" sub-title="数据完整，未被篡改" />
    </div>
  </Transition>
</template>
