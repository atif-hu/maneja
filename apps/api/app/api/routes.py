from __future__ import annotations

import logging
import uuid
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.auth import AuthUser, get_current_user, get_membership, require_admin, verify_internal_secret
from app.core.db import get_db
from app.models.entities import (
    Approval,
    ApprovalDecision,
    Brand,
    BrandMember,
    BrandPrompt,
    BrandStatus,
    ContentIdea,
    GeneratedImage,
    GenerationRun,
    ImageStatus,
    MemberRole,
    ReferenceImage,
)
from app.schemas.api import (
    ApprovalOut,
    ApprovalRequest,
    BrandCreate,
    BrandOut,
    BrandPromptCreate,
    BrandPromptOut,
    BrandStatsOut,
    BrandUpdate,
    ContentIdeaSummary,
    EnqueueDailyResponse,
    GeneratedImageOut,
    GenerationRunOut,
    slugify,
)
from app.services.queue import enqueue_daily_generate
from app.services.storage import create_signed_url, create_signed_urls, promote_to_approved

logger = logging.getLogger(__name__)
router = APIRouter()


async def _run_orchestrator_agent(
    brand_id: uuid.UUID,
    scheduled_for: date,
    db: AsyncSession,
) -> GenerationRunOut:
    """
    Test endpoint: directly run the orchestrator agent without queue.
    Import here to avoid circular dependencies and optional orchestrator package.
    """
    try:
        from orchestrator.agent import AgentOrchestrator
    except ImportError:
        raise HTTPException(
            status_code=503,
            detail="Orchestrator not installed. "
            "Run: pip install -e apps/orchestrator in the API environment",
        )

    agent = AgentOrchestrator()
    try:
        await agent.run_daily_generate(str(brand_id), scheduled_for.isoformat())
    finally:
        await agent.close()

    # Fetch the completed run (most recent one for this brand/date)
    result = await db.execute(
        select(GenerationRun)
        .where(
            GenerationRun.brand_id == brand_id,
            GenerationRun.scheduled_for == scheduled_for,
        )
        .options(selectinload(GenerationRun.images))
        .order_by(GenerationRun.created_at.desc())
    )
    run = result.scalars().unique().first()
    if run is None:
        raise HTTPException(status_code=500, detail="Run not created")

    return GenerationRunOut.model_validate(run)


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/brands", response_model=list[BrandOut])
async def list_brands(
    user: AuthUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[Brand]:
    result = await db.execute(
        select(Brand)
        .join(BrandMember, BrandMember.brand_id == Brand.id)
        .where(BrandMember.user_id == user.id)
        .order_by(Brand.name)
    )
    return list(result.scalars().unique().all())


@router.post("/brands", response_model=BrandOut, status_code=status.HTTP_201_CREATED)
async def create_brand(
    body: BrandCreate,
    user: AuthUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Brand:
    base_slug = body.slug or slugify(body.name)
    slug = base_slug
    suffix = 2
    while (await db.execute(select(Brand.id).where(Brand.slug == slug))).first():
        if body.slug:
            raise HTTPException(status_code=400, detail="Slug already exists")
        slug = f"{base_slug}-{suffix}"
        suffix += 1

    brand = Brand(
        name=body.name,
        slug=slug,
        timezone=body.timezone,
        daily_run_at=body.daily_run_at,
        style_guide=body.style_guide,
        status=BrandStatus.active,
    )
    db.add(brand)
    await db.flush()
    db.add(BrandMember(brand_id=brand.id, user_id=user.id, role=MemberRole.owner))
    db.add(
        BrandPrompt(
            brand_id=brand.id,
            name="default",
            template=(
                "Create a brand-aligned marketing image for {brand_name}. "
                "Style guide: {style_guide}. Variation: {angle}."
            ),
            is_active=True,
            sort_order=0,
        )
    )
    await db.commit()
    await db.refresh(brand)
    return brand


@router.get("/brands/{brand_id}", response_model=BrandOut)
async def get_brand(
    brand_id: uuid.UUID,
    user: AuthUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Brand:
    await get_membership(brand_id, user, db)
    brand = await db.get(Brand, brand_id)
    if brand is None:
        raise HTTPException(status_code=404, detail="Brand not found")
    return brand


@router.patch("/brands/{brand_id}", response_model=BrandOut)
async def update_brand(
    brand_id: uuid.UUID,
    body: BrandUpdate,
    user: AuthUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Brand:
    membership = await get_membership(brand_id, user, db)
    require_admin(membership)
    brand = await db.get(Brand, brand_id)
    if brand is None:
        raise HTTPException(status_code=404, detail="Brand not found")

    data = body.model_dump(exclude_unset=True)
    if "status" in data and data["status"] is not None:
        try:
            brand.status = BrandStatus(data.pop("status"))
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="Invalid status") from exc
    for key, value in data.items():
        setattr(brand, key, value)
    await db.commit()
    await db.refresh(brand)
    return brand


@router.get("/brands/{brand_id}/prompts", response_model=list[BrandPromptOut])
async def list_prompts(
    brand_id: uuid.UUID,
    user: AuthUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[BrandPrompt]:
    await get_membership(brand_id, user, db)
    result = await db.execute(
        select(BrandPrompt)
        .where(BrandPrompt.brand_id == brand_id)
        .order_by(BrandPrompt.sort_order, BrandPrompt.name)
    )
    return list(result.scalars().all())


@router.post(
    "/brands/{brand_id}/prompts",
    response_model=BrandPromptOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_prompt(
    brand_id: uuid.UUID,
    body: BrandPromptCreate,
    user: AuthUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> BrandPrompt:
    membership = await get_membership(brand_id, user, db)
    require_admin(membership)
    prompt = BrandPrompt(brand_id=brand_id, **body.model_dump())
    db.add(prompt)
    await db.commit()
    await db.refresh(prompt)
    return prompt


@router.get("/brands/{brand_id}/images", response_model=list[GeneratedImageOut])
async def list_images(
    brand_id: uuid.UUID,
    status_filter: str | None = Query(default=None, alias="status"),
    user: AuthUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[GeneratedImageOut]:
    await get_membership(brand_id, user, db)
    stmt = (
        select(GeneratedImage, ContentIdea)
        .outerjoin(ContentIdea, GeneratedImage.content_idea_id == ContentIdea.id)
        .where(GeneratedImage.brand_id == brand_id)
    )
    if status_filter:
        try:
            stmt = stmt.where(GeneratedImage.status == ImageStatus(status_filter))
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="Invalid image status") from exc
    stmt = stmt.order_by(GeneratedImage.created_at.desc())
    result = await db.execute(stmt)
    rows = result.all()

    urls = await create_signed_urls(
        [(image.storage_path, image.status == ImageStatus.approved) for image, _ in rows]
    )
    out: list[GeneratedImageOut] = []
    for (image, content_idea), signed_url in zip(rows, urls):
        item = GeneratedImageOut.model_validate(image)
        item.signed_url = signed_url
        if content_idea is not None:
            item.content_idea = ContentIdeaSummary.model_validate(content_idea)
        out.append(item)
    return out


@router.get("/brands/{brand_id}/stats", response_model=BrandStatsOut)
async def get_brand_stats(
    brand_id: uuid.UUID,
    user: AuthUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> BrandStatsOut:
    await get_membership(brand_id, user, db)
    since = datetime.now(timezone.utc) - timedelta(days=7)

    pending_review = await db.scalar(
        select(func.count())
        .select_from(GeneratedImage)
        .where(
            GeneratedImage.brand_id == brand_id,
            GeneratedImage.status == ImageStatus.pending_review,
        )
    )
    approved_this_week = await db.scalar(
        select(func.count())
        .select_from(Approval)
        .join(GeneratedImage, Approval.image_id == GeneratedImage.id)
        .where(
            GeneratedImage.brand_id == brand_id,
            Approval.decision == ApprovalDecision.approved,
            Approval.decided_at >= since,
        )
    )
    rejected_this_week = await db.scalar(
        select(func.count())
        .select_from(Approval)
        .join(GeneratedImage, Approval.image_id == GeneratedImage.id)
        .where(
            GeneratedImage.brand_id == brand_id,
            Approval.decision == ApprovalDecision.rejected,
            Approval.decided_at >= since,
        )
    )
    total_reference_images = await db.scalar(
        select(func.count())
        .select_from(ReferenceImage)
        .where(ReferenceImage.brand_id == brand_id)
    )

    return BrandStatsOut(
        pending_review=pending_review or 0,
        approved_this_week=approved_this_week or 0,
        rejected_this_week=rejected_this_week or 0,
        total_reference_images=total_reference_images or 0,
    )


@router.get("/brands/{brand_id}/runs", response_model=list[GenerationRunOut])
async def list_runs(
    brand_id: uuid.UUID,
    user: AuthUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[GenerationRunOut]:
    await get_membership(brand_id, user, db)
    result = await db.execute(
        select(GenerationRun)
        .where(GenerationRun.brand_id == brand_id)
        .options(selectinload(GenerationRun.images))
        .order_by(GenerationRun.scheduled_for.desc())
        .limit(30)
    )
    runs = list(result.scalars().unique().all())
    return [GenerationRunOut.model_validate(run) for run in runs]


async def _decide_image(
    image_id: uuid.UUID,
    decision: ApprovalDecision,
    body: ApprovalRequest,
    user: AuthUser,
    db: AsyncSession,
) -> ApprovalOut:
    image = await db.get(GeneratedImage, image_id)
    if image is None:
        raise HTTPException(status_code=404, detail="Image not found")

    membership = await get_membership(image.brand_id, user, db)
    require_admin(membership)

    if image.status != ImageStatus.pending_review:
        raise HTTPException(
            status_code=409,
            detail=f"Image is {image.status.value}, expected pending_review",
        )

    image.status = (
        ImageStatus.approved if decision == ApprovalDecision.approved else ImageStatus.rejected
    )
    approval = Approval(
        image_id=image.id,
        reviewer_id=user.id,
        decision=decision,
        note=body.note,
    )
    db.add(approval)
    await db.commit()
    await db.refresh(approval)

    if decision == ApprovalDecision.approved and image.storage_path:
        await promote_to_approved(image.storage_path)

    return ApprovalOut.model_validate(approval)


@router.post("/images/{image_id}/approve", response_model=ApprovalOut)
async def approve_image(
    image_id: uuid.UUID,
    body: ApprovalRequest,
    user: AuthUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApprovalOut:
    return await _decide_image(image_id, ApprovalDecision.approved, body, user, db)


@router.post("/images/{image_id}/reject", response_model=ApprovalOut)
async def reject_image(
    image_id: uuid.UUID,
    body: ApprovalRequest,
    user: AuthUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApprovalOut:
    return await _decide_image(image_id, ApprovalDecision.rejected, body, user, db)


@router.post("/internal/jobs/enqueue-daily", response_model=EnqueueDailyResponse)
async def enqueue_daily(
    _: None = Depends(verify_internal_secret),
    db: AsyncSession = Depends(get_db),
) -> EnqueueDailyResponse:
    """Cron-protected: enqueue generation for every active brand due now."""
    result = await db.execute(select(Brand).where(Brand.status == BrandStatus.active))
    brands = list(result.scalars().all())
    enqueued: list[uuid.UUID] = []
    now_utc = datetime.now(timezone.utc)

    for brand in brands:
        try:
            tz = ZoneInfo(brand.timezone)
        except Exception:
            tz = ZoneInfo("UTC")
        local_now = now_utc.astimezone(tz)
        scheduled_for = local_now.date()
        # Due if local time is at/after daily_run_at
        if local_now.timetz().replace(tzinfo=None) < brand.daily_run_at:
            continue

        existing = await db.execute(
            select(GenerationRun).where(
                GenerationRun.brand_id == brand.id,
                GenerationRun.scheduled_for == scheduled_for,
            )
        )
        if existing.scalar_one_or_none():
            continue

        run = GenerationRun(
            brand_id=brand.id,
            scheduled_for=scheduled_for,
        )
        db.add(run)
        try:
            await db.commit()
        except Exception:
            await db.rollback()
            logger.info("Run already exists for brand=%s date=%s", brand.id, scheduled_for)
            continue

        enqueue_daily_generate(brand.id, scheduled_for.isoformat())
        enqueued.append(brand.id)

    return EnqueueDailyResponse(enqueued=len(enqueued), brand_ids=enqueued)


@router.post("/internal/jobs/enqueue-brand/{brand_id}", response_model=EnqueueDailyResponse)
async def enqueue_brand(
    brand_id: uuid.UUID,
    scheduled_for: date | None = None,
    _: None = Depends(verify_internal_secret),
    db: AsyncSession = Depends(get_db),
) -> EnqueueDailyResponse:
    """Manually enqueue a brand generation (ops / local testing)."""
    brand = await db.get(Brand, brand_id)
    if brand is None:
        raise HTTPException(status_code=404, detail="Brand not found")

    day = scheduled_for or date.today()
    existing = await db.execute(
        select(GenerationRun).where(
            GenerationRun.brand_id == brand.id,
            GenerationRun.scheduled_for == day,
        ).order_by(GenerationRun.created_at.desc()).limit(1)
    )
    run = existing.scalar_one_or_none()
    if run is None:
        run = GenerationRun(brand_id=brand.id, scheduled_for=day)
        db.add(run)
        await db.commit()

    enqueue_daily_generate(brand.id, day.isoformat())
    return EnqueueDailyResponse(enqueued=1, brand_ids=[brand.id])


@router.post("/internal/jobs/test-orchestrate/{brand_id}", response_model=GenerationRunOut)
async def test_orchestrate(
    brand_id: uuid.UUID,
    scheduled_for: date | None = None,
    _: None = Depends(verify_internal_secret),
    db: AsyncSession = Depends(get_db),
) -> GenerationRunOut:
    """
    Test endpoint: directly run orchestrator without queue.
    Useful for development/debugging — blocks until complete.
    """
    brand = await db.get(Brand, brand_id)
    if brand is None:
        raise HTTPException(status_code=404, detail="Brand not found")

    day = scheduled_for or date.today()

    # Check/create generation run
    existing = await db.execute(
        select(GenerationRun).where(
            GenerationRun.brand_id == brand.id,
            GenerationRun.scheduled_for == day,
        ).order_by(GenerationRun.created_at.desc()).limit(1)
    )
    run = existing.scalar_one_or_none()
    if run is None:
        run = GenerationRun(brand_id=brand.id, scheduled_for=day)
        db.add(run)
        await db.commit()

    logger.info("Testing orchestrator for brand=%s date=%s", brand_id, day)

    try:
        return await _run_orchestrator_agent(brand_id, day, db)
    except Exception as e:
        logger.exception("Test orchestration failed")
        raise HTTPException(status_code=500, detail=str(e))
