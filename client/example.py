"""
Minimal OpenAI-compatible usage example.
"""

from openai import OpenAI

client = OpenAI(
    base_url="https://qwen-api.vtrsharvin.workers.dev/v1",
    api_key="sharvin",
)

response = client.chat.completions.create(
    model="qwen3.5-4b-uncensored",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello!"},
    ],
    max_tokens=200,
    temperature=0.7,
)

print(response.choices[0].message.content)
