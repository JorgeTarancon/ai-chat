"""LLM integration for the chatbot."""

import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()


def ask_llm(question: str) -> str:
	api_key = os.getenv("LITELLM_API_KEY", "").strip()
	proxy_root = os.getenv("LITELLM_BASE_URL", "").strip().rstrip("/")
	model = os.getenv("LITELLM_MODEL", "").strip()

	if not api_key:
		raise ValueError("Set LITELLM_API_KEY in .env.")
	if not proxy_root:
		raise ValueError("Set LITELLM_BASE_URL in .env.")
	if not model:
		raise ValueError("Set LITELLM_MODEL in .env.")

	base_url = proxy_root if proxy_root.endswith("/v1") else f"{proxy_root}/v1"
	client = OpenAI(api_key=api_key, base_url=base_url)
	response = client.chat.completions.create(
		model=model,
		messages=[{"role": "user", "content": question}],
	)
	answer = response.choices[0].message.content
	if not answer:
		raise ValueError("The model returned an empty response.")
	return answer.strip()