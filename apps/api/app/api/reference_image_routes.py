from __future__ import annotations

import logging
import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import AuthUser, get_current_user, get_membership, require_admin
from app.core.db import get_db
from app.models.entities import Brand, ReferenceCategory, ReferenceImage
from app.schemas.api import ReferenceImageOut, ReferenceImagePriorityUpdate
from app.services.queue import enqueue_embed_reference_image
from app.services.storage import create_signed_url, create_signed_urls, upload_reference_image

logger = logging.getLogger(__name__)
router = APIRouter()

REFERENCE_BUCKET = "brand-references"

_ALLOWED_CONTENT_TYPES = {
    "image/png": "png",
    "image/jpeg": "jpg",
    "image/webp": "webp",
}


async def _to_out(image: ReferenceImage) -> ReferenceImageOut:
    out = ReferenceImageOut.model_validate(image)
    out.signed_url = await create_signed_url(image.storage_path, bucket=REFERENCE_BUCKET)
    return out


@router.post(
    "/brands/{brand_id}/reference-images",
    response_model=ReferenceImageOut,
    status_code=status.HTTP_201_CREATED,
)
async def upload_reference_image_route(
    brand_id: uuid.UUID,
    file: UploadFile = File(...),
    category: str = Form(default=ReferenceCategory.inspiration.value),
    title: str | None = Form(default=None),
    product_id: uuid.UUID | None = Form(default=None),
    user: AuthUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ReferenceImageOut:
    membership = await get_membership(brand_id, user, db)
    require_admin(membership)
    brand = await db.get(Brand, brand_id)
    if brand is None:
        raise HTTPException(status_code=404, detail="Brand not found")

    ext = _ALLOWED_CONTENT_TYPES.get(file.content_type or "")
    if ext is None:
        raise HTTPException(
            status_code=400, detail="Unsupported file type; use png, jpeg, or webp"
        )

    try:
        category_enum = ReferenceCategory(category)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid category") from exc

    reference_image = ReferenceImage(
        brand_id=brand_id,
        product_id=product_id,
        category=category_enum,
        storage_path="",
        title=title,
        embedding_status="pending",
        uploaded_by=user.id,
    )
    db.add(reference_image)
    await db.flush()

    storage_path = f"{brand_id}/{reference_image.id}.{ext}"
    content = await file.read()
    ok = await upload_reference_image(storage_path, content, file.content_type)
    if not ok:
        await db.rollback()
        raise HTTPException(status_code=502, detail="Failed to upload reference image")

    reference_image.storage_path = storage_path
    await db.commit()
    await db.refresh(reference_image)

    enqueue_embed_reference_image(reference_image.id)

    return await _to_out(reference_image)


@router.get("/brands/{brand_id}/reference-images", response_model=list[ReferenceImageOut])
async def list_reference_images(
    brand_id: uuid.UUID,
    category: str | None = Query(default=None),
    user: AuthUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[ReferenceImageOut]:
    await get_membership(brand_id, user, db)
    stmt = select(ReferenceImage).where(ReferenceImage.brand_id == brand_id)
    if category:
        try:
            stmt = stmt.where(ReferenceImage.category == ReferenceCategory(category))
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="Invalid category") from exc
    stmt = stmt.order_by(ReferenceImage.is_priority.desc(), ReferenceImage.uploaded_at.desc())
    result = await db.execute(stmt)
    images = list(result.scalars().all())
    urls = await create_signed_urls(
        [(image.storage_path, False) for image in images], bucket=REFERENCE_BUCKET
    )
    outs = [ReferenceImageOut.model_validate(image) for image in images]
    for out, url in zip(outs, urls):
        out.signed_url = url
    return outs


async def _get_reference_image_or_404(
    brand_id: uuid.UUID, ref_id: uuid.UUID, db: AsyncSession
) -> ReferenceImage:
    image = await db.get(ReferenceImage, ref_id)
    if image is None or image.brand_id != brand_id:
        raise HTTPException(status_code=404, detail="Reference image not found")
    return image


@router.patch(
    "/brands/{brand_id}/reference-images/{ref_id}", response_model=ReferenceImageOut
)
async def update_reference_image_priority(
    brand_id: uuid.UUID,
    ref_id: uuid.UUID,
    body: ReferenceImagePriorityUpdate,
    user: AuthUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ReferenceImageOut:
    membership = await get_membership(brand_id, user, db)
    require_admin(membership)
    image = await _get_reference_image_or_404(brand_id, ref_id, db)
    image.is_priority = body.is_priority
    await db.commit()
    await db.refresh(image)
    return await _to_out(image)


@router.delete(
    "/brands/{brand_id}/reference-images/{ref_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def delete_reference_image(
    brand_id: uuid.UUID,
    ref_id: uuid.UUID,
    user: AuthUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    membership = await get_membership(brand_id, user, db)
    require_admin(membership)
    image = await _get_reference_image_or_404(brand_id, ref_id, db)
    # Storage object cleanup is out of scope for this phase.
    await db.delete(image)
    await db.commit()
