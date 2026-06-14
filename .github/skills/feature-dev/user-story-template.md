# User Story Template

## Title
[Feature/Capability Name]

## Priority
- [ ] P0: Critical MVP (must have)
- [ ] P1: Important Enhancement
- [ ] P2: Nice-to-Have Future Stretch

## Description

As a [user/developer], I want to [specific capability] so that [benefit/motivation].

### Context
[Brief background, problem statement, or why this matters]

---

## Acceptance Criteria

- [ ] **AC1:** [Criterion describing expected behavior]
- [ ] **AC2:** [Criterion describing expected behavior]
- [ ] **AC3:** [Criterion describing expected behavior]
- [ ] **AC4:** [Criterion describing expected behavior]

---

## Scope & Dependencies

**Scope:** Does this fit in a single PR? Yes / No

**Depends on:**
- [ ] [Task/Story X]
- [ ] [Task/Story Y]

**Blocked by:**
- [ ] [Task/Story Z]

---

## Implementation Notes

[Any architectural decisions, file references, or implementation hints for the SWE]

---

## Definition of Done

- [ ] All acceptance criteria met
- [ ] Unit tests pass (`uv run pytest`)
- [ ] Ruff passes (`uv run ruff check . --fix && uv run ruff format .`)
- [ ] README updated (if applicable)
- [ ] No hardcoded secrets
- [ ] Tech Lead approved
