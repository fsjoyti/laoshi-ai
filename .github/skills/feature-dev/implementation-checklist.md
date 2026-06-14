# Implementation Checklist for SWE

Use this checklist when implementing a feature following the PM's user story and QA's test cases.

## Pre-Implementation

- [ ] User story and acceptance criteria are clear
- [ ] Test cases written and reviewed by QA
- [ ] Tests currently fail (TDD: red state)
- [ ] All dependencies listed (need a new package? Update `pyproject.toml`)

## Development

- [ ] Feature branch created: `git checkout -b feature/[name]`
- [ ] Code written with explicit type-hinting (Python 3.11+)
- [ ] Docstrings added to functions and classes
- [ ] Modern LangChain LCEL patterns used (if applicable)
- [ ] No hardcoded secrets (use `.env` and `load_dotenv()`)
- [ ] Error messages are user-friendly

## Testing & Linting

- [ ] All tests pass: `uv run pytest`
- [ ] Ruff linting passes: `uv run ruff check . --fix`
- [ ] Ruff formatting passes: `uv run ruff format .`
- [ ] No lingering `print()` statements or debug code
- [ ] New files follow project naming conventions

## Documentation

- [ ] `README.md` updated (if new CLI commands, setup steps, or deploy notes)
- [ ] Docstrings complete and clear
- [ ] Complex logic has inline comments
- [ ] Example usage shown in docstrings if helpful

## Docker & CI

- [ ] Works locally: `uv run chainlit run chainlit_app.py`
- [ ] Works in Docker: `docker compose up --build`
- [ ] Tested manually in http://localhost:8000
- [ ] `.env.example` updated if new env vars added
- [ ] No `.env` secrets committed to git

## Code Quality

- [ ] No dead imports or unused variables
- [ ] No global state (use dependency injection)
- [ ] Async code is safe (Chainlit handlers use proper patterns)
- [ ] Error handling covers edge cases
- [ ] No external API calls without mocking in tests

## Before Opening PR

```bash
# Full verification suite
uv sync --extra dev
uv run pytest -v
uv run ruff check . --fix
uv run ruff format .
docker compose up --build
# Test manually at http://localhost:8000
docker compose down
```

- [ ] All commands above pass
- [ ] Commit message is clear and concise
- [ ] Branch is pushed: `git push origin feature/[name]`
- [ ] PR opened against `main` with description

## PR Template

```markdown
## Description

[Describe the feature and how it solves the problem]

## Acceptance Criteria

- [x] AC1: [Criterion met]
- [x] AC2: [Criterion met]
- [x] AC3: [Criterion met]

## Testing

- Tests added: `tests/test_[feature].py`
- All tests pass: ✅
- Ruff passes: ✅
- Docker tested: ✅

## Related Issues

Closes #[issue-number]

## Notes for Reviewer

[Any architectural decisions, trade-offs, or gotchas for the Tech Lead]
```

## Post-Merge

- [ ] Monitor CI for any lingering issues
- [ ] Verify Docker image builds on GitHub Actions
- [ ] Close related GitHub issues

---

**Definition of Done:** All checkboxes above are checked, and Tech Lead has approved. 🎉
