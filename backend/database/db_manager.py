"""数据库连接管理器"""
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Optional

from settings import DB_PATH as _DB_PATH


class DatabaseManager:
    """统一数据库连接管理"""

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or _DB_PATH

    @contextmanager
    def connect(self):
        """获取数据库连接（自动提交/回滚/关闭）"""
        conn = sqlite3.connect(str(self.db_path))
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def execute(self, sql: str, params=()):
        """执行单条 SQL（自动提交）"""
        with self.connect() as conn:
            return conn.execute(sql, params)

    def executemany(self, sql: str, seq):
        """批量执行 SQL"""
        with self.connect() as conn:
            conn.executemany(sql, seq)

    def fetchall(self, sql: str, params=()):
        """查询并获取全部结果"""
        with self.connect() as conn:
            return conn.execute(sql, params).fetchall()

    def fetchone(self, sql: str, params=()):
        """查询并获取单条结果"""
        with self.connect() as conn:
            return conn.execute(sql, params).fetchone()


# 默认全局实例
default_db = DatabaseManager()
