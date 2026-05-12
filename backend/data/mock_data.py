"""模拟数据生成模块"""
import logging
import random
from datetime import datetime, timedelta
from typing import List

from database.db_manager import default_db
from database.models import Carrier, Vehicle, Shipper, ScoreEvent, AlertRecord, ModelPerformance, ModelRegistry, BusinessRule

logger = logging.getLogger(__name__)

# 承运商企业名称池
CARRIER_NAMES = [
    "顺达物流", "安达运输", "恒通快运", "远航货运", "中铁集运",
    "通达供应链", "鑫驰物流", "华运通", "捷安达", "万联运输",
    "腾飞货运", "九州物流", "长运通达", "汇通快线", "信达运输",
]

# 司机姓名池
DRIVER_SURNAMES = ["张", "李", "王", "刘", "陈", "杨", "赵", "黄", "周", "吴",
                   "徐", "孙", "马", "朱", "胡", "郭", "何", "高", "林", "罗"]
DRIVER_GIVEN = ["伟", "强", "磊", "军", "勇", "明", "华", "斌", "涛", "鹏",
                "建", "国", "志", "文", "峰", "刚", "辉", "杰", "亮", "飞",
                "海", "波", "超", "龙", "洋"]

# 牌照前缀池
PLATE_PREFIXES = [
    ("陕A", "西安"), ("陕K", "榆林"), ("陕J", "延安"),
    ("蒙A", "呼和浩特"), ("蒙K", "鄂尔多斯"),
    ("鲁A", "济南"), ("鲁E", "东营"),
    ("晋A", "太原"), ("晋H", "忻州"),
    ("甘A", "兰州"), ("甘M", "庆阳"),
    ("宁A", "银川"), ("豫A", "郑州"),
]


def generate_mock_shippers(n: int = 30) -> List[Shipper]:
    shippers = []
    shipper_types = ["企业", "个人"]
    for i in range(n):
        total_orders = random.randint(20, 200)
        completed = random.randint(int(total_orders * 0.8), total_orders)
        payment_rate = random.uniform(0.6, 1.0)
        overdue_count = random.randint(0, 5) if payment_rate < 0.9 else 0
        overdue_amount = random.uniform(0, 30000) if overdue_count > 0 else 0
        shippers.append(Shipper(
            shipper_id=f"S{i+1:03d}",
            name=f"货主{i+1}",
            shipper_type=random.choice(shipper_types),
            total_orders=total_orders,
            completed_orders=completed,
            on_time_payment_rate=payment_rate,
            overdue_count=overdue_count,
            overdue_amount=overdue_amount,
            avg_order_value=random.uniform(1000, 50000),
            complaint_count=random.randint(0, 3),
            cooperation_months=random.randint(1, 36),
            credit_trend_score=random.uniform(60, 100),
        ))
    return shippers


def save_shippers_to_db(shippers: List[Shipper]):
    with default_db.connect() as conn:
        for s in shippers:
            conn.execute(
                """INSERT OR REPLACE INTO shippers (
                    shipper_id, name, shipper_type, total_orders, completed_orders,
                    on_time_payment_rate, overdue_count, overdue_amount,
                    avg_order_value, complaint_count, cooperation_months, credit_trend_score
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (s.shipper_id, s.name, s.shipper_type, s.total_orders, s.completed_orders,
                 s.on_time_payment_rate, s.overdue_count, s.overdue_amount,
                 s.avg_order_value, s.complaint_count, s.cooperation_months,
                 s.credit_trend_score),
            )
    logger.info("已保存 %d 条货主数据", len(shippers))


def get_shippers_from_db() -> List[Shipper]:
    rows = default_db.fetchall(
        """SELECT shipper_id, name, shipper_type, total_orders, completed_orders,
                  on_time_payment_rate, overdue_count, overdue_amount,
                  avg_order_value, complaint_count, cooperation_months, credit_trend_score
           FROM shippers"""
    )
    return [
        Shipper(shipper_id=r[0], name=r[1], shipper_type=r[2], total_orders=r[3],
                completed_orders=r[4], on_time_payment_rate=r[5], overdue_count=r[6],
                overdue_amount=r[7], avg_order_value=r[8], complaint_count=r[9],
                cooperation_months=r[10], credit_trend_score=r[11])
        for r in rows
    ]


# ═══════════════════════════════════════════════════════════════
# 承运商企业（不再作为评价对象）
# ═══════════════════════════════════════════════════════════════

def generate_mock_carriers(n: int = 15) -> List[Carrier]:
    """生成模拟承运商企业数据"""
    carriers = []
    cooperation_modes = ["长期协议", "长期协议", "长期协议", "临时竞价"]  # 75% 长期协议
    qualifications = ["全资质", "全资质", "单一-普货", "单一-危化品"]

    for i in range(n):
        cooperation_months = random.randint(6, 72)
        start_year = datetime.now().year - cooperation_months // 12
        start_month = 12 - (cooperation_months % 12)
        if start_month <= 0:
            start_year -= 1
            start_month += 12
        cooperation_start = f"{start_year}-{start_month:02d}"

        fleet_size = random.randint(2, 150)

        carriers.append(Carrier(
            carrier_id=f"C{i+1:03d}",
            name=CARRIER_NAMES[i] if i < len(CARRIER_NAMES) else f"承运商{i+1}",
            unified_credit_code=f"91310115MA1K{i+1:04d}X8",
            cooperation_start_date=cooperation_start,
            cooperation_mode=random.choice(cooperation_modes),
            fleet_size=fleet_size,
            qualification=random.choice(qualifications),
        ))

    return carriers


def save_carriers_to_db(carriers: List[Carrier]):
    with default_db.connect() as conn:
        for c in carriers:
            conn.execute(
                """INSERT OR REPLACE INTO carriers (
                    carrier_id, name, unified_credit_code,
                    cooperation_start_date, cooperation_mode, fleet_size, qualification
                ) VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (c.carrier_id, c.name, c.unified_credit_code,
                 c.cooperation_start_date, c.cooperation_mode, c.fleet_size, c.qualification),
            )
    logger.info("已保存 %d 条承运商企业数据", len(carriers))


def get_carriers_from_db() -> List[Carrier]:
    rows = default_db.fetchall(
        """SELECT carrier_id, name, unified_credit_code,
                  cooperation_start_date, cooperation_mode, fleet_size, qualification
           FROM carriers"""
    )
    return [
        Carrier(carrier_id=r[0], name=r[1], unified_credit_code=r[2] if len(r) > 2 and r[2] else "",
                cooperation_start_date=r[3] if len(r) > 3 and r[3] else "",
                cooperation_mode=r[4] if len(r) > 4 and r[4] else "长期协议",
                fleet_size=r[5] if len(r) > 5 else 0,
                qualification=r[6] if len(r) > 6 else "全资质")
        for r in rows
    ]


# ═══════════════════════════════════════════════════════════════
# 车辆（评价对象）
# ═══════════════════════════════════════════════════════════════

def generate_mock_vehicles(carrier_ids: List[str], n: int = 100) -> List[Vehicle]:
    """为给定承运商生成模拟车辆数据"""
    vehicles = []
    transport_categories = [
        "普货", "普货", "普货",
        "危化品-易燃液体", "危化品-气体", "危化品-剧毒品",
    ]
    risk_labels = ["正常", "正常", "正常", "正常", "关注", "预警"]

    for i in range(n):
        carrier_id = random.choice(carrier_ids)
        plate_prefix, _ = random.choice(PLATE_PREFIXES)
        license_plate = f"{plate_prefix}{random.randint(10000, 99999)}"

        surname = random.choice(DRIVER_SURNAMES)
        given = random.choice(DRIVER_GIVEN) + (random.choice(DRIVER_GIVEN) if random.random() > 0.5 else "")
        driver_name = surname + given

        total_orders = random.randint(50, 500)
        completed = random.randint(int(total_orders * 0.7), total_orders)
        on_time = random.randint(int(completed * 0.6), completed)
        recent_3m = random.randint(5, 60)

        accident_count = random.randint(0, 5)
        violation_count = random.randint(0, 10) if accident_count > 0 else random.randint(0, 3)
        license_valid = random.choice([True, True, True, True, False])

        payment_rate = random.uniform(0.5, 1.0)
        overdue_amount = random.uniform(0, 50000) if payment_rate < 0.8 else 0
        cooperation_months = random.randint(1, 48)

        complaint_count = random.randint(0, int(completed * 0.05))
        if not license_valid or accident_count >= 3:
            risk_label = "预警"
        elif complaint_count > 5:
            risk_label = "关注"
        else:
            risk_label = random.choice(risk_labels)

        vehicles.append(Vehicle(
            vehicle_id=f"V{i+1:03d}",
            carrier_id=carrier_id,
            license_plate=license_plate,
            driver_name=driver_name,
            transport_category=random.choice(transport_categories),
            total_orders=total_orders,
            completed_orders=completed,
            on_time_orders=on_time,
            complaint_count=complaint_count,
            accident_count=accident_count,
            violation_count=violation_count,
            license_valid=license_valid,
            on_time_payment_rate=payment_rate,
            overdue_amount=overdue_amount,
            avg_customer_rating=random.uniform(3.0, 5.0),
            damage_rate=random.uniform(0, 0.05),
            cooperation_months=cooperation_months,
            credit_trend_score=random.uniform(60, 100),
            recent_3m_orders=recent_3m,
            risk_label=risk_label,
        ))

    return vehicles


def save_vehicles_to_db(vehicles: List[Vehicle]):
    with default_db.connect() as conn:
        for v in vehicles:
            conn.execute(
                """INSERT OR REPLACE INTO vehicles (
                    vehicle_id, carrier_id, license_plate, driver_name,
                    transport_category, total_orders, completed_orders, on_time_orders,
                    complaint_count, accident_count, violation_count,
                    license_valid, on_time_payment_rate, overdue_amount,
                    avg_customer_rating, damage_rate, cooperation_months,
                    credit_trend_score, recent_3m_orders, risk_label
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (v.vehicle_id, v.carrier_id, v.license_plate, v.driver_name,
                 v.transport_category, v.total_orders, v.completed_orders, v.on_time_orders,
                 v.complaint_count, v.accident_count, v.violation_count,
                 v.license_valid, v.on_time_payment_rate, v.overdue_amount,
                 v.avg_customer_rating, v.damage_rate, v.cooperation_months,
                 v.credit_trend_score, v.recent_3m_orders, v.risk_label),
            )
    logger.info("已保存 %d 条车辆数据", len(vehicles))


def get_vehicles_from_db() -> List[Vehicle]:
    rows = default_db.fetchall(
        """SELECT vehicle_id, carrier_id, license_plate, driver_name,
                  transport_category, total_orders, completed_orders, on_time_orders,
                  complaint_count, accident_count, violation_count,
                  license_valid, on_time_payment_rate, overdue_amount,
                  avg_customer_rating, damage_rate, cooperation_months,
                  credit_trend_score, recent_3m_orders, risk_label
           FROM vehicles"""
    )
    result = []
    for r in rows:
        result.append(Vehicle(
            vehicle_id=r[0], carrier_id=r[1],
            license_plate=r[2] if len(r) > 2 and r[2] else "",
            driver_name=r[3] if len(r) > 3 and r[3] else "",
            transport_category=r[4] if len(r) > 4 and r[4] else "普货",
            total_orders=r[5] if len(r) > 5 else 0,
            completed_orders=r[6] if len(r) > 6 else 0,
            on_time_orders=r[7] if len(r) > 7 else 0,
            complaint_count=r[8] if len(r) > 8 else 0,
            accident_count=r[9] if len(r) > 9 else 0,
            violation_count=r[10] if len(r) > 10 else 0,
            license_valid=bool(r[11]) if len(r) > 11 else True,
            on_time_payment_rate=r[12] if len(r) > 12 else 0.0,
            overdue_amount=r[13] if len(r) > 13 else 0.0,
            avg_customer_rating=r[14] if len(r) > 14 else 0.0,
            damage_rate=r[15] if len(r) > 15 else 0.0,
            cooperation_months=r[16] if len(r) > 16 else 0,
            credit_trend_score=r[17] if len(r) > 17 else 80.0,
            recent_3m_orders=r[18] if len(r) > 18 else 0,
            risk_label=r[19] if len(r) > 19 else "正常",
        ))
    return result


# ═══════════════════════════════════════════════════════════════
# 评分事件、预警记录、模型性能、模型注册、业务规则
# ═══════════════════════════════════════════════════════════════

def generate_mock_score_events(entity_ids: List[str]) -> List[ScoreEvent]:
    """生成模拟评分事件"""
    events = []
    event_templates = [
        ("deduction", "扣分", "货损超标: 货损率超过5%阈值", -5),
        ("deduction", "扣分", "客户投诉: 服务态度差", -3),
        ("deduction", "扣分", "配送延误: 超时12小时", -2),
        ("addition", "加分", "连续三月无投诉奖励", 5),
        ("addition", "加分", "季度优秀车辆", 8),
        ("addition", "加分", "客户表扬: 紧急任务出色完成", 3),
        ("one_vote_veto", "一票否决", "许可证过期", -50),
        ("one_vote_veto", "一票否决", "重大安全事故: 危化品泄漏", -60),
    ]

    now = datetime.now()
    for _ in range(80):
        template = random.choice(event_templates)
        entity_id = random.choice(entity_ids)
        event_time = now - timedelta(days=random.randint(0, 365))
        events.append(ScoreEvent(
            entity_id=entity_id,
            event_type=template[0],
            event_desc=template[2],
            score_change=template[3],
            event_time=event_time,
            category=template[1],
        ))
    return events


def save_score_events_to_db(events: List[ScoreEvent]):
    with default_db.connect() as conn:
        for e in events:
            conn.execute(
                """INSERT INTO score_events (entity_id, event_type, event_desc, score_change, category, event_time)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (e.entity_id, e.event_type, e.event_desc, e.score_change, e.category, e.event_time.isoformat()),
            )
    logger.info("已保存 %d 条评分事件", len(events))


def generate_mock_alerts(entity_ids: List[str], entity_names: List[str]) -> List[AlertRecord]:
    """生成模拟预警记录"""
    alerts = []
    alert_types = ["评分快速下滑", "一票否决触发", "许可证即将过期", "连续多单投诉"]
    severities = ["高", "中", "低"]
    statuses = ["未处理", "未处理", "处理中", "已处理"]

    now = datetime.now()
    for _ in range(30):
        idx = random.randint(0, len(entity_ids) - 1)
        alert_type = random.choice(alert_types)
        severity = "高" if alert_type in ("一票否决触发", "许可证即将过期") else random.choice(severities)
        alerts.append(AlertRecord(
            entity_id=entity_ids[idx],
            entity_name=entity_names[idx] if idx < len(entity_names) else f"车辆{idx+1}",
            alert_type=alert_type,
            severity=severity,
            trigger_time=now - timedelta(days=random.randint(0, 30)),
            current_score=random.uniform(40, 85),
            status=random.choice(statuses),
            handler_note="已通知运营团队" if random.random() > 0.5 else "",
        ))
    return alerts


def save_alerts_to_db(alerts: List[AlertRecord]):
    with default_db.connect() as conn:
        for a in alerts:
            conn.execute(
                """INSERT INTO alert_records (entity_id, entity_name, alert_type, severity, trigger_time, current_score, status, handler_note)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (a.entity_id, a.entity_name, a.alert_type, a.severity,
                 a.trigger_time.isoformat(), a.current_score, a.status, a.handler_note),
            )
    logger.info("已保存 %d 条预警记录", len(alerts))


def generate_mock_model_performance() -> List[ModelPerformance]:
    """生成模拟模型性能指标（近12个月）"""
    records = []
    now = datetime.now()
    for i in range(12, 0, -1):
        period_date = now - timedelta(days=30 * i)
        period = period_date.strftime("%Y-%m")
        records.append(ModelPerformance(
            period=period, model_version="champion",
            ks=random.uniform(0.35, 0.52),
            auc=random.uniform(0.72, 0.85),
            psi=random.uniform(0.02, 0.08),
            record_time=period_date,
        ))
        spearman = random.uniform(0.70, 0.88)
        records.append(ModelPerformance(
            period=period, model_version="challenger",
            ks=random.uniform(0.36, 0.54),
            auc=random.uniform(0.73, 0.87),
            psi=random.uniform(0.03, 0.09),
            spearman=spearman,
            epv_satisfied=spearman > 0.75,
            record_time=period_date,
        ))
    return records


def save_model_performance_to_db(records: List[ModelPerformance]):
    with default_db.connect() as conn:
        for r in records:
            conn.execute(
                """INSERT INTO model_performance (period, model_version, ks, auc, psi, spearman, epv_satisfied, record_time)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (r.period, r.model_version, r.ks, r.auc, r.psi, r.spearman, r.epv_satisfied, r.record_time.isoformat()),
            )
    logger.info("已保存 %d 条模型性能记录", len(records))


def generate_mock_model_registry() -> List[ModelRegistry]:
    """生成模拟模型注册信息"""
    return [
        ModelRegistry(
            model_version="v1.0", model_role="champion",
            online_date="2025-06-01", update_cycle="月度",
            dimension_count=5, status="运行中",
            consecutive_pass_months=0,
        ),
        ModelRegistry(
            model_version="v2.0", model_role="challenger",
            online_date="2025-12-01", update_cycle="月度",
            dimension_count=5, status="影子运行中",
            consecutive_pass_months=4,
        ),
    ]


def save_model_registry_to_db(registry: List[ModelRegistry]):
    with default_db.connect() as conn:
        for m in registry:
            conn.execute(
                """INSERT OR REPLACE INTO model_registry (model_version, model_role, online_date, update_cycle, dimension_count, status, consecutive_pass_months)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (m.model_version, m.model_role, m.online_date, m.update_cycle, m.dimension_count, m.status, m.consecutive_pass_months),
            )
    logger.info("已保存 %d 条模型注册信息", len(registry))


def generate_default_business_rules() -> List[BusinessRule]:
    """生成默认业务联动规则"""
    import json
    rules = [
        BusinessRule(rule_type="access_threshold", rule_key="min_score",
                     rule_value=json.dumps({"min_score": 60, "min_grade": "B", "auto_reject": True}),
                     description="准入阈值: 低于60分自动拒绝"),
        BusinessRule(rule_type="access_threshold", rule_key="min_grade",
                     rule_value=json.dumps({"value": "B"}),
                     description="入驻最低等级要求"),
        BusinessRule(rule_type="dispatch_priority", rule_key="weight",
                     rule_value=json.dumps({"AAA": 1.5, "AA": 1.3, "A": 1.1, "B": 1.0, "C": 0.5}),
                     description="派单权重系数"),
        BusinessRule(rule_type="margin_ratio", rule_key="rate",
                     rule_value=json.dumps({"AAA": 0.03, "AA": 0.05, "A": 0.08, "B": 0.10, "C": 0.15}),
                     description="保证金费率"),
        BusinessRule(rule_type="financial_service", rule_key="prepay_limit",
                     rule_value=json.dumps({"AAA": 500000, "AA": 300000, "A": 200000, "B": 100000, "C": 0}),
                     description="运费预付额度上限"),
        BusinessRule(rule_type="financial_service", rule_key="loan_rate",
                     rule_value=json.dumps({"AAA": 0.04, "AA": 0.05, "A": 0.06, "B": 0.08, "C": 0.12}),
                     description="贷款利率档位"),
        BusinessRule(rule_type="one_vote_veto", rule_key="events",
                     rule_value=json.dumps(["许可证过期", "重大安全事故", "危化品泄漏", "列入行业黑名单"]),
                     description="一票否决事件类型"),
        BusinessRule(rule_type="alert_threshold", rule_key="score_drop",
                     rule_value=json.dumps({"single_month_drop": 50, "consecutive_complaints": 3}),
                     description="预警阈值: 单月降幅>50分 或 连续3单投诉"),
    ]
    return rules


def save_business_rules_to_db(rules: List[BusinessRule]):
    with default_db.connect() as conn:
        for r in rules:
            conn.execute(
                """INSERT INTO business_rules (rule_type, rule_key, rule_value, description, is_active)
                   VALUES (?, ?, ?, ?, ?)""",
                (r.rule_type, r.rule_key, r.rule_value, r.description, r.is_active),
            )
    logger.info("已保存 %d 条业务规则", len(rules))


def seed_score_history(vehicles: List[Vehicle]):
    """为每辆车生成近12个月的历史评分快照"""
    import json
    now = datetime.now()
    with default_db.connect() as conn:
        for v in vehicles:
            base_score = random.uniform(50, 95)
            for m in range(12, 0, -1):
                period_date = now - timedelta(days=30 * m)
                period = period_date.strftime("%Y-%m")
                noise = random.uniform(-8, 8)
                score = max(10, min(100, base_score + noise))
                base_score = score
                dims = {dim: round(score * w, 2) for dim, w in [
                    ("企业资质", 0.17), ("履约能力", 0.28), ("服务质量", 0.22),
                    ("行为合规", 0.16), ("经营信用", 0.17),
                ]}
                grade = "C"
                for g, t in [("AAA", 90), ("AA", 80), ("A", 70), ("B", 60), ("C", 0)]:
                    if score >= t:
                        grade = g
                        break
                conn.execute(
                    """INSERT INTO score_history (entity_id, entity_type, score_value, grade, dimension_scores, eval_period, eval_time, model_version)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (v.vehicle_id, "vehicle", round(score, 2), grade, json.dumps(dims), period, period_date.isoformat(), "v1.0"),
                )
    logger.info("已为 %d 辆车生成12个月历史评分", len(vehicles))


def generate_mock_blockchain_records(entity_ids: list[str]) -> list[dict]:
    """生成模拟区块链存证记录"""
    import hashlib
    records = []
    now = datetime.now()
    for eid in entity_ids:
        score_hash = hashlib.sha256(f"{eid}:{random.randint(50,100)}".encode()).hexdigest()[:16]
        tx_hash = "0x" + hashlib.sha256(f"{eid}:{now.timestamp()}".encode()).hexdigest()
        records.append({
            "entity_id": eid,
            "score_hash": score_hash,
            "tx_hash": tx_hash,
            "block_number": random.randint(100000, 999999),
            "on_chain_time": (now - timedelta(days=random.randint(0, 30))).isoformat(),
        })
    return records


def save_blockchain_records_to_db(records: list[dict]):
    with default_db.connect() as conn:
        for r in records:
            conn.execute(
                """INSERT INTO blockchain_records (entity_id, score_hash, tx_hash, block_number, on_chain_time, verified)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (r["entity_id"], r["score_hash"], r["tx_hash"], r["block_number"], r["on_chain_time"], 1),
            )
    logger.info("已保存 %d 条区块链存证记录", len(records))


if __name__ == "__main__":
    from database.init_db import init_database
    init_database()
    carriers = generate_mock_carriers(15)
    save_carriers_to_db(carriers)
    logger.info("生成 %d 条模拟承运商企业数据", len(carriers))
    vehicle_ids = [c.carrier_id for c in carriers]
    vehicles = generate_mock_vehicles(vehicle_ids, 100)
    save_vehicles_to_db(vehicles)
    logger.info("生成 %d 条模拟车辆数据", len(vehicles))
