"""Streamlit chat interface backed by the local FastAPI service."""

import base64
import json
import os

import httpx
import streamlit as st
from dotenv import load_dotenv

from chatbot.config import MAX_IMAGE_BYTES, MAX_IMAGES_PER_MESSAGE

load_dotenv()

API_URL = os.getenv("CHATBOT_API_URL", "http://127.0.0.1:8000").rstrip("/")
IMAGE_TYPES = ["png", "jpg", "jpeg", "webp", "gif"]
MIME_BY_EXTENSION = {
	"png": "image/png",
	"jpg": "image/jpeg",
	"jpeg": "image/jpeg",
	"webp": "image/webp",
	"gif": "image/gif",
}

st.set_page_config(page_title="AI Chat", page_icon=":material/forum:", layout="wide")
st.markdown(
	"""
	<style>
	@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Manrope:wght@400;500;600;700;800&display=swap');
	:root {
		--ink: #1c2925;
		--muted: #718078;
		--paper: #f3f5ef;
		--line: #dce3db;
		--forest: #203b34;
		--lime: #d8f56a;
		--coral: #e77a5b;
	}
	:root { color-scheme: light; }
	html, body, [class*="css"] {
		font-family: 'Manrope', sans-serif;
		color: var(--ink);
	}
	[data-testid="stAppViewContainer"] { background: var(--paper); }
	[data-testid="stAppViewContainer"] h1,
	[data-testid="stAppViewContainer"] h1 * { color: var(--ink) !important; }
	[data-testid="stHeader"] { background: transparent; }
	button[aria-controls="stSidebar"][aria-expanded="false"] {
		color: #fff !important;
		background: var(--forest) !important;
		border: 1px solid #416458 !important;
		border-radius: 6px !important;
	}
	button[aria-controls="stSidebar"][aria-expanded="false"] * {
		color: #fff !important;
	}
	button[aria-controls="stSidebar"][aria-expanded="false"] svg {
		fill: #fff !important;
	}
	button[aria-controls="stSidebar"][aria-expanded="false"]:hover {
		background: #2b4c42 !important;
	}
	[data-testid="stBottom"], [data-testid="stBottomBlockContainer"] {
		background: var(--paper) !important;
	}
	[data-testid="stSidebar"] { background: var(--forest); }
	[data-testid="stSidebar"] * { color: #f3f5ef; }
	[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] code {
		color: var(--lime);
		background: #2b4c42;
		border: 1px solid #416458;
	}
	[data-testid="stSidebar"] .stButton button {
		color: var(--ink);
		background: var(--lime);
		border: 0;
		font-weight: 700;
	}
	[data-testid="stSidebar"] .stButton button * { color: var(--ink) !important; }
	[data-testid="stSidebar"] .stButton button:hover { background: #e4ff91; }
	.main .block-container { max-width: 900px; padding-top: 2.4rem; padding-bottom: 2rem; }
	.eyebrow {
		font: 500 0.72rem 'DM Mono', monospace;
		letter-spacing: 0.08em;
		color: #557267;
		text-transform: uppercase;
		margin-bottom: 0.5rem;
	}
	h1 { font-weight: 800 !important; letter-spacing: 0 !important; }
	[data-testid="stChatMessage"] {
		background: #fff;
		border: 1px solid var(--line);
		border-radius: 10px;
		padding: 0.85rem 1rem;
		margin: 0.65rem 0;
		color: var(--ink);
	}
	[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {
		background: var(--forest);
		border-color: var(--forest);
		color: #fff;
	}
	[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] p,
	[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] li,
	[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] ol,
	[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] ul,
	[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] span,
	[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] strong,
	[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] em {
		color: var(--ink) !important;
		line-height: 1.65;
	}
	[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] li::marker {
		color: var(--ink) !important;
	}
	[data-testid="stChatMessage"] [data-testid="stCaptionContainer"],
	[data-testid="stChatMessage"] [data-testid="stCaptionContainer"] p {
		color: #64746b !important;
	}
	/* Keep streamed text fully opaque instead of Streamlit's fade-in while it arrives. */
	[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"],
	[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] * {
		opacity: 1 !important;
	}
	[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) [data-testid="stMarkdownContainer"] p,
	[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) [data-testid="stMarkdownContainer"] li,
	[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) [data-testid="stMarkdownContainer"] span,
	[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) [data-testid="stMarkdownContainer"] strong,
	[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) [data-testid="stMarkdownContainer"] em {
		color: #fff !important;
	}
	[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) [data-testid="stMarkdownContainer"] li::marker {
		color: #fff !important;
	}
	[data-testid="stChatMessage"] [data-testid="stAlert"],
	[data-testid="stChatMessage"] [role="alert"] {
		background: #fde8e7 !important;
		border-color: #e4a29e !important;
		color: #681f1c !important;
	}
	[data-testid="stChatMessage"] [data-testid="stAlert"] *,
	[data-testid="stChatMessage"] [role="alert"] * {
		color: #681f1c !important;
	}
	[data-testid="stChatInput"] > div {
		background: #fff !important;
		border: 1px solid #bdc9bf !important;
		border-radius: 10px;
	}
	[data-testid="stChatInput"] textarea {
		font-family: 'Manrope', sans-serif;
		color: var(--ink) !important;
		background: #fff !important;
	}
	[data-testid="stChatInput"] textarea::placeholder {
		color: #64746b !important;
		opacity: 1;
	}
	[data-testid="stChatInput"] button { color: var(--ink) !important; }
	code, pre { font-family: 'DM Mono', monospace !important; }
	@media (max-width: 700px) {
		.main .block-container { padding: 1.2rem 1rem 1rem; }
	}
	</style>
	""",
	unsafe_allow_html=True,
)


def get_error_detail(error: httpx.HTTPStatusError) -> str:
	try:
		payload = error.response.json()
		if isinstance(payload, dict) and payload.get("detail"):
			return str(payload["detail"])
	except ValueError:
		pass
	return error.response.text or str(error)


@st.cache_data(ttl=300)
def get_available_models() -> list[str]:
	response = httpx.get(f"{API_URL}/models", timeout=10)
	response.raise_for_status()
	models = response.json()
	if not isinstance(models, list) or not all(isinstance(model, str) for model in models):
		raise ValueError("The API returned an invalid model list.")
	return models


@st.cache_data(ttl=300)
def get_image_models() -> list[str]:
	try:
		response = httpx.get(f"{API_URL}/models/image", timeout=15)
		response.raise_for_status()
		return [model for model in response.json() if isinstance(model, str)]
	except (httpx.HTTPError, ValueError):
		return []


def generate_image(prompt: str, model: str) -> str:
	response = httpx.post(
		f"{API_URL}/images/generate",
		json={"prompt": prompt, "model": model},
		timeout=180,
	)
	response.raise_for_status()
	return response.json()["data"]


def stream_answer(messages: list[dict], model: str, usage: dict):
	# Generated images stay local; the chat API only accepts images on user turns.
	payload = [{"role": m["role"], "content": m["content"], "images": m.get("images", []) if m["role"] == "user" else []} for m in messages]
	with httpx.stream(
		"POST",
		f"{API_URL}/chat/stream",
		json={"messages": payload, "model": model},
		timeout=120,
	) as response:
		try:
			response.raise_for_status()
		except httpx.HTTPStatusError as error:
			# Buffer the body so get_error_detail can read the JSON detail.
			error.response.read()
			raise
		for line in response.iter_lines():
			if not line:
				continue
			event = json.loads(line)
			if event.get("type") == "content":
				yield event["content"]
			elif event.get("type") == "usage":
				usage.update(event)


if "messages" not in st.session_state:
	st.session_state.messages = []
if "api_status" not in st.session_state:
	st.session_state.api_status = None

with st.sidebar:
	st.markdown("<div class='eyebrow'>AI CHAT / WORKSPACE</div>", unsafe_allow_html=True)
	st.markdown("## Session")
	try:
		available_models = get_available_models()
	except (httpx.HTTPError, ValueError) as error:
		available_models = []
		st.error(f"Could not load models: {error}")

	if available_models:
		selected_model = st.selectbox("Model", available_models)
		is_image_model = selected_model in get_image_models()
		if is_image_model:
			st.caption("Image generation model: your messages are used as prompts.")
	else:
		selected_model = None
		is_image_model = False
	st.caption("API ENDPOINT")
	st.code(API_URL, language=None)

	if st.button("New conversation", icon=":material/add_comment:", use_container_width=True):
		st.session_state.messages = []
		st.rerun()

	if st.button("Check API", icon=":material/sync:", use_container_width=True):
		try:
			health = httpx.get(f"{API_URL}/health", timeout=5)
			health.raise_for_status()
			st.session_state.api_status = "online"
		except httpx.HTTPError:
			st.session_state.api_status = "offline"

	if st.session_state.api_status == "online":
		st.success("API online")
	elif st.session_state.api_status == "offline":
		st.error("API unavailable")

st.markdown("<div class='eyebrow'>CONVERSATION / 01</div>", unsafe_allow_html=True)
st.title("AI Chat")

def render_message(message: dict) -> None:
	for image in message.get("images", []):
		st.image(base64.b64decode(image["data"]), width=240)
	if message["content"]:
		st.markdown(message["content"])
	if message["role"] == "assistant" and "total_tokens" in message:
		call_tokens = message["total_tokens"]
		chat_tokens = message.get("chat_tokens")
		call_label = f"{call_tokens:,}" if call_tokens is not None else "unavailable"
		chat_label = f"{chat_tokens:,}" if chat_tokens is not None else "unavailable"
		st.caption(f"This call: {call_label} tokens · Chat total: {chat_label} tokens")


def encode_images(files: list) -> list[dict[str, str]]:
	images = []
	for file in files:
		extension = file.name.rsplit(".", 1)[-1].lower()
		mime_type = MIME_BY_EXTENSION.get(extension)
		if mime_type is None:
			raise ValueError(f"Unsupported image type: {file.name}")
		raw = file.getvalue()
		if len(raw) > MAX_IMAGE_BYTES:
			raise ValueError(f"{file.name} exceeds the {MAX_IMAGE_BYTES // (1024 * 1024)} MB limit.")
		images.append({"data": base64.b64encode(raw).decode("ascii"), "mime_type": mime_type})
	return images


for message in st.session_state.messages:
	with st.chat_message(message["role"]):
		render_message(message)

if submission := st.chat_input(
	"Write a message or attach images...",
	accept_file="multiple",
	file_type=IMAGE_TYPES,
	disabled=selected_model is None,
):
	text = submission.text.strip()
	files = list(submission.files)
	new_message = None
	if len(files) > MAX_IMAGES_PER_MESSAGE:
		st.error(f"You can attach up to {MAX_IMAGES_PER_MESSAGE} images per message.")
	elif text or files:
		try:
			new_message = {"role": "user", "content": text, "images": encode_images(files)}
		except ValueError as error:
			st.error(str(error))

	if new_message:
		st.session_state.messages.append(new_message)
		with st.chat_message("user"):
			render_message(new_message)

		if is_image_model:
			with st.chat_message("assistant"):
				if not text:
					st.session_state.messages.pop()
					st.error("Write a text prompt to generate an image.")
				else:
					with st.spinner("Generating image..."):
						try:
							image_data = generate_image(text, selected_model)
						except httpx.HTTPStatusError as error:
							st.session_state.messages.pop()
							st.error(f"API error: {get_error_detail(error)}")
						except (httpx.RequestError, KeyError, ValueError) as error:
							st.session_state.messages.pop()
							st.error(f"Could not generate the image: {error}")
						else:
							result = {
								"role": "assistant",
								"content": f"[Image generated from prompt: {text}]",
								"images": [{"data": image_data, "mime_type": "image/png"}],
							}
							st.session_state.messages.append(result)
							st.image(base64.b64decode(image_data))
		else:
			with st.chat_message("assistant"):
				with st.spinner("Thinking..."):
					usage = {}
					try:
						answer = st.write_stream(stream_answer(st.session_state.messages, selected_model, usage))
					except httpx.HTTPStatusError as error:
						st.session_state.messages.pop()
						st.error(f"API error: {get_error_detail(error)}")
					except (httpx.RequestError, ValueError) as error:
						st.session_state.messages.pop()
						st.error(f"Could not reach the chatbot API: {error}")
					else:
						answer = answer.strip() if isinstance(answer, str) else "".join(answer).strip()
						if answer:
							previous_calls = [
								message.get("total_tokens")
								for message in st.session_state.messages
								if message["role"] == "assistant" and "total_tokens" in message
							]
							call_tokens = usage.get("total_tokens")
							chat_tokens = (
								sum(previous_calls) + call_tokens
								if call_tokens is not None and all(tokens is not None for tokens in previous_calls)
								else None
							)
							result = {
								"role": "assistant",
								"content": answer,
								"total_tokens": call_tokens,
								"chat_tokens": chat_tokens,
							}
							st.session_state.messages.append(result)
							call_label = f"{call_tokens:,}" if call_tokens is not None else "unavailable"
							chat_label = f"{chat_tokens:,}" if chat_tokens is not None else "unavailable"
							st.caption(f"This call: {call_label} tokens · Chat total: {chat_label} tokens")
						else:
							st.session_state.messages.pop()
							st.error("The chatbot API returned an invalid response.")