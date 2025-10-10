-- Temporary Web Pages Management System
-- For sharing reports, student files, receipts with UUID-based access

-- Enable extensions
create extension if not exists pgcrypto;
create extension if not exists "uuid-ossp";

-- Temporary Pages Table (for time-sensitive access)
create table if not exists public.temporary_pages (
    id uuid primary key default gen_random_uuid(),
    access_code uuid unique not null default gen_random_uuid(),
    title text not null,
    content jsonb not null,
    content_type text default 'report', -- report, student_file, receipt, etc.
    created_by text not null, -- user who created it
    created_at timestamptz default now(),
    expires_at timestamptz not null,
    is_active boolean default true,
    access_count integer default 0,
    max_access_count integer default null, -- null = unlimited
    allowed_actions text[] default '{read,print}', -- read, print, download
    metadata jsonb default '{}'::jsonb -- additional data
);

-- Permanent Receipts Table (for payment proofs)
create table if not exists public.receipts (
    id uuid primary key default gen_random_uuid(),
    receipt_code uuid unique not null default gen_random_uuid(),
    title text not null,
    content jsonb not null,
    receipt_type text default 'payment', -- payment, inscription, etc.
    reference_id text, -- links to original transaction/inscription
    amount numeric(10,2) default 0,
    created_by text not null,
    created_at timestamptz default now(),
    is_active boolean default true,
    access_count integer default 0,
    metadata jsonb default '{}'::jsonb
);

-- Access Logs Table
create table if not exists public.page_access_logs (
    id uuid primary key default gen_random_uuid(),
    page_id uuid,
    page_type text not null, -- temporary, receipt
    access_code uuid,
    ip_address inet,
    user_agent text,
    accessed_at timestamptz default now(),
    action text default 'view', -- view, print, download
    success boolean default true
);

-- Indexes for performance
create index if not exists idx_temporary_pages_access_code on public.temporary_pages(access_code);
create index if not exists idx_temporary_pages_expires_at on public.temporary_pages(expires_at);
create index if not exists idx_temporary_pages_active on public.temporary_pages(is_active);
create index if not exists idx_receipts_receipt_code on public.receipts(receipt_code);
create index if not exists idx_receipts_active on public.receipts(is_active);
create index if not exists idx_page_access_logs_page_id on public.page_access_logs(page_id);
create index if not exists idx_page_access_logs_access_code on public.page_access_logs(access_code);
create index if not exists idx_page_access_logs_accessed_at on public.page_access_logs(accessed_at);

-- Functions for managing temporary pages

-- Create temporary page
create or replace function public.create_temporary_page(
    p_title text,
    p_content jsonb,
    p_content_type text default 'report',
    p_created_by text,
    p_expires_in interval default '24 hours',
    p_max_access_count integer default null,
    p_allowed_actions text[] default '{read,print}'
)
returns uuid
language plpgsql
security definer
as $$
declare
    v_access_code uuid;
begin
    insert into public.temporary_pages (
        title, content, content_type, created_by,
        expires_at, max_access_count, allowed_actions
    ) values (
        p_title, p_content, p_content_type, p_created_by,
        now() + p_expires_in, p_max_access_count, p_allowed_actions
    ) returning access_code into v_access_code;

    return v_access_code;
end;
$$;

-- Get temporary page by access code
create or replace function public.get_temporary_page(p_access_code uuid)
returns table (
    id uuid,
    title text,
    content jsonb,
    content_type text,
    created_by text,
    created_at timestamptz,
    expires_at timestamptz,
    access_count integer,
    max_access_count integer,
    allowed_actions text[]
)
language plpgsql
security definer
as $$
begin
    return query
    update public.temporary_pages
    set access_count = access_count + 1
    where access_code = p_access_code
    and is_active = true
    and expires_at > now()
    and (max_access_count is null or access_count < max_access_count)
    returning id, title, content, content_type, created_by, created_at, expires_at, access_count, max_access_count, allowed_actions;
end;
$$;

-- Create permanent receipt
create or replace function public.create_receipt(
    p_title text,
    p_content jsonb,
    p_receipt_type text default 'payment',
    p_reference_id text default null,
    p_amount numeric(10,2) default 0,
    p_created_by text
)
returns uuid
returns uuid
language plpgsql
security definer
as $$
declare
    v_receipt_code uuid;
begin
    insert into public.receipts (
        title, content, receipt_type, reference_id, amount, created_by
    ) values (
        p_title, p_content, p_receipt_type, p_reference_id, p_amount, p_created_by
    ) returning receipt_code into v_receipt_code;

    return v_receipt_code;
end;
$$;

-- Get receipt by code
create or replace function public.get_receipt(p_receipt_code uuid)
returns table (
    id uuid,
    title text,
    content jsonb,
    receipt_type text,
    reference_id text,
    amount numeric(10,2),
    created_by text,
    created_at timestamptz,
    access_count integer
)
language plpgsql
security definer
as $$
begin
    return query
    update public.receipts
    set access_count = access_count + 1
    where receipt_code = p_receipt_code
    and is_active = true
    returning id, title, content, receipt_type, reference_id, amount, created_by, created_at, access_count;
end;
$$;

-- Log page access
create or replace function public.log_page_access(
    p_page_id uuid,
    p_page_type text,
    p_access_code uuid,
    p_ip_address inet default null,
    p_user_agent text default null,
    p_action text default 'view',
    p_success boolean default true
)
returns void
language plpgsql
security definer
as $$
begin
    insert into public.page_access_logs (
        page_id, page_type, access_code, ip_address, user_agent, action, success
    ) values (
        p_page_id, p_page_type, p_access_code, p_ip_address, p_user_agent, p_action, p_success
    );
end;
$$;

-- Clean up expired temporary pages
create or replace function public.cleanup_expired_pages()
returns integer
language plpgsql
security definer
as $$
declare
    v_deleted_count integer;
begin
    delete from public.temporary_pages
    where expires_at <= now()
    or (max_access_count is not null and access_count >= max_access_count);

    get diagnostics v_deleted_count = row_count;
    return v_deleted_count;
end;
$$;

-- Get statistics
create or replace function public.get_page_stats()
returns table (
    active_temp_pages integer,
    expired_temp_pages integer,
    total_receipts integer,
    total_access_logs integer
)
language plpgsql
security definer
as $$
begin
    return query
    select
        (select count(*) from temporary_pages where is_active = true and expires_at > now()),
        (select count(*) from temporary_pages where is_active = false or expires_at <= now()),
        (select count(*) from receipts where is_active = true),
        (select count(*) from page_access_logs);
end;
$$;

-- Comments
comment on table public.temporary_pages is 'Temporary pages with UUID access codes for time-sensitive sharing';
comment on table public.receipts is 'Permanent receipts with UUID codes for payment proofs and documentation';
comment on table public.page_access_logs is 'Access logs for all page views and actions';
comment on function public.create_temporary_page is 'Create a new temporary page with expiration and access controls';
comment on function public.get_temporary_page is 'Get temporary page by access code and increment access count';
comment on function public.create_receipt is 'Create a permanent receipt with UUID code';
comment on function public.get_receipt is 'Get receipt by code and increment access count';
comment on function public.cleanup_expired_pages is 'Clean up expired temporary pages';