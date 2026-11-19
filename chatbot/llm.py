"""LLM integration for the chatbot."""

import base64
import os
from collections.abc import Iterator

import httpx
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


# Fallback when the proxy does not expose /model/info.
IMAGE_MODEL_HINTS = ("dall-e", "gpt-image", "imagen", "flux", "stable-diffusion", "sdxl")


def list_image_models() -> list[str]:
	api_key, base_url = _get_api_settings()
	available = list_available_models()
	try:
		response = httpx.get(
			f"{base_url.removesuffix('/v1')}/model/info",
			headers={"Authorization": f"Bearer {api_key}"},
			timeout=10,
		)
		response.raise_for_status()
		entries = response.json()["data"]
		names = {
			entry["model_name"]
			for entry in entries
			if (entry.get("model_info") or {}).get("mode") == "image_generation"
		}
		return [name for name in available if name in names]
	except (httpx.HTTPError, ValueError, KeyError, TypeError):
		return [name for name in available if any(hint in name.lower() for hint in IMAGE_MODEL_HINTS)]


def generate_image(prompt: str, model: str) -> str:
	"""Return the generated image as a base64 string."""
	api_key, base_url = _get_api_settings()
	client = OpenAI(api_key=api_key, base_url=base_url)
	result = client.images.generate(model=model, prompt=prompt, n=1)
	if not result.data:
		raise ValueError("The model returned no image.")
	image = result.data[0]
	if image.b64_json:
		return image.b64_json
	if image.url:
		# dall-e style models return a URL instead of inline data.
		download = httpx.get(image.url, timeout=60)
		download.raise_for_status()
		return base64.b64encode(download.content).decode("ascii")
	raise ValueError("The model returned no image.")


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