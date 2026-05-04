<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { Van, Monitor, Setting, Lock, Connection, DataAnalysis, Bell, Briefcase, Sunny, Moon } from '@element-plus/icons-vue'

const route = useRoute()
const isDark = ref(false)

onMounted(() => {
  const saved = localStorage.getItem('theme')
  if (saved === 'dark') {
    isDark.value = true
    document.documentElement.setAttribute('data-theme', 'dark')
  }
})

function toggleTheme() {
  isDark.value = !isDark.value
  const theme = isDark.value ? 'dark' : 'light'
  document.documentElement.setAttribute('data-theme', theme)
  localStorage.setItem('theme', theme)
}

const navItems = [
  { path: '/', name: '承运商', icon: Van },
  { path: '/monitor', name: '模型监控', icon: Monitor },
  { path: '/business', name: '联动配置', icon: Briefcase },
  { path: '/alerts', name: '风险预警', icon: Bell },
  { path: '/signature', name: '签名', icon: Lock },
  { path: '/blockchain', name: '区块链', icon: Connection },
  { path: '/config', name: '评分配置', icon: Setting },
  { path: '/status', name: '系统状态', icon: DataAnalysis },
]
</script>

<template>
  <div class="app-layout" :class="{ 'is-dark': isDark }">
    <aside class="sidebar">
      <div class="sidebar-logo">
        <ElIcon size="28" color="#D4A017"><Van /></ElIcon>
        <h1>延长物流信用评价系统（Demo）</h1>
        <p>Carrier CredEval v2.0</p>
      </div>

      <ElMenu :default-active="route.path" class="sidebar-menu" router :collapse="false">
        <ElMenuItem v-for="item in navItems" :key="item.path" :index="item.path">
          <ElIcon><component :is="item.icon" /></ElIcon>
          <span>{{ item.name }}</span>
        </ElMenuItem>
      </ElMenu>

      <div class="sidebar-footer">v2.0 · Flask + Vue 3<br />作者：中韩物流研究院</div>
    </aside>

    <main class="main-content">
      <router-view v-slot="{ Component }">
        <keep-alive include="CarrierList,AlertDashboard">
          <component :is="Component" />
        </keep-alive>
      </router-view>
    </main>

    <button class="theme-toggle" @click="toggleTheme" :title="isDark ? '切换到亮色模式' : '切换到暗色模式'">
      <ElIcon size="18"><component :is="isDark ? Sunny : Moon" /></ElIcon>
    </button>
  </div>
</template>
