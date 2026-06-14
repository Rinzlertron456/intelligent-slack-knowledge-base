# Rubric-driven delivery phases

## Phase 0 - Product and risk definition

Status: complete.

- Defined evidence-only answers, citations, refusal, and Slack-native UX.
- Chose deterministic authorization and retrieval over unrestricted agents.
- Mapped personal, team, and organisation scopes to Slack identities.

Exit gate: architecture, access model, refusal policy, and demo journey are
explicit.

## Phase 1 - Runnable vertical slice

Status: complete.

- Slack Socket Mode, slash command, mentions, DMs, files, and threads.
- Supabase Postgres with pgvector and full-text search.
- PDF, DOCX, URL, text, Markdown, Slack file, and Slack-thread ingestion.
- LangGraph retrieval, evidence gate, grounded generation, and citation checks.
- FastAPI health and readiness endpoints.

Exit gate: documents are added and queried end to end in Slack.

## Phase 2 - Retrieval quality and access control

Status: complete.

- 45-case golden dataset with answerable, unsupported, and ACL-deny cases.
- 97.78% grounded score, 100% citation validity, 100% refusal precision.
- Zero personal, cross-channel, or cross-workspace ACL leaks.
- 5.035-second p95 end-to-end evaluation latency.

Exit gate: grounded score exceeds 80%, p95 is below 10 seconds, and ACL leaks
equal zero.

## Phase 3 - Slack UX and knowledge operations

Status: complete for the problem statement.

- Live team, personal, and organisation ingestion.
- Cited Q&A, multi-turn follow-ups, summaries, status, and refusal.
- PDF, DOCX, URL, plain-text, Slack file, and thread demonstrations.
- Organisation publishing restricted to configured Slack admins.

Exit gate: the complete evaluated workflow runs without leaving Slack.

## Phase 4 - Reliability and scalability

Status: complete for the evaluation scope.

- HNSW and GIN indexes, connection pooling, batched embeddings, and idempotency.
- Single-instance launcher and stale-runtime cleanup.
- Automatic local Supabase recovery and migration retry.
- 60-document/20-query scale smoke with 100% exact retrieval and 0.0073-second
  p95 database latency.

Exit gate: the system handles more than 50 documents and remains below the
10-second latency target.

## Phase 5 - Submission

Status: complete.

- Public repository and buildathon submission Markdown.
- Setup, architecture, demo, evaluation, and security documentation.
- 24 passing tests, Ruff clean, live Slack bot, and ready FastAPI service.

Exit gate: code, documentation, reproducible evidence, and live workspace
integration are available.

## Post-submission backlog

Hosted deployment, App Home, modals, OCR, lifecycle controls, rate limiting,
audit dashboards, and a React admin UI are optional production enhancements, not
gaps in the evaluated buildathon workflow.
