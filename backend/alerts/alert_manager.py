"""预警管理模块"""
import logging
from typing import List, Optional

from database.db_manager import default_db
from database.models import AlertRecord

logger = logging.getLogger(__name__)


def create_alert(
    entity_id: str,
    entity_name: str,
    alert_type: str,
    severity: str,
    current_score: float = 0.0,
) -> int:
    """创建预警记录"""
    with default_db.connect() as conn:
        cursor = conn.execute(
            """INSERT INTO alert_records (entity_id, entity_name, alert_type, severity, trigger_time, current_score, status)
               VALUES (?, ?, ?, ?, datetime('now'), ?, '未处理')""",
            (entity_id, entity_name, alert_type, severity, current_score),
        )
        return cursor.lastrowid


def get_alerts(
    alert_type: Optional[str] = None,
    severity: Optional[str] = None,
    status: Optional[str] = None,
    days: int = 90,
) -> List[dict]:
    """查询预警记录"""
    query = """SELECT a.alert_id, a.entity_id, a.entity_name, a.alert_type, a.severity,
                      a.trigger_time, a.current_score, a.status, a.handler_note
               FROM alert_records a WHERE a.trigger_time >= datetime('now', ?)"""
    params = [f"-{days} days"]

    if alert_type:
        query += " AND a.alert_type = ?"
        params.append(alert_type)
    if severity:
        query += " AND a.severity = ?"
        params.append(severity)
    if status:
        query += " AND a.status = ?"
        params.append(status)

    query += " ORDER BY a.trigger_time DESC"

    rows = default_db.fetchall(query, tuple(params))
    return [
        {
            "alert_id": r[0], "entity_id": r[1], "entity_name": r[2],
            "alert_type": r[3], "severity": r[4], "trigger_time": r[5],
            "current_score": r[6], "status": r[7], "handler_note": r[8],
        }
        for r in rows
    ]


def update_alert_status(alert_id: int, status: str, handler_note: str = ""):
    """更新预警处理状态"""
    default_db.execute(
        """UPDATE alert_records SET status = ?, handler_note = ? WHERE alert_id = ?""",
        (status, handler_note, alert_id),
    )


def get_alert_stats() -> dict:
    """获取预警统计"""
    total = default_db.fetchone("SELECT COUNT(*) FROM alert_records")[0]
    unprocessed = default_db.fetchone("SELECT COUNT(*) FROM alert_records WHERE status = '未处理'")[0]
    high = default_db.fetchone("SELECT COUNT(*) FROM alert_records WHERE severity = '高' AND status = '未处理'")[0]
    return {"total": total, "unprocessed": unprocessed, "high_severity": high}


def check_score_drop(entity_id: str, entity_name: str, current: float, previous: float):
    """检查评分快速下滑"""
    if previous > 0 and (previous - current) >= 50:
        create_alert(entity_id, entity_name, "评分快速下滑", "高", current)
        logger.warning("预警: %s 评分从 %.1f 降至 %.1f", entity_id, previous, current)
