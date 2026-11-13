# AI-chat

## Setup

Requires Python 3.10 or later.

From the project directory, install the dependencies:

```
python -m pip install -r requirements.txt
```

Copy `.env.example` to `.env` and set `LITELLM_BASE_URL`, `LITELLM_API_KEY` and `LITELLM_MODEL`. Do not share this file or commit it to Git.

## Project layout

```text
ai-chat/
|-- chatbot/
|   |-- __init__.py
|   |-- __main__.py  # Enables python -m chatbot
|   |-- api.py       # FastAPI application
|   |-- cli.py       # Terminal interface
|   |-- web.py       # Streamlit web interface
|   `-- llm.py       # LangChain integration with LiteLLM
|-- requirements.txt
|-- .env.example
`-- README.md
```

The chatbot keeps the conversation history in memory while it is running. Type `/exit` or `/quit` to end the chat; the history is discarded when the process exits.

Start the API in one terminal:

```
python -m uvicorn chatbot.api:app --reload
```

Then start the chat client in another terminal:

```
python -m chatbot
```

The API is available at `http://127.0.0.1:8000`; its interactive docs are at `/docs`.

To use the Streamlit web interface, start it in a separate terminal:

```
python -m streamlit run chatbot/web.py
```
