<script setup>
import { ref, onMounted, computed } from 'vue'
import { Setting, DocumentChecked } from '@element-plus/icons-vue'
import { getConfig, updateConfig } from '../api'

const config = ref({})
const weights = ref({})
const originalWeights = ref({})
const saving = ref(false)
const configLoading = ref(false)

onMounted(() => {
  configLoading.value = true
  getConfig().then(data => {
    config.value = data
    if (data.dimensions) {
      for (const [name, dim] of Object.entries(data.dimensions)) {
        weights.value[name] = dim.weight
        originalWeights.value[name] = dim.weight
      }
    }
  }).catch(() => {}).finally(() => { configLoading.value = false })
})

const totalWeight = computed(() => Object.values(weights.value).reduce((s, w) => s + w, 0))
const isValid = computed(() => Math.abs(totalWeight.value - 1.0) < 0.01)
const hasChanges = computed(() => Object.keys(weights.value).some(name => weights.value[name] !== originalWeights.value[name]))
const sliderMarks = { 0: '0%', 0.25: '25%', 0.5: '50%' }
const dimColors = { '企业资质': '#2563EB', '履约能力': '#10B981', '服务质量': '#8B5CF6', '行为合规': '#F59E0B', '经营信用': '#EC4899' }

async function handleSave() {
  saving.value = true
  try {
    await updateConfig(weights.value)
    for (const name of Object.keys(weights.value)) originalWeights.value[name] = weights.value[name]
    ElMessage.success('配置已保存')
  } catch (e) { ElMessage.error('保存失败: ' + e.message) }
  saving.value = false
}
</script>

<template>
  <div class="page-header">
    <div class="page-breadcrumb">
      <el-breadcrumb separator="/">
        <el-breadcrumb-item :to="{ path: '/' }">首页</el-breadcrumb-item>
        <el-breadcrumb-item>评分配置</el-breadcrumb-item>
      </el-breadcrumb>
    </div>
    <h1 class="page-title"><el-icon size="22" color="#D4A017"><Setting /></el-icon>评分配置</h1>
    <p class="page-desc">动态调整评分维度权重 · 修改后需重新评估</p>
  </div>

  <div class="config-dimension-grid" v-loading="configLoading">
    <div class="config-dim-card" v-for="(weight, name) in weights" :key="name">
      <div class="config-dim-header">
        <span class="config-dim-name">
          <span class="tech-stack-dot" :style="{ background: dimColors[name] || '#94A3B8', display: 'inline-block', margin: '0 8px 0 0', verticalAlign: 'middle' }" />
          {{ name }}
        </span>
        <span class="config-dim-value" :class="{ changed: weight !== originalWeights[name] }">{{ (weight * 100).toFixed(0) }}%</span>
      </div>
      <el-slider v-model="weights[name]" :min="0" :max="0.5" :step="0.05" :marks="sliderMarks" :format-tooltip="(val) => `${(val * 100).toFixed(0)}%`" />
      <div style="display: flex; justify-content: space-between; font-size: 11px; color: var(--text-muted); margin-top: 4px;">
        <span>当前</span><span>原始: {{ (originalWeights[name] * 100).toFixed(0) }}%</span>
      </div>
    </div>
  </div>

  <el-card style="margin-bottom: 15px;">
    <el-row align="middle" justify="space-between">
      <el-col :span="12">
        <div style="display: flex; align-items: center; gap: 16px;">
          <div style="position: relative; width: 72px; height: 72px;">
            <svg width="72" height="72" viewBox="0 0 72 72">
              <circle cx="36" cy="36" r="30" fill="none" stroke="var(--border-light)" stroke-width="6" />
              <circle cx="36" cy="36" r="30" fill="none" :stroke="isValid ? '#0B8A5E' : '#C62828'" stroke-width="6" stroke-linecap="round" :stroke-dasharray="188.5" :stroke-dashoffset="188.5 - (188.5 * Math.min(totalWeight, 1.5) / 1.5)" transform="rotate(-90 36 36)" style="transition: all 0.6s ease;" />
            </svg>
            <div style="position: absolute; inset: 0; display: flex; align-items: center; justify-content: center; font-size: 18px; font-weight: 800; color: var(--text-primary);">{{ (totalWeight * 100).toFixed(0) }}%</div>
          </div>
          <div>
            <div style="font-size: 14px; font-weight: 600;">权重总和</div>
            <div style="font-size: 12px; color: var(--text-muted);">须等于 100%</div>
          </div>
        </div>
      </el-col>
      <el-col :span="12" style="text-align: right;">
        <el-tag :type="isValid ? 'success' : 'danger'" size="large">{{ isValid ? '配置正确' : '需调整为 1.0' }}</el-tag>
        <el-button type="primary" @click="handleSave" :loading="saving" :disabled="!hasChanges || !isValid" size="large" style="margin-left: 12px;"><el-icon><DocumentChecked /></el-icon> 保存配置</el-button>
      </el-col>
    </el-row>
  </el-card>

  <Transition name="page-fade">
    <el-alert v-if="hasChanges" type="warning" title="检测到未保存的改动" :closable="false" show-icon style="margin-bottom: 15px;" />
  </Transition>

  <el-collapse style="margin-bottom: 15px;">
    <el-collapse-item title="查看完整配置">
      <pre class="code-block">{{ JSON.stringify(config, null, 2) }}</pre>
    </el-collapse-item>
  </el-collapse>
</template>
