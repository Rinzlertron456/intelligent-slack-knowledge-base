create schema if not exists extensions;
create extension if not exists vector with schema extensions;
create extension if not exists pgcrypto;

create table if not exists public.documents (
  id uuid primary key default gen_random_uuid(),
  workspace_id text not null,
  owner_user_id text,
  scope text not null check (scope in ('personal', 'team', 'org')),
  scope_id text,
  title text not null,
  source_type text not null,
  source_url text,
  content_hash text not null,
  tags text[] not null default '{}',
  metadata jsonb not null default '{}'::jsonb,
  status text not null default 'ready'
    check (status in ('processing', 'ready', 'failed', 'archived')),
  created_by text not null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint valid_scope_identity check (
    (scope = 'personal' and owner_user_id is not null and scope_id is null)
    or (scope = 'team' and scope_id is not null)
    or (scope = 'org' and owner_user_id is null and scope_id is null)
  ),
  unique (workspace_id, content_hash, scope, scope_id, owner_user_id)
);

create table if not exists public.chunks (
  id uuid primary key default gen_random_uuid(),
  document_id uuid not null references public.documents(id) on delete cascade,
  workspace_id text not null,
  chunk_index integer not null,
  content text not null,
  token_estimate integer not null,
  embedding extensions.vector(1536) not null,
  search_vector tsvector generated always as (
    to_tsvector('english', coalesce(content, ''))
  ) stored,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  unique (document_id, chunk_index)
);

create table if not exists public.conversation_messages (
  id bigserial primary key,
  workspace_id text not null,
  channel_id text not null,
  thread_key text not null,
  user_id text not null,
  role text not null check (role in ('user', 'assistant')),
  content text not null,
  created_at timestamptz not null default now()
);

create table if not exists public.ingestion_jobs (
  id uuid primary key default gen_random_uuid(),
  workspace_id text not null,
  requested_by text not null,
  source_label text not null,
  status text not null default 'processing'
    check (status in ('processing', 'ready', 'failed')),
  document_id uuid references public.documents(id) on delete set null,
  error_message text,
  created_at timestamptz not null default now(),
  completed_at timestamptz
);

create index if not exists documents_workspace_scope_idx
  on public.documents (workspace_id, scope, scope_id, owner_user_id);
create index if not exists chunks_workspace_idx on public.chunks (workspace_id);
create index if not exists chunks_search_idx on public.chunks using gin (search_vector);
create index if not exists chunks_embedding_hnsw_idx
  on public.chunks using hnsw (embedding extensions.vector_cosine_ops);
create index if not exists conversation_lookup_idx
  on public.conversation_messages (
    workspace_id, channel_id, thread_key, user_id, created_at desc
  );

do $$
begin
  if exists (select 1 from pg_roles where rolname = 'anon') then
    revoke all on table public.documents from anon;
    revoke all on table public.chunks from anon;
    revoke all on table public.conversation_messages from anon;
    revoke all on table public.ingestion_jobs from anon;
  end if;
  if exists (select 1 from pg_roles where rolname = 'authenticated') then
    revoke all on table public.documents from authenticated;
    revoke all on table public.chunks from authenticated;
    revoke all on table public.conversation_messages from authenticated;
    revoke all on table public.ingestion_jobs from authenticated;
  end if;
end
$$;

create or replace function public.match_authorized_chunks(
  query_embedding extensions.vector(1536),
  query_text text,
  request_workspace_id text,
  request_user_id text,
  request_channel_id text,
  match_threshold double precision default 0.35,
  match_count integer default 8
)
returns table (
  chunk_id uuid,
  document_id uuid,
  title text,
  content text,
  source_url text,
  tags text[],
  similarity double precision,
  lexical_rank real,
  score double precision
)
language sql
stable
security invoker
set search_path = public, extensions
as $$
  with authorized as (
    select
      c.id as chunk_id,
      d.id as document_id,
      d.title,
      c.content,
      d.source_url,
      d.tags,
      1 - (c.embedding <=> query_embedding) as similarity,
      ts_rank_cd(c.search_vector, plainto_tsquery('english', query_text)) as lexical_rank
    from public.chunks c
    join public.documents d on d.id = c.document_id
    where d.workspace_id = request_workspace_id
      and c.workspace_id = request_workspace_id
      and d.status = 'ready'
      and (
        d.scope = 'org'
        or (d.scope = 'personal' and d.owner_user_id = request_user_id)
        or (
          d.scope = 'team'
          and request_channel_id is not null
          and d.scope_id = request_channel_id
        )
      )
      and 1 - (c.embedding <=> query_embedding) >= match_threshold
  )
  select
    authorized.chunk_id,
    authorized.document_id,
    authorized.title,
    authorized.content,
    authorized.source_url,
    authorized.tags,
    authorized.similarity,
    authorized.lexical_rank,
    (authorized.similarity * 0.85 + least(authorized.lexical_rank, 1.0) * 0.15) as score
  from authorized
  order by score desc
  limit greatest(1, least(match_count, 20));
$$;
