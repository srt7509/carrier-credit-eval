"""评分引擎核心模块 — 支持双模型（冠军/挑战者）"""
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional

import yaml

from database.models import Carrier, Shipper, CreditScore
from database.db_manager import DatabaseManager, default_db
from scoring.safe_eval import SafeEvaluator, SafeEvalError
from settings import CONFIG_PATH

logger = logging.getLogger(__name__)


class ScoreConfig:
    """评分配置加载器"""

    def __init__(self, config_path: Optional[Path] = None, model_version: str = "v1.0"):
        self.config_path = config_path or CONFIG_PATH
        self.config: dict = {}
        self.model_version = model_version
        self._load_config()

    def _load_config(self):
        with open(self.config_path, encoding="utf-8") as f:
            self.config = yaml.safe_load(f)

    def _get_dimensions_key(self):
        """根据模型版本获取对应的维度配置键"""
        if self.model_version == "v2.0" and "dimensions_v2" in self.config:
            return "dimensions_v2"
        return "dimensions"

    def get_dimension_weights(self) -> Dict[str, float]:
        key = self._get_dimensions_key()
        return {k: v["weight"] for k, v in self.config[key].items()}

    def get_dimensions(self) -> dict:
        key = self._get_dimensions_key()
        return self.config[key]

    def get_grade(self, score: float) -> str:
        thresholds = self.config["grade_thresholds"]
        for grade, threshold in sorted(thresholds.items(), key=lambda x: -x[1]):
            if score >= threshold:
                return grade
        return "C"

    def get_risk_thresholds(self) -> Dict[str, Any]:
        return self.config["risk_thresholds"]


class CreditScorer:
    """信用评分引擎 — 单模型版本"""

    def __init__(self, config_path: Optional[Path] = None, model_version: str = "v1.0"):
        self.config = ScoreConfig(config_path, model_version)
        self.model_version = model_version

    def _build_formula_vars(self, entity) -> Dict[str, float]:
        vars_dict = {
            "completed_orders": float(entity.completed_orders),
            "total_orders": float(entity.total_orders),
            "on_time_payment_rate": float(entity.on_time_payment_rate),
            "complaint_count": float(entity.complaint_count),
            "cooperation_months": float(entity.cooperation_months),
            "credit_trend_score": float(entity.credit_trend_score),
        }

        if isinstance(entity, Carrier):
            vars_dict.update({
                "on_time_orders": float(entity.on_time_orders),
                "accident_count": float(entity.accident_count),
                "violation_count": float(entity.violation_count),
                "license_valid": 1.0 if entity.license_valid else 0.0,
                "overdue_amount": float(entity.overdue_amount),
                "avg_customer_rating": float(entity.avg_customer_rating),
                "damage_rate": float(entity.damage_rate),
                "recent_3m_orders": float(getattr(entity, "recent_3m_orders", 0)),
                "overdue_count": 0.0,
                "avg_order_value": 10000.0,
            })
        else:
            vars_dict.update({
                "on_time_orders": float(entity.completed_orders),
                "overdue_amount": float(entity.overdue_amount),
                "avg_customer_rating": 4.0,
                "damage_rate": 0.0,
                "recent_3m_orders": 0.0,
                "overdue_count": float(entity.overdue_count),
                "avg_order_value": float(entity.avg_order_value),
                "accident_count": 0.0,
                "violation_count": 0.0,
                "license_valid": 1.0,
            })

        return vars_dict

    def _evaluate_formula(self, formula: str, vars_dict: Dict[str, float]) -> float:
        evaluator = SafeEvaluator(vars_dict)
        try:
            return evaluator.evaluate(formula)
        except SafeEvalError as e:
            logger.warning("公式计算错误: %s - %s", formula, e)
            return 0.0

    def calculate_score(self, entity, eval_mode: str = "普运") -> CreditScore:
        """计算单个实体的信用评分"""
        dimension_scores = {}
        vars_dict = self._build_formula_vars(entity)
        dimensions = self.config.get_dimensions()

        for dim_name, dim_config in dimensions.items():
            dim_weight = dim_config["weight"]
            indicator_scores = []

            for ind_name, ind_config in dim_config["indicators"].items():
                ind_weight = ind_config["weight"]
                formula = ind_config["formula"]
                is_penalty = ind_config.get("penalty", False)

                ind_score = self._evaluate_formula(formula, vars_dict)
                if is_penalty:
                    ind_score = max(0.0, ind_score)

                indicator_scores.append(ind_score * ind_weight)

            dim_total = round(sum(indicator_scores) * dim_weight, 2)
            dimension_scores[dim_name] = dim_total

        total_score = round(sum(dimension_scores.values()), 2)
        grade = self.config.get_grade(total_score)
        risk_flags = self._check_risks(entity, total_score)

        if isinstance(entity, Carrier):
            entity_id = entity.carrier_id
            entity_type = "carrier"
        else:
            entity_id = entity.shipper_id
            entity_type = "shipper"

        return CreditScore(
            entity_id=entity_id,
            entity_type=entity_type,
            score_value=total_score,
            grade=grade,
            dimension_scores=dimension_scores,
            risk_flags=risk_flags,
            model_version=self.model_version,
            eval_mode=eval_mode,
        )

    def _check_risks(self, entity, score: float) -> List[str]:
        risks = []
        thresholds = self.config.get_risk_thresholds()

        if entity.total_orders > 0:
            complaint_rate = entity.complaint_count / entity.total_orders * 100
            if complaint_rate > thresholds["complaint_rate"]:
                risks.append(f"投诉率过高: {round(complaint_rate, 2)}%")

        if isinstance(entity, Carrier):
            if entity.accident_count > thresholds["accident_count"]:
                risks.append(f"安全事故次数过多: {entity.accident_count}次")
            if not entity.license_valid:
                risks.append("证照已失效")
        else:
            if entity.overdue_count > 0:
                risks.append(f"逾期次数: {entity.overdue_count}次")
            if entity.overdue_amount > 10000:
                risks.append(f"逾期金额过高: ¥{entity.overdue_amount:,.2f}")

        return risks

    def calculate_all(self, entities: List, eval_mode: str = "普运") -> List[CreditScore]:
        return [self.calculate_score(entity, eval_mode) for entity in entities]


class DualModelScorer:
    """双模型评分引擎 — 同时运行冠军和挑战者模型"""

    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path
        self.champion = CreditScorer(config_path, model_version="v1.0")
        self.challenger = CreditScorer(config_path, model_version="v2.0")

    def calculate_all(self, entities: List) -> Dict[str, List[CreditScore]]:
        return {
            "champion": self.champion.calculate_all(entities),
            "challenger": self.challenger.calculate_all(entities),
        }


def save_scores_to_db(scores: List[CreditScore]):
    """保存评分结果到数据库"""
    with default_db.connect() as conn:
        conn.execute("UPDATE credit_scores SET is_current = 0")

        for score in scores:
            conn.execute(
                """INSERT INTO credit_scores (
                    entity_id, entity_type, score_value, grade,
                    dimension_scores, risk_flags, signature, tx_hash,
                    eval_period, eval_time, is_current, model_version, eval_mode
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), 1, ?, ?)""",
                (
                    score.entity_id, score.entity_type, score.score_value,
                    score.grade, json.dumps(score.dimension_scores),
                    json.dumps(score.risk_flags), score.signature,
                    score.tx_hash, score.eval_period,
                    score.model_version, score.eval_mode,
                ),
            )

            # 同时写入 score_history
            conn.execute(
                """INSERT INTO score_history (entity_id, entity_type, score_value, grade, dimension_scores, eval_period, eval_time, model_version)
                   VALUES (?, ?, ?, ?, ?, ?, datetime('now'), ?)""",
                (score.entity_id, score.entity_type, score.score_value, score.grade,
                 json.dumps(score.dimension_scores), score.eval_period, score.model_version),
            )

    logger.info("已保存 %d 条评分结果", len(scores))


def get_all_scores_from_db() -> List[Dict]:
    """从数据库获取所有当前评分"""
    rows = default_db.fetchall(
        """SELECT entity_id, entity_type, score_value, grade,
                  dimension_scores, risk_flags, signature, tx_hash, eval_time, model_version, eval_mode
           FROM credit_scores WHERE is_current = 1"""
    )

    results = []
    for row in rows:
        results.append({
            "entity_id": row[0],
            "entity_type": row[1],
            "score_value": row[2],
            "grade": row[3],
            "dimension_scores": json.loads(row[4]) if row[4] else {},
            "risk_flags": json.loads(row[5]) if row[5] else [],
            "signature": row[6],
            "tx_hash": row[7],
            "eval_time": row[8],
            "model_version": row[9] if len(row) > 9 else "",
            "eval_mode": row[10] if len(row) > 10 else "普运",
        })
    return results


def get_score_history(entity_id: str, months: int = 12) -> List[Dict]:
    """获取实体历史评分"""
    rows = default_db.fetchall(
        """SELECT score_value, grade, dimension_scores, eval_period, eval_time, model_version
           FROM score_history WHERE entity_id = ?
           ORDER BY eval_time DESC LIMIT ?""",
        (entity_id, months),
    )
    results = []
    for r in rows:
        results.append({
            "score_value": r[0],
            "grade": r[1],
            "dimension_scores": json.loads(r[2]) if r[2] else {},
            "eval_period": r[3],
            "eval_time": r[4],
            "model_version": r[5],
        })
    return list(reversed(results))


def calculate_psi(scores_old: List[CreditScore], scores_new: List[CreditScore]) -> float:
    """计算 Population Stability Index"""
    import math
    if not scores_old or not scores_new:
        return 0.0
    buckets = [0, 50, 60, 70, 80, 90, 101]
    n_old = len(scores_old)
    n_new = len(scores_new)
    psi = 0.0
    for i in range(len(buckets) - 1):
        low, high = buckets[i], buckets[i + 1]
        old_pct = sum(1 for s in scores_old if low <= s.score_value < high) / n_old
        new_pct = sum(1 for s in scores_new if low <= s.score_value < high) / n_new
        old_pct = max(old_pct, 0.001)
        new_pct = max(new_pct, 0.001)
        psi += (new_pct - old_pct) * math.log(new_pct / old_pct)
    return round(psi, 4)


if __name__ == "__main__":
    from data.mock_data import generate_mock_carriers
    from database.init_db import init_database

    init_database()
    carriers = generate_mock_carriers(10)

    print("=== 冠军模型 v1.0 ===")
    scorer = CreditScorer(model_version="v1.0")
    scores = scorer.calculate_all(carriers)
    for s in scores:
        print(f"{s.entity_id}: {s.score_value} ({s.grade}) - {s.dimension_scores}")

    print("\n=== 挑战者模型 v2.0 ===")
    scorer2 = CreditScorer(model_version="v2.0")
    scores2 = scorer2.calculate_all(carriers)
    for s in scores2:
        print(f"{s.entity_id}: {s.score_value} ({s.grade})")

    print(f"\nPSI = {calculate_psi(scores, scores2)}")
