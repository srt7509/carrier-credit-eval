import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import 'element-plus/dist/index.css'
import './styles/global.css'

const app = createApp(App)
app.use(router).mount('#app')

// 后台预加载 ECharts，消除页面切换时的下载延迟
setTimeout(() => {
  import('echarts/charts')
  import('echarts/components')
  import('echarts/core')
  import('echarts/renderers')
}, 500)