---
name: feature-dev
description: "Use when: planning a new feature or capability using the PM → QA → SWE → TL workflow. Creates user story, test templates, and implementation guide."
---

# Feature Development Workflow

This skill guides you through the **four-persona iterative cycle** to plan and implement a feature:

1. **PM** — Define user story and acceptance criteria
2. **QA** — Draft test cases that codify the requirements
3. **SWE** — Implement the feature, ensure tests pass
4. **TL** — Review architecture, security, and quality

---

## Phase 1: Project Manager — Define the Story

**Output:** User story with priority and acceptance criteria.

```markdown
## User Story

**Title:** [Feature Name]

**Priority:** P0 / P1 / P2

**Description:**
As a [user/developer], I want to [capability] so that [benefit].

---

## Acceptance Criteria

- [ ] [Criterion 1]
- [ ] [Criterion 2]
- [ ] [Criterion 3]

---

## Scope

Does this fit in a single PR? Yes / No
```

---

## Phase 2: QA Tester — Draft Tests

**Output:** Unit tests under `tests/` that codify acceptance criteria.

```python
# tests/test_[feature].py

import pytest
from unittest.mock import patch, MagicMock

def test_[feature_basic]():
    """Verify basic behavior."""
    # Arrange
    # Act
    # Assert

def test_[feature_edge_case]():
    """Verify edge case handling."""
    # Arrange
    # Act
    # Assert

@pytest.mark.asyncio
async def test_[feature_async]():
    """Verify async behavior (if applicable)."""
    # Arrange
    # Act
    # Assert
```

**Guidelines:**
- Mock external APIs (OpenAI, etc.) — no live key required
- Use `pytest` and `pytest-asyncio` for async LangChain/Chainlit code
- One test per acceptance criterion ideally
- Tests should fail before code is written (TDD)

---

## Phase 3: Software Developer — Implement

**Steps:**

1. **Create feature branch:**
   ```bash
   git checkout -b feature/[name]
   ```

2. **Implement code:**
   - Follow Python 3.11+ conventions
   - Use explicit type-hinting
   - Use modern LangChain LCEL patterns
   - Update docstrings

3. **Verify tests pass locally:**
   ```bash
   uv sync --extra dev
   uv run pytest
   uv run ruff check . --fix
   uv run ruff format .
   ```

4. **Update `README.md` if needed:**
   - New setup steps
   - New CLI commands
   - New deployment notes

5. **Commit and open PR:**
   ```bash
   git add .
   git commit -m "[Feature]: [Short description]"
   git push origin feature/[name]
   ```

---

## Phase 4: Tech Lead — Review

**Checklist:**

- [ ] No hardcoded secrets (`.env` required, not in git)
- [ ] Error handling is sensible and user-friendly
- [ ] Async code is safe (Chainlit handlers use `cl.Message(...).send()` correctly)
- [ ] No unintended side effects or breaking changes
- [ ] Tests are green
- [ ] Ruff passes (`uv run ruff check . --fix && uv run ruff format .`)
- [ ] README updated if applicable
- [ ] Acceptance criteria met
- [ ] Approve ✅ or request changes with specifics

---

## Docker & CI/CD

All features must:
- Work in Docker (see `docker-compose.yml`)
- Pass GitHub Actions CI (ruff, pytest)
- Have no `.env` hardcoded secrets

Test locally before pushing:
```bash
docker compose up --build
# Open http://localhost:8000 and test manually
docker compose down
```

---

## Quick Reference

| Command | Purpose |
|---------|---------|
| `uv sync --extra dev` | Install deps with dev tools |
| `uv run chainlit run chainlit_app.py` | Run app locally |
| `uv run pytest` | Run all tests |
| `uv run ruff check . --fix` | Lint and auto-fix |
| `uv run ruff format .` | Format code |
| `docker compose up --build` | Build and run in Docker |

---

## Files to Update

- `agent.py` — LangChain agent, tools, system prompt
- `chainlit_app.py` — Chat UI and message handlers
- `utils.py` — Utility functions and LangChain tools
- `dictionary.py` — CC-CEDICT integration
- `hsk_selector.py` — HSK-level prompt customization (example)
- `tests/test_*.py` — Unit tests
- `README.md` — Setup, run, and deploy instructions
- `.github/copilot-instructions.md` — This workflow (for future sessions)

---

## Success Criteria

✅ User story accepted by PM
✅ Tests written and reviewed by QA
✅ Code implements all acceptance criteria
✅ All tests pass (uv run pytest)
✅ Ruff clean (uv run ruff check . && uv run ruff format .)
✅ README updated
✅ Tech Lead approval
✅ PR merged and feature deployed
