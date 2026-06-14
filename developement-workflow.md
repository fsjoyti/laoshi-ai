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

### 🔜 Sprint 2 — P1 (recommended next)
| Story | Priority | Acceptance criteria |
|-------|----------|---------------------|
| Streaming responses | P1 | Tutor reply streams token-by-token in Chainlit |
| Migrate to `create_agent` + checkpointing | P1 | Replace deprecated `ConversationBufferMemory`; multi-turn memory still works |
| HSK level selector | P1 | User picks beginner/intermediate; system prompt adapts |
| Deployment (Docker) | P1 | `Dockerfile` + documented deploy to one cloud target |

### 📋 Sprint 3+ — P2 (stretch)
- User authentication (Chainlit OAuth)
- Session persistence across server restarts
- Quiz / flashcard tool
- Pronunciation feedback (TTS)

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
