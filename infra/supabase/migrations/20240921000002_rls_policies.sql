-- Row Level Security policies (defense in depth; FastAPI remains primary authz)

alter table public.brands enable row level security;
alter table public.brand_members enable row level security;
alter table public.brand_prompts enable row level security;
alter table public.generation_runs enable row level security;
alter table public.generated_images enable row level security;
alter table public.approvals enable row level security;

-- Brands: members can read; admins can update
create policy brands_select_member
  on public.brands for select
  to authenticated
  using (public.is_brand_member(id));

create policy brands_update_admin
  on public.brands for update
  to authenticated
  using (public.is_brand_admin(id))
  with check (public.is_brand_admin(id));

-- Brand members: members can see roster; owners manage
create policy brand_members_select
  on public.brand_members for select
  to authenticated
  using (public.is_brand_member(brand_id));

create policy brand_members_insert_owner
  on public.brand_members for insert
  to authenticated
  with check (
    exists (
      select 1 from public.brand_members bm
      where bm.brand_id = brand_members.brand_id
        and bm.user_id = auth.uid()
        and bm.role = 'owner'
    )
  );

create policy brand_members_update_owner
  on public.brand_members for update
  to authenticated
  using (
    exists (
      select 1 from public.brand_members bm
      where bm.brand_id = brand_members.brand_id
        and bm.user_id = auth.uid()
        and bm.role = 'owner'
    )
  );

create policy brand_members_delete_owner
  on public.brand_members for delete
  to authenticated
  using (
    exists (
      select 1 from public.brand_members bm
      where bm.brand_id = brand_members.brand_id
        and bm.user_id = auth.uid()
        and bm.role = 'owner'
    )
  );

-- Brand prompts
create policy brand_prompts_select
  on public.brand_prompts for select
  to authenticated
  using (public.is_brand_member(brand_id));

create policy brand_prompts_write_admin
  on public.brand_prompts for all
  to authenticated
  using (public.is_brand_admin(brand_id))
  with check (public.is_brand_admin(brand_id));

-- Generation runs: members read
create policy generation_runs_select
  on public.generation_runs for select
  to authenticated
  using (public.is_brand_member(brand_id));

-- Generated images: members read
create policy generated_images_select
  on public.generated_images for select
  to authenticated
  using (public.is_brand_member(brand_id));

-- Approvals: members read; admins insert
create policy approvals_select
  on public.approvals for select
  to authenticated
  using (
    exists (
      select 1 from public.generated_images gi
      where gi.id = approvals.image_id
        and public.is_brand_member(gi.brand_id)
    )
  );

create policy approvals_insert_admin
  on public.approvals for insert
  to authenticated
  with check (
    reviewer_id = auth.uid()
    and exists (
      select 1 from public.generated_images gi
      where gi.id = approvals.image_id
        and public.is_brand_admin(gi.brand_id)
    )
  );

-- Service role (API / orchestrator) bypasses RLS by default.
-- No insert/update policies for generation tables for authenticated users;
-- writes go through FastAPI with service role.
