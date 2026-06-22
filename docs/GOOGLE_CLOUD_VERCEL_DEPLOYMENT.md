# Google Cloud Run + Vercel deployment

This path uses Google Cloud Run for the always-on Slack backend and Vercel for
the public status/front-door layer.

## Why this shape

- Cloud Run runs the existing FastAPI + Slack Socket Mode process from
  `slack_kb.render_app:app`.
- The Cloud Run service should keep one minimum instance warm so the Slack Socket
  Mode connection stays alive without a manual local server.
- Vercel serves `public/index.html` and proxies `/healthz` and `/readyz` to the
  Cloud Run backend through `BACKEND_URL`.

## Required runtime configuration

Cloud Run backend:

```text
OPENAI_API_KEY
DATABASE_URL
SLACK_BOT_TOKEN
SLACK_APP_TOKEN
ORG_ADMIN_USER_IDS
OPENAI_CHAT_MODEL
OPENAI_EMBEDDING_MODEL
EMBEDDING_DIMENSIONS
RETRIEVAL_LIMIT
MIN_SIMILARITY
LOG_LEVEL
```

Vercel front door:

```text
BACKEND_URL=https://<cloud-run-service-url>
```

## Deploy backend to Cloud Run

From the repository root:

```powershell
gcloud run deploy intelligent-slack-knowledge-base `
  --source . `
  --region asia-south1 `
  --allow-unauthenticated `
  --min-instances 1 `
  --no-cpu-throttling `
  --memory 1Gi `
  --timeout 900 `
  --env-vars-file C:\tmp\slack-kb-cloudrun-env.yaml
```

The env-vars file is intentionally not committed. Generate it from local secrets
and delete it after deployment.

After deployment:

```powershell
gcloud run services describe intelligent-slack-knowledge-base `
  --region asia-south1 `
  --format "value(status.url)"
```

Verify:

```powershell
Invoke-RestMethod "$CLOUD_RUN_URL/healthz"
Invoke-RestMethod "$CLOUD_RUN_URL/readyz"
```

## Deploy Vercel front door

Set `BACKEND_URL` to the Cloud Run URL and deploy:

```powershell
npx vercel env add BACKEND_URL production
npx vercel --prod
```

Verify:

```powershell
Invoke-RestMethod "$VERCEL_URL/healthz"
Invoke-RestMethod "$VERCEL_URL/readyz"
```

## Slack verification

Because this keeps Socket Mode enabled, the existing Slack app manifest does not
need HTTP event URLs. Once Cloud Run is live, test in Slack:

```text
@Knowledge Base add team Google Cloud deployment marker GCP-E2E-FINAL.
@Knowledge Base ask What is the Google Cloud deployment marker?
```

Expected result: the bot indexes the marker and answers with a cited source.

## Storage note

The app still requires a PostgreSQL database with pgvector. Supabase free Nano
compute is useful for the demo, but it has a recommended 500 MB database size.
For truly unbounded storage, use a paid managed Postgres/vector database or a
self-managed Postgres instance.
