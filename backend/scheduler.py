"""定时任务调度模块 — 月度评分更新、事件监控"""
import logging
import threading
import time
from datetime import datetime

from database.db_manager import default_db
from scoring.scoring_model import DualModelScorer, save_scores_to_db, calculate_psi, get_all_scores_from_db
from data.mock_data import get_carriers_from_db
from alerts.alert_manager import check_score_drop, create_alert
from business.rule_engine import get_veto_events

logger = logging.getLogger(__name__)


class CreditScheduler:
    """评分系统定时任务调度器"""

    def __init__(self, check_interval: int = 3600):
        """
        Args:
            check_interval: 检查间隔（秒），默认 3600（1小时）
        """
        self.check_interval = check_interval
        self._running = False
        self._thread = None

    def start(self):
        """启动后台调度线程"""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        logger.info("调度器已启动，检查间隔: %ds", self.check_interval)

    def stop(self):
        """停止调度器"""
        self._running = False
        logger.info("调度器已停止")

    def _run_loop(self):
        while self._running:
            try:
                self._check_monthly_scoring()
                self._check_veto_events()
            except Exception as e:
                logger.error("调度检查异常: %s", e)
            time.sleep(self.check_interval)

    def _check_monthly_scoring(self):
        """检查是否需要月度评分更新（每月1日）"""
        now = datetime.now()
        if now.day != 1 or now.hour != 2:  # 每月1日凌晨2点触发
            return

        # 检查本月是否已执行
        period = now.strftime("%Y-%m")
        existing = default_db.fetchone(
            "SELECT COUNT(*) FROM score_history WHERE eval_period = ?", (period,)
        )
        if existing and existing[0] > 0:
            return  # 本月已执行

        logger.info("=== 月度评分更新开始: %s ===", period)
        try:
            carriers = get_carriers_from_db()
            if not carriers:
                return

            # 旧评分
            old_scores = get_all_scores_from_db()

            # 双模型计算
            dual = DualModelScorer()
            results = dual.calculate_all(carriers)

            # PSI 检查
            psi = calculate_psi(
                [type('S', (), {'score_value': s['score_value']}) for s in old_scores],
                results["champion"],
            )

            if psi < 0.1:
                save_scores_to_db(results["champion"])
                logger.info("月度评分更新完成，PSI=%.4f", psi)
                self._notify_grade_changes(old_scores, results["champion"])
            else:
                logger.warning("PSI=%.4f >= 0.1，触发人工复核流程", psi)
                create_alert("SYSTEM", "评分系统", "PSI异常", "高", 0)
        except Exception as e:
            logger.error("月度评分更新失败: %s", e)

    def _notify_grade_changes(self, old_scores, new_scores):
        """通知等级变动"""
        old_map = {s["entity_id"]: s["grade"] for s in old_scores}
        for ns in new_scores:
            old_grade = old_map.get(ns.entity_id, "")
            if old_grade and old_grade != ns.grade:
                logger.info("等级变动: %s %s -> %s", ns.entity_id, old_grade, ns.grade)

    def _check_veto_events(self):
        """检查一票否决事件"""
        veto_events = get_veto_events()
        if not veto_events:
            return

        # 查询近期未处理的否决事件
        rows = default_db.fetchall(
            """SELECT entity_id, event_desc, event_time FROM score_events
               WHERE event_type = 'one_vote_veto'
               AND event_time >= datetime('now', '-1 day')
               ORDER BY event_time DESC"""
        )

        for row in rows:
            entity_id, event_desc, event_time = row

            # 检查是否已处理
            name_row = default_db.fetchone("SELECT name FROM carriers WHERE carrier_id = ?", (entity_id,))
            entity_name = name_row[0] if name_row else entity_id

            logger.warning("一票否决事件: %s - %s", entity_id, event_desc)
            create_alert(entity_id, entity_name, "一票否决触发", "高", 0)

            # 自动降级为 C
            default_db.execute(
                """UPDATE credit_scores SET grade = 'C', score_value = MIN(score_value, 30)
                   WHERE entity_id = ? AND is_current = 1""",
                (entity_id,),
            )

    def run_manual(self):
        """手动触发一次全量评分更新"""
        logger.info("手动触发评分更新")
        carriers = get_carriers_from_db()
        if not carriers:
            return {"error": "无承运商数据"}

        old_scores = get_all_scores_from_db()
        dual = DualModelScorer()
        results = dual.calculate_all(carriers)
        psi = calculate_psi(
            [type('S', (), {'score_value': s['score_value']}) for s in old_scores],
            results["champion"],
        )
        save_scores_to_db(results["champion"])

        return {
            "carriers": len(carriers),
            "psi": psi,
            "champion_mean": round(sum(s.score_value for s in results["champion"]) / len(results["champion"]), 2),
            "challenger_mean": round(sum(s.score_value for s in results["challenger"]) / len(results["challenger"]), 2),
        }


# 全局调度器实例
default_scheduler = CreditScheduler()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    scheduler = CreditScheduler(check_interval=10)
    scheduler.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        scheduler.stop()
