from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import AuthUser, get_current_user, get_membership, require_admin
from app.core.db import get_db
from app.models.entities import ContentPillar
from app.schemas.api import ContentPillarCreate, ContentPillarOut, ContentPillarUpdate

router = APIRouter()


@router.get("/brands/{brand_id}/pillars", response_model=list[ContentPillarOut])
async def list_pillars(
    brand_id: uuid.UUID,
    user: AuthUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[ContentPillar]:
    await get_membership(brand_id, user, db)
    result = await db.execute(
        select(ContentPillar)
        .where(ContentPillar.brand_id == brand_id)
        .order_by(ContentPillar.sort_order, ContentPillar.name)
    )
    return list(result.scalars().all())


@router.post(
    "/brands/{brand_id}/pillars",
    response_model=ContentPillarOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_pillar(
    brand_id: uuid.UUID,
    body: ContentPillarCreate,
    user: AuthUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ContentPillar:
    membership = await get_membership(brand_id, user, db)
    require_admin(membership)
    pillar = ContentPillar(brand_id=brand_id, **body.model_dump())
    db.add(pillar)
    await db.commit()
    await db.refresh(pillar)
    return pillar


async def _get_pillar_or_404(pillar_id: uuid.UUID, db: AsyncSession) -> ContentPillar:
    pillar = await db.get(ContentPillar, pillar_id)
    if pillar is None:
        raise HTTPException(status_code=404, detail="Content pillar not found")
    return pillar


@router.patch("/pillars/{pillar_id}", response_model=ContentPillarOut)
async def update_pillar(
    pillar_id: uuid.UUID,
    body: ContentPillarUpdate,
    user: AuthUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ContentPillar:
    pillar = await _get_pillar_or_404(pillar_id, db)
    membership = await get_membership(pillar.brand_id, user, db)
    require_admin(membership)
    data = body.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(pillar, key, value)
    await db.commit()
    await db.refresh(pillar)
    return pillar


@router.delete("/pillars/{pillar_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_pillar(
    pillar_id: uuid.UUID,
    user: AuthUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    pillar = await _get_pillar_or_404(pillar_id, db)
    membership = await get_membership(pillar.brand_id, user, db)
    require_admin(membership)
    await db.delete(pillar)
    await db.commit()
