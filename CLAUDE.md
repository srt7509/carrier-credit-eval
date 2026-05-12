# CLAUDE.md — credit-web

延长物流信用评价系统（Vehicle CredEval v2.0）。以承运商所属**车辆**为评价对象，基于 Flask + Vue 3，支持五维信用评分、双模型监控、风险预警、区块链存证。

## Commit Rules
- 不要添加 `Co-Authored-By: Claude` 到 git commit 消息中

## Environment
- **Python 3.13.x** via pnpm/pixi (project root)
- Backend: `cd backend && pixi run python app.py` (port 5001)
- Frontend: `cd frontend && npm run dev` (port 5173, proxies /api → 5001)
- Seed data: `cd backend && pixi run python seed_all.py`

## Architecture
```
Browser → Nginx (:80) → /api/* → Gunicorn (:5001) → Flask → SQLite
                       → /*     → Vue SPA (static)
```
- Frontend Dockerfile copies pre-built `dist/` (no Node on server)
- Backend entrypoint auto-detects schema version, re-seeds if needed

## Key Files
| File | Purpose |
|------|---------|
| `backend/app.py` | Flask API (vehicles, carriers, scores, alerts, blockchain) |
| `backend/scoring/scoring_model.py` | DualModelScorer (champion v1.0 / challenger v2.0) |
| `backend/scoring/config.yaml` | Five-dimension weights & indicator formulas |
| `backend/database/models.py` | Vehicle, Carrier, Shipper, CreditScore dataclasses |
| `backend/database/init_db.py` | SQLite schema (10 tables) |
| `backend/data/mock_data.py` | Mock data generators (15 carriers, 100 vehicles) |
| `backend/seed_all.py` | One-shot DB init + scoring |
| `frontend/src/views/VehicleList.vue` | Vehicle list with category×grade default filter |
| `frontend/src/views/VehicleProfile.vue` | Vehicle credit profile (radar, trend, events) |
| `frontend/src/api/index.js` | Axios API layer with 30s memory cache |

## Data Model (v2.0)
- **Carrier** (承运商企业): carrier_id, name, cooperation_mode, fleet_size, qualification
- **Vehicle** (车辆, evaluation target): vehicle_id, carrier_id(FK), license_plate, driver_name, transport_category + 16 scoring fields
- **Shipper** (货主): unchanged
- **CreditScore**: entity_type = "vehicle" | "shipper", entity_id references vehicle_id or shipper_id
- Vehicle ID prefix "V", Carrier prefix "C", Shipper prefix "S"

## Scoring Dimensions (5-dim)
企业资质(0.17), 履约能力(0.28), 服务质量(0.22), 行为合规(0.16), 经营信用(0.17)

## Deployment
```bash
# One-click (builds frontend locally, uploads, deploys via Docker)
./deploy.sh <server-ip> root --reset-db

# Manual Docker
docker compose build && docker compose up -d
```
- Frontend is pre-built locally (dist/ included in tarball) to avoid Node OOM on low-spec servers
- `--reset-db` flag deletes persistent volume for schema migrations

## Code Conventions
- Backend: Python dataclasses for models, Flask blueprints-style single app.py
- Frontend: Vue 3 `<script setup>` with Composition API, Element Plus components
- New API endpoints follow `/api/<resource>` pattern
- Mock data functions in `data/mock_data.py`, DB I/O in same file
- Scoring formulas in `config.yaml`, evaluated by `SafeEvaluator` (AST-based)
