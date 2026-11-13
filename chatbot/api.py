"""FastAPI application that exposes the chatbot model."""

from typing import Literal

from fastapi import FastAPI, HTTPException
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from pydantic import BaseModel, Field

from .llm import ask_llm

app = FastAPI(title="AI Chat API")


class ChatMessage(BaseModel):
	role: Literal["user", "assistant"]
	content: str = Field(min_length=1)


class ChatRequest(BaseModel):
	messages: list[ChatMessage] = Field(min_length=1)


class ChatResponse(BaseModel):
	answer: str


@app.get("/health")
def health() -> dict[str, str]:
	return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
	history: list[BaseMessage] = []
	for message in request.messages:
		if message.role == "user":
			history.append(HumanMessage(content=message.content))
		else:
			history.append(AIMessage(content=message.content))

	try:
		answer = ask_llm(history)
	except ValueError as error:
		raise HTTPException(status_code=503, detail=str(error)) from error

	return ChatResponse(answer=answer)