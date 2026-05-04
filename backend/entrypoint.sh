#!/bin/bash
set -e

cd /app

# Initialize database on first run
if [ ! -f /app/data/credit_scores.db ]; then
    echo "=== Initializing database with seed data ==="
    python seed_all.py
    if [ -f credit_scores.db ]; then
        mv credit_scores.db /app/data/
    fi
fi

# Symlink DB from persistent volume
ln -sf /app/data/credit_scores.db credit_scores.db

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
