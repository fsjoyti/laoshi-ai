# Handoff: PM Backlog Planning — Chinese Tutor AI

Date: 2026-06-14
Prepared by: AI assistant using Copilot CLI runtime in VS Code (Project Manager persona)

Purpose
-------
This handoff bundles the prioritized Kanban backlog and formal user stories for the next development wave: migrate deprecated memory, implement streaming, improve persistence & auth, and add pedagogy features (HSK modes, quiz, pronunciation feedback). Use this to begin QA test drafting and SWE implementation.

Kanban Board
------------
- Todo (Not Started)
  - Multi-user auth + role model
  - Session persistence across restarts (DB-backed)
  - Interactive quiz tool
  - Pronunciation feedback (STT + scoring)
- In Progress
  - None (planning phase)
- Done (Implemented)
  - Memory migration to agent/checkpointed history
  - Token streaming into Chainlit UI
  - HSK-level learning modes
  - `chainlit_app.py` — basic chat UI + single-user MVP
  - `README.md` — setup & run instructions
  - `pyproject.toml` / `requirements.txt` — pinned deps
  - Basic LLM handler using ConversationBufferMemory (legacy MVP)

Prioritized User Stories
------------------------
P1: Security & Persistence

3) Multi-User Authentication (OAuth / Chainlit)
- As a product owner, I want multi-user auth so learners sign in and sessions bind to accounts for access control and analytics.
- Technical Considerations:
  - Evaluate Chainlit built-in auth vs OAuth providers (Google, GitHub) and session cookie management.
  - Role model (student/teacher/admin) metadata on user accounts.
- Acceptance Criteria:
  - Users can sign up/sign in via selected provider(s).
  - Protected endpoints return 401 when unauthenticated.
  - Tests mock OAuth and assert session binding and role assignment.

4) Session Persistence & Resilience
- As an operator, I want sessions to persist across server restarts so learners return to ongoing conversations.
- Technical Considerations:
  - Durable DB (Postgres recommended). Transactional writes after each message.
  - Rehydrate session state on startup; document session GC policy.
- Acceptance Criteria:
  - After restart, session_id reloads full message history and context.
  - Restart simulation tests show no message loss for committed messages.
  - Configurable retention and GC documented.

5) Secure Storage & Secrets Management
- As a security lead, I want secrets kept out of the repo and CI so credentials remain safe.
- Technical Considerations:
  - Use environment variables and secret manager guidance in README; .env.example only.
  - Add repo scan / CI check for leaked secrets.
- Acceptance Criteria:
  - No API keys/secrets in repository (scan passes).
  - CI step blocks commits with secret-pattern matches.
  - README documents secret setup.

P2: Feature Enhancements (Pedagogy & Tools)

7) Interactive Quiz Tool
- As a teacher, I want to generate interactive quizzes so learners practice with instant feedback.
- Technical Considerations:
  - Implement as LangChain tool or Chainlit action; support MCQ, fill-in, and spoken prompts.
  - Store quiz attempts and scores per user.
- Acceptance Criteria:
  - Tool generates quizzes configurable by length and HSK level.
  - Answers are graded; feedback and numeric score returned.
  - Tests mock generation and grading logic.

8) Speech-to-Text Pronunciation Feedback
- As a learner, I want to record and receive pronunciation feedback so I can improve speaking.
- Technical Considerations:
  - Accept audio uploads; use Whisper or hosted STT for transcription.
  - Use phoneme-alignment or scoring model to generate score + actionable hints; support async job queue if needed.
- Acceptance Criteria:
  - Upload returns transcription + pronunciation score (0–100) and 3 actionable hints.
  - Short clip baseline latency documented; async job documented if >5s.
  - Tests stub STT and scoring and validate output format and hint content.

Cross-cutting
------------
9) Observability & Metrics (P1)
- Track request rates, stream latencies, errors; expose Prometheus metrics.
- Acceptance Criteria: metrics endpoint, basic dashboards, alert thresholds documented.

10) Scalability Plan (P1)
- Define horizontal scaling, sticky vs stateless session choices, and load test plan.
- Acceptance Criteria: scaling doc and baseline load-test results.

Next Steps / Handoff
-------------------
- PM sign-off on P0 scope (Memory Migration + Streaming) required before QA writes tests.
- QA persona to draft pytest cases (with mocks) for each Acceptance Criteria.
- SWE persona to implement P0 items in a single PR per the project's four-persona workflow.

Attachments / Notes
-------------------
- Migration script should include a dry-run mode and a reversible plan.
- Keep changes backwards-compatible for a transition window.

-- End of Handoff --
