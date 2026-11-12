import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

api_key = os.getenv("LITELLM_API_KEY")
proxy_root = os.getenv("LITELLM_BASE_URL", "").rstrip("/")

if not api_key:
    raise RuntimeError("Set LITELLM_API_KEY in .env.")
if not proxy_root:
    raise RuntimeError("Set LITELLM_BASE_URL in .env.")

api_base = proxy_root if proxy_root.endswith("/v1") else f"{proxy_root}/v1"
client = OpenAI(api_key=api_key, base_url=api_base)

MODELS = {
    "text": "gpt-5.6-luna",
    "embedding": "text-embedding-3-small",
    "image": "gpt-image-2",
}

print(f"Connected to {api_base} (API key loaded but hidden).")

# Confirm which models this virtual key can currently see.
available_models = sorted(model.id for model in client.models.list().data)
print(*available_models, sep="\n")

response = client.responses.create(
    model=MODELS["text"],
    instructions="You are a concise assistant for an AI engineering training course.",
    input="Explain cosine similarity in two short sentences.",
)

print(response.output_text)
