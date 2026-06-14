# Laoshi AI — Chinese Learning Tutor

A text-based conversational Chinese tutor for English speakers, built with LangChain, OpenAI GPT-4o, and Chainlit.

Uses `langchain-classic` for `create_tool_calling_agent`, `AgentExecutor`, and `ConversationBufferMemory` (the supported API on LangChain v1).

## Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/getting-started/installation/)
- An [OpenAI API key](https://platform.openai.com/api-keys)

## Setup

```bash
# Install dependencies and create .venv
uv sync

# Configure environment
copy .env.example .env   # Windows
# cp .env.example .env   # macOS / Linux
# Edit .env and set OPENAI_API_KEY
```

## Download CC-CEDICT dictionary

The tutor uses the offline **CC-CEDICT** file for accurate word lookups.

1. Download the UTF-8 simplified/traditional dictionary archive from MDBG:
   - [https://www.mdbg.net/chinese/export/cedict/cedict_1_0_ts_utf-8.zip](https://www.mdbg.net/chinese/export/cedict/cedict_1_0_ts_utf-8_mdbg.zip)
2. Extract the archive and copy **`cedict_ts.u8`** into the project root (same directory as `dictionary.py`).
3. Optional: set a custom path in `.env`:
   ```env
   CEDICT_PATH=path/to/cedict_ts.u8
   ```

## Run the app

```bash
uv run chainlit run chainlit_app.py
```

Open the URL shown in the terminal (usually `http://localhost:8000`).

## Development

```bash
uv sync --extra dev
uv run ruff check . --fix
uv run ruff format .
uv run pytest
```

See `developement-workflow.md` for the PM → QA → SWE → TL process and backlog.

## Troubleshooting

### Restart the server

Stop the running server with **`Ctrl + C`** in the terminal where Chainlit is running, then start it again:

```bash
uv run chainlit run chainlit_app.py
```

Refresh **http://localhost:8000** and click **New Chat** to begin a fresh session.

### Port 8000 already in use

If you see an error like `WinError 10048` or `address already in use`, an old Chainlit process is still running.

**Windows (PowerShell):**

```powershell
netstat -ano | findstr :8000
taskkill /PID <PID> /F
uv run chainlit run chainlit_app.py
```

Use the PID from the **LISTENING** row (last column). On macOS/Linux, use `lsof -i :8000` and `kill <PID>` instead.

### Messages send but no reply appears

The tutor usually takes **5–15 seconds** to respond. You should see a **"Thinking"** step while it works.

If the greeting appears but replies never show:

1. Restart the server (see above).
2. Click **New Chat** — do not reuse an old browser tab/session.
3. Confirm `.env` has a valid `OPENAI_API_KEY`.
4. Check the terminal for errors after sending a message.

### Connection / SSL errors

If the chat shows `APIConnectionError` or `SSL: CERTIFICATE_VERIFY_FAILED`, the app uses `truststore` to load your OS certificate store (common fix on Windows with corporate proxies or antivirus).

If `uv sync` fails with TLS/certificate errors:

```bash
uv sync --native-tls
```

Also check VPN/proxy settings if problems persist.

### Harmless startup warnings

These are normal and do not stop the app from running:

- `Created default chainlit markdown file` — Chainlit auto-generated `chainlit.md`.
- `Translated markdown file for en-US not found` — Falls back to `chainlit.md`.
- `Missing custom logo` — Uses the default Chainlit logo.
- `ConversationBufferMemory was deprecated` — Informational only; memory still works.

### Welcome page vs. chat

The **Readme** screen is Chainlit's landing page. Click **New Chat** (top left) to start a lesson — the tutor greeting and chat input appear there.

## Project layout

| File | Purpose |
|------|---------|
| `pyproject.toml` | Project metadata and dependencies (managed by uv) |
| `agent.py` | System prompt, LangChain agent, tools, and memory |
| `utils.py` | `to_pinyin` tool (pypinyin) |
| `dictionary.py` | CC-CEDICT parser and `lookup_word` tool |
| `chainlit_app.py` | Chat UI |
| `tests/` | Unit tests (dictionary, pinyin, agent wiring) |
