#!/usr/bin/env bash
# Kill everything and do a clean restart

echo "[restart] Killing all api_server and start.sh processes..."
ps aux | awk '/api_server|start\.sh/{print $2}' | xargs kill -9 2>/dev/null

sleep 2

echo "[restart] Freeing port 8000..."
fuser -k 8000/tcp 2>/dev/null

sleep 2

echo "[restart] Starting fresh..."
nohup bash /data/home/start.sh > /data/home/watchdog.log 2>&1 &
echo "[restart] Done. PID=$!"
