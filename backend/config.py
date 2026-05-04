"""Flask 后端配置"""
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

DB_PATH = BASE_DIR / "credit_scores.db"
CONFIG_PATH = BASE_DIR / "scoring" / "config.yaml"