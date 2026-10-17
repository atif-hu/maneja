-- Storage bucket for owner-uploaded reference images

insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values
  (
    'brand-references',
    'brand-references',
    false,
    20971520,
    array['image/png', 'image/jpeg', 'image/webp']
  )
on conflict (id) do nothing;

-- Path convention: {brand_id}/{reference_image_id}.{ext}

create policy brand_references_select_member
  on storage.objects for select
  to authenticated
  using (
    bucket_id = 'brand-references'
    and public.is_brand_member((storage.foldername(name))[1]::uuid)
  );

-- Uploads/deletes are performed by service role from the API only.
