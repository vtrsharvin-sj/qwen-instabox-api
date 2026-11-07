from huggingface_hub import hf_hub_download
import os

os.makedirs("/data/home/models", exist_ok=True)
path = hf_hub_download(
    repo_id="InterpreticAI/Qwen3.5-4B-Uncensored-v2-GGUF",
    filename="Qwen3.5-4B-Uncensored-v2-Q4_K_M.gguf",
    local_dir="/data/home/models"
)
print(f"Downloaded to: {path}")
