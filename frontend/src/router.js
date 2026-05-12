import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/', name: 'VehicleList', component: () => import('./views/VehicleList.vue'), meta: { title: '车辆管理 - 延长物流信用评价系统（Demo）' } },
  { path: '/profile/:id', name: 'VehicleProfile', component: () => import('./views/VehicleProfile.vue'), meta: { title: '信用画像 - 延长物流信用评价系统（Demo）' } },
  { path: '/monitor', name: 'ModelMonitor', component: () => import('./views/ModelMonitor.vue'), meta: { title: '模型监控 - 延长物流信用评价系统（Demo）' } },
  { path: '/business', name: 'BusinessConfig', component: () => import('./views/BusinessConfig.vue'), meta: { title: '业务联动配置 - 延长物流信用评价系统（Demo）' } },
  { path: '/alerts', name: 'AlertDashboard', component: () => import('./views/AlertDashboard.vue'), meta: { title: '风险预警 - 延长物流信用评价系统（Demo）' } },
  { path: '/signature', name: 'Signature', component: () => import('./views/Signature.vue'), meta: { title: '签名校验 - 延长物流信用评价系统（Demo）' } },
  { path: '/blockchain', name: 'Blockchain', component: () => import('./views/Blockchain.vue'), meta: { title: '区块链验证 - 延长物流信用评价系统（Demo）' } },
  { path: '/config', name: 'Config', component: () => import('./views/Config.vue'), meta: { title: '评分配置 - 延长物流信用评价系统（Demo）' } },
  { path: '/status', name: 'Status', component: () => import('./views/Status.vue'), meta: { title: '系统状态 - 延长物流信用评价系统（Demo）' } },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.afterEach((to) => {
  document.title = to.meta.title || '延长物流信用评价系统（Demo）'
})

export default router
