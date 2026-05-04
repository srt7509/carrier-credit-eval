<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import { Lock, Document, Key, Warning } from '@element-plus/icons-vue'
import { getScores, verifySignature } from '../api'

const scores = ref([])
const selectedId = ref('')
const verifyResult = ref(null)
const tamperResult = ref(null)
const verifying = ref(false)
const scoresLoading = ref(false)

const selectedScore = computed(() => scores.value.find(s => s.entity_id === selectedId.value))
const currentStep = computed(() => {
  if (!selectedId.value) return 0
  if (!verifyResult.value && !tamperResult.value) return 1
  return 2
})

onMounted(() => {
  scoresLoading.value = true
  getScores().then(data => {
    scores.value = data
    if (data.length) selectedId.value = data[0].entity_id
  }).catch(() => {}).finally(() => { scoresLoading.value = false })
})

watch(selectedId, () => { verifyResult.value = null; tamperResult.value = null })

async function handleVerify() {
  verifying.value = true; verifyResult.value = null
  try {
    const res = await verifySignature(selectedId.value, false)
    verifyResult.value = res
  } catch (e) { verifyResult.value = { error: e.message }; ElMessage.error('校验失败: ' + e.message) }
  verifying.value = false
}

async function handleTamper() {
  verifying.value = true; tamperResult.value = null
  try {
    const res = await verifySignature(selectedId.value, true)
    tamperResult.value = res
  } catch (e) { tamperResult.value = { error: e.message }; ElMessage.error('检测失败: ' + e.message) }
  verifying.value = false
}

function gradeClass(g) { return { 'grade-badge': true, [`grade-${g}`]: true } }
</script>

<template>
  <div class="page-header">
    <div class="page-breadcrumb">
      <el-breadcrumb separator="/">
        <el-breadcrumb-item :to="{ path: '/' }">首页</el-breadcrumb-item>
        <el-breadcrumb-item>签名校验</el-breadcrumb-item>
      </el-breadcrumb>
    </div>
    <h1 class="page-title"><el-icon size="22" color="#D4A017"><Lock /></el-icon>签名校验</h1>
    <p class="page-desc">数字签名用于验证评分数据是否被篡改</p>
  </div>

  <div class="step-indicator" style="margin-bottom: 20px; justify-content: center;">
    <div class="step-dot" :class="{ completed: currentStep >= 1 }">1</div>
    <div class="step-line" :class="{ completed: currentStep >= 2 }" />
    <div class="step-dot" :class="{ active: currentStep === 2, completed: currentStep >= 2 }">2</div>
    <div class="step-line" :class="{ completed: currentStep >= 3 }" />
    <div class="step-dot" :class="{ active: currentStep >= 2, completed: currentStep >= 2 }">3</div>
  </div>
  <div style="text-align: center; margin-bottom: 20px; font-size: 12px; color: var(--text-muted);">选择实体 → 执行校验 → 查看结果</div>

  <div class="filter-card" style="margin-bottom: 15px;">
    <el-select v-model="selectedId" placeholder="选择实体" style="width: 300px;" filterable :loading="scoresLoading">
      <el-option v-for="s in scores" :key="s.entity_id" :label="`${s.entity_id} - ${s.entity_type === 'carrier' ? '承运商' : '货主'}`" :value="s.entity_id" />
    </el-select>
  </div>

  <div class="two-col" style="margin-bottom: 15px;">
    <div class="col-equal">
      <div class="data-card">
        <div class="data-card-header"><span class="data-card-label"><el-icon><Document /></el-icon> 评分数据</span></div>
        <el-descriptions v-if="selectedScore" :column="1" border size="small">
          <el-descriptions-item label="实体ID">{{ selectedScore.entity_id }}</el-descriptions-item>
          <el-descriptions-item label="类型">{{ selectedScore.entity_type === 'carrier' ? '承运商' : '货主' }}</el-descriptions-item>
          <el-descriptions-item label="评分"><span style="font-weight: 700;">{{ selectedScore.score_value.toFixed(1) }}</span></el-descriptions-item>
          <el-descriptions-item label="等级"><span :class="gradeClass(selectedScore.grade)">{{ selectedScore.grade }}</span></el-descriptions-item>
        </el-descriptions>
      </div>
    </div>
    <div class="col-equal">
      <div class="data-card">
        <div class="data-card-header"><span class="data-card-label"><el-icon><Key /></el-icon> 存储的签名</span></div>
        <div class="code-block" style="font-size: 10px;">{{ selectedScore?.signature?.slice(0, 40) || '无签名' }}<br />{{ selectedScore?.signature?.slice(40) || '' }}</div>
      </div>
    </div>
  </div>

  <el-row :gutter="15" style="margin-top: 15px;">
    <el-col :span="12">
      <el-button type="primary" @click="handleVerify" :loading="verifying" size="large" style="width: 100%;"><el-icon><Lock /></el-icon> 校验签名</el-button>
    </el-col>
    <el-col :span="12">
      <el-button @click="handleTamper" :loading="verifying" size="large" style="width: 100%;"><el-icon><Warning /></el-icon> 模拟篡改检测</el-button>
    </el-col>
  </el-row>

  <Transition name="page-fade">
    <div v-if="verifyResult" class="glass-card" style="margin-top: 15px; padding: 24px; text-align: center;">
      <el-result :icon="verifyResult.valid ? 'success' : 'error'" :title="verifyResult.valid ? '签名有效' : '签名无效'" :sub-title="verifyResult.error || '数据可能被篡改'" />
    </div>
  </Transition>
  <Transition name="page-fade">
    <div v-if="tamperResult" class="glass-card" style="margin-top: 15px; padding: 24px; text-align: center;">
      <el-result :icon="!tamperResult.valid ? 'success' : 'error'" :title="!tamperResult.valid ? '成功检测到篡改' : '校验意外通过'" sub-title="签名系统正常工作" />
    </div>
  </Transition>
</template>
