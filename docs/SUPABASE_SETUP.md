# Supabase setup

## Local database

The local Supabase stack is started with:

```powershell
npx.cmd --yes supabase@latest start
```

Backend database URL:

```text
postgresql://postgres:postgres@127.0.0.1:54322/postgres
```

Apply the schema:

```powershell
uv run slack-kb-migrate
```

Supabase Studio is available at `http://127.0.0.1:54323`.

## Hosted project

1. Create a Supabase project in the dashboard.
2. Select **Connect** and copy the **Session pooler** connection string.
3. Replace its password placeholder and save the complete string as
   `DATABASE_URL` in `.env.local`.
4. Run `uv run slack-kb-migrate`.

Session mode is the right default for the persistent Socket Mode worker and
FastAPI process. Use transaction mode only for serverless deployments and account
for its prepared-statement restrictions.

Do not expose the database URL to React or Slack clients. It contains database
credentials and belongs only in backend environment configuration.

Supabase references:

- [Connecting to Postgres](https://supabase.com/docs/guides/database/connecting-to-postgres)
- [Vector columns and similarity search](https://supabase.com/docs/guides/ai/vector-columns)
- [Row Level Security](https://supabase.com/docs/guides/database/postgres/row-level-security)
