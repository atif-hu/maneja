-- Storage buckets for draft and approved brand images

insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values
  (
    'brand-drafts',
    'brand-drafts',
    false,
    52428800,
    array['image/png', 'image/jpeg', 'image/webp']
  ),
  (
    'brand-approved',
    'brand-approved',
    false,
    52428800,
    array['image/png', 'image/jpeg', 'image/webp']
  )
on conflict (id) do nothing;

-- Path convention: {brand_id}/{run_id}/{slot}.{ext}

create policy brand_drafts_select_member
  on storage.objects for select
  to authenticated
  using (
    bucket_id = 'brand-drafts'
    and public.is_brand_member((storage.foldername(name))[1]::uuid)
  );

create policy brand_approved_select_member
  on storage.objects for select
  to authenticated
  using (
    bucket_id = 'brand-approved'
    and public.is_brand_member((storage.foldername(name))[1]::uuid)
  );

-- Uploads/deletes are performed by service role from API/orchestrator only.
