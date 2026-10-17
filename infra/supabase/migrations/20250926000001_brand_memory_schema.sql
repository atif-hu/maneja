-- Brand Memory schema (Phase 1)
-- Structured brand profile, products, content pillars, reference images + embeddings,
-- content ideas (concept briefs), notifications, and Phase-2 publishing scaffolding.

create extension if not exists "vector";

-- ---------------------------------------------------------------------------
-- Enums
-- ---------------------------------------------------------------------------
create type public.concept_type as enum ('product', 'lifestyle', 'engagement');
create type public.reference_category as enum (
  'products', 'brand', 'lifestyle', 'people', 'locations', 'inspiration'
);
create type public.notification_type as enum ('generation_ready', 'system');
create type public.embedding_source as enum ('reference_image', 'generated_image');
create type public.social_platform as enum ('instagram', 'facebook');
create type public.post_status as enum ('draft', 'scheduled', 'published', 'failed');
create type public.run_kind as enum ('scheduled', 'on_demand');

-- ---------------------------------------------------------------------------
-- Brand profiles (structured Brand Memory identity, 1:1 with brands)
-- ---------------------------------------------------------------------------
create table public.brand_profiles (
  id uuid primary key default gen_random_uuid(),
  brand_id uuid not null unique references public.brands (id) on delete cascade,

  -- Business
  industry text,
  description text,
  website text,
  location text,

  -- Audience
  target_customer text,
  audience_age_range text,
  audience_interests text,

  -- Visual identity
  brand_colors jsonb not null default '[]'::jsonb, -- [{hex, label}]
  typography text,
  photography_style text,

  -- Content personality
  tone text,
  voice text,
  brand_dna jsonb not null default '[]'::jsonb, -- ["Warm", "Premium", ...]

  -- Preferences / avoid-list
  things_i_like text,
  things_i_dislike text,
  visual_elements_to_avoid text,
  words_to_avoid text,
  avoid_neon boolean not null default false,
  avoid_clutter boolean not null default false,

  -- AI behaviour sliders (1-3)
  creativity_level smallint not null default 2 check (creativity_level between 1 and 3),
  brand_consistency_level smallint not null default 3 check (brand_consistency_level between 1 and 3),
  reference_priority_level smallint not null default 3 check (reference_priority_level between 1 and 3),
  content_diversity_level smallint not null default 2 check (content_diversity_level between 1 and 3),

  logo_storage_path text,

  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index brand_profiles_brand_idx on public.brand_profiles (brand_id);

-- ---------------------------------------------------------------------------
-- Products / services
-- ---------------------------------------------------------------------------
create table public.products (
  id uuid primary key default gen_random_uuid(),
  brand_id uuid not null references public.brands (id) on delete cascade,
  name text not null,
  description text,
  price text,
  category text,
  is_active boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index products_brand_idx on public.products (brand_id);

-- ---------------------------------------------------------------------------
-- Content pillars
-- ---------------------------------------------------------------------------
create table public.content_pillars (
  id uuid primary key default gen_random_uuid(),
  brand_id uuid not null references public.brands (id) on delete cascade,
  name text not null,
  description text,
  sort_order int not null default 0,
  created_at timestamptz not null default now()
);

create index content_pillars_brand_idx on public.content_pillars (brand_id);

-- ---------------------------------------------------------------------------
-- Reference images (owner-uploaded, first-class inputs to generation)
-- ---------------------------------------------------------------------------
create table public.reference_images (
  id uuid primary key default gen_random_uuid(),
  brand_id uuid not null references public.brands (id) on delete cascade,
  product_id uuid references public.products (id) on delete set null,
  category public.reference_category not null default 'inspiration',
  storage_path text not null,
  title text,
  is_priority boolean not null default false,
  usage_count int not null default 0,
  ai_caption text,
  ai_tags jsonb not null default '[]'::jsonb,
  embedding_status text not null default 'pending'
    check (embedding_status in ('pending', 'ready', 'failed')),
  uploaded_by uuid references auth.users (id),
  uploaded_at timestamptz not null default now(),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index reference_images_brand_idx on public.reference_images (brand_id);
create index reference_images_brand_category_idx
  on public.reference_images (brand_id, category);

-- ---------------------------------------------------------------------------
-- Image embeddings (polymorphic: reference images today, generated images later)
-- ---------------------------------------------------------------------------
create table public.image_embeddings (
  id uuid primary key default gen_random_uuid(),
  brand_id uuid not null references public.brands (id) on delete cascade,
  source_type public.embedding_source not null,
  source_id uuid not null,
  model text not null,
  embedding vector(512) not null,
  created_at timestamptz not null default now(),
  unique (source_type, source_id)
);

create index image_embeddings_brand_idx on public.image_embeddings (brand_id);
create index image_embeddings_vector_idx
  on public.image_embeddings using ivfflat (embedding vector_cosine_ops)
  with (lists = 100);

-- ---------------------------------------------------------------------------
-- Content ideas (the concept brief written before image generation)
-- ---------------------------------------------------------------------------
create table public.content_ideas (
  id uuid primary key default gen_random_uuid(),
  run_id uuid not null references public.generation_runs (id) on delete cascade,
  brand_id uuid not null references public.brands (id) on delete cascade,
  slot int not null check (slot between 1 and 3),
  concept_type public.concept_type not null,
  headline text not null,
  rationale text,
  content_pillar_id uuid references public.content_pillars (id) on delete set null,
  product_id uuid references public.products (id) on delete set null,
  reference_image_ids uuid[] not null default '{}',
  prompt_brief jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  unique (run_id, slot)
);

create index content_ideas_brand_idx on public.content_ideas (brand_id);
create index content_ideas_run_idx on public.content_ideas (run_id);

-- ---------------------------------------------------------------------------
-- Link generated_images / generation_runs into the new concept model
-- ---------------------------------------------------------------------------
alter table public.generated_images
  add column content_idea_id uuid references public.content_ideas (id) on delete set null,
  add column concept_type public.concept_type;

alter table public.generation_runs
  add column run_type public.run_kind not null default 'scheduled';

-- Once-per-day uniqueness only applies to the cron-scheduled path; on-demand
-- ("generate now") runs must be able to coexist with the day's scheduled run.
alter table public.generation_runs
  drop constraint generation_runs_brand_id_scheduled_for_key;

create unique index generation_runs_scheduled_unique
  on public.generation_runs (brand_id, scheduled_for)
  where run_type = 'scheduled';

-- ---------------------------------------------------------------------------
-- Notifications (in-app only for Phase 1)
-- ---------------------------------------------------------------------------
create table public.notifications (
  id uuid primary key default gen_random_uuid(),
  brand_id uuid not null references public.brands (id) on delete cascade,
  user_id uuid not null references auth.users (id) on delete cascade,
  type public.notification_type not null default 'generation_ready',
  title text not null,
  body text,
  link_path text,
  read_at timestamptz,
  created_at timestamptz not null default now()
);

create index notifications_user_idx on public.notifications (user_id, read_at);
create index notifications_brand_idx on public.notifications (brand_id);

-- ---------------------------------------------------------------------------
-- Phase 2 scaffolding only — tables exist, no application logic yet
-- ---------------------------------------------------------------------------
create table public.social_accounts (
  id uuid primary key default gen_random_uuid(),
  brand_id uuid not null references public.brands (id) on delete cascade,
  platform public.social_platform not null,
  external_account_id text,
  display_name text,
  access_token_encrypted text,
  status text not null default 'disconnected',
  connected_at timestamptz,
  created_at timestamptz not null default now(),
  unique (brand_id, platform)
);

create table public.scheduled_posts (
  id uuid primary key default gen_random_uuid(),
  brand_id uuid not null references public.brands (id) on delete cascade,
  image_id uuid not null references public.generated_images (id) on delete cascade,
  social_account_id uuid references public.social_accounts (id) on delete set null,
  platform public.social_platform not null,
  caption text,
  scheduled_for timestamptz,
  status public.post_status not null default 'draft',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index scheduled_posts_brand_idx on public.scheduled_posts (brand_id);

create table public.publishing_events (
  id uuid primary key default gen_random_uuid(),
  scheduled_post_id uuid not null references public.scheduled_posts (id) on delete cascade,
  event_type text not null,
  detail jsonb not null default '{}'::jsonb,
  occurred_at timestamptz not null default now()
);

create index publishing_events_post_idx on public.publishing_events (scheduled_post_id);

-- ---------------------------------------------------------------------------
-- updated_at triggers (reuse existing public.set_updated_at())
-- ---------------------------------------------------------------------------
create trigger brand_profiles_updated_at
  before update on public.brand_profiles
  for each row execute function public.set_updated_at();

create trigger products_updated_at
  before update on public.products
  for each row execute function public.set_updated_at();

create trigger reference_images_updated_at
  before update on public.reference_images
  for each row execute function public.set_updated_at();

create trigger scheduled_posts_updated_at
  before update on public.scheduled_posts
  for each row execute function public.set_updated_at();
