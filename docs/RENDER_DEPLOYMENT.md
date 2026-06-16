# Render deployment

The production layout uses one always-on Render web service and one managed
Render Postgres database:

```text
Render web service
  - FastAPI health/readiness endpoints
  - Slack Socket Mode connection
  - automatic database migrations at startup
  - automatic deploys from GitHub main

Render Postgres
  - pgvector + HNSW
  - PostgreSQL full-text search
  - documents, chunks, memory, and ACL metadata
```

Combining FastAPI and Socket Mode in one process avoids duplicate Slack event
consumers and a second paid worker. The service uses the Starter plan because
free web services sleep after 15 minutes of no inbound traffic.

## Costs

At Render's June 2026 pricing:

- Starter web service: USD 7/month.
- Basic-256mb Postgres: USD 6/month.
- Total baseline: approximately USD 13/month, plus any usage overages.

The database can be changed to `free` for a temporary demo, but free Render
Postgres expires after 30 days. A free web service is not suitable for an
always-on Slack Socket Mode connection.

## Deployment

The repository contains `render.yaml` for reproducible deployment. Required
secrets are configured only in Render:

- `OPENAI_API_KEY`
- `SLACK_BOT_TOKEN`
- `SLACK_APP_TOKEN`
- `ORG_ADMIN_USER_IDS`

Render injects `DATABASE_URL` from the managed database. The application applies
idempotent migrations before opening the Slack connection.

The start command uses `uv run --frozen --no-dev` so production startup never
resolves or installs development dependencies.

As of June 16, 2026, the managed Render deployment is live at
`https://intelligent-slack-knowledge-base.onrender.com` and has passed public
health, readiness, Slack ingestion, Slack cited Q&A, Render PostgreSQL
persistence, and OpenAI `200 OK` checks. The application is functionally
deployed on Render.

The current limitation is durability, not functionality. The Render PostgreSQL
instance is still on the free plan and expires on July 15, 2026. An attempted
upgrade to `basic_256mb` returned HTTP 402 because the workspace has no payment
method. Add billing, then upgrade the database to the paid `basic-256mb`
Blueprint plan. Recheck the web service plan afterward; the live service list
still reports it as `free` even after a `starter` update command returned
success.

Note: `render.yaml` uses Blueprint plan names such as `basic-256mb`. The Render
CLI/API uses underscore names such as `basic_256mb` for direct updates.

## Verification

1. Confirm the Render deploy is live.
2. Open `/healthz` and expect `{"status":"ok"}`.
3. Open `/readyz` and expect `{"status":"ready"}`.
4. Send `@Knowledge Base status` in Slack.
5. Add a team note and ask a cited question.

Do not run the local Socket Mode bot at the same time as Render. Two consumers
using the same app token can process the same Slack workflow unpredictably.
