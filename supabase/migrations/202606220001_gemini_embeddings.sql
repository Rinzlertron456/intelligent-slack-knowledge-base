-- Migration: Switch embedding dimensions from OpenAI (1536) to Gemini (768)
-- Existing embeddings are incompatible and must be regenerated.

-- Drop the HNSW index first (required before column type change)
drop index if exists public.chunks_embedding_hnsw_idx;

-- Remove existing embeddings (documents and text chunks are preserved)
truncate public.chunks;

-- Change the embedding column dimension
alter table public.chunks
  alter column embedding type extensions.vector(768)
  using embedding::extensions.vector(768);

-- Recreate the HNSW index for the new dimension
create index chunks_embedding_hnsw_idx
  on public.chunks using hnsw (embedding extensions.vector_cosine_ops);

-- Replace the search function with the updated vector dimension
create or replace function public.match_authorized_chunks(
  query_embedding extensions.vector(768),
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
