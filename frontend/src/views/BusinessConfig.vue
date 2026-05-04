<script setup>
import { ref, onMounted, computed } from 'vue'
import { Setting, DocumentChecked, Edit, Van, Money, Warning, Bell } from '@element-plus/icons-vue'
import { getBusinessRules, updateBusinessRule } from '../api'

const rules = ref([])
const loading = ref(false)
const saving = ref(false)
const editingRule = ref(null)
const editValue = ref('')
const showEditDialog = ref(false)

const ruleTypeLabels = {
  access_threshold: { label: '准入阈值配置', icon: Van, desc: '承运商入驻平台的最低信用分/等级要求' },
  dispatch_priority: { label: '派单优先级配置', icon: Setting, desc: '信用等级对应的派单权重系数' },
  margin_ratio: { label: '保证金比例配置', icon: Money, desc: '信用等级对应的保证金费率' },
  financial_service: { label: '金融服务配置', icon: DocumentChecked, desc: '运费预付额度、贷款利率、还款周期' },
  one_vote_veto: { label: '一票否决规则配置', icon: Warning, desc: '触发立即降级和暂停合作的事件' },
  alert_threshold: { label: '预警阈值配置', icon: Bell, desc: '评分快速下滑、连续投诉等预警条件' },
}

const groupedRules = computed(() => {
  const groups = {}
  rules.value.forEach(r => {
    if (!groups[r.rule_type]) groups[r.rule_type] = []
    groups[r.rule_type].push(r)
  })
  return groups
})

const ruleTypes = computed(() => Object.keys(groupedRules.value))

onMounted(async () => {
  loading.value = true
  try { rules.value = await getBusinessRules() } catch (e) { console.error(e) }
  loading.value = false
})

function openEdit(rule) {
  editingRule.value = rule
  editValue.value = JSON.stringify(rule.rule_value, null, 2)
  showEditDialog.value = true
}

async function saveRule() {
  saving.value = true
  try {
    let parsed
    try { parsed = JSON.parse(editValue.value) } catch { ElMessage.error('JSON 格式错误'); saving.value = false; return }
    await updateBusinessRule(editingRule.value.rule_id, {
      rule_value: parsed,
      description: editingRule.value.description,
      is_active: editingRule.value.is_active,
    })
    ElMessage.success('已保存，实时生效')
    showEditDialog.value = false
    rules.value = await getBusinessRules()
  } catch (e) { ElMessage.error('保存失败: ' + e.message) }
  saving.value = false
}

function formatValue(val) {
  if (typeof val === 'object') return JSON.stringify(val, null, 2)
  return String(val)
}
</script>

<template>
  <div class="page-header">
    <div class="page-breadcrumb">
      <el-breadcrumb separator="/">
        <el-breadcrumb-item :to="{ path: '/' }">首页</el-breadcrumb-item>
        <el-breadcrumb-item>业务联动配置</el-breadcrumb-item>
      </el-breadcrumb>
    </div>
    <h1 class="page-title"><el-icon size="22" color="#D4A017"><Setting /></el-icon>业务决策联动配置</h1>
    <p class="page-desc">将信用评价结果嵌入平台核心业务环节 · 在线编辑，实时生效</p>
  </div>

  <div v-loading="loading">
    <el-card v-for="rt in ruleTypes" :key="rt" style="margin-bottom:15px;">
      <template #header>
        <div style="display:flex; align-items:center; gap:8px;">
          <el-icon size="18" color="#D4A017"><component :is="ruleTypeLabels[rt]?.icon || Setting" /></el-icon>
          <span style="font-weight:700;">{{ ruleTypeLabels[rt]?.label || rt }}</span>
          <span style="font-size:12px; color:var(--text-muted);">— {{ ruleTypeLabels[rt]?.desc }}</span>
        </div>
      </template>
      <el-table :data="groupedRules[rt]" stripe size="small">
        <el-table-column prop="rule_key" label="规则键" width="180" />
        <el-table-column label="规则值" min-width="300">
          <template #default="{ row }">
            <pre class="code-block" style="margin:0; font-size:11px; max-height:120px; overflow:auto;">{{ formatValue(row.rule_value) }}</pre>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="80">
          <template #default="{ row }"><el-tag :type="row.is_active ? 'success' : 'info'" size="small">{{ row.is_active ? '启用' : '停用' }}</el-tag></template>
        </el-table-column>
        <el-table-column label="操作" width="100">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="openEdit(row)"><el-icon><Edit /></el-icon> 编辑</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>

  <!-- 编辑弹窗 -->
  <el-dialog v-model="showEditDialog" title="编辑业务规则" width="600px">
    <el-input v-model="editValue" type="textarea" :rows="12" placeholder="JSON 格式的规则值" />
    <template #footer>
      <el-button @click="showEditDialog = false">取消</el-button>
      <el-button type="primary" @click="saveRule" :loading="saving"><el-icon><DocumentChecked /></el-icon> 保存并生效</el-button>
    </template>
  </el-dialog>
</template>
