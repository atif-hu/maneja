from __future__ import annotations

import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.auth import AuthUser, get_current_user, get_membership, require_admin
from app.core.db import get_db
from app.models.entities import Brand, GenerationRun, RunKind
from app.schemas.api import GenerationRunOut, OnDemandGenerateRequest
from app.services.queue import enqueue_daily_generate

router = APIRouter()


@router.post("/brands/{brand_id}/jobs/generate-now", response_model=GenerationRunOut)
async def generate_now(
    brand_id: uuid.UUID,
    body: OnDemandGenerateRequest,
    user: AuthUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> GenerationRun:
    """
    User-triggered "generate now" (Create page quick-create) — NOT the internal
    cron path. Always inserts a new run row: the partial unique index on
    generation_runs only covers run_type='scheduled', so on-demand runs may
    coexist with the day's scheduled run and with each other.
    """
    membership = await get_membership(brand_id, user, db)
    require_admin(membership)
    brand = await db.get(Brand, brand_id)
    if brand is None:
        raise HTTPException(status_code=404, detail="Brand not found")

    scheduled_for = date.today()
    run = GenerationRun(
        brand_id=brand_id,
        scheduled_for=scheduled_for,
        run_type=RunKind.on_demand,
        agent_meta={"on_demand_brief": body.model_dump()},
    )
    db.add(run)
    await db.commit()

    # The orchestrator worker reads run_type/agent_meta off the run row itself,
    # not off the queue payload — reuse the exact same enqueue call as the cron path.
    enqueue_daily_generate(brand.id, scheduled_for.isoformat())

    result = await db.execute(
        select(GenerationRun)
        .where(GenerationRun.id == run.id)
        .options(selectinload(GenerationRun.images))
    )
    return result.scalar_one()
