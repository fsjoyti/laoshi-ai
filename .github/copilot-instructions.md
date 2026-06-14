# Laoshi AI — Multi-Role Development Workflow

This project uses a **four-persona iterative cycle** to ensure quality, testability, and architectural integrity on every feature.

## The Four Personas

Follow this sequence **in order** for every new capability or component.

### 📋 Phase 1: Project Manager (PM)
**Define the story and acceptance criteria.**

1. Write a user story with priority (`P0: Critical MVP`, `P1: Important`, `P2: Nice-to-Have`).
2. List acceptance criteria as checkboxes.
3. Confirm scope fits in a single PR where possible.

**Output:** User story, acceptance criteria, priority.

---

### 🧪 Phase 2: QA Tester (QA)
**Draft tests before code.**

1. Review PM's acceptance criteria.
2. Write unit tests (using `pytest` and `pytest-asyncio` for async LangChain/Chainlit calls).
3. Tests must pass without a live OpenAI API key (use mocks for LLM calls).

**Output:** Test cases under `tests/` that codify acceptance criteria.

---

### 💻 Phase 3: Software Developer (SWE)
**Implement the smallest diff that satisfies acceptance criteria.**

1. Pull the highest-priority `P0` stories.
2. Write implementation code adhering to Python 3.11+, explicit type-hinting, and modern LangChain LCEL design patterns.
3. Ensure all tests pass locally:
   ```bash
   uv sync --extra dev
   uv run ruff check . --fix
   uv run ruff format .
   uv run pytest
   ```
4. Update `README.md` if setup or run instructions change.

**Output:** Implementation, passing tests, no ruff violations.

---

### 👑 Phase 4: Tech Lead (TL)
**Review system health, security, and architecture.**

1. Verify no secrets, sensible error handling, and async-safe Chainlit handlers.
2. Confirm CI is green.
3. Approve merge or request changes with specific failing criteria.

**Output:** Code review approval or targeted feedback.

---

## Definition of Done

✅ Acceptance criteria met
✅ Tests green (uv run pytest)
✅ Ruff clean (uv run ruff check . --fix && uv run ruff format .)
✅ README updated (if applicable)
✅ No `.env` secrets in git
✅ Tech Lead approval

---

## Key Files & References

- **Development workflow details:** `developement-workflow.md`
- **Test suite:** `tests/`
- **Ruff config:** `pyproject.toml` (under `[tool.ruff]`)
- **Project setup:** `pyproject.toml`, `uv.lock`

---

## Quick Commands

```bash
# Full setup with dev tools
uv sync --extra dev

# Run the app locally
uv run chainlit run chainlit_app.py

# Lint and format
uv run ruff check . --fix
uv run ruff format .

# Test
uv run pytest

# Docker deployment
docker compose up --build
```

---

## Docker Notes

This project runs in a Docker container (see `Dockerfile`, `docker-compose.yml`). All local development follows the same patterns; Docker ensures consistency across environments.

