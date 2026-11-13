"""LLM integration for the chatbot."""

import os

from dotenv import load_dotenv
from langchain_core.messages import BaseMessage
from langchain_openai import ChatOpenAI

load_dotenv()


def ask_llm(messages: list[BaseMessage]) -> str:
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
	chat_model = ChatOpenAI(model=model, api_key=api_key, base_url=base_url)
	# Send the full history so the model can use previous turns.
	response = chat_model.invoke(messages)
	answer = response.content
	if not isinstance(answer, str) or not answer.strip():
		raise ValueError("The model returned an empty response.")
	return answer.strip()