# ai-chat

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
|   |-- cli.py       # Terminal interface
|   `-- llm.py       # LangChain integration with LiteLLM
|-- requirements.txt
|-- .env.example
`-- README.md
```

The chatbot accepts one question in the terminal and prints one LLM response. 

Run the chatbot from the project directory:

```
python -m chatbot
```
