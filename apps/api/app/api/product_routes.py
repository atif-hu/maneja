from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import AuthUser, get_current_user, get_membership, require_admin
from app.core.db import get_db
from app.models.entities import Product
from app.schemas.api import ProductCreate, ProductOut, ProductUpdate

router = APIRouter()


@router.get("/brands/{brand_id}/products", response_model=list[ProductOut])
async def list_products(
    brand_id: uuid.UUID,
    user: AuthUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[Product]:
    await get_membership(brand_id, user, db)
    result = await db.execute(
        select(Product).where(Product.brand_id == brand_id).order_by(Product.name)
    )
    return list(result.scalars().all())


@router.post(
    "/brands/{brand_id}/products",
    response_model=ProductOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_product(
    brand_id: uuid.UUID,
    body: ProductCreate,
    user: AuthUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Product:
    membership = await get_membership(brand_id, user, db)
    require_admin(membership)
    product = Product(brand_id=brand_id, **body.model_dump())
    db.add(product)
    await db.commit()
    await db.refresh(product)
    return product


async def _get_product_or_404(product_id: uuid.UUID, db: AsyncSession) -> Product:
    product = await db.get(Product, product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.patch("/products/{product_id}", response_model=ProductOut)
async def update_product(
    product_id: uuid.UUID,
    body: ProductUpdate,
    user: AuthUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Product:
    product = await _get_product_or_404(product_id, db)
    membership = await get_membership(product.brand_id, user, db)
    require_admin(membership)
    data = body.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(product, key, value)
    await db.commit()
    await db.refresh(product)
    return product


@router.delete("/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: uuid.UUID,
    user: AuthUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    product = await _get_product_or_404(product_id, db)
    membership = await get_membership(product.brand_id, user, db)
    require_admin(membership)
    await db.delete(product)
    await db.commit()
