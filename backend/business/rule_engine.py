"""业务规则引擎"""
import json
from typing import Dict, Any, List, Optional

from database.db_manager import default_db


def get_all_rules() -> List[Dict]:
    """获取所有业务规则"""
    rows = default_db.fetchall(
        """SELECT rule_id, rule_type, rule_key, rule_value, description, is_active
           FROM business_rules ORDER BY rule_type, rule_key"""
    )
    return [
        {
            "rule_id": r[0], "rule_type": r[1], "rule_key": r[2],
            "rule_value": json.loads(r[3]) if r[3] else {},
            "description": r[4], "is_active": bool(r[5]),
        }
        for r in rows
    ]


def get_rules_by_type(rule_type: str) -> List[Dict]:
    rows = default_db.fetchall(
        """SELECT rule_id, rule_type, rule_key, rule_value, description, is_active
           FROM business_rules WHERE rule_type = ?""",
        (rule_type,),
    )
    return [
        {
            "rule_id": r[0], "rule_type": r[1], "rule_key": r[2],
            "rule_value": json.loads(r[3]) if r[3] else {},
            "description": r[4], "is_active": bool(r[5]),
        }
        for r in rows
    ]


def update_rule(rule_id: int, rule_value: Any, description: Optional[str] = None, is_active: Optional[bool] = None):
    """更新业务规则"""
    updates = ["rule_value = ?", "updated_at = datetime('now')"]
    params: list = [json.dumps(rule_value, ensure_ascii=False)]

    if description is not None:
        updates.append("description = ?")
        params.append(description)
    if is_active is not None:
        updates.append("is_active = ?")
        params.append(1 if is_active else 0)

    params.append(rule_id)
    default_db.execute(f"UPDATE business_rules SET {', '.join(updates)} WHERE rule_id = ?", tuple(params))


def evaluate_access(score_value: float, grade: str) -> Dict:
    """评估准入资格"""
    rules = get_rules_by_type("access_threshold")
    result = {"allowed": True, "reason": ""}
    for r in rules:
        val = r["rule_value"]
        if r["rule_key"] == "min_score" and score_value < val.get("min_score", 0):
            result = {"allowed": False, "reason": f"信用分 {score_value} 低于最低要求 {val['min_score']}"}
        if r["rule_key"] == "min_grade":
            grades = ["C", "B", "A", "AA", "AAA"]
            if grades.index(grade) < grades.index(val.get("value", "B")):
                result = {"allowed": False, "reason": f"信用等级 {grade} 低于最低要求 {val['value']}"}
    return result


def get_dispatch_weight(grade: str) -> float:
    """获取派单权重"""
    rules = get_rules_by_type("dispatch_priority")
    for r in rules:
        if r["rule_key"] == "weight":
            return r["rule_value"].get(grade, 1.0)
    return 1.0


def get_margin_rate(grade: str) -> float:
    """获取保证金费率"""
    rules = get_rules_by_type("margin_ratio")
    for r in rules:
        if r["rule_key"] == "rate":
            return r["rule_value"].get(grade, 0.10)
    return 0.10


def get_financial_service(grade: str, service_type: str) -> Any:
    """获取金融服务参数"""
    rules = get_rules_by_type("financial_service")
    for r in rules:
        if r["rule_key"] == service_type:
            return r["rule_value"].get(grade, 0)
    return 0


def get_veto_events() -> List[str]:
    """获取一票否决事件列表"""
    rules = get_rules_by_type("one_vote_veto")
    for r in rules:
        if r["rule_key"] == "events":
            return r["rule_value"]
    return []


def get_alert_thresholds() -> Dict:
    """获取预警阈值"""
    rules = get_rules_by_type("alert_threshold")
    result = {}
    for r in rules:
        result[r["rule_key"]] = r["rule_value"]
    return result
