"""Flask REST API - 承运商信用评价系统 v2.0"""
import json
import logging
import io
import os
from datetime import datetime
from pathlib import Path

from flask import Flask, jsonify, request, send_file, send_from_directory
from flask_cors import CORS
import yaml

from settings import CONFIG_PATH
from database.db_manager import default_db
from database.models import Carrier, Vehicle
from scoring.scoring_model import (
    get_all_scores_from_db, get_score_history, DualModelScorer,
    save_scores_to_db, calculate_psi,
)
from scoring.model_monitor import (
    calculate_ks, calculate_auc, calculate_spearman,
)
from security.signature import verify_signature
from security.blockchain import get_chain_status, verify_on_chain, get_transaction_details
from alerts.alert_manager import get_alerts, update_alert_status, get_alert_stats, create_alert
from business.rule_engine import (
    get_all_rules, get_rules_by_type, update_rule,
    evaluate_access, get_dispatch_weight, get_margin_rate, get_financial_service,
)

FRONTEND_DIST = (Path(__file__).parent / ".." / "frontend" / "dist").resolve()

app = Flask(__name__, static_folder=str(FRONTEND_DIST / "assets"), static_url_path="/assets")
CORS(app)

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
# 辅助函数
# ═══════════════════════════════════════════════════════════════

def _vehicle_row_to_dict(r) -> dict:
    """将 vehicles 表行转为字典"""
    return {
        "vehicle_id": r[0],
        "carrier_id": r[1] if len(r) > 1 and r[1] else "",
        "license_plate": r[2] if len(r) > 2 and r[2] else "",
        "driver_name": r[3] if len(r) > 3 and r[3] else "",
        "transport_category": r[4] if len(r) > 4 and r[4] else "普货",
        "total_orders": r[5] if len(r) > 5 else 0,
        "completed_orders": r[6] if len(r) > 6 else 0,
        "on_time_orders": r[7] if len(r) > 7 else 0,
        "complaint_count": r[8] if len(r) > 8 else 0,
        "accident_count": r[9] if len(r) > 9 else 0,
        "violation_count": r[10] if len(r) > 10 else 0,
        "license_valid": bool(r[11]) if len(r) > 11 else True,
        "on_time_payment_rate": r[12] if len(r) > 12 else 0.0,
        "overdue_amount": r[13] if len(r) > 13 else 0.0,
        "avg_customer_rating": r[14] if len(r) > 14 else 0.0,
        "damage_rate": r[15] if len(r) > 15 else 0.0,
        "cooperation_months": r[16] if len(r) > 16 else 0,
        "credit_trend_score": r[17] if len(r) > 17 else 80.0,
        "recent_3m_orders": r[18] if len(r) > 18 else 0,
        "risk_label": r[19] if len(r) > 19 else "正常",
    }


def _carrier_row_to_dict(r) -> dict:
    """将 carriers 表行转为字典（企业信息）"""
    return {
        "carrier_id": r[0],
        "name": r[1] if len(r) > 1 and r[1] else "",
        "unified_credit_code": r[2] if len(r) > 2 and r[2] else "",
        "cooperation_start_date": r[3] if len(r) > 3 and r[3] else "",
        "cooperation_mode": r[4] if len(r) > 4 and r[4] else "长期协议",
        "fleet_size": r[5] if len(r) > 5 else 0,
        "qualification": r[6] if len(r) > 6 else "全资质",
    }


# ═══════════════════════════════════════════════════════════════
# 车辆列表与筛选（评价对象）
# ═══════════════════════════════════════════════════════════════

@app.route("/api/vehicles", methods=["GET"])
def get_vehicles():
    """获取车辆列表（支持多条件筛选和排序）"""
    grade = request.args.get("grade")
    transport_category = request.args.get("transport_category")
    risk_label = request.args.get("risk_label")
    score_min = request.args.get("score_min", type=float)
    score_max = request.args.get("score_max", type=float)
    carrier_id = request.args.get("carrier_id")
    cooperation_mode = request.args.get("cooperation_mode")
    scale = request.args.get("scale")
    qualification = request.args.get("qualification")
    sort_by = request.args.get("sort_by", "vehicle_id")
    sort_order = request.args.get("sort_order", "asc")
    search = request.args.get("search", "")

    allowed_sort = {"vehicle_id", "license_plate", "driver_name", "score_value", "grade", "total_orders", "recent_3m_orders"}
    if sort_by not in allowed_sort:
        sort_by = "vehicle_id"
    if sort_order not in ("asc", "desc"):
        sort_order = "asc"

    query = """
        SELECT v.vehicle_id, v.carrier_id, v.license_plate, v.driver_name,
               v.transport_category, v.total_orders, v.completed_orders,
               v.on_time_orders, v.complaint_count, v.accident_count,
               v.violation_count, v.license_valid, v.on_time_payment_rate,
               v.overdue_amount, v.avg_customer_rating, v.damage_rate,
               v.cooperation_months, v.credit_trend_score,
               v.recent_3m_orders, v.risk_label,
               ca.name as carrier_name,
               COALESCE(s.score_value, 0) as score_value,
               COALESCE(s.grade, 'C') as grade
        FROM vehicles v
        LEFT JOIN credit_scores s ON v.vehicle_id = s.entity_id AND s.is_current = 1
        LEFT JOIN carriers ca ON v.carrier_id = ca.carrier_id
        WHERE 1=1
    """
    params = []

    if grade:
        query += " AND s.grade = ?"
        params.append(grade)
    if transport_category:
        query += " AND v.transport_category LIKE ?"
        params.append(f"%{transport_category}%")
    if risk_label:
        query += " AND v.risk_label = ?"
        params.append(risk_label)
    if score_min is not None:
        query += " AND s.score_value >= ?"
        params.append(score_min)
    if score_max is not None:
        query += " AND s.score_value <= ?"
        params.append(score_max)
    if carrier_id:
        query += " AND v.carrier_id = ?"
        params.append(carrier_id)
    if cooperation_mode:
        query += " AND ca.cooperation_mode = ?"
        params.append(cooperation_mode)
    if qualification:
        query += " AND ca.qualification = ?"
        params.append(qualification)
    if scale:
        if scale == "大型":
            query += " AND ca.fleet_size >= 100"
        elif scale == "中型":
            query += " AND ca.fleet_size >= 50 AND ca.fleet_size < 100"
        elif scale == "小型":
            query += " AND ca.fleet_size < 50"
    if search:
        query += " AND (v.license_plate LIKE ? OR v.driver_name LIKE ? OR v.vehicle_id LIKE ?)"
        params.extend([f"%{search}%", f"%{search}%", f"%{search}%"])

    query += f" ORDER BY {sort_by} {sort_order.upper()}"

    rows = default_db.fetchall(query, tuple(params))
    results = []
    for r in rows:
        d = _vehicle_row_to_dict(r)
        d["carrier_name"] = r[20] if len(r) > 20 else ""
        d["score_value"] = r[21] if len(r) > 21 else 0
        d["grade"] = r[22] if len(r) > 22 else "C"
        results.append(d)

    return jsonify(results)


@app.route("/api/carriers", methods=["GET"])
def get_carriers_enterprise():
    """获取承运商企业列表（用于下拉筛选）"""
    rows = default_db.fetchall(
        """SELECT carrier_id, name, unified_credit_code,
                  cooperation_start_date, cooperation_mode, fleet_size, qualification
           FROM carriers ORDER BY name"""
    )
    return jsonify([_carrier_row_to_dict(r) for r in rows])


@app.route("/api/vehicles/<vehicle_id>", methods=["GET"])
def get_vehicle_detail(vehicle_id):
    """获取车辆完整画像"""
    row = default_db.fetchone(
        """SELECT v.vehicle_id, v.carrier_id, v.license_plate, v.driver_name,
                  v.transport_category, v.total_orders, v.completed_orders,
                  v.on_time_orders, v.complaint_count, v.accident_count,
                  v.violation_count, v.license_valid, v.on_time_payment_rate,
                  v.overdue_amount, v.avg_customer_rating, v.damage_rate,
                  v.cooperation_months, v.credit_trend_score,
                  v.recent_3m_orders, v.risk_label,
                  ca.name as carrier_name, ca.cooperation_mode
           FROM vehicles v
           LEFT JOIN carriers ca ON v.carrier_id = ca.carrier_id
           WHERE v.vehicle_id = ?""",
        (vehicle_id,),
    )
    if not row:
        return jsonify({"error": "Not found"}), 404

    vehicle = _vehicle_row_to_dict(row)
    vehicle["carrier_name"] = row[20] if len(row) > 20 else ""
    vehicle["carrier_info"] = {
        "name": row[20] if len(row) > 20 else "",
        "cooperation_mode": row[21] if len(row) > 21 else "",
    }

    # 当前评分
    score_row = default_db.fetchone(
        """SELECT entity_id, entity_type, score_value, grade, dimension_scores,
                  risk_flags, signature, tx_hash, eval_time, model_version, eval_mode
           FROM credit_scores WHERE entity_id = ? AND is_current = 1""",
        (vehicle_id,),
    )
    if score_row:
        vehicle["current_score"] = {
            "score_value": score_row[2],
            "grade": score_row[3],
            "dimension_scores": json.loads(score_row[4]) if score_row[4] else {},
            "risk_flags": json.loads(score_row[5]) if score_row[5] else [],
            "signature": score_row[6],
            "tx_hash": score_row[7],
            "eval_time": score_row[8],
            "model_version": score_row[9] if len(score_row) > 9 else "",
            "eval_mode": score_row[10] if len(score_row) > 10 else "普运",
        }
    else:
        vehicle["current_score"] = None

    # 历史评分
    vehicle["score_history"] = get_score_history(vehicle_id, 12)

    # 评分事件
    event_rows = default_db.fetchall(
        """SELECT event_id, entity_id, event_type, event_desc, score_change, category, event_time
           FROM score_events WHERE entity_id = ? ORDER BY event_time DESC LIMIT 20""",
        (vehicle_id,),
    )
    vehicle["events"] = [
        {
            "event_id": er[0], "event_type": er[2], "event_desc": er[3],
            "score_change": er[4], "category": er[5], "event_time": er[6],
        }
        for er in event_rows
    ]

    # 上月评分（计算环比变动）
    prev_score = default_db.fetchone(
        """SELECT score_value FROM score_history WHERE entity_id = ?
           ORDER BY eval_time DESC LIMIT 1 OFFSET 1""",
        (vehicle_id,),
    )
    if prev_score and vehicle["current_score"]:
        vehicle["score_change"] = round(vehicle["current_score"]["score_value"] - prev_score[0], 2)
    else:
        vehicle["score_change"] = 0

    return jsonify(vehicle)


# ═══════════════════════════════════════════════════════════════
# 7.2.1 信用画像 - 评分历史、事件、维度对比
# ═══════════════════════════════════════════════════════════════

@app.route("/api/scores/<entity_id>/history", methods=["GET"])
def score_history(entity_id):
    """获取实体评分历史"""
    months = request.args.get("months", 12, type=int)
    history = get_score_history(entity_id, months)
    return jsonify(history)


@app.route("/api/scores/<entity_id>/events", methods=["GET"])
def score_events(entity_id):
    """获取实体评分事件"""
    rows = default_db.fetchall(
        """SELECT event_id, entity_id, event_type, event_desc, score_change, category, event_time
           FROM score_events WHERE entity_id = ? ORDER BY event_time DESC""",
        (entity_id,),
    )
    return jsonify([
        {
            "event_id": r[0], "event_type": r[2], "event_desc": r[3],
            "score_change": r[4], "category": r[5], "event_time": r[6],
        }
        for r in rows
    ])


@app.route("/api/scores/dimension-averages", methods=["GET"])
def dimension_averages():
    """获取各维度平台均值（用于雷达图对比）"""
    rows = default_db.fetchall(
        """SELECT dimension_scores FROM credit_scores WHERE is_current = 1 AND entity_type = 'vehicle'"""
    )
    if not rows:
        return jsonify({})

    sums = {}
    count = 0
    for r in rows:
        dims = json.loads(r[0]) if r[0] else {}
        for k, v in dims.items():
            sums[k] = sums.get(k, 0) + v
        count += 1

    return jsonify({k: round(v / count, 2) for k, v in sums.items()} if count > 0 else {})


# ═══════════════════════════════════════════════════════════════
# 原有评分接口（增强）
# ═══════════════════════════════════════════════════════════════

@app.route("/api/scores", methods=["GET"])
def get_scores():
    """获取所有评分列表"""
    entity_type = request.args.get("type")

    if entity_type:
        query = """SELECT entity_id, entity_type, score_value, grade,
                          dimension_scores, risk_flags, signature, tx_hash, eval_time, model_version, eval_mode
                   FROM credit_scores WHERE is_current = 1 AND entity_type = ?"""
        rows = default_db.fetchall(query, (entity_type,))
    else:
        query = """SELECT entity_id, entity_type, score_value, grade,
                          dimension_scores, risk_flags, signature, tx_hash, eval_time, model_version, eval_mode
                   FROM credit_scores WHERE is_current = 1"""
        rows = default_db.fetchall(query)

    results = []
    for row in rows:
        results.append({
            "entity_id": row[0],
            "entity_type": row[1],
            "score_value": round(row[2], 2),
            "grade": row[3],
            "dimension_scores": json.loads(row[4]) if row[4] else {},
            "risk_flags": json.loads(row[5]) if row[5] else [],
            "signature": row[6],
            "tx_hash": row[7],
            "eval_time": row[8],
            "model_version": row[9] if len(row) > 9 else "",
            "eval_mode": row[10] if len(row) > 10 else "普运",
        })
    return jsonify(results)


@app.route("/api/scores/<entity_id>", methods=["GET"])
def get_score_detail(entity_id):
    """获取单个评分详情"""
    row = default_db.fetchone(
        """SELECT entity_id, entity_type, score_value, grade, dimension_scores,
                  risk_flags, signature, tx_hash, eval_time, model_version, eval_mode
           FROM credit_scores WHERE entity_id = ? AND is_current = 1""",
        (entity_id,),
    )
    if not row:
        return jsonify({"error": "Not found"}), 404

    entity = _get_entity_info(entity_id, row[1])
    history = get_score_history(entity_id, 12)

    return jsonify({
        "entity_id": row[0],
        "entity_type": row[1],
        "score_value": round(row[2], 2),
        "grade": row[3],
        "dimension_scores": json.loads(row[4]) if row[4] else {},
        "risk_flags": json.loads(row[5]) if row[5] else [],
        "signature": row[6],
        "tx_hash": row[7],
        "eval_time": row[8],
        "model_version": row[9] if len(row) > 9 else "",
        "eval_mode": row[10] if len(row) > 10 else "普运",
        "entity": entity,
        "score_history": history,
    })


def _get_entity_info(entity_id, entity_type):
    """获取实体基本信息"""
    if entity_type == "vehicle":
        row = default_db.fetchone(
            """SELECT vehicle_id, carrier_id, license_plate, driver_name,
                      transport_category, total_orders, completed_orders,
                      on_time_orders, complaint_count, accident_count,
                      violation_count, license_valid, on_time_payment_rate,
                      overdue_amount, avg_customer_rating, damage_rate,
                      cooperation_months, credit_trend_score,
                      recent_3m_orders, risk_label
               FROM vehicles WHERE vehicle_id = ?""",
            (entity_id,),
        )
        if not row:
            return None
        return _vehicle_row_to_dict(row)
    elif entity_type == "carrier":
        row = default_db.fetchone(
            """SELECT carrier_id, name, unified_credit_code,
                      cooperation_start_date, cooperation_mode,
                      fleet_size, qualification
               FROM carriers WHERE carrier_id = ?""",
            (entity_id,),
        )
        if not row:
            return None
        return _carrier_row_to_dict(row)

    row = default_db.fetchone(
        """SELECT shipper_id, name, shipper_type, total_orders, completed_orders,
                  on_time_payment_rate, overdue_count, overdue_amount,
                  avg_order_value, complaint_count, cooperation_months
           FROM shippers WHERE shipper_id = ?""",
        (entity_id,),
    )
    if not row:
        return None
    return {
        "id": row[0], "name": row[1], "type": row[2],
        "total_orders": row[3], "completed_orders": row[4],
        "on_time_payment_rate": row[5], "overdue_count": row[6],
        "overdue_amount": row[7], "avg_order_value": row[8],
        "complaint_count": row[9], "cooperation_months": row[10],
    }


# ═══════════════════════════════════════════════════════════════
# 7.2.5 风险预警看板
# ═══════════════════════════════════════════════════════════════

@app.route("/api/alerts", methods=["GET"])
def alerts_list():
    """获取预警列表"""
    alert_type = request.args.get("alert_type")
    severity = request.args.get("severity")
    status = request.args.get("status")
    days = request.args.get("days", 90, type=int)
    alerts = get_alerts(alert_type, severity, status, days)
    return jsonify(alerts)


@app.route("/api/alerts/stats", methods=["GET"])
def alerts_stats():
    """获取预警统计"""
    return jsonify(get_alert_stats())


@app.route("/api/alerts/<int:alert_id>", methods=["PUT"])
def alerts_update(alert_id):
    """更新预警处理状态"""
    data = request.get_json()
    status = data.get("status", "处理中")
    handler_note = data.get("handler_note", "")
    update_alert_status(alert_id, status, handler_note)
    return jsonify({"success": True})


# ═══════════════════════════════════════════════════════════════
# 7.2.2 模型监控看板
# ═══════════════════════════════════════════════════════════════

@app.route("/api/model/performance", methods=["GET"])
def model_performance():
    """获取模型性能指标"""
    rows = default_db.fetchall(
        """SELECT period, model_version, ks, auc, psi, spearman, epv_satisfied, record_time
           FROM model_performance ORDER BY period ASC"""
    )
    result = {"champion": [], "challenger": []}
    for r in rows:
        entry = {
            "period": r[0], "model_version": r[1], "ks": r[2], "auc": r[3],
            "psi": r[4], "spearman": r[5], "epv_satisfied": bool(r[6]) if r[6] is not None else None,
            "record_time": r[7],
        }
        if r[1] == "champion":
            result["champion"].append(entry)
        else:
            result["challenger"].append(entry)
    return jsonify(result)


@app.route("/api/model/registry", methods=["GET"])
def model_registry():
    """获取模型注册信息"""
    rows = default_db.fetchall(
        """SELECT model_version, model_role, online_date, update_cycle, dimension_count, status, consecutive_pass_months
           FROM model_registry"""
    )
    return jsonify([
        {
            "model_version": r[0], "model_role": r[1], "online_date": r[2],
            "update_cycle": r[3], "dimension_count": r[4], "status": r[5],
            "consecutive_pass_months": r[6],
        }
        for r in rows
    ])


@app.route("/api/model/switch-status", methods=["GET"])
def model_switch_status():
    """获取模型切换判定状态"""
    config_row = default_db.fetchone("SELECT rule_value FROM business_rules WHERE rule_type = 'alert_threshold'")
    challenger = default_db.fetchone(
        "SELECT status, consecutive_pass_months FROM model_registry WHERE model_role = 'challenger'"
    )
    perf = default_db.fetchall(
        """SELECT period, model_version, ks, auc, psi, spearman, epv_satisfied
           FROM model_performance WHERE period = (SELECT MAX(period) FROM model_performance)
           ORDER BY model_version"""
    )

    with open(CONFIG_PATH, encoding="utf-8") as f:
        config = yaml.safe_load(f)

    conditions = config.get("switch_conditions", {})
    latest = {}
    for p in perf:
        latest[p[1]] = {"ks": p[2], "auc": p[3], "psi": p[4], "spearman": p[5]}

    champ = latest.get("champion", {})
    chall = latest.get("challenger", {})

    checks = {
        "epv_satisfied": chall.get("epv_satisfied") if "epv_satisfied" in latest.get("challenger", {}) else None,
        "ks_not_lower": chall.get("ks", 0) >= champ.get("ks", 0),
        "psi_ok": chall.get("psi", 1) < conditions.get("max_psi", 0.1),
        "spearman_ok": chall.get("spearman", 0) > conditions.get("min_spearman", 0.75),
        "consecutive_months": challenger[1] if challenger else 0,
        "required_months": conditions.get("min_consecutive_months", 6),
    }

    all_met = (
        checks["epv_satisfied"] and checks["ks_not_lower"] and
        checks["psi_ok"] and checks["spearman_ok"] and
        checks["consecutive_months"] >= checks["required_months"]
    )

    return jsonify({
        "conditions": checks,
        "all_met": all_met,
        "suggest_switch": all_met,
        "champion_status": default_db.fetchone("SELECT status FROM model_registry WHERE model_role = 'champion'"),
        "challenger_status": challenger[0] if challenger else "未知",
    })


# ═══════════════════════════════════════════════════════════════
# 7.2.4 业务决策联动配置
# ═══════════════════════════════════════════════════════════════

@app.route("/api/business-rules", methods=["GET"])
def business_rules():
    """获取所有业务规则"""
    rule_type = request.args.get("rule_type")
    if rule_type:
        return jsonify(get_rules_by_type(rule_type))
    return jsonify(get_all_rules())


@app.route("/api/business-rules/<int:rule_id>", methods=["PUT"])
def business_rules_update(rule_id):
    """更新业务规则"""
    data = request.get_json()
    rule_value = data.get("rule_value")
    description = data.get("description")
    is_active = data.get("is_active")
    if rule_value is None:
        return jsonify({"error": "rule_value required"}), 400
    update_rule(rule_id, rule_value, description, is_active)
    return jsonify({"success": True})


@app.route("/api/business/evaluate-access", methods=["POST"])
def business_evaluate_access():
    """评估承运商准入资格"""
    data = request.get_json()
    score_value = data.get("score_value", 0)
    grade = data.get("grade", "C")
    return jsonify(evaluate_access(score_value, grade))


# ═══════════════════════════════════════════════════════════════
# 统计
# ═══════════════════════════════════════════════════════════════

@app.route("/api/stats", methods=["GET"])
def get_stats():
    """获取系统统计数据"""
    vehicle_count = default_db.fetchone("SELECT COUNT(*) FROM vehicles")[0]
    carrier_count = default_db.fetchone("SELECT COUNT(*) FROM carriers")[0]
    shipper_count = default_db.fetchone("SELECT COUNT(*) FROM shippers")[0]
    score_count = default_db.fetchone("SELECT COUNT(*) FROM credit_scores WHERE is_current = 1")[0]
    record_count = default_db.fetchone("SELECT COUNT(*) FROM blockchain_records")[0]
    alert_unprocessed = default_db.fetchone("SELECT COUNT(*) FROM alert_records WHERE status = '未处理'")[0]

    # 等级分布
    grade_rows = default_db.fetchall(
        "SELECT grade, COUNT(*) FROM credit_scores WHERE is_current = 1 GROUP BY grade"
    )
    grade_distribution = {r[0]: r[1] for r in grade_rows}

    return jsonify({
        "vehicle_count": vehicle_count,
        "carrier_count": carrier_count,
        "shipper_count": shipper_count,
        "score_count": score_count,
        "record_count": record_count,
        "alert_unprocessed": alert_unprocessed,
        "grade_distribution": grade_distribution,
    })


# ═══════════════════════════════════════════════════════════════
# 评分重算（手动触发）
# ═══════════════════════════════════════════════════════════════

@app.route("/api/scores/recalculate", methods=["POST"])
def recalculate_scores():
    """手动触发全量评分重算"""
    from data.mock_data import get_vehicles_from_db
    vehicles = get_vehicles_from_db()
    if not vehicles:
        return jsonify({"error": "No vehicles found"}), 400

    dual = DualModelScorer()
    results = dual.calculate_all(vehicles)

    # 计算 PSI
    old_scores = get_all_scores_from_db()
    psi = calculate_psi(
        [type('S', (), {'score_value': s['score_value']}) for s in old_scores],
        results["champion"],
    )

    save_scores_to_db(results["champion"])

    return jsonify({
        "success": True,
        "vehicles_processed": len(vehicles),
        "psi": psi,
        "champion_mean": round(sum(s.score_value for s in results["champion"]) / len(results["champion"]), 2),
        "challenger_mean": round(sum(s.score_value for s in results["challenger"]) / len(results["challenger"]), 2),
    })


# ═══════════════════════════════════════════════════════════════
# 区块链 & 签名
# ═══════════════════════════════════════════════════════════════

@app.route("/api/blockchain/status", methods=["GET"])
def blockchain_status():
    try:
        status = get_chain_status()
        return jsonify(status)
    except Exception as e:
        return jsonify({"error": str(e), "connected": False}), 500


@app.route("/api/blockchain/records", methods=["GET"])
def blockchain_records():
    entity_type = request.args.get("type")
    query = """SELECT entity_id, score_hash, tx_hash, block_number, on_chain_time, verified
               FROM blockchain_records"""
    rows = default_db.fetchall(query)
    results = []
    for row in rows:
        if entity_type:
            prefix = "V" if entity_type == "vehicle" else ("S" if entity_type == "shipper" else "C")
            if not row[0].startswith(prefix):
                continue
        results.append({
            "entity_id": row[0], "score_hash": row[1], "tx_hash": row[2],
            "block_number": row[3], "on_chain_time": row[4], "verified": bool(row[5]),
        })
    return jsonify(results)


@app.route("/api/blockchain/verify", methods=["POST"])
def blockchain_verify():
    data = request.get_json()
    tx_hash = data.get("tx_hash")
    if not tx_hash:
        return jsonify({"error": "tx_hash required"}), 400
    row = default_db.fetchone(
        "SELECT entity_id, score_hash FROM blockchain_records WHERE tx_hash = ?", (tx_hash,)
    )
    if not row:
        return jsonify({"error": "Not found"}), 404
    try:
        result = verify_on_chain(tx_hash, row[1], row[0])
        details = get_transaction_details(tx_hash)
        return jsonify({"result": result, "details": details})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/signature/verify", methods=["POST"])
def signature_verify():
    data = request.get_json()
    entity_id = data.get("entity_id")
    simulate_tamper = data.get("simulate_tamper", False)
    if not entity_id:
        return jsonify({"error": "entity_id required"}), 400
    row = default_db.fetchone(
        """SELECT entity_id, entity_type, score_value, grade, signature
           FROM credit_scores WHERE entity_id = ? AND is_current = 1""",
        (entity_id,),
    )
    if not row:
        return jsonify({"error": "Not found"}), 404
    score_data = {"entity_id": row[0], "entity_type": row[1], "score_value": row[2], "grade": row[3]}
    stored_sig = row[4]
    if not stored_sig:
        return jsonify({"error": "No signature"}), 400
    if simulate_tamper:
        score_data["score_value"] += 10
    try:
        valid = verify_signature(score_data, stored_sig)
        return jsonify({"valid": valid, "simulated_tamper": simulate_tamper})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ═══════════════════════════════════════════════════════════════
# 评分配置
# ═══════════════════════════════════════════════════════════════

@app.route("/api/config", methods=["GET"])
def get_config():
    try:
        with open(CONFIG_PATH, encoding="utf-8") as f:
            config = yaml.safe_load(f)
        return jsonify(config)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/config", methods=["PUT"])
def update_config():
    data = request.get_json()
    try:
        with open(CONFIG_PATH, encoding="utf-8") as f:
            config = yaml.safe_load(f)
        if "dimensions" in data:
            for name, weight in data["dimensions"].items():
                if name in config["dimensions"]:
                    config["dimensions"][name]["weight"] = weight
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            yaml.dump(config, f, allow_unicode=True)
        return jsonify({"success": True, "config": config})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ═══════════════════════════════════════════════════════════════
# 导出
# ═══════════════════════════════════════════════════════════════

@app.route("/api/export", methods=["GET"])
def export_csv():
    """导出评分为 CSV"""
    entity_type = request.args.get("type")
    if entity_type:
        query = """SELECT entity_id, entity_type, score_value, grade, eval_time
                   FROM credit_scores WHERE is_current = 1 AND entity_type = ?"""
        rows = default_db.fetchall(query, (entity_type,))
    else:
        query = """SELECT entity_id, entity_type, score_value, grade, eval_time
                   FROM credit_scores WHERE is_current = 1"""
        rows = default_db.fetchall(query)

    csv_content = "ID,Type,Score,Grade,Time\n"
    for row in rows:
        if row[1] == "vehicle":
            type_name = "车辆"
        elif row[1] == "carrier":
            type_name = "承运商"
        else:
            type_name = "货主"
        csv_content += f"{row[0]},{type_name},{row[2]},{row[3]},{row[4]}\n"

    return send_file(
        io.BytesIO(csv_content.encode("utf-8")),
        mimetype="text/csv",
        as_attachment=True,
        download_name="credit_scores.csv",
    )


@app.route("/api/export/pdf/<entity_id>", methods=["GET"])
def export_pdf(entity_id):
    """导出车辆信用报告为 PDF 格式的 JSON（前端渲染）"""
    row = default_db.fetchone(
        """SELECT v.vehicle_id, v.carrier_id, v.license_plate, v.driver_name,
                  v.transport_category, ca.name as carrier_name
           FROM vehicles v
           LEFT JOIN carriers ca ON v.carrier_id = ca.carrier_id
           WHERE v.vehicle_id = ?""",
        (entity_id,),
    )
    if not row:
        return jsonify({"error": "Not found"}), 404

    score_row = default_db.fetchone(
        """SELECT score_value, grade, dimension_scores, eval_time
           FROM credit_scores WHERE entity_id = ? AND is_current = 1""",
        (entity_id,),
    )
    history = get_score_history(entity_id, 12)
    events = default_db.fetchall(
        "SELECT event_type, event_desc, score_change, event_time FROM score_events WHERE entity_id = ? ORDER BY event_time DESC LIMIT 10",
        (entity_id,),
    )

    report = {
        "vehicle": {
            "id": row[0], "carrier_id": row[1],
            "license_plate": row[2], "driver_name": row[3],
            "transport_category": row[4] if len(row) > 4 else "",
            "carrier_name": row[5] if len(row) > 5 else "",
        },
        "score": {
            "score_value": score_row[0], "grade": score_row[1],
            "dimension_scores": json.loads(score_row[2]) if score_row[2] else {},
            "eval_time": score_row[3],
        } if score_row else None,
        "history": history,
        "events": [
            {"event_type": e[0], "event_desc": e[1], "score_change": e[2], "event_time": e[3]}
            for e in events
        ],
        "generated_at": datetime.now().isoformat(),
    }
    return jsonify(report)


# ═══════════════════════════════════════════════════════════════
# 前端静态文件 & SPA 路由
# ═══════════════════════════════════════════════════════════════

@app.route("/")
def serve_index():
    return send_from_directory(str(FRONTEND_DIST), "index.html")


@app.route("/favicon.svg")
def serve_favicon():
    return send_from_directory(str(FRONTEND_DIST), "favicon.svg")


@app.route("/icons.svg")
def serve_icons():
    return send_from_directory(str(FRONTEND_DIST), "icons.svg")


@app.route("/<path:path>")
def serve_spa(path):
    """SPA catch-all: 非 api 路径返回 index.html"""
    if path.startswith("api/"):
        return jsonify({"error": "Not found"}), 404
    file_path = FRONTEND_DIST / path
    if file_path.exists() and file_path.is_file():
        return send_from_directory(str(FRONTEND_DIST), path)
    return send_from_directory(str(FRONTEND_DIST), "index.html")


# ═══════════════════════════════════════════════════════════════
# 后台初始化（Gunicorn / 直接启动均生效）
# ═══════════════════════════════════════════════════════════════

import threading


def _warmup():
    try:
        from security.blockchain import _init_blockchain
        _init_blockchain()
        logger.info("Blockchain warmed up")
    except ImportError:
        logger.warning("Blockchain disabled: web3/eth-tester not installed")
    except Exception as e:
        logger.warning("Blockchain warmup failed: %s", e)


threading.Thread(target=_warmup, daemon=True).start()

if __name__ == "__main__":
    app.run(debug=True, port=5001)
