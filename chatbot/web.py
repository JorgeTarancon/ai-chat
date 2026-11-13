"""Streamlit chat interface backed by the local FastAPI service."""

import os

import httpx
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

API_URL = os.getenv("CHATBOT_API_URL", "http://127.0.0.1:8000").rstrip("/")
MODEL = os.getenv("LITELLM_MODEL", "Model not configured")

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
	}
	[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] p { line-height: 1.65; }
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


def request_answer(messages: list[dict[str, str]]) -> str:
	response = httpx.post(
		f"{API_URL}/chat",
		json={"messages": messages},
		timeout=120,
	)
	response.raise_for_status()
	payload = response.json()
	answer = payload.get("answer") if isinstance(payload, dict) else None
	if not isinstance(answer, str) or not answer.strip():
		raise ValueError("The chatbot API returned an invalid response.")
	return answer.strip()


if "messages" not in st.session_state:
	st.session_state.messages = []
if "api_status" not in st.session_state:
	st.session_state.api_status = None

with st.sidebar:
	st.markdown("<div class='eyebrow'>AI CHAT / WORKSPACE</div>", unsafe_allow_html=True)
	st.markdown("## Session")
	st.caption("MODEL")
	st.code(MODEL, language=None)
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

for message in st.session_state.messages:
	with st.chat_message(message["role"]):
		st.markdown(message["content"])

if prompt := st.chat_input("Write a message..."):
	new_message = {"role": "user", "content": prompt.strip()}
	if new_message["content"]:
		st.session_state.messages.append(new_message)
		with st.chat_message("user"):
			st.markdown(new_message["content"])

		with st.chat_message("assistant"):
			with st.spinner("Thinking..."):
				try:
					answer = request_answer(st.session_state.messages)
				except httpx.HTTPStatusError as error:
					st.session_state.messages.pop()
					st.error(f"API error: {get_error_detail(error)}")
				except (httpx.RequestError, ValueError) as error:
					st.session_state.messages.pop()
					st.error(f"Could not reach the chatbot API: {error}")
				else:
					st.session_state.messages.append({"role": "assistant", "content": answer})
					st.markdown(answer)