"""
Minimal OpenAI-compatible usage example.
Replace BASE_URL with your own Instabox tunnel URL.
"""

from openai import OpenAI

BASE_URL = "https://qwen-api.vtrsharvin.workers.dev/v1"
API_KEY  = "sharvin"

client = OpenAI(base_url=BASE_URL, api_key=API_KEY)

response = client.chat.completions.create(
    model="qwen3.5-4b-uncensored",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "What is the capital of France?"},
    ],
    max_tokens=200,
    temperature=0.7,
)

print(response.choices[0].message.content)
