# 信用评价系统前端（Credit Evaluation System Frontend）

这是一个基于 Vue 3 + Element Plus 的信用评价系统演示项目，用于展示承运商和货主的信用评分、区块链验证、数字签名等功能。

## 🚀 快速开始

### 一键启动（推荐）

```bash
# 构建并启动预览服务器
npm run start

# 访问 http://localhost:4173
```

### 分步启动

```bash
# 1. 构建生产版本
npm run build

# 2. 启动预览服务器
npm run preview

# 访问 http://localhost:4173
```

**注意**：需要先启动后端服务（端口 5001），否则前端无法获取数据。

## 📋 功能模块

### 1. 评分概览（Overview）
- 展示所有实体的信用评分列表
- 评分分布柱状图和等级占比饼图
- 支持按类型筛选（承运商/货主）
- 支持 CSV 数据导出

### 2. 评分详情（Detail）
- 查看单个实体的详细评分信息
- 五维度雷达图展示
- 基本信息描述
- 风险预警提示

### 3. 签名校验（Signature）
- 数字签名验证功能
- 支持篡改模拟测试
- 验证结果可视化展示

### 4. 区块链验证（Blockchain）
- 区块链存证记录查看
- 交易哈希验证
- 上链状态展示

### 5. 评分配置（Config）
- 五维度评分权重配置
- 实时更新评分结果
- 配置持久化保存

### 6. 系统状态（Status）
- 后端服务状态监控
- 区块链节点连接状态
- 技术栈信息展示

## 🏗️ 项目结构

```
frontend/
├── public/              # 静态资源
├── src/
│   ├── api/            # API 接口封装
│   │   └── index.js    # 包含内存缓存机制
│   ├── assets/         # 图片等资源
│   ├── components/     # Vue 组件（自动导入）
│   ├── styles/
│   │   └── global.css  # 全局样式
│   ├── views/          # 页面组件
│   │   ├── Overview.vue      # 评分概览
│   │   ├── Detail.vue        # 评分详情
│   │   ├── Signature.vue     # 签名校验
│   │   ├── Blockchain.vue    # 区块链验证
│   │   ├── Config.vue        # 评分配置
│   │   └── Status.vue        # 系统状态
│   ├── App.vue         # 主应用组件（含 KeepAlive 缓存）
│   ├── main.js         # 应用入口
│   └── router.js       # 路由配置
├── dist/               # 构建输出目录
├── package.json        # 项目依赖
├── vite.config.js      # Vite 构建配置
└── README.md           # 本文件
```

## 🛠️ 技术栈

- **Vue 3.5.32** - 前端框架
- **Vue Router 4.6.4** - 路由管理
- **Element Plus 2.13.7** - UI 组件库
- **ECharts 6.0.0** - 数据可视化
- **Axios 1.15.2** - HTTP 请求
- **Vite 8.0.10** - 构建工具

## ⚙️ 性能优化

本项目针对 demo 演示进行了以下优化：

1. **组件缓存（KeepAlive）** - 页面切换时组件不会重新创建，避免重复渲染
2. **API 缓存机制** - 30秒内存缓存，避免重复请求相同数据
3. **代码分割** - Element Plus、ECharts 等库独立打包，按需加载
4. **页面过渡动画** - 200ms 平滑切换动画，提升用户体验

## 🔧 配置说明

### 后端 API 地址

默认代理到 `http://localhost:5001`，可在 `vite.config.js` 中修改：

```javascript
server: {
  proxy: {
    "/api": "http://localhost:5001",  // 修改为实际后端地址
  },
}
```

### 评分维度权重

默认权重配置：
- 履约能力：30%
- 合规记录：20%
- 财务信用：15%
- 服务质量：15%
- 历史信用：20%

可在"配置"页面动态调整。

## 📦 构建产物

执行 `npm run build` 后，`dist/` 目录包含：

```
dist/
├── index.html          # 入口 HTML
├── assets/
│   ├── index-[hash].js      # 主应用代码
│   ├── element-plus-[hash].js  # Element Plus 库
│   ├── echarts-[hash].js    # ECharts 库
│   ├── vue-vendor-[hash].js # Vue 相关库
│   └── index-[hash].css     # 样式文件
```

## 🌐 浏览器兼容性

- Chrome 90+
- Edge 90+
- Firefox 90+
- Safari 14+

## 📝 更新说明

如需修改代码，请按以下流程操作：

1. 修改源代码（`src/` 目录）
2. 重新构建：`npm run build`
3. 重新启动预览：`npm run preview`
4. 刷新浏览器查看更新

## 🎨 主题切换

支持亮色/暗色主题切换，点击页面右下角的主题按钮即可切换，主题偏好会保存在本地存储。

## 📞 技术支持

如有问题，请检查：
1. 后端服务是否正常运行（端口 5001）
2. 网络请求是否成功（查看浏览器开发者工具 Network 标签）
3. 控制台是否有错误信息

---

**版本**：v1.0  
**框架**：Flask + Vue 3  
**构建时间**：2024