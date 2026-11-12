"""Single-question terminal interface for the chatbot."""

import sys

from .llm import ask_llm


def main() -> int:
	question = input("You: ").strip()
	if not question:
		print("Enter a question before sending it.", file=sys.stderr)
		return 1

	try:
		answer = ask_llm(question)
	except ValueError as error:
		print(f"Error: {error}", file=sys.stderr)
		return 1

	print(f"Assistant: {answer}")
	return 0