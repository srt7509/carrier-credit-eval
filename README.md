# 延长物流信用评价系统（承运商信用评价 Demo）

基于 Flask + Vue 3 的承运商信用评价系统。支持信用画像、双模型评分、业务联动配置、风险预警、区块链存证等功能。

## 系统架构

```
┌──────────┐    ┌──────────────┐    ┌──────────────┐
│ 浏览器    │───▶│ Nginx (80)    │───▶│ Flask API     │
│          │    │ 静态文件 + 反向代理 │    │ :5001         │
└──────────┘    └──────────────┘    └───────┬───────┘
                                            │
                                    ┌───────▼───────┐
                                    │ SQLite         │
                                    │ credit_scores  │
                                    └───────────────┘
```

## 快速部署（Docker）

### 前提

- 服务器安装 Docker 和 docker-compose-plugin
- Python 3.13+（仅开发需要）

### 一键部署

```bash
# 从本地打包并上传部署
./deploy.sh <服务器IP>

# 示例
./deploy.sh 123.123.123.123 root
```

### 手动部署

```bash
# 在服务器上
cd /root
tar xzf credit-web.tar.gz
cd credit-web

# 构建并启动
docker compose build
docker compose up -d

# 查看状态
docker compose ps
docker compose logs -f
```

### 容器管理

| 命令 | 用途 |
|------|------|
| `docker compose ps` | 查看容器状态 |
| `docker compose logs backend` | 查看后端日志 |
| `docker compose logs frontend` | 查看前端日志 |
| `docker compose up -d` | 启动服务 |
| `docker compose down` | 停止服务 |
| `docker compose down -v` | 停止并清空数据卷 |
| `docker compose build --no-cache backend` | 强制重建后端 |

## 本地开发

### 后端

```bash
cd backend
pip install -r requirements.txt
python seed_all.py   # 建表 + 填充模拟数据
python app.py        # 启动 Flask :5001
```

### 前端

```bash
cd frontend
npm install
npm run dev          # 启动 Vite 开发服务器 :5173
```

## 功能模块

| 模块 | 路由 | 说明 |
|------|------|------|
| 承运商列表 | `/` | 多条件筛选、排序 |
| 信用画像 | `/profile/:id` | 六维雷达图、评分趋势、事件时间线 |
| 模型监控 | `/monitor` | 冠军/挑战者双模型性能指标 |
| 业务联动配置 | `/business` | 准入、派单、保证金、金融服务规则 |
| 风险预警 | `/alerts` | 预警列表、状态流转 |
| 区块链验证 | `/blockchain` | 存证记录查询、交易哈希链上验证 |
| 签名校验 | `/signature` | HMAC-SHA256 签名验证 |
| 评分配置 | `/config` | 六维度权重调整 |
| 系统状态 | `/status` | 统计数据、技术栈 |

## 技术栈

| 组件 | 技术 |
|------|------|
| 前端框架 | Vue 3 + Vue Router |
| UI 组件 | Element Plus |
| 可视化 | ECharts 6 |
| 后端框架 | Flask (Gunicorn) |
| 数据库 | SQLite |
| 部署容器 | Docker + docker-compose |
| Web 服务器 | Nginx |
| 区块链 | eth-tester (本地模拟) |

## 评分维度

| 维度 | 权重 |
|------|------|
| 企业资质 | 15% |
| 履约能力 | 25% |
| 服务质量 | 20% |
| 行为合规 | 15% |
| 经营信用 | 15% |
| 生态协同 | 10% |

---

**版本**：v2.0  
**作者**：中韩物流研究院
