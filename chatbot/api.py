"""FastAPI application that exposes the chatbot model."""

import base64
import binascii
from typing import Literal

from fastapi import FastAPI, HTTPException
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from pydantic import BaseModel, Field, field_validator, model_validator

from .config import MAX_IMAGE_BYTES, MAX_IMAGES_PER_MESSAGE
from .llm import ask_llm

app = FastAPI(title="AI Chat API")

# Base64 inflates size by 4/3; this bounds the string before decoding it.
MAX_IMAGE_BASE64_CHARS = MAX_IMAGE_BYTES * 4 // 3 + 4


class ImagePayload(BaseModel):
	data: str = Field(min_length=1, max_length=MAX_IMAGE_BASE64_CHARS)
	mime_type: Literal["image/png", "image/jpeg", "image/webp", "image/gif"]

	@field_validator("data")
	@classmethod
	def check_base64(cls, value: str) -> str:
		try:
			decoded = base64.b64decode(value, validate=True)
		except (binascii.Error, ValueError) as error:
			raise ValueError("Image data is not valid base64.") from error
		if len(decoded) > MAX_IMAGE_BYTES:
			raise ValueError(f"Image exceeds the {MAX_IMAGE_BYTES // (1024 * 1024)} MB limit.")
		return value


class ChatMessage(BaseModel):
	role: Literal["user", "assistant"]
	content: str = ""
	images: list[ImagePayload] = Field(default_factory=list, max_length=MAX_IMAGES_PER_MESSAGE)

	@model_validator(mode="after")
	def check_not_empty(self) -> "ChatMessage":
		if not self.content.strip() and not self.images:
			raise ValueError("A message needs text or at least one image.")
		if self.role == "assistant" and self.images:
			raise ValueError("Assistant messages cannot include images.")
		return self


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
		if message.role == "user" and message.images:
			blocks: list[str | dict] = []
			if message.content.strip():
				blocks.append({"type": "text", "text": message.content})
			for image in message.images:
				url = f"data:{image.mime_type};base64,{image.data}"
				blocks.append({"type": "image_url", "image_url": {"url": url}})
			history.append(HumanMessage(content=blocks))
		elif message.role == "user":
			history.append(HumanMessage(content=message.content))
		else:
			history.append(AIMessage(content=message.content))

	try:
		answer = ask_llm(history)
	except ValueError as error:
		raise HTTPException(status_code=503, detail=str(error)) from error

	return ChatResponse(answer=answer)