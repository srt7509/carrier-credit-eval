"""全局配置集中管理"""
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
DB_PATH = PROJECT_ROOT / "credit_scores.db"
CONFIG_PATH = PROJECT_ROOT / "scoring" / "config.yaml"

SECRET_KEY = os.getenv("CREDIT_SECRET_KEY", "credit_prototype_secret_key_2025")

LOG_LEVEL = os.getenv("CREDIT_LOG_LEVEL", "INFO")