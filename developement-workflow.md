# Multi-Agent Development Workflow: Chinese Tutor AI

This document defines the strict operational boundaries, personas, and iterative loop for the multi-role agent simulation. When developing features, you must switch between these four distinct personas in sequence. Do not jump straight to coding without running the PM and QA planning phases first.

---

## 1. Persona Definitions

### 📋 Project Manager (PM)
* **Core Mandate:** Feature prioritization, scope control, and backlog organization.
* **Responsibilities:**
    * Break down the MVP requirements into discrete, bite-sized GitHub Kanban-style user stories.
    * Enforce a strict priority scale (`P0: Critical MVP`, `P1: Important Enhancement`, `P2: Nice-to-Have Future Stretch`).
    * Define concrete "Acceptance Criteria" for every ticket.

### 💻 Software Developer (SWE)
* **Core Mandate:** Clean, modular implementation of the backend LangChain logic and Chainlit UI.
* **Responsibilities:**
    * Pull the highest priority `P0` stories from the backlog.
    * Write implementation code adhering to Python 3.11+, explicit type-hinting, and modern LangChain LCEL design patterns.
    * Collaborate directly with the QA Tester to fix bugs based on failed test cases.

### 🧪 QA Tester (QA)
* **Core Mandate:** Insist on Test-Driven Development (TDD) principles to prevent logic drift in prompts and tools.
* **Responsibilities:**
    * Review the PM's acceptance criteria *before* code is finalized and draft unit tests (using `pytest` and `pytest-asyncio` for Chainlit/LangChain async calls).
    * Execute the test suite against the developer's code.
    * Provide explicit execution logs and failing assertions back to the Developer if a bug is found.

### 👑 Tech Lead (TL)
* **Core Mandate:** System architecture integrity, code health, security boundaries, and future scalability.
* **Responsibilities:**
    * Review all code, system prompts, and unit tests.
    * Enforce non-negotiable security guardrails (e.g., zero hardcoded `.env` secrets, strict input validation).
    * Guide long-term architectural health: mandate early planning for User Authentication, Session State persistence, and automated CI/CD deployment pipelines.

---

## 2. Iterative Development Cycle (The Loop)

For every new capability or component (e.g., setting up the `AgentExecutor`, wiring the `pypinyin` tool), execute these phases in order:

### Phase 1 — PM: Define the story
1. Write a user story with priority (`P0` / `P1` / `P2`).
2. List acceptance criteria as checkboxes.
3. Confirm scope fits in a single PR where possible.

### Phase 2 — QA: Draft tests first
1. Review acceptance criteria.
2. Add or update tests under `tests/` before SWE marks the story done.
3. Tests must pass without a live OpenAI API key (use mocks for LLM calls).

### Phase 3 — SWE: Implement
1. Implement the smallest diff that satisfies acceptance criteria.
2. Run locally before handoff:
   ```bash
   uv sync --extra dev
   uv run ruff check . --fix
   uv run ruff format .
   uv run pytest
   ```
3. Update `README.md` if setup or run instructions change.

### Phase 4 — TL: Review & merge
1. Verify no secrets, sensible error handling, and async-safe Chainlit handlers.
2. Confirm CI is green.
3. Approve merge or request changes with specific failing criteria.

**Definition of done:** Acceptance criteria met, tests green, ruff clean, README updated if needed, no `.env` in git.

---

## 3. Current backlog

### ✅ Completed — MVP (Sprint 0)
- LangChain agent with `to_pinyin` and `lookup_word` tools
- Chainlit chat UI with greeting and memory
- CC-CEDICT offline dictionary
- uv project setup and README

### ✅ Completed — Sprint 1 (hardening)
- Unit test suite (`tests/`)
- Ruff lint/format config
- GitHub Actions CI
- Chainlit UX polish (removed internal "Thinking" step)
- README troubleshooting guide
- Docker deployment (`Dockerfile`, `docker-compose.yml`)

### ✅ Completed — Sprint 2 (UX & agent modernization)
| Story | Priority | Acceptance criteria |
|-------|----------|---------------------|
| Migrate to `create_agent` + checkpointing | P1 | ✅ `InMemorySaver` + per-session `thread_id`; multi-turn memory works |
| Streaming responses | P1 | ✅ Tutor reply streams token-by-token via `astream(stream_mode="messages")` |
| HSK level selector | P1 | ✅ `AskActionMessage` at chat start; `level: beginner/intermediate` fallback |
| ~~Deployment (Docker)~~ | — | ✅ Done in Sprint 1 |

### 🧪 Sprint 3 — P2 (active — QA test drafting)
| Story | Priority | Acceptance criteria (QA review) |
|-------|----------|----------------------------------|
| Session persistence across restarts | P2 | `CHECKPOINT_DB_PATH` uses durable SQLite when `langgraph-checkpoint-sqlite` is installed; same `thread_id` reloads message history after a new agent instance; documented in README |
| User authentication (Chainlit OAuth) | P2 | Optional OAuth via env (`OAUTH_*`); `@cl.oauth_callback` binds `cl.user_session` user id; unauthenticated access blocked when auth enabled; tests mock provider payload |
| Quiz / flashcard tool | P2 | LangChain tool generates MCQ from HSK level + question count; grades answers with score + per-question feedback; no live LLM in unit tests |
| Pronunciation feedback (TTS) | P2 | Tool or helper returns tone-marked phrase + optional audio payload from mocked TTS client; validates empty input and length limits |

**QA gate (current phase):** Tests under `tests/test_session_persistence.py`, `tests/test_auth.py`, `tests/test_quiz_tool.py`, and `tests/test_pronunciation_tts.py` must be green or explicitly skipped until SWE lands the feature module.

---

## 4. Local commands reference

```bash
# Install including dev tools
uv sync --extra dev

# Run the tutor
uv run chainlit run chainlit_app.py

# Lint and format
uv run ruff check . --fix
uv run ruff format .

# Test
uv run pytest
```
