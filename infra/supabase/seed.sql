# Optional seed helpers (run via SQL editor after creating a user in Auth)
# Replace USER_UUID with auth.users.id from the dashboard.

-- insert into public.brands (id, name, slug, timezone, daily_run_at, style_guide)
-- values (
--   gen_random_uuid(),
--   'Demo Brand',
--   'demo-brand',
--   'UTC',
--   time '00:00',
--   'Minimal, natural light, muted greens'
-- );
