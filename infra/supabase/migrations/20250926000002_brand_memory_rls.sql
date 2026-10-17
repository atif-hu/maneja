-- RLS policies for Brand Memory tables (Phase 1)
-- Same convention as 20240921000002_rls_policies.sql: member-select,
-- admin-write where owner-editable; agent/service-role-only writes elsewhere.

alter table public.brand_profiles enable row level security;
alter table public.products enable row level security;
alter table public.content_pillars enable row level security;
alter table public.reference_images enable row level security;
alter table public.image_embeddings enable row level security;
alter table public.content_ideas enable row level security;
alter table public.notifications enable row level security;
alter table public.social_accounts enable row level security;
alter table public.scheduled_posts enable row level security;
alter table public.publishing_events enable row level security;

-- Brand profiles: members read, admins write
create policy brand_profiles_select
  on public.brand_profiles for select
  to authenticated
  using (public.is_brand_member(brand_id));

create policy brand_profiles_write_admin
  on public.brand_profiles for all
  to authenticated
  using (public.is_brand_admin(brand_id))
  with check (public.is_brand_admin(brand_id));

-- Products: members read, admins write
create policy products_select
  on public.products for select
  to authenticated
  using (public.is_brand_member(brand_id));

create policy products_write_admin
  on public.products for all
  to authenticated
  using (public.is_brand_admin(brand_id))
  with check (public.is_brand_admin(brand_id));

-- Content pillars: members read, admins write
create policy content_pillars_select
  on public.content_pillars for select
  to authenticated
  using (public.is_brand_member(brand_id));

create policy content_pillars_write_admin
  on public.content_pillars for all
  to authenticated
  using (public.is_brand_admin(brand_id))
  with check (public.is_brand_admin(brand_id));

-- Reference images: members read, admins upload/curate
create policy reference_images_select
  on public.reference_images for select
  to authenticated
  using (public.is_brand_member(brand_id));

create policy reference_images_write_admin
  on public.reference_images for all
  to authenticated
  using (public.is_brand_admin(brand_id))
  with check (public.is_brand_admin(brand_id));

-- Image embeddings: internal machinery only — no authenticated policies.
-- API/orchestrator access this via the service-role connection.

-- Content ideas: members read (surfaces "why this concept" in the UI);
-- writes are agent-generated, service-role only.
create policy content_ideas_select
  on public.content_ideas for select
  to authenticated
  using (public.is_brand_member(brand_id));

-- Notifications: a user sees/updates only their own rows; inserts are
-- service-role only (the agent fans out one row per brand member).
create policy notifications_select_own
  on public.notifications for select
  to authenticated
  using (user_id = auth.uid());

create policy notifications_update_own
  on public.notifications for update
  to authenticated
  using (user_id = auth.uid())
  with check (user_id = auth.uid());

-- Social accounts: may eventually hold tokens — restrict read to admins.
create policy social_accounts_select_admin
  on public.social_accounts for select
  to authenticated
  using (public.is_brand_admin(brand_id));

-- Scheduled posts / publishing events: members read; no write policies yet
-- (Phase 2 — writes will go through a dedicated publishing service).
create policy scheduled_posts_select
  on public.scheduled_posts for select
  to authenticated
  using (public.is_brand_member(brand_id));

create policy publishing_events_select
  on public.publishing_events for select
  to authenticated
  using (
    exists (
      select 1 from public.scheduled_posts sp
      where sp.id = publishing_events.scheduled_post_id
        and public.is_brand_member(sp.brand_id)
    )
  );
