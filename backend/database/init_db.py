"""SQLite数据库初始化"""
from database.db_manager import DatabaseManager, default_db


def get_connection():
    return default_db.connect()


def init_database():
    """初始化数据库表结构"""
    with default_db.connect() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS shippers (
                shipper_id TEXT PRIMARY KEY,
                name TEXT,
                shipper_type TEXT,
                total_orders INTEGER,
                completed_orders INTEGER,
                on_time_payment_rate REAL,
                overdue_count INTEGER,
                overdue_amount REAL,
                avg_order_value REAL,
                complaint_count INTEGER,
                cooperation_months INTEGER,
                credit_trend_score REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS carriers (
                carrier_id TEXT PRIMARY KEY,
                name TEXT,
                unified_credit_code TEXT DEFAULT '',
                cooperation_start_date TEXT DEFAULT '',
                cooperation_mode TEXT DEFAULT '长期协议',
                fleet_size INTEGER DEFAULT 0,
                qualification TEXT DEFAULT '全资质',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS vehicles (
                vehicle_id TEXT PRIMARY KEY,
                carrier_id TEXT,
                license_plate TEXT,
                driver_name TEXT,
                transport_category TEXT DEFAULT '普货',
                total_orders INTEGER DEFAULT 0,
                completed_orders INTEGER DEFAULT 0,
                on_time_orders INTEGER DEFAULT 0,
                complaint_count INTEGER DEFAULT 0,
                accident_count INTEGER DEFAULT 0,
                violation_count INTEGER DEFAULT 0,
                license_valid INTEGER DEFAULT 1,
                on_time_payment_rate REAL DEFAULT 0.0,
                overdue_amount REAL DEFAULT 0.0,
                avg_customer_rating REAL DEFAULT 0.0,
                damage_rate REAL DEFAULT 0.0,
                cooperation_months INTEGER DEFAULT 0,
                credit_trend_score REAL DEFAULT 80.0,
                recent_3m_orders INTEGER DEFAULT 0,
                risk_label TEXT DEFAULT '正常',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS credit_scores (
                score_id INTEGER PRIMARY KEY AUTOINCREMENT,
                entity_id TEXT,
                entity_type TEXT,
                score_value REAL,
                grade TEXT,
                dimension_scores TEXT,
                risk_flags TEXT,
                signature TEXT,
                tx_hash TEXT,
                eval_period TEXT,
                eval_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_current INTEGER DEFAULT 1,
                model_version TEXT DEFAULT '',
                eval_mode TEXT DEFAULT '普运'
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS blockchain_records (
                record_id INTEGER PRIMARY KEY AUTOINCREMENT,
                entity_id TEXT,
                score_hash TEXT,
                tx_hash TEXT,
                block_number INTEGER,
                on_chain_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                verified INTEGER DEFAULT 0
            )
        """)

        # === 新增表 ===

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS score_history (
                history_id INTEGER PRIMARY KEY AUTOINCREMENT,
                entity_id TEXT,
                entity_type TEXT,
                score_value REAL,
                grade TEXT,
                dimension_scores TEXT,
                eval_period TEXT,
                eval_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                model_version TEXT DEFAULT ''
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS score_events (
                event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                entity_id TEXT,
                event_type TEXT,
                event_desc TEXT,
                score_change REAL,
                category TEXT DEFAULT '',
                event_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS alert_records (
                alert_id INTEGER PRIMARY KEY AUTOINCREMENT,
                entity_id TEXT,
                entity_name TEXT,
                alert_type TEXT,
                severity TEXT,
                trigger_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                current_score REAL,
                status TEXT DEFAULT '未处理',
                handler_note TEXT DEFAULT ''
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS model_performance (
                perf_id INTEGER PRIMARY KEY AUTOINCREMENT,
                period TEXT,
                model_version TEXT,
                ks REAL,
                auc REAL,
                psi REAL,
                spearman REAL,
                epv_satisfied INTEGER,
                record_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS model_registry (
                registry_id INTEGER PRIMARY KEY AUTOINCREMENT,
                model_version TEXT,
                model_role TEXT,
                online_date TEXT,
                update_cycle TEXT DEFAULT '月度',
                dimension_count INTEGER DEFAULT 5,
                status TEXT DEFAULT '运行中',
                consecutive_pass_months INTEGER DEFAULT 0
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS business_rules (
                rule_id INTEGER PRIMARY KEY AUTOINCREMENT,
                rule_type TEXT,
                rule_key TEXT,
                rule_value TEXT,
                description TEXT DEFAULT '',
                is_active INTEGER DEFAULT 1,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

    print(f"数据库初始化完成: {default_db.db_path}")


def reset_database():
    """重置数据库（删除所有表后重新创建）"""
    with default_db.connect() as conn:
        cursor = conn.cursor()
        cursor.execute("DROP TABLE IF EXISTS shippers")
        cursor.execute("DROP TABLE IF EXISTS vehicles")
        cursor.execute("DROP TABLE IF EXISTS carriers")
        cursor.execute("DROP TABLE IF EXISTS credit_scores")
        cursor.execute("DROP TABLE IF EXISTS blockchain_records")
        cursor.execute("DROP TABLE IF EXISTS score_history")
        cursor.execute("DROP TABLE IF EXISTS score_events")
        cursor.execute("DROP TABLE IF EXISTS alert_records")
        cursor.execute("DROP TABLE IF EXISTS model_performance")
        cursor.execute("DROP TABLE IF EXISTS model_registry")
        cursor.execute("DROP TABLE IF EXISTS business_rules")

    init_database()
    print("数据库已重置")


if __name__ == "__main__":
    init_database()
