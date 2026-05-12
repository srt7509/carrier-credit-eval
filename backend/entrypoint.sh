#!/bin/bash
set -e

cd /app

DB_PATH="/app/data/credit_scores.db"
DB_VERSION_FILE="/app/data/.db_version"
CURRENT_VERSION="2.0"

need_seed=false

if [ ! -f "$DB_PATH" ]; then
    echo "=== 数据库不存在，执行初始化 ==="
    need_seed=true
elif [ ! -f "$DB_VERSION_FILE" ] || [ "$(cat $DB_VERSION_FILE)" != "$CURRENT_VERSION" ]; then
    echo "=== 数据库版本不匹配（当前: $(cat $DB_VERSION_FILE 2>/dev/null || echo '无'), 需要: $CURRENT_VERSION），重新初始化 ==="
    rm -f "$DB_PATH"
    need_seed=true
elif ! python -c "
import sqlite3
conn = sqlite3.connect('$DB_PATH')
tables = [r[0] for r in conn.execute(\"SELECT name FROM sqlite_master WHERE type='table'\").fetchall()]
conn.close()
assert 'vehicles' in tables, 'vehicles table missing'
" 2>/dev/null; then
    echo "=== vehicles 表不存在，需要数据库迁移，重新初始化 ==="
    rm -f "$DB_PATH"
    need_seed=true
fi

if $need_seed; then
    echo "=== 运行 seed_all.py 初始化数据 ==="
    python seed_all.py
    if [ -f credit_scores.db ]; then
        mv credit_scores.db "$DB_PATH"
    fi
    echo "$CURRENT_VERSION" > "$DB_VERSION_FILE"
else
    echo "=== 数据库已就绪（版本 $CURRENT_VERSION）==="
fi

# Symlink DB from persistent volume
ln -sf "$DB_PATH" credit_scores.db

# Start scheduler in background
echo "Starting background scheduler..."
nohup python -u -c "
import sys, time
sys.path.insert(0, '/app')
from scheduler import default_scheduler
default_scheduler.start()
while True:
    time.sleep(60)
" > /tmp/scheduler.log 2>&1 &

# Start gunicorn
echo "Starting Gunicorn on port 5001..."
exec gunicorn -w 2 -b 0.0.0.0:5001 \
    --access-logfile - \
    --error-logfile - \
    --log-level info \
    app:app
