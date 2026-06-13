# Architecture decisions

## Why this is RAG-first, not agent-first

The highest-risk decisions are authorization, retrieval, and refusal. Those are
deterministic services. LangGraph coordinates the query states, but an LLM never
chooses which private records a user may see.

## Trust boundaries

1. Slack authenticates workspace and user identity.
2. The command router derives the only allowed scope IDs.
3. PostgreSQL applies workspace/user/channel filters inside the retrieval query.
4. The generator receives only filtered chunks.
5. Citation validation rejects uncited generated answers.

## Scope model

Team scope maps to a Slack channel, not a free-form team label. A requester can
only query team content from the same channel, which makes Slack itself the
membership boundary and prevents cross-channel leakage.

## Retrieval

OpenAI `text-embedding-3-small` vectors are stored in pgvector. Retrieval blends
cosine similarity and PostgreSQL full-text rank. A minimum similarity gate
prevents weak matches from reaching generation.

## Conversation memory

Memory is scoped by workspace, channel, thread, and user. Only a bounded recent
window is used. Retrieved private context is never copied into a global memory.

## Cost posture

- One embedding request per chunk, batched during ingestion.
- One query embedding per question.
- A compact configurable generation model.
- No default second-model verifier; deterministic evidence and citation gates run
  on every answer.
- Optional quality improvements are introduced only after eval evidence supports
  their cost.

## FastAPI boundary

FastAPI provides health and readiness endpoints for deployment and monitoring.
Slack remains the only user-facing query transport in Phase 1. Data APIs are not
exposed until an authenticated admin surface is designed, avoiding an accidental
permission bypass around Slack identity.
