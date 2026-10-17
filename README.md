# Brand Manager

Production-oriented monorepo for daily brand image generation with a human approval workflow.

## Architecture

| Piece | Path | Role |
|-------|------|------|
| Web dashboard | `apps/web` | Next.js App Router — auth, review, library |
| API | `apps/api` | FastAPI — brands, images, approve/reject, enqueue |
| Orchestrator | `apps/orchestrator` | Worker + scheduler — generates 3 images/day |
| Data | `infra/supabase` | Postgres schema, RLS, Storage buckets |
| Local stack | `infra/docker-compose.yml` | Redis, API, worker, scheduler |

```
Cron/scheduler → POST /internal/jobs/enqueue-daily
              → Redis queue
              → Worker (3 images → pending_review)
              → Dashboard Review → approve/reject → Library
```

## Prerequisites

- Node.js 20+
- Python 3.11+
- Docker (Redis / optional full stack)
- [Supabase CLI](https://supabase.com/docs/guides/cli) for local Postgres + Auth + Storage

## Quick start

### 1. Environment

```bash
cp .env.example .env
cp apps/web/.env.local.example apps/web/.env.local
```

After `supabase start`, copy the printed `anon` / `service_role` keys and JWT secret into both env files.

### 2. Supabase

```bash
cd infra/supabase
supabase start
supabase db reset   # applies migrations
```

### 3. API

```bash
cd apps/api
python -m venv .venv
# Windows: .venv\Scripts\activate
source .venv/bin/activate
pip install -e .
uvicorn app.main:app --reload --port 8000
```

### 4. Redis + worker + scheduler

```bash
cd infra
docker compose up redis -d

# from apps/orchestrator
cd ../apps/orchestrator
python -m venv .venv
source .venv/bin/activate   # or .venv\Scripts\activate on Windows
pip install -e .
python -m orchestrator.worker
# another terminal:
python -m orchestrator.scheduler
```

Or run the full compose stack (API + worker + scheduler + Redis):

```bash
cd infra
docker compose up --build
```

### 5. Web

```bash
npm install
npm run dev:web
```

Open http://localhost:3000 — sign up, create a brand, then trigger a run:

```bash
curl -X POST "http://localhost:8000/internal/jobs/enqueue-brand/<BRAND_UUID>" \
  -H "Authorization: Bearer change-me-internal-cron-secret"
```

With `IMAGE_PROVIDER=stub` the worker writes placeholder PNGs into `brand-drafts`. Set `IMAGE_PROVIDER=openai` and `OPENAI_API_KEY` for real generation.

## API (authenticated with Supabase JWT)

- `GET/POST /brands`
- `GET/PATCH /brands/{id}`
- `GET /brands/{id}/images?status=pending_review|approved`
- `GET /brands/{id}/runs`
- `POST /images/{id}/approve`
- `POST /images/{id}/reject`
- `POST /internal/jobs/enqueue-daily` (internal secret)
- `POST /internal/jobs/enqueue-brand/{id}` (internal secret)

## Idempotency

`generation_runs` has a unique constraint on `(brand_id, scheduled_for)`. Double-cron cannot create two runs for the same day. The worker skips completed runs and reuses in-progress slots that already have `pending_review` images.

## Image status

`generating` → `pending_review` → `approved` | `rejected`

Only `approved` images appear in the Library. Review shows `pending_review`.

## Roles

Brand members: `owner`, `admin`, `viewer`. Approve/reject requires `owner` or `admin`.
