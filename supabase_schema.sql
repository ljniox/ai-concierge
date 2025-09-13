-- Supabase schema for gust-ai service catalog, sessions, interactions, artifacts
-- Run this in Supabase SQL editor (with pgvector enabled)

-- Enable pgcrypto for gen_random_uuid and pgvector for embeddings
create extension if not exists pgcrypto;
create extension if not exists vector;

-- Services catalog
create table if not exists public.services (
  code text primary key,
  title text not null,
  description text,
  keywords text[] default '{}',
  enabled boolean default true,
  display_options text,
  flow jsonb default '{}'::jsonb,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

-- Sessions
create table if not exists public.sessions (
  id uuid primary key default gen_random_uuid(),
  phone text not null,
  status text not null default 'active', -- active | in_service | closed
  service_code text references public.services(code),
  context jsonb not null default '{}'::jsonb,
  started_at timestamptz default now(),
  ended_at timestamptz,
  last_message_at timestamptz default now()
);
create index if not exists idx_sessions_phone_status on public.sessions (phone, status);

-- Interactions (chat turns)
create table if not exists public.interactions (
  id uuid primary key default gen_random_uuid(),
  session_id uuid references public.sessions(id) on delete cascade,
  ts timestamptz default now(),
  role text not null, -- user | assistant | tool | system
  content text not null,
  meta jsonb default '{}'::jsonb,
  -- store embedding as json for portability; optional vector column below
  embedding_json jsonb
);
create index if not exists idx_interactions_session_ts on public.interactions (session_id, ts);

-- Optional: vector column (adjust dimension to your embedding model)
-- alter table public.interactions add column if not exists embedding vector(384);
-- create index if not exists idx_interactions_embedding on public.interactions using hnsw (embedding vector_cosine_ops);

-- Artifacts (reports, files, actions)
create table if not exists public.artifacts (
  id uuid primary key default gen_random_uuid(),
  session_id uuid references public.sessions(id) on delete cascade,
  service_code text,
  type text not null, -- report | file | action
  content text,
  meta jsonb default '{}'::jsonb,
  created_at timestamptz default now()
);

-- Simple RPC example for retrieving active session by phone
create or replace function public.get_active_session_by_phone(p_phone text)
returns setof public.sessions
language sql stable as $$
  select * from public.sessions
  where phone = p_phone and status in ('active','in_service')
  order by started_at desc
  limit 1;
$$;

-- Timestamps trigger for updated_at on services
create or replace function public.set_updated_at()
returns trigger as $$
begin
  new.updated_at = now();
  return new;
end;
$$ language plpgsql;

drop trigger if exists services_set_updated_at on public.services;
create trigger services_set_updated_at
before update on public.services
for each row execute function public.set_updated_at();

