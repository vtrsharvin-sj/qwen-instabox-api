from openai import OpenAI

client = OpenAI(
    base_url="https://8000-agq3kirkx25dxx5s7haejfgk4a.instabox.tech/v1",
    api_key="none",
)

response = client.chat.completions.create(
    model="qwen3.5-4b-uncensored",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "What is the capital of France?"},
    ],
)

print(response.choices[0].message.content)
