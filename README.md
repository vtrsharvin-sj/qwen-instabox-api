# Qwen3.5-4B Uncensored — Free Self-Hosted API

Run **Qwen3.5-4B Uncensored** as an OpenAI-compatible REST API on a free [Instabox](https://instabox.sh) server. No GPU needed, no paid tier, works with any OpenAI SDK.

---

## What's inside

| File | Purpose |
|------|---------|
| `server/api_server.py` | FastAPI server — OpenAI-compatible endpoints |
| `server/start.sh` | Starts the API + keep-alive loop (prevents idle sleep) |
| `server/setup.sh` | One-shot setup: installs deps, downloads model, starts server |
| `cloudflare-worker/worker.js` | Cloudflare Worker proxy with API key auth |
| `client/chat.py` | Interactive terminal chat assistant |
| `client/example.py` | Minimal OpenAI SDK usage example |
| `client/test_api.bat` | Windows CMD test suite (health, models, chat) |

---

## Quick Start

### 1 — Get a free Instabox server

1. Go to [instabox.sh](https://instabox.sh) and sign up (free)
2. Run `npx instabox@latest sh` — it opens an SSH shell into your machine
3. Note your **SSH credentials** and **port tunnel URL** (e.g. `https://8000-xxx.instabox.tech`)

### 2 — Deploy the API server

SSH into your Instabox machine and run:

```bash
curl -fsSL https://raw.githubusercontent.com/vtrsharvin-sj/qwen-instabox-api/main/server/setup.sh | bash
```

That's it. The script will:
- Create a Python venv
- Install `llama-cpp-python`, `fastapi`, `uvicorn`
- Download `Qwen3.5-4B-Uncensored-v2-Q4_K_M.gguf` (~2.6 GB) from HuggingFace
- Start the API server on port 8000
- Start the keep-alive loop (pings every 27 min so the server never sleeps)

### 3 — Use the API

**Python (OpenAI SDK):**
```python
from openai import OpenAI

client = OpenAI(
    base_url="https://qwen-api.vtrsharvin.workers.dev/v1",
    api_key="YOUR_API_KEY",
)

response = client.chat.completions.create(
    model="qwen3.5-4b-uncensored",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello!"},
    ],
)

print(response.choices[0].message.content)
```

**curl:**
```bash
curl -X POST https://qwen-api.vtrsharvin.workers.dev/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{
    "model": "qwen3.5-4b-uncensored",
    "messages": [{"role": "user", "content": "Hello!"}],
    "max_tokens": 200
  }'
```

**LangChain:**
```python
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(
    base_url="https://qwen-api.vtrsharvin.workers.dev/v1",
    api_key="YOUR_API_KEY",
    model="qwen3.5-4b-uncensored",
)
```

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/docs` | Interactive Swagger UI (no auth needed) |
| `GET` | `/v1/models` | List available models |
| `POST` | `/v1/chat/completions` | Chat (OpenAI-compatible) |
| `POST` | `/v1/completions` | Raw text completion |

---

## Client Tools

### Terminal Chat (`client/chat.py`)

```bash
python client/chat.py
```

Interactive multi-turn conversation in your terminal.

| Command | Action |
|---------|--------|
| `/clear` | Reset conversation history |
| `/history` | Show conversation so far |
| `/exit` | Quit |

### Test Suite (`client/test_api.bat`) — Windows only

Double-click or run from CMD. Runs health check, model list, and a chat completion test.

### Minimal Example (`client/example.py`)

```bash
python client/example.py
```

---

## Configuration

Environment variables you can set before running `api_server.py`:

| Variable | Default | Description |
|----------|---------|-------------|
| `MODEL_PATH` | `/data/home/models/Qwen3.5-4B-Uncensored-v2-Q4_K_M.gguf` | Path to GGUF model |
| `N_CTX` | `4096` | Context window size |
| `N_THREADS` | `4` | CPU threads for inference |
| `HOST` | `0.0.0.0` | Bind address |
| `PORT` | `8000` | Bind port |

---

## Keep-Alive

The `start.sh` script runs a background loop that logs system info every 27 minutes — this prevents the Instabox free tier from suspending your machine due to inactivity.

Logs are written to `/data/home/keepalive.log`.

---

## Restart After Server Reboot

If your Instabox machine restarts, SSH in and run:

```bash
nohup bash /data/home/start.sh > /data/home/server.log 2>&1 &
```

---

## Model Info

- **Model:** [InterpreticAI/Qwen3.5-4B-Uncensored-v2-GGUF](https://huggingface.co/InterpreticAI/Qwen3.5-4B-Uncensored-v2-GGUF)
- **Quantization:** Q4_K_M (~2.6 GB)
- **Context:** 4096 tokens
- **Inference:** CPU (no GPU required)

---

## Requirements

**Server (Instabox / any Linux machine):**
- Python 3.10+
- 4 GB+ RAM
- 4 GB+ free disk

**Client (your machine):**
- Python 3.8+
- `openai` library (`pip install openai`)
