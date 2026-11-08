"""
Qwen3.5-4B Uncensored — Fully OpenAI-compatible API server
Powered by llama-cpp-python
"""

import json
import os
import re
import time
import uuid
from typing import Any, Dict, Iterator, List, Optional, Union

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field, field_validator
from llama_cpp import Llama

# ── Config ────────────────────────────────────────────────────────────────────
MODEL_PATH = os.environ.get(
    "MODEL_PATH",
    "/data/home/models/Qwen3.5-4B-Uncensored-v2-Q4_K_M.gguf",
)
N_CTX      = int(os.environ.get("N_CTX", "4096"))
N_THREADS  = int(os.environ.get("N_THREADS", "4"))
HOST       = os.environ.get("HOST", "0.0.0.0")
PORT       = int(os.environ.get("PORT", "8000"))
MODEL_ID   = "qwen3.5-4b-uncensored"
MODEL_CREATED = 1700000000  # fixed timestamp

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

# ── OpenAI-format error handler ───────────────────────────────────────────────
def openai_error(
    message: str,
    status: int = 400,
    error_type: str = "invalid_request_error",
    param: Optional[str] = None,
    code: Optional[str] = None,
) -> JSONResponse:
    return JSONResponse(
        status_code=status,
        content={
            "error": {
                "message": message,
                "type": error_type,
                "param": param,
                "code": code,
            }
        },
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return openai_error(exc.detail, exc.status_code)

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    return openai_error(str(exc), 500, "internal_server_error")

# ── Schemas ───────────────────────────────────────────────────────────────────
class Message(BaseModel):
    role: str
    content: str
    name: Optional[str] = None

class ChatCompletionRequest(BaseModel):
    model: Optional[str] = MODEL_ID
    messages: List[Message]
    max_tokens: Optional[int] = Field(default=256, ge=1, le=1024)
    temperature: Optional[float] = Field(default=0.7, ge=0.0, le=2.0)
    top_p: Optional[float] = Field(default=0.95, ge=0.0, le=1.0)
    frequency_penalty: Optional[float] = Field(default=0.0, ge=-2.0, le=2.0)
    presence_penalty: Optional[float] = Field(default=0.0, ge=-2.0, le=2.0)
    stop: Optional[Union[str, List[str]]] = None
    stream: Optional[bool] = False
    n: Optional[int] = Field(default=1, ge=1, le=1)  # only 1 supported
    user: Optional[str] = None
    seed: Optional[int] = None
    logprobs: Optional[bool] = None
    top_logprobs: Optional[int] = None
    logit_bias: Optional[Dict[str, float]] = None
    response_format: Optional[Dict[str, str]] = None

    @field_validator("messages")
    @classmethod
    def messages_not_empty(cls, v):
        if not v:
            raise ValueError("messages must not be empty")
        return v

class CompletionRequest(BaseModel):
    model: Optional[str] = MODEL_ID
    prompt: Union[str, List[str]]
    max_tokens: Optional[int] = Field(default=256, ge=1, le=1024)
    temperature: Optional[float] = Field(default=0.7, ge=0.0, le=2.0)
    top_p: Optional[float] = Field(default=0.95, ge=0.0, le=1.0)
    frequency_penalty: Optional[float] = Field(default=0.0, ge=-2.0, le=2.0)
    presence_penalty: Optional[float] = Field(default=0.0, ge=-2.0, le=2.0)
    stop: Optional[Union[str, List[str]]] = None
    stream: Optional[bool] = False
    n: Optional[int] = Field(default=1, ge=1, le=1)
    user: Optional[str] = None
    seed: Optional[int] = None
    logprobs: Optional[int] = None
    echo: Optional[bool] = False
    suffix: Optional[str] = None
    best_of: Optional[int] = 1

# ── Helpers ───────────────────────────────────────────────────────────────────
def strip_think(text: str) -> str:
    """Remove <think>...</think> blocks Qwen3 emits, including unclosed ones."""
    # Remove complete blocks
    text = re.sub(r"<think>[\s\S]*?</think>", "", text)
    # Remove unclosed block (model hit max_tokens mid-think)
    text = re.sub(r"<think>[\s\S]*", "", text)
    return text.strip()

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
        elif msg.role == "tool":
            prompt += f"<|im_start|>tool\n{msg.content}<|im_end|>\n"
    prompt += "<|im_start|>assistant\n"
    return prompt

def finish_reason(output: dict) -> str:
    """Map llama.cpp finish reason to OpenAI finish reason."""
    raw = output["choices"][0].get("finish_reason", "stop")
    if raw == "length":
        return "length"
    return "stop"

def model_card() -> dict:
    return {
        "id": MODEL_ID,
        "object": "model",
        "created": MODEL_CREATED,
        "owned_by": "user",
        "permission": [],
        "root": MODEL_ID,
        "parent": None,
    }

# ── SSE streaming helpers ─────────────────────────────────────────────────────
def stream_chat(req: ChatCompletionRequest, prompt: str, stop_tokens: list) -> Iterator[str]:
    """Yield SSE chunks for /v1/chat/completions?stream=true."""
    cmpl_id = f"chatcmpl-{uuid.uuid4().hex}"
    created = int(time.time())

    # opening chunk with role
    chunk = {
        "id": cmpl_id,
        "object": "chat.completion.chunk",
        "created": created,
        "model": req.model,
        "choices": [{"index": 0, "delta": {"role": "assistant", "content": ""}, "finish_reason": None}],
    }
    yield f"data: {json.dumps(chunk)}\n\n"

    buffer = ""
    for token in llm(
        prompt,
        max_tokens=req.max_tokens,
        temperature=req.temperature,
        top_p=req.top_p,
        frequency_penalty=req.frequency_penalty,
        presence_penalty=req.presence_penalty,
        stop=stop_tokens,
        stream=True,
    ):
        text = token["choices"][0].get("text", "")
        buffer += text
        # stream tokens as they arrive (skip think blocks on-the-fly)
        if "<think>" in buffer:
            continue
        if "</think>" in buffer:
            buffer = re.sub(r"<think>.*?</think>", "", buffer, flags=re.DOTALL)
        chunk = {
            "id": cmpl_id,
            "object": "chat.completion.chunk",
            "created": created,
            "model": req.model,
            "choices": [{"index": 0, "delta": {"content": buffer}, "finish_reason": None}],
        }
        yield f"data: {json.dumps(chunk)}\n\n"
        buffer = ""

    # closing chunk
    chunk = {
        "id": cmpl_id,
        "object": "chat.completion.chunk",
        "created": created,
        "model": req.model,
        "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}],
    }
    yield f"data: {json.dumps(chunk)}\n\n"
    yield "data: [DONE]\n\n"

def stream_completion(req: CompletionRequest, prompt: str, stop_tokens: list) -> Iterator[str]:
    """Yield SSE chunks for /v1/completions?stream=true."""
    cmpl_id = f"cmpl-{uuid.uuid4().hex}"
    created = int(time.time())

    for token in llm(
        prompt,
        max_tokens=req.max_tokens,
        temperature=req.temperature,
        top_p=req.top_p,
        frequency_penalty=req.frequency_penalty,
        presence_penalty=req.presence_penalty,
        stop=stop_tokens,
        stream=True,
    ):
        text = token["choices"][0].get("text", "")
        chunk = {
            "id": cmpl_id,
            "object": "text_completion",
            "created": created,
            "model": req.model,
            "choices": [{"text": text, "index": 0, "logprobs": None, "finish_reason": None}],
        }
        yield f"data: {json.dumps(chunk)}\n\n"

    chunk = {
        "id": cmpl_id,
        "object": "text_completion",
        "created": created,
        "model": req.model,
        "choices": [{"text": "", "index": 0, "logprobs": None, "finish_reason": "stop"}],
    }
    yield f"data: {json.dumps(chunk)}\n\n"
    yield "data: [DONE]\n\n"

# ── Routes ────────────────────────────────────────────────────────────────────
@app.get("/")
def root():
    return {"status": "ok", "model": MODEL_ID, "docs": "/docs"}

@app.get("/v1/models")
def list_models():
    return {"object": "list", "data": [model_card()]}

@app.get("/v1/models/{model_id}")
def get_model(model_id: str):
    if model_id != MODEL_ID:
        return openai_error(f"Model '{model_id}' not found.", 404, "invalid_request_error")
    return model_card()

@app.post("/v1/chat/completions")
def chat_completions(req: ChatCompletionRequest):
    prompt = build_prompt(req.messages)
    stop_tokens = req.stop or ["<|im_end|>", "<|endoftext|>"]
    if isinstance(stop_tokens, str):
        stop_tokens = [stop_tokens]

    # ── Streaming ─────────────────────────────────────────────────────────────
    if req.stream:
        return StreamingResponse(
            stream_chat(req, prompt, stop_tokens),
            media_type="text/event-stream",
            headers={"X-Accel-Buffering": "no", "Cache-Control": "no-cache"},
        )

    # ── Non-streaming ─────────────────────────────────────────────────────────
    output = llm(
        prompt,
        max_tokens=req.max_tokens,
        temperature=req.temperature,
        top_p=req.top_p,
        frequency_penalty=req.frequency_penalty,
        presence_penalty=req.presence_penalty,
        stop=stop_tokens,
    )

    text           = strip_think(output["choices"][0]["text"].strip())
    reason         = finish_reason(output)
    prompt_tokens  = output["usage"]["prompt_tokens"]
    completion_tok = output["usage"]["completion_tokens"]

    return {
        "id": f"chatcmpl-{uuid.uuid4().hex}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": req.model,
        "system_fingerprint": f"fp_{uuid.uuid4().hex[:8]}",
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": text},
                "logprobs": None,
                "finish_reason": reason,
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
    prompt = req.prompt if isinstance(req.prompt, str) else req.prompt[0]
    stop_tokens = req.stop or ["<|im_end|>", "<|endoftext|>"]
    if isinstance(stop_tokens, str):
        stop_tokens = [stop_tokens]

    # ── Streaming ─────────────────────────────────────────────────────────────
    if req.stream:
        return StreamingResponse(
            stream_completion(req, prompt, stop_tokens),
            media_type="text/event-stream",
            headers={"X-Accel-Buffering": "no", "Cache-Control": "no-cache"},
        )

    # ── Non-streaming ─────────────────────────────────────────────────────────
    output = llm(
        prompt,
        max_tokens=req.max_tokens,
        temperature=req.temperature,
        top_p=req.top_p,
        frequency_penalty=req.frequency_penalty,
        presence_penalty=req.presence_penalty,
        stop=stop_tokens,
    )

    text           = strip_think(output["choices"][0]["text"])
    reason         = finish_reason(output)
    prompt_tokens  = output["usage"]["prompt_tokens"]
    completion_tok = output["usage"]["completion_tokens"]

    return {
        "id": f"cmpl-{uuid.uuid4().hex}",
        "object": "text_completion",
        "created": int(time.time()),
        "model": req.model,
        "system_fingerprint": f"fp_{uuid.uuid4().hex[:8]}",
        "choices": [
            {
                "text": text,
                "index": 0,
                "logprobs": None,
                "finish_reason": reason,
            }
        ],
        "usage": {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tok,
            "total_tokens": prompt_tokens + completion_tok,
        },
    }

@app.post("/v1/embeddings")
def embeddings():
    return openai_error(
        "Embeddings are not supported by this model.",
        501,
        "not_supported_error",
    )

# ── Entry ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=HOST, port=PORT)
