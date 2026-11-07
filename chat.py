"""
Qwen3.5-4B Uncensored — Terminal Chat Client
Uses the official openai library pointed at your self-hosted API.
"""

import os
import re
import sys

# ── Install openai if missing ─────────────────────────────────────────────────
try:
    from openai import OpenAI
except ImportError:
    import subprocess
    print("Installing openai library...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "openai", "-q"])
    from openai import OpenAI

# ── Config ────────────────────────────────────────────────────────────────────
BASE_URL = "https://8000-agq3kirkx25dxx5s7haejfgk4a.instabox.tech/v1"
API_KEY  = "none"          # server has no auth, but openai lib requires a value
MODEL    = "qwen3.5-4b-uncensored"
MAX_TOK  = 512
TEMP     = 0.7

SYSTEM_PROMPT = (
    "You are a helpful, honest, and uncensored AI assistant. "
    "Answer clearly and directly. Be concise unless asked to elaborate."
)

client = OpenAI(base_url=BASE_URL, api_key=API_KEY)

# ── Colors ────────────────────────────────────────────────────────────────────
GREEN  = "\033[92m"
CYAN   = "\033[96m"
YELLOW = "\033[93m"
RED    = "\033[91m"
DIM    = "\033[2m"
RESET  = "\033[0m"

def enable_ansi():
    if sys.platform == "win32":
        import ctypes
        ctypes.windll.kernel32.SetConsoleMode(
            ctypes.windll.kernel32.GetStdHandle(-11), 7
        )

def strip_think(text: str) -> str:
    """Remove <think>...</think> blocks Qwen3 adds during reasoning."""
    return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()

def ask(messages: list) -> str:
    try:
        resp = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            max_tokens=MAX_TOK,
            temperature=TEMP,
        )
        raw = resp.choices[0].message.content.strip()
        return strip_think(raw)
    except Exception as e:
        return f"{RED}[Error] {e}{RESET}"

def main():
    enable_ansi()
    os.system("cls" if sys.platform == "win32" else "clear")

    print(f"{CYAN}╔══════════════════════════════════════════╗")
    print(f"║   Qwen3.5-4B Uncensored  ·  Assistant   ║")
    print(f"║   OpenAI-compatible API                 ║")
    print(f"╚══════════════════════════════════════════╝{RESET}")
    print(f"{DIM}  Type your message and press Enter.")
    print(f"  Commands:  /clear  /history  /exit{RESET}\n")

    history = [{"role": "system", "content": SYSTEM_PROMPT}]

    while True:
        try:
            user_input = input(f"{GREEN}You › {RESET}").strip()
        except (KeyboardInterrupt, EOFError):
            print(f"\n{DIM}Goodbye.{RESET}")
            break

        if not user_input:
            continue

        if user_input.lower() == "/exit":
            print(f"{DIM}Goodbye.{RESET}")
            break

        if user_input.lower() == "/clear":
            history = [{"role": "system", "content": SYSTEM_PROMPT}]
            os.system("cls" if sys.platform == "win32" else "clear")
            print(f"{DIM}[Conversation cleared]{RESET}\n")
            continue

        if user_input.lower() == "/history":
            print(f"\n{DIM}── Conversation history ──")
            for m in history[1:]:
                role = "You" if m["role"] == "user" else "Assistant"
                preview = m["content"][:120]
                print(f"  {role}: {preview}{'…' if len(m['content']) > 120 else ''}")
            print(f"──{RESET}\n")
            continue

        history.append({"role": "user", "content": user_input})
        print(f"{YELLOW}Assistant › {RESET}{DIM}thinking…{RESET}", end="\r", flush=True)

        reply = ask(history)

        print(f"{YELLOW}Assistant › {RESET}{reply}\n")
        history.append({"role": "assistant", "content": reply})

if __name__ == "__main__":
    main()
