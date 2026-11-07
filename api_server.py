"""
Qwen3.5-4B Uncensored — OpenAI-compatible API server
Powered by llama-cpp-python
"""

import os
import re
import time
import uuid
from typing import List, Optional, Union

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from llama_cpp import Llama

# ── Config ────────────────────────────────────────────────────────────────────
MODEL_PATH = os.environ.get(
    "MODEL_PATH",
    "/data/home/models/Qwen3.5-4B-Uncensored-v2-Q4_K_M.gguf"
)
N_CTX       = int(os.environ.get("N_CTX", "4096"))
N_THREADS   = int(os.environ.get("N_THREADS", "4"))
HOST        = os.environ.get("HOST", "0.0.0.0")
PORT        = int(os.environ.get("PORT", "8000"))

# ── Load model ────────────────────────────────────────────────────────────────
print(f"Loading model from {MODEL_PATH} …")
llm = Llama(
    model_path=MODEL_PATH,
    n_ctx=N_CTX,
    n_threads=N_THREADS,
    verbose=False,
)
print("Model loaded.")

# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(title="Qwen3.5-4B Uncensored API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Schemas ───────────────────────────────────────────────────────────────────
class Message(BaseModel):
    role: str          # system | user | assistant
    content: str

class ChatCompletionRequest(BaseModel):
    model: Optional[str] = "qwen3.5-4b-uncensored"
    messages: List[Message]
    max_tokens: Optional[int] = 512
    temperature: Optional[float] = 0.7
    top_p: Optional[float] = 0.95
    stop: Optional[Union[str, List[str]]] = None
    stream: Optional[bool] = False

class CompletionRequest(BaseModel):
    model: Optional[str] = "qwen3.5-4b-uncensored"
    prompt: str
    max_tokens: Optional[int] = 512
    temperature: Optional[float] = 0.7
    top_p: Optional[float] = 0.95
    stop: Optional[Union[str, List[str]]] = None

# ── Helpers ───────────────────────────────────────────────────────────────────
def strip_think(text: str) -> str:
    """Remove <think>...</think> reasoning blocks Qwen3 emits."""
    return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()

def build_prompt(messages: List[Message]) -> str:
    """Convert chat messages to Qwen ChatML format."""
    prompt = ""
    for msg in messages:
        if msg.role == "system":
            prompt += f"<|im_start|>system\n{msg.content}<|im_end|>\n"
        elif msg.role == "user":
            prompt += f"<|im_start|>user\n{msg.content}<|im_end|>\n"
        elif msg.role == "assistant":
            prompt += f"<|im_start|>assistant\n{msg.content}<|im_end|>\n"
    prompt += "<|im_start|>assistant\n"
    return prompt

# ── Routes ────────────────────────────────────────────────────────────────────
@app.get("/")
def root():
    return {"status": "ok", "model": "qwen3.5-4b-uncensored", "docs": "/docs"}

@app.get("/v1/models")
def list_models():
    return {
        "object": "list",
        "data": [
            {
                "id": "qwen3.5-4b-uncensored",
                "object": "model",
                "created": int(time.time()),
                "owned_by": "user",
            }
        ],
    }

@app.post("/v1/chat/completions")
def chat_completions(req: ChatCompletionRequest):
    if req.stream:
        raise HTTPException(status_code=400, detail="Streaming not supported yet.")

    prompt = build_prompt(req.messages)
    stop_tokens = req.stop or ["<|im_end|>", "<|endoftext|>"]
    if isinstance(stop_tokens, str):
        stop_tokens = [stop_tokens]

    output = llm(
        prompt,
        max_tokens=req.max_tokens,
        temperature=req.temperature,
        top_p=req.top_p,
        stop=stop_tokens,
    )

    text = strip_think(output["choices"][0]["text"].strip())
    prompt_tokens  = output["usage"]["prompt_tokens"]
    completion_tok = output["usage"]["completion_tokens"]

    return {
        "id": f"chatcmpl-{uuid.uuid4().hex}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": req.model,
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": text},
                "finish_reason": "stop",
            }
        ],
        "usage": {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tok,
            "total_tokens": prompt_tokens + completion_tok,
        },
    }

@app.post("/v1/completions")
def completions(req: CompletionRequest):
    stop_tokens = req.stop or ["<|im_end|>", "<|endoftext|>"]
    if isinstance(stop_tokens, str):
        stop_tokens = [stop_tokens]

    output = llm(
        req.prompt,
        max_tokens=req.max_tokens,
        temperature=req.temperature,
        top_p=req.top_p,
        stop=stop_tokens,
    )

    text = strip_think(output["choices"][0]["text"])
    prompt_tokens  = output["usage"]["prompt_tokens"]
    completion_tok = output["usage"]["completion_tokens"]

    return {
        "id": f"cmpl-{uuid.uuid4().hex}",
        "object": "text_completion",
        "created": int(time.time()),
        "model": req.model,
        "choices": [
            {
                "text": text,
                "index": 0,
                "finish_reason": "stop",
            }
        ],
        "usage": {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tok,
            "total_tokens": prompt_tokens + completion_tok,
        },
    }

# ── Entry ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=HOST, port=PORT)
