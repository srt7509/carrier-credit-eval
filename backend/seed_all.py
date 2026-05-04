"""一键初始化: 数据库建表 + 模拟数据 + 评分计算"""
import logging
import sys
sys.path.insert(0, '.')

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

from database.init_db import reset_database
from data.mock_data import (
    generate_mock_carriers, save_carriers_to_db,
    generate_mock_shippers, save_shippers_to_db,
    generate_mock_score_events, save_score_events_to_db,
    generate_mock_alerts, save_alerts_to_db,
    generate_mock_model_performance, save_model_performance_to_db,
    generate_mock_model_registry, save_model_registry_to_db,
    generate_default_business_rules, save_business_rules_to_db,
    seed_score_history, generate_mock_blockchain_records,
    save_blockchain_records_to_db,
)
from scoring.scoring_model import DualModelScorer, save_scores_to_db, get_all_scores_from_db
from data.mock_data import get_carriers_from_db


def main():
    logger.info("=== 重置数据库 ===")
    reset_database()

    logger.info("=== 生成承运商数据 ===")
    carriers = generate_mock_carriers(50)
    save_carriers_to_db(carriers)

    logger.info("=== 生成货主数据 ===")
    shippers = generate_mock_shippers(30)
    save_shippers_to_db(shippers)

    logger.info("=== 双模型评分 ===")
    dual = DualModelScorer()
    all_carriers = get_carriers_from_db()
    results = dual.calculate_all(all_carriers)

    # 保存冠军模型评分
    save_scores_to_db(results["champion"])
    logger.info("冠军模型平均分: %.2f", sum(s.score_value for s in results["champion"]) / len(results["champion"]))
    logger.info("挑战者模型平均分: %.2f", sum(s.score_value for s in results["challenger"]) / len(results["challenger"]))

    logger.info("=== 生成评分事件 ===")
    carrier_ids = [c.carrier_id for c in carriers]
    events = generate_mock_score_events(carrier_ids)
    save_score_events_to_db(events)

    logger.info("=== 生成预警记录 ===")
    carrier_names = [c.name for c in carriers]
    alerts = generate_mock_alerts(carrier_ids, carrier_names)
    save_alerts_to_db(alerts)

    logger.info("=== 生成模型性能指标 ===")
    perf = generate_mock_model_performance()
    save_model_performance_to_db(perf)

    logger.info("=== 保存模型注册信息 ===")
    registry = generate_mock_model_registry()
    save_model_registry_to_db(registry)

    logger.info("=== 保存业务规则 ===")
    rules = generate_default_business_rules()
    save_business_rules_to_db(rules)

    logger.info("=== 生成历史评分快照 ===")
    seed_score_history(all_carriers)

    logger.info("=== 生成区块链存证记录 ===")
    carrier_ids = [c.carrier_id for c in carriers]
    bc_records = generate_mock_blockchain_records(carrier_ids)
    save_blockchain_records_to_db(bc_records)

    logger.info("=== 初始化完成 ===")
    logger.info("承运商: %d, 货主: %d, 评分: %d", len(carriers), len(shippers), len(results["champion"]))
    logger.info("评分事件: %d, 预警: %d, 模型性能: %d", len(events), len(alerts), len(perf))
    logger.info("启动后端: pixi run python credit-web/backend/app.py")


if __name__ == "__main__":
    main()
