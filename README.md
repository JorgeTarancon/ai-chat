# ai-chat

## Setup

Requires Python 3.9 or later.

From the project directory, install the dependencies:

```
python -m pip install -r requirements.txt
```

Copy `.env.example` to `.env` and set `LITELLM_BASE_URL` and `LITELLM_API_KEY`. Do not share this file or commit it to Git.

## Project layout

```text
ai-chat/
|-- chatbot/
|   |-- __init__.py
|   |-- __main__.py  # Enables python -m chatbot
|   |-- cli.py       # Terminal interface
|   `-- llm.py       # LiteLLM API integration
|-- test.py          # Personal connection test
|-- requirements.txt
|-- .env.example
`-- README.md
```

`test.py` is a personal test script and is separate from the chatbot application. The chatbot code lives in `chatbot/`; its first feature accepts one question in the terminal and prints one LLM response.

Set `LITELLM_MODEL` in `.env` to the model name configured in your LiteLLM deployment.

Run the chatbot from the project directory:

```
python -m chatbot
```

To run the personal connection test:

```
python test.py
```