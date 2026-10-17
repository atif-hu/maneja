-- Brand Manager core schema
-- Multi-tenant brands, generation runs, images, approvals

create extension if not exists "pgcrypto";

-- ---------------------------------------------------------------------------
-- Enums
-- ---------------------------------------------------------------------------
create type public.member_role as enum ('owner', 'admin', 'viewer');
create type public.brand_status as enum ('active', 'paused', 'archived');
create type public.run_status as enum ('pending', 'running', 'completed', 'failed');
create type public.image_status as enum (
  'generating',
  'pending_review',
  'approved',
  'rejected',
  'archived'
);
create type public.approval_decision as enum ('approved', 'rejected');

-- ---------------------------------------------------------------------------
-- Brands
-- ---------------------------------------------------------------------------
create table public.brands (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  slug text not null unique,
  timezone text not null default 'UTC',
  daily_run_at time not null default time '09:00',
  status public.brand_status not null default 'active',
  style_guide text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index brands_status_idx on public.brands (status);

-- ---------------------------------------------------------------------------
-- Brand members (maps auth.users → brands)
-- ---------------------------------------------------------------------------
create table public.brand_members (
  id uuid primary key default gen_random_uuid(),
  brand_id uuid not null references public.brands (id) on delete cascade,
  user_id uuid not null references auth.users (id) on delete cascade,
  role public.member_role not null default 'viewer',
  created_at timestamptz not null default now(),
  unique (brand_id, user_id)
);

create index brand_members_user_idx on public.brand_members (user_id);
create index brand_members_brand_idx on public.brand_members (brand_id);

-- ---------------------------------------------------------------------------
-- Brand prompt templates / agent hints
-- ---------------------------------------------------------------------------
create table public.brand_prompts (
  id uuid primary key default gen_random_uuid(),
  brand_id uuid not null references public.brands (id) on delete cascade,
  name text not null,
  template text not null,
  is_active boolean not null default true,
  sort_order int not null default 0,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index brand_prompts_brand_idx on public.brand_prompts (brand_id);

-- ---------------------------------------------------------------------------
-- Generation runs (idempotent: one run per brand per calendar day)
-- ---------------------------------------------------------------------------
create table public.generation_runs (
  id uuid primary key default gen_random_uuid(),
  brand_id uuid not null references public.brands (id) on delete cascade,
  scheduled_for date not null,
  status public.run_status not null default 'pending',
  agent_meta jsonb not null default '{}'::jsonb,
  error_message text,
  started_at timestamptz,
  completed_at timestamptz,
  created_at timestamptz not null default now(),
  unique (brand_id, scheduled_for)
);

create index generation_runs_brand_idx on public.generation_runs (brand_id);
create index generation_runs_status_idx on public.generation_runs (status);

-- ---------------------------------------------------------------------------
-- Generated images (exactly 3 slots per run in normal operation)
-- ---------------------------------------------------------------------------
create table public.generated_images (
  id uuid primary key default gen_random_uuid(),
  run_id uuid not null references public.generation_runs (id) on delete cascade,
  brand_id uuid not null references public.brands (id) on delete cascade,
  slot int not null check (slot between 1 and 3),
  prompt text not null,
  storage_path text,
  status public.image_status not null default 'generating',
  provider text,
  provider_meta jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (run_id, slot)
);

create index generated_images_brand_status_idx
  on public.generated_images (brand_id, status);
create index generated_images_run_idx on public.generated_images (run_id);

-- ---------------------------------------------------------------------------
-- Approvals (audit trail for approve/reject)
-- ---------------------------------------------------------------------------
create table public.approvals (
  id uuid primary key default gen_random_uuid(),
  image_id uuid not null references public.generated_images (id) on delete cascade,
  reviewer_id uuid not null references auth.users (id) on delete restrict,
  decision public.approval_decision not null,
  note text,
  decided_at timestamptz not null default now()
);

create index approvals_image_idx on public.approvals (image_id);

-- ---------------------------------------------------------------------------
-- updated_at helper
-- ---------------------------------------------------------------------------
create or replace function public.set_updated_at()
returns trigger
language plpgsql
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

create trigger brands_updated_at
  before update on public.brands
  for each row execute function public.set_updated_at();

create trigger brand_prompts_updated_at
  before update on public.brand_prompts
  for each row execute function public.set_updated_at();

create trigger generated_images_updated_at
  before update on public.generated_images
  for each row execute function public.set_updated_at();

-- ---------------------------------------------------------------------------
-- Membership helpers (security definer to avoid RLS recursion)
-- ---------------------------------------------------------------------------
create or replace function public.is_brand_member(p_brand_id uuid)
returns boolean
language sql
stable
security definer
set search_path = public
as $$
  select exists (
    select 1
    from public.brand_members bm
    where bm.brand_id = p_brand_id
      and bm.user_id = auth.uid()
  );
$$;

create or replace function public.is_brand_admin(p_brand_id uuid)
returns boolean
language sql
stable
security definer
set search_path = public
as $$
  select exists (
    select 1
    from public.brand_members bm
    where bm.brand_id = p_brand_id
      and bm.user_id = auth.uid()
      and bm.role in ('owner', 'admin')
  );
$$;

grant execute on function public.is_brand_member(uuid) to authenticated;
grant execute on function public.is_brand_admin(uuid) to authenticated;
