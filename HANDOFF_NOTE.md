# Handoff: PM Backlog Planning — Chinese Tutor AI

Date: 2026-06-14
Prepared by: AI assistant using Copilot CLI runtime in VS Code (Project Manager persona)

Purpose
-------
This handoff bundles the prioritized Kanban backlog and formal user stories for the next development wave: migrate deprecated memory, implement streaming, improve persistence & auth, and add pedagogy features (HSK modes, quiz, pronunciation feedback). Use this to begin QA test drafting and SWE implementation.

Kanban Board
------------
- Todo (Not Started)
  - Memory migration to agent/checkpointed history
  - Token streaming into Chainlit UI
  - Multi-user auth + role model
  - Session persistence across restarts (DB-backed)
  - HSK-level learning modes
  - Interactive quiz tool
  - Pronunciation feedback (STT + scoring)
- In Progress
  - None (planning phase)
- Done (MVP grounding)
  - `chainlit_app.py` — basic chat UI + single-user MVP
  - `README.md` — setup & run instructions
  - `pyproject.toml` / `requirements.txt` — pinned deps
  - Basic LLM handler using ConversationBufferMemory (legacy MVP)

Prioritized User Stories
------------------------
P0: Critical Architecture & UX Fixes

1) Memory Migration — Replace ConversationBufferMemory
- As a developer, I want to migrate off ConversationBufferMemory to an agent + checkpointed history so that the app stays compatible with LangChain 2.0 and conversation context is durable.
- Technical Considerations:
  - Investigate `create_tool_calling_agent` / LangChain agent patterns and LangGraph options.
  - Use DB-backed message history (e.g., LangChain ChatMessageHistory backed by Postgres) or LangChain checkpoints API.
  - Schema: session_id, message_id, role, text, tokens, metadata, timestamp.
  - Provide migration script to export existing ConversationBufferMemory.
- Acceptance Criteria:
  - No remaining use of `ConversationBufferMemory` in the codebase.
  - Message history persists to DB and can be rehydrated by session_id.
  - Migration script converts existing histories with timestamp fidelity.
  - Unit tests mock LangChain history and verify rehydrate/load flows.

2) Streaming Responses into Chainlit UI
- As a learner, I want tokens to appear as the model generates them so I receive near-instant feedback and improved UX.
- Technical Considerations:
  - Use LLM streaming callbacks (LangChain callbacks or OpenAI streaming client) integrated with Chainlit `@cl.on_message` streaming handlers.
  - Implement partial-message buffering, UI append semantics, and cancellation handling.
  - Ensure backpressure and ordering.
- Acceptance Criteria:
  - First token visible within 500ms of stream start in test harness.
  - UI progressively appends tokens; final assembled message matches model output.
  - Cancellation halts generation cleanly and marks partial response.
  - Tests mock streaming LLM and assert callback invocation order and partial-update events.

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

6) HSK-Level Modes
- As a learner, I want to select an HSK level so content matches my proficiency.
- Technical Considerations:
  - Prompt templates per HSK level with system message injection.
  - Persist user preference per account.
- Acceptance Criteria:
  - UI exposes HSK1..HSK6 options.
  - Generated content respects vocabulary/grammar constraints (validated by unit tests on prompt templates).
  - Preference persists across sessions.

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
