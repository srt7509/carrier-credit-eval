import axios from "axios";

const API_BASE = "/api";

const api = axios.create({
  timeout: 5000,
});

// 内存缓存
const cache = new Map();
const CACHE_DURATION = 30000;

function isCacheExpired(timestamp) {
  return Date.now() - timestamp > CACHE_DURATION;
}

function cleanExpiredCache() {
  for (const [key, value] of cache.entries()) {
    if (isCacheExpired(value.timestamp)) cache.delete(key);
  }
}

async function cachedGet(url) {
  cleanExpiredCache();
  const cached = cache.get(url);
  if (cached && !isCacheExpired(cached.timestamp)) return cached.data;
  const res = await api.get(url);
  cache.set(url, { data: res.data, timestamp: Date.now() });
  return res.data;
}

// === 车辆（评价对象） ===
export async function getVehicles(params = {}) {
  const qs = new URLSearchParams(params).toString();
  return cachedGet(`${API_BASE}/vehicles${qs ? "?" + qs : ""}`);
}

export async function getVehicleDetail(id) {
  return cachedGet(`${API_BASE}/vehicles/${id}`);
}

// === 承运商企业 ===
export async function getCarrierCompanies() {
  return cachedGet(`${API_BASE}/carriers`);
}

// === 评分 ===
export async function getScores(type = null) {
  const url = type ? `${API_BASE}/scores?type=${type}` : `${API_BASE}/scores`;
  return cachedGet(url);
}

export async function getScoreDetail(entityId) {
  return cachedGet(`${API_BASE}/scores/${entityId}`);
}

export async function getScoreHistory(entityId, months = 12) {
  return cachedGet(`${API_BASE}/scores/${entityId}/history?months=${months}`);
}

export async function getScoreEvents(entityId) {
  return cachedGet(`${API_BASE}/scores/${entityId}/events`);
}

export async function getDimensionAverages() {
  return cachedGet(`${API_BASE}/scores/dimension-averages`);
}

export async function recalculateScores() {
  const res = await api.post(`${API_BASE}/scores/recalculate`);
  return res.data;
}

// === 预警 ===
export async function getAlerts(params = {}) {
  const qs = new URLSearchParams(params).toString();
  return cachedGet(`${API_BASE}/alerts${qs ? "?" + qs : ""}`);
}

export async function getAlertStats() {
  return cachedGet(`${API_BASE}/alerts/stats`);
}

export async function updateAlert(alertId, data) {
  const res = await api.put(`${API_BASE}/alerts/${alertId}`, data);
  return res.data;
}

// === 模型监控 ===
export async function getModelPerformance() {
  return cachedGet(`${API_BASE}/model/performance`);
}

export async function getModelRegistry() {
  return cachedGet(`${API_BASE}/model/registry`);
}

export async function getModelSwitchStatus() {
  return cachedGet(`${API_BASE}/model/switch-status`);
}

// === 业务规则 ===
export async function getBusinessRules(ruleType = null) {
  const url = ruleType ? `${API_BASE}/business-rules?rule_type=${ruleType}` : `${API_BASE}/business-rules`;
  return cachedGet(url);
}

export async function updateBusinessRule(ruleId, data) {
  const res = await api.put(`${API_BASE}/business-rules/${ruleId}`, data);
  return res.data;
}

export async function evaluateAccess(scoreValue, grade) {
  const res = await api.post(`${API_BASE}/business/evaluate-access`, { score_value: scoreValue, grade });
  return res.data;
}

// === 统计 ===
export async function getStats() {
  return cachedGet(`${API_BASE}/stats`);
}

// === 区块链 ===
export async function getBlockchainStatus() {
  return cachedGet(`${API_BASE}/blockchain/status`);
}

export async function getBlockchainRecords(type = null) {
  const url = type ? `${API_BASE}/blockchain/records?type=${type}` : `${API_BASE}/blockchain/records`;
  return cachedGet(url);
}

export async function verifyBlockchain(txHash) {
  const res = await api.post(`${API_BASE}/blockchain/verify`, { tx_hash: txHash });
  return res.data;
}

// === 签名 ===
export async function verifySignature(entityId, simulateTamper = false) {
  const res = await api.post(`${API_BASE}/signature/verify`, { entity_id: entityId, simulate_tamper: simulateTamper });
  return res.data;
}

// === 配置 ===
export async function getConfig() {
  return cachedGet(`${API_BASE}/config`);
}

export async function updateConfig(dimensions) {
  const res = await api.put(`${API_BASE}/config`, { dimensions });
  return res.data;
}

// === 导出 ===
export async function exportCsv(type = null) {
  const url = type ? `${API_BASE}/export?type=${type}` : `${API_BASE}/export`;
  const res = await api.get(url, { responseType: "blob" });
  return res.data;
}

export async function exportPdf(entityId) {
  return cachedGet(`${API_BASE}/export/pdf/${entityId}`);
}

export function clearAllCache() {
  cache.clear();
}
