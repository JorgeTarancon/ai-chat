"""Terminal chat interface for the chatbot."""

import os
import sys

import httpx
from dotenv import load_dotenv

load_dotenv()

API_URL = os.getenv("CHATBOT_API_URL", "http://127.0.0.1:8000").rstrip("/")


def main() -> int:
	history: list[dict[str, str]] = []
	print("Chat started. Type /exit to quit.")

	with httpx.Client(base_url=API_URL, timeout=120) as client:
		while True:
			try:
				question = input("You: ").strip()
			except EOFError:
				print()
				return 0

			if question.casefold() in {"/exit", "/quit"}:
				return 0
			elif question.casefold() == "/health":
				try:
					response = client.get("/health")
					response.raise_for_status()
					print("API is healthy.")
				except httpx.HTTPError as error:
					print(f"API health check failed: {error}", file=sys.stderr)
					return 1
				continue
			if not question:
				continue

			# Keep each exchange in memory so later questions have context.
			history.append({"role": "user", "content": question})
			try:
				response = client.post("/chat", json={"messages": history})
				response.raise_for_status()
				answer = response.json()["answer"]
			except httpx.HTTPStatusError as error:
				history.pop()
				try:
					payload = error.response.json()
					detail = payload.get("detail", str(error)) if isinstance(payload, dict) else str(error)
				except ValueError:
					detail = str(error)
				print(f"API error: {detail}", file=sys.stderr)
				return 1
			except (httpx.RequestError, KeyError, ValueError) as error:
				history.pop()
				print(f"Could not get a response from the chatbot API: {error}", file=sys.stderr)
				return 1

			history.append({"role": "assistant", "content": answer})
			print(f"Assistant: {answer}")