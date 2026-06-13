# Rubric-driven delivery plan

## Phase 0 - Product and risk definition

Status: complete.

- Translate the problem statement into a permission-aware RAG product contract.
- Rank work by judging weight: groundedness, Slack UX, access control, content
  breadth, then production readiness.
- Reject generic-chatbot and unrestricted-agent designs.

Exit gate: architecture, demo journey, refusal policy, and access model are
explicit.

## Phase 1 - Runnable vertical slice

Status: local vertical slice complete; Slack dashboard credentials pending.

- Configure Slack Socket Mode, scopes, slash command, mentions, and file access.
- Create Supabase pgvector schema.
- Ingest PDF, DOCX, URL, text, Markdown, and Slack-hosted files.
- Answer with ACL-filtered retrieval, citations, follow-up memory, and refusal.
- Add summaries, auto-tags, ingestion status, tests, and structured logs.

Exit gate: one document can be added and queried end-to-end in Slack.

## Phase 2 - Retrieval quality

- Build a 40-60 question golden dataset with answerable and unanswerable cases.
- Tune chunk size, overlap, similarity threshold, lexical weighting, and top-k.
- Add contextual chunk headers and optional reranking.
- Measure context precision, citation precision, refusal precision, latency, and
  answer groundedness.

Exit gate: at least 80% grounded answer score on the demo dataset and zero ACL
leaks in negative tests.

## Phase 3 - Slack UX and knowledge operations

- Add message shortcut and modal-based scope selection.
- Add App Home: recently indexed items, failed jobs, tags, and help.
- Support Slack thread ingestion by permalink.
- Add document lifecycle commands: list, inspect, re-index, archive, and delete.

Exit gate: the full demo can be run without leaving Slack.

## Phase 4 - Security and production hardening

- Encrypt or redact sensitive metadata and define retention controls.
- Add idempotency, retry/dead-letter handling, rate limits, and audit events.
- Add tenant-isolation, prompt-injection, malformed-file, and oversized-file tests.
- Deploy a persistent worker and monitor latency/error budgets.

Exit gate: threat model reviewed and operational failure paths demonstrated.

## Phase 5 - Submission

- Record a crisp demo: ingestion, direct Q&A, follow-up, summary, refusal, and ACL
  denial.
- Create architecture and evaluation slides.
- Publish the project repository and add only the required submission Markdown to
  the buildathon index repository.

Exit gate: public repository, setup guide, demo, deck, and submission PR are live.
