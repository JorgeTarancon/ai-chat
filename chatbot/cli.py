"""Terminal chat interface for the chatbot."""

import sys

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage

from .llm import ask_llm


def main() -> int:
	history: list[BaseMessage] = []
	print("Chat started. Type /exit to quit.")

	while True:
		try:
			question = input("You: ").strip()
		except EOFError:
			print()
			return 0

		if question.casefold() in {"/exit", "/quit"}:
			return 0
		if not question:
			continue

		# Keep each exchange in memory so later questions have context.
		history.append(HumanMessage(content=question))
		try:
			answer = ask_llm(history)
		except ValueError as error:
			history.pop()
			print(f"Error: {error}", file=sys.stderr)
			return 1

		history.append(AIMessage(content=answer))
		print(f"Assistant: {answer}")