from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import AuthUser, get_current_user, get_membership, require_admin
from app.core.db import get_db
from app.models.entities import Brand, BrandProfile
from app.schemas.api import BrandProfileOut, BrandProfileUpdate

router = APIRouter()


async def _get_or_create_profile(brand_id: uuid.UUID, db: AsyncSession) -> BrandProfile:
    result = await db.execute(select(BrandProfile).where(BrandProfile.brand_id == brand_id))
    profile = result.scalar_one_or_none()
    if profile is None:
        # Lazily create an empty profile row on first access rather than at
        # brand-creation time — simpler, and every brand ends up with exactly
        # one profile row the first time anyone looks at it.
        profile = BrandProfile(brand_id=brand_id)
        db.add(profile)
        await db.commit()
        await db.refresh(profile)
    return profile


@router.get("/brands/{brand_id}/profile", response_model=BrandProfileOut)
async def get_brand_profile(
    brand_id: uuid.UUID,
    user: AuthUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> BrandProfile:
    await get_membership(brand_id, user, db)
    brand = await db.get(Brand, brand_id)
    if brand is None:
        raise HTTPException(status_code=404, detail="Brand not found")
    return await _get_or_create_profile(brand_id, db)


@router.patch("/brands/{brand_id}/profile", response_model=BrandProfileOut)
async def update_brand_profile(
    brand_id: uuid.UUID,
    body: BrandProfileUpdate,
    user: AuthUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> BrandProfile:
    membership = await get_membership(brand_id, user, db)
    require_admin(membership)
    brand = await db.get(Brand, brand_id)
    if brand is None:
        raise HTTPException(status_code=404, detail="Brand not found")

    profile = await _get_or_create_profile(brand_id, db)
    data = body.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(profile, key, value)
    await db.commit()
    await db.refresh(profile)
    return profile
