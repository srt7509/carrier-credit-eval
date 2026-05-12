# 延长物流信用评价系统前端（Demo）

本项目是团队参加2026年中国国际大学生创新大赛（产业赛道）的作品。基于 Vue 3 + Element Plus 的车辆信用评价系统，以承运商所属车辆为评价对象，展示信用画像、模型监控、业务联动配置、风险预警、区块链存证等功能。

## 快速开始

### 开发模式

```bash
npm run dev
# 访问 http://localhost:5173
```

### 生产构建

```bash
npm run build
# 产物在 dist/ 目录，由 Flask 后端统一服务（端口 5001）
```

## 功能模块

### 1. 车辆管理（VehicleList）
- 默认筛选：运输品类 + 信用等级（组合展示，突出安全优先）
- 扩展筛选：合作模式、企业规模、资质完整性、承运商
- 多字段排序、点击跳转信用画像

### 2. 信用画像（VehicleProfile）
- 五维雷达图（企业资质、履约能力、服务质量、行为合规、经营信用）
- 平台均值对比
- 近12月评分趋势折线图
- 扣分/加分事件时间线
- 评分构成解释
- 导出信用报告

### 3. 模型监控（ModelMonitor）
- 冠军/挑战者双模型状态
- KS、AUC、PSI、Spearman 趋势图
- 切换判定仪表盘

### 4. 业务联动配置（BusinessConfig）
- 准入阈值、派单优先级、保证金比例、金融服务、一票否决、预警阈值
- 在线编辑，实时生效

### 5. 风险预警（AlertDashboard）
- 预警列表（评分下滑、一票否决、许可证过期等）
- 多维度筛选
- 处理状态流转

### 6. 签名校验（Signature）
- HMAC-SHA256 数字签名验证
- 篡改模拟检测

### 7. 区块链验证（Blockchain）
- 存证记录查看
- 交易哈希验证

### 8. 评分配置（Config）
- 五维度评分权重调整

### 9. 系统状态（Status）
- 统计数据、API 端点、技术栈

## 项目结构

```
frontend/
├── public/              # 静态资源
├── src/
│   ├── api/
│   │   └── index.js     # API 封装（含缓存）
│   ├── styles/
│   │   └── global.css   # 全局样式
│   ├── views/
│   │   ├── VehicleList.vue      # 车辆管理
│   │   ├── VehicleProfile.vue    # 信用画像
│   │   ├── ModelMonitor.vue     # 模型监控
│   │   ├── BusinessConfig.vue   # 业务联动配置
│   │   ├── AlertDashboard.vue   # 风险预警
│   │   ├── Signature.vue        # 签名校验
│   │   ├── Blockchain.vue       # 区块链验证
│   │   ├── Config.vue           # 评分配置
│   │   └── Status.vue           # 系统状态
│   ├── App.vue           # 主应用
│   ├── main.js           # 入口
│   └── router.js         # 路由
├── index.html
├── package.json
├── vite.config.js
└── README.md
```

## 技术栈

- **Vue 3.5** — 前端框架
- **Vue Router 4** — 路由管理
- **Element Plus 2** — UI 组件库
- **ECharts 6** — 数据可视化
- **Axios** — HTTP 请求
- **Vite 8** — 构建工具

## 评分维度权重

五维度评价体系（与后端 config.yaml 一致）：

| 维度 | 权重 |
|------|------|
| 企业资质 | 17% |
| 履约能力 | 28% |
| 服务质量 | 22% |
| 行为合规 | 16% |
| 经营信用 | 17% |

## 部署说明

生产环境由 Flask 后端统一服务，前后端一体化部署：

1. 构建前端：`npm run build`
2. 启动后端：`cd ../backend && pixi run python app.py`
3. 访问 `http://localhost:5001`

---

**版本**：v2.0  
**作者**：中韩物流研究院  
**构建时间**：2026
