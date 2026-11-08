#!/usr/bin/env bash
# Start the Qwen3.5-4B Uncensored API server + keep-alive loop

BASE=/data/home
cd "$BASE"
source venv/bin/activate

# ── Kill any previous instance on port 8000 ───────────────────────────────────
OLD_PID=$(lsof -ti tcp:8000 2>/dev/null)
if [ -n "$OLD_PID" ]; then
    echo "[start.sh] Killing old process on port 8000 (PID $OLD_PID)"
    kill "$OLD_PID" 2>/dev/null
    sleep 2
fi

# ── Keep-alive ────────────────────────────────────────────────────────────────
# Logs system info every 27 minutes so the Instabox free server never sleeps.
keepalive() {
    local INTERVAL=$((27 * 60))
    local LOG=$BASE/keepalive.log

    while true; do
        {
            echo "──────────────────────────────────────"
            echo "[$(date '+%Y-%m-%d %H:%M:%S')] Keep-alive ping"
            echo "  uptime  : $(uptime -p)"
            echo "  kernel  : $(uname -r)"
            echo "  memory  : $(free -h | awk '/^Mem/{print $3 " used / " $2 " total"}')"
            echo "  disk    : $(df -h / | awk 'NR==2{print $3 " used / " $2 " total (" $5 ")"}')"
            echo "  load    : $(cut -d' ' -f1-3 /proc/loadavg)"
        } >> "$LOG" 2>&1
        sleep "$INTERVAL"
    done
}

keepalive &
KEEPALIVE_PID=$!
echo "[start.sh] Keep-alive started (PID $KEEPALIVE_PID, every 27 min) → keepalive.log"

# ── Watchdog — restarts API server if it crashes ──────────────────────────────
echo "[start.sh] Starting API server watchdog..."
while true; do
    echo "[watchdog] $(date '+%Y-%m-%d %H:%M:%S') Starting api_server.py..."
    python3 "$BASE/api_server.py"
    EXIT_CODE=$?
    echo "[watchdog] $(date '+%Y-%m-%d %H:%M:%S') Server exited (code $EXIT_CODE). Restarting in 5s..."
    sleep 5
done
