# Intelligent Slack Knowledge Base

A Slack-native, permission-aware retrieval-augmented generation system for
Problem Statement 02 of the React Hyderabad x Masters' Union AI Buildathon.

The product contract is intentionally strict:

- Answers come only from indexed company knowledge.
- Every substantive answer includes source citations.
- Personal, team, and organisation scopes are filtered before generation.
- Weak evidence produces an explicit refusal instead of a plausible guess.
- Conversation memory is isolated by workspace, channel, Slack thread, and user.

## Capabilities

- Slack Socket Mode with `/knowledge` and `@mention` interactions.
- PDF, DOCX, text, Markdown, URL, and Slack file ingestion.
- Same-channel past Slack-thread ingestion and direct-message interaction.
- OpenAI embeddings with Supabase Postgres and pgvector.
- LangGraph retrieval, evidence gate, generation, and citation validation.
- Personal, channel-backed team, and organisation scopes.
- Auto-tagging, source citations, summaries, ingestion status, and safe refusal.
- A 45-case quality and access-control evaluation harness.

## Architecture

```text
Slack command / mention
        |
        v
Command router -----> ingestion worker -----> parsers/chunker/tagger
        |                                      |
        v                                      v
LangGraph query flow <---------------- Supabase Postgres + pgvector
        |
        +--> ACL-filtered hybrid retrieval
        +--> evidence threshold
        +--> grounded OpenAI response
        +--> deterministic citation validator
        |
        v
Slack thread reply with source links
```

LLMs do not decide access. Team knowledge is bound to the Slack channel where it
was added and can only be retrieved from that same channel. Personal knowledge
requires the same Slack user ID. Organisation knowledge is available throughout
the same workspace.

## Quick start

1. Install Python through `uv` and sync dependencies:

   ```powershell
   uv sync
   ```

2. Copy `.env.example` to `.env.local` and fill the secrets locally.

3. Create a Supabase project, use its session pooler connection string for
   `DATABASE_URL`, then run:

   ```powershell
   uv run slack-kb-migrate
   ```

   For the local stack, use
   `postgresql://postgres:postgres@127.0.0.1:54322/postgres`. See
   [docs/SUPABASE_SETUP.md](docs/SUPABASE_SETUP.md).

4. Apply `slack-manifest.yaml` to Slack app `A0BABMXDYJW`, install/reinstall it,
   and create an app-level token with `connections:write`.
   See [docs/SLACK_SETUP.md](docs/SLACK_SETUP.md).

5. Start the complete local stack:

   ```powershell
   .\scripts\start-demo.ps1
   ```

   The script starts or recovers local Supabase, applies migrations, launches
   FastAPI, and opens one guarded Slack Socket Mode process. Health endpoints are
   available at `/healthz` and `/readyz`.

## Slack usage

```text
/knowledge help
/knowledge add personal My note text
/knowledge add team https://example.com/handbook
/knowledge add team https://workspace.slack.com/archives/C.../p...
/knowledge ask What is our leave policy?
/knowledge summarize <document-id>
/knowledge status
```

For files, attach a PDF, DOCX, TXT, or Markdown file to a message that mentions
the bot:

```text
@Knowledge Base add team
```

Continue asking follow-up questions in the bot's Slack thread to preserve
conversation context.

## Scope rules

| Scope | Stored identity | Retrieval rule |
|---|---|---|
| Personal | Slack user ID | Same workspace and same user |
| Team | Slack channel ID | Same workspace and same channel |
| Organisation | Workspace ID | Any requester in the workspace |

`team` ingestion is rejected in direct messages because a DM is not a team
knowledge boundary.

Organisation-wide ingestion is denied unless the Slack user ID is listed in
`ORG_ADMIN_USER_IDS`.

## Secret handling

Never commit `.env`, `.env.local`, Slack tokens, Supabase passwords, or OpenAI
keys. Rotate a credential immediately if it is pasted into a chat, issue, commit,
or screenshot.

## Delivery phases

See [PHASES.md](PHASES.md) for the rubric-driven build plan and demo gates.

## Evaluation

With Supabase running and migrations applied:

```powershell
uv run slack-kb-eval
```

The evaluator fails the run below 80% grounded score or on any ACL leak, and
reports answer accuracy, citation validity, refusal precision, and latency.
The current synthetic baseline is documented in
[evals/BASELINE.md](evals/BASELINE.md).

Verify the 50-document scalability requirement:

```powershell
uv run slack-kb-scale-smoke
```

See [docs/EVALUATION_AUDIT.md](docs/EVALUATION_AUDIT.md) for live Slack evidence
and the criterion-by-criterion completion audit.

## Render deployment

The repository includes `render.yaml` for an always-on Render deployment that
runs FastAPI and Slack Socket Mode in one service with managed PostgreSQL and
pgvector. See [docs/RENDER_DEPLOYMENT.md](docs/RENDER_DEPLOYMENT.md).
