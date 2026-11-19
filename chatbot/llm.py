"""LLM integration for the chatbot."""

import os
from collections.abc import Iterator

from openai import OpenAI
from dotenv import load_dotenv
from langchain_core.messages import BaseMessage
from langchain_openai import ChatOpenAI

load_dotenv()


def _get_api_settings() -> tuple[str, str]:
	api_key = os.getenv("LITELLM_API_KEY", "").strip()
	proxy_root = os.getenv("LITELLM_BASE_URL", "").strip().rstrip("/")

	if not api_key:
		raise ValueError("Set LITELLM_API_KEY in .env.")
	if not proxy_root:
		raise ValueError("Set LITELLM_BASE_URL in .env.")
	base_url = proxy_root if proxy_root.endswith("/v1") else f"{proxy_root}/v1"
	return api_key, base_url


def list_available_models() -> list[str]:
	api_key, base_url = _get_api_settings()
	client = OpenAI(api_key=api_key, base_url=base_url)
	return sorted(model.id for model in client.models.list().data)


def _build_chat_model(model: str | None = None) -> ChatOpenAI:
	api_key, base_url = _get_api_settings()
	selected_model = (model or os.getenv("LITELLM_MODEL", "")).strip()
	if not selected_model:
		raise ValueError("Set LITELLM_MODEL in .env.")

	return ChatOpenAI(model=selected_model, api_key=api_key, base_url=base_url)


def ask_llm(messages: list[BaseMessage], model: str | None = None) -> str:
	chat_model = _build_chat_model(model)
	# Send the full history so the model can use previous turns.
	response = chat_model.invoke(messages)
	answer = response.content
	if not isinstance(answer, str) or not answer.strip():
		raise ValueError("The model returned an empty response.")
	return answer.strip()


def stream_llm(messages: list[BaseMessage], model: str | None = None) -> Iterator[str]:
	# Build the model eagerly so missing config raises before streaming starts.
	chat_model = _build_chat_model(model)

	def _tokens() -> Iterator[str]:
		for chunk in chat_model.stream(messages):
			content = chunk.content
			if isinstance(content, str) and content:
				yield content

	return _tokens()