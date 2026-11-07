#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# One-shot setup for Qwen3.5-4B Uncensored API on Instabox (or any Linux box)
# Usage: curl -fsSL <raw_url>/server/setup.sh | bash
# ─────────────────────────────────────────────────────────────────────────────
set -e

BASE=/data/home
MODEL_REPO="InterpreticAI/Qwen3.5-4B-Uncensored-v2-GGUF"
MODEL_FILE="Qwen3.5-4B-Uncensored-v2-Q4_K_M.gguf"
REPO_RAW="https://raw.githubusercontent.com/vtrsharvin-sj/qwen-instabox-api/main"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Qwen3.5-4B Uncensored API — Setup"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# ── 1. Python venv ────────────────────────────────────────────────────────────
echo "[1/4] Creating Python venv..."
cd "$BASE"
python3 -m venv venv
source venv/bin/activate
pip install --quiet --upgrade pip

# ── 2. Dependencies ───────────────────────────────────────────────────────────
echo "[2/4] Installing dependencies..."
pip install --quiet fastapi uvicorn huggingface_hub llama-cpp-python

# ── 3. Download model ─────────────────────────────────────────────────────────
echo "[3/4] Downloading model (~2.6 GB, please wait)..."
mkdir -p "$BASE/models"
python3 - <<PYEOF
from huggingface_hub import hf_hub_download
path = hf_hub_download(
    repo_id="$MODEL_REPO",
    filename="$MODEL_FILE",
    local_dir="$BASE/models",
)
print(f"  Saved to: {path}")
PYEOF

# ── 4. Download server files ──────────────────────────────────────────────────
echo "[4/4] Downloading server scripts..."
curl -fsSL "$REPO_RAW/server/api_server.py" -o "$BASE/api_server.py"
curl -fsSL "$REPO_RAW/server/start.sh"      -o "$BASE/start.sh"
chmod +x "$BASE/start.sh"

# ── Start ─────────────────────────────────────────────────────────────────────
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Setup complete! Starting server..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
nohup bash "$BASE/start.sh" > "$BASE/server.log" 2>&1 &
sleep 12
cat "$BASE/server.log"
echo ""
echo "  API is live on port 8000"
echo "  Use your Instabox tunnel URL: https://8000-<your-id>.instabox.tech"
