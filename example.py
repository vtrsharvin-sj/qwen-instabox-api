from openai import OpenAI

client = OpenAI(
    base_url="https://qwen-api.vtrsharvin.workers.dev/v1",
    api_key="sharvin",
    timeout=120,
)

# ── 1. Basic chat ─────────────────────────────────────────────────────────────
print("=== Basic Chat ===")
response = client.chat.completions.create(
    model="qwen3.5-4b-uncensored",
    messages=[
        {"role": "system", "content": "You are a helpful assistant. Be concise."},
        {"role": "user",   "content": "What is the capital of France?"},
    ],
    max_tokens=200,
    temperature=0.7,
)
print(response.choices[0].message.content)
print()

# ── 2. Streaming chat ─────────────────────────────────────────────────────────
print("=== Streaming Chat ===")
stream = client.chat.completions.create(
    model="qwen3.5-4b-uncensored",
    messages=[
        {"role": "system", "content": "You are a helpful assistant. Be concise."},
        {"role": "user",   "content": "Count from 1 to 5, one number per line."},
    ],
    max_tokens=200,
    stream=True,
)
for chunk in stream:
    delta = chunk.choices[0].delta.content
    if delta:
        print(delta, end="", flush=True)
print("\n")

# ── 3. Multi-turn conversation ────────────────────────────────────────────────
print("=== Multi-turn ===")
history = [
    {"role": "system",  "content": "You are a helpful assistant. Be concise."},
    {"role": "user",    "content": "My name is Sharvin."},
]
resp = client.chat.completions.create(
    model="qwen3.5-4b-uncensored",
    messages=history,
    max_tokens=200,
)
reply = resp.choices[0].message.content
print(f"Assistant: {reply}")

history.append({"role": "assistant", "content": reply})
history.append({"role": "user",      "content": "What is my name?"})

resp2 = client.chat.completions.create(
    model="qwen3.5-4b-uncensored",
    messages=history,
    max_tokens=200,
)
print(f"Assistant: {resp2.choices[0].message.content}")
print()

# ── 4. Raw text completion ────────────────────────────────────────────────────
print("=== Text Completion ===")
comp = client.completions.create(
    model="qwen3.5-4b-uncensored",
    prompt="The first man to walk on the moon was",
    max_tokens=30,
    temperature=0.3,
)
print(comp.choices[0].text.strip())
print()

# ── 5. List models ────────────────────────────────────────────────────────────
print("=== Models ===")
models = client.models.list()
for m in models.data:
    print(f"  id={m.id}  owned_by={m.owned_by}")
