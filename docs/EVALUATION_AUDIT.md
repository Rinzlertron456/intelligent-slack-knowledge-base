# Problem Statement 02 - Evaluation Audit

Verified on June 16, 2026 against the running local stack, managed Render
deployment, and target Slack app `A0BABMXDYJW`.

## Requirement evidence

| Requirement | Evidence | Result |
|---|---|---|
| Slack-native bot/app | Socket Mode session connected; mention, DM, slash-command manifest, and threaded replies implemented | Pass |
| PDF ingestion | [Live PDF ingestion](https://buildathon-slack-bot.slack.com/archives/C0BABMD6QV8/p1781348524608959) | Pass |
| DOCX ingestion | [Live DOCX ingestion](https://buildathon-slack-bot.slack.com/archives/C0BABMD6QV8/p1781343843413939) | Pass |
| URL ingestion | [Live URL ingestion](https://buildathon-slack-bot.slack.com/archives/C0BABMD6QV8/p1781348693092549) | Pass |
| Plain-text ingestion | [Live team note ingestion](https://buildathon-slack-bot.slack.com/archives/C0BABMD6QV8/p1781370695971539) | Pass |
| Slack-thread ingestion | Same-channel permalink loader and unit tests | Pass |
| Grounded Q&A with citations | [Live cited answer](https://buildathon-slack-bot.slack.com/archives/C0BABMD6QV8/p1781370716378129) | Pass |
| Multi-turn follow-up | Same live answer thread includes a Python-version follow-up | Pass |
| Explicit refusal | [Live unsupported question](https://buildathon-slack-bot.slack.com/archives/C0BABMD6QV8/p1781370763946019) | Pass |
| Document summary | [Live summary](https://buildathon-slack-bot.slack.com/archives/C0BABMD6QV8/p1781443440493539) | Pass |
| Status/listing | [Live status command](https://buildathon-slack-bot.slack.com/archives/C0BABMD6QV8/p1781370889262919) | Pass |
| Personal scope | Live private DM ingestion and cited Q&A; automated cross-user denial | Pass |
| Team scope | Channel-bound SQL retrieval; automated cross-channel denial | Pass |
| Organisation scope | [Admin-published org note](https://buildathon-slack-bot.slack.com/archives/C0BABMD6QV8/p1781370837451759) and cross-context retrieval | Pass |
| Auto-tagging | OpenAI JSON tags with deterministic heuristic fallback | Pass |
| At least 80% grounded | 100% across 45 cases on the live Render database | Pass |
| Under 10-second latency | 7.613-second p95 end-to-end evaluation latency | Pass |
| At least 50 documents | 60-document Render database smoke, 100% exact retrieval | Pass |
| Access control | Zero ACL leaks across personal, channel, and workspace negative cases | Pass |
| Managed deployment | Render web service is live; public `/healthz` and `/readyz` pass | Pass |
| Cloud Slack end to end | [Render-backed ingestion](https://buildathon-slack-bot.slack.com/archives/C0BABMD6QV8/p1781580288592249) and [Render-backed cited answer](https://buildathon-slack-bot.slack.com/archives/C0BABMD6QV8/p1781580333509629) | Pass |

## Reproduction

```powershell
.\scripts\start-demo.ps1
uv run pytest -q
uv run ruff check .
uv run slack-kb-eval --output evals/latest-report.json
uv run slack-kb-scale-smoke
```

## Current runtime

- FastAPI readiness: verified at
  `https://intelligent-slack-knowledge-base.onrender.com/readyz`
- FastAPI health: verified at
  `https://intelligent-slack-knowledge-base.onrender.com/healthz`
- Managed database: Render PostgreSQL with pgvector
- Slack transport: Socket Mode from the Render web process
- Workspace channel: `#all-buildathon-slack-bot`
- Live Slack recheck: [June 15 status response](https://buildathon-slack-bot.slack.com/archives/C0BABMD6QV8/p1781493815808619)
- Final cloud verification: document
  `7161db37-65f3-484c-a3e0-d3501f6630b2` was persisted as team knowledge for
  channel `C0BABMD6QV8`, and a cited Slack answer returned the expected
  "Aurora Lantern" / "Vinayak" facts.
- Production durability note: the Render PostgreSQL instance is still on the
  free plan and expires on July 15, 2026. Upgrading it to `basic_256mb` returned
  HTTP 402 because Render billing has no payment method.

Secrets remain only in ignored local environment files and are not included in
this audit.
