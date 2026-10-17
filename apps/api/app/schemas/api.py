from __future__ import annotations

import re
import uuid
from datetime import date, datetime, time
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class BrandCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    slug: str | None = None
    timezone: str = "UTC"
    daily_run_at: time = time(9, 0)
    style_guide: str | None = None


class BrandUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    timezone: str | None = None
    daily_run_at: time | None = None
    style_guide: str | None = None
    status: str | None = None


class BrandOut(ORMModel):
    id: uuid.UUID
    name: str
    slug: str
    timezone: str
    daily_run_at: time
    status: str
    style_guide: str | None
    created_at: datetime
    updated_at: datetime


class BrandPromptCreate(BaseModel):
    name: str
    template: str
    is_active: bool = True
    sort_order: int = 0


class BrandPromptOut(ORMModel):
    id: uuid.UUID
    brand_id: uuid.UUID
    name: str
    template: str
    is_active: bool
    sort_order: int


class ContentIdeaSummary(ORMModel):
    headline: str
    rationale: str | None
    concept_type: str | None = None


class GeneratedImageOut(ORMModel):
    id: uuid.UUID
    run_id: uuid.UUID
    brand_id: uuid.UUID
    slot: int
    prompt: str
    storage_path: str | None
    status: str
    provider: str | None
    signed_url: str | None = None
    concept_type: str | None = None
    content_idea: ContentIdeaSummary | None = None
    created_at: datetime
    updated_at: datetime


class GenerationRunOut(ORMModel):
    id: uuid.UUID
    brand_id: uuid.UUID
    scheduled_for: date
    status: str
    agent_meta: dict[str, Any]
    error_message: str | None
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime
    images: list[GeneratedImageOut] = []


class ApprovalRequest(BaseModel):
    note: str | None = None


class ApprovalOut(ORMModel):
    id: uuid.UUID
    image_id: uuid.UUID
    reviewer_id: uuid.UUID
    decision: str
    note: str | None
    decided_at: datetime


class EnqueueDailyResponse(BaseModel):
    enqueued: int
    brand_ids: list[uuid.UUID]


class BrandProfileOut(ORMModel):
    id: uuid.UUID
    brand_id: uuid.UUID
    industry: str | None
    description: str | None
    website: str | None
    location: str | None
    target_customer: str | None
    audience_age_range: str | None
    audience_interests: str | None
    brand_colors: list[Any]
    typography: str | None
    photography_style: str | None
    tone: str | None
    voice: str | None
    brand_dna: list[Any]
    things_i_like: str | None
    things_i_dislike: str | None
    visual_elements_to_avoid: str | None
    words_to_avoid: str | None
    avoid_neon: bool
    avoid_clutter: bool
    creativity_level: int
    brand_consistency_level: int
    reference_priority_level: int
    content_diversity_level: int
    logo_storage_path: str | None
    created_at: datetime
    updated_at: datetime


class BrandProfileUpdate(BaseModel):
    industry: str | None = None
    description: str | None = None
    website: str | None = None
    location: str | None = None
    target_customer: str | None = None
    audience_age_range: str | None = None
    audience_interests: str | None = None
    brand_colors: list[Any] | None = None
    typography: str | None = None
    photography_style: str | None = None
    tone: str | None = None
    voice: str | None = None
    brand_dna: list[Any] | None = None
    things_i_like: str | None = None
    things_i_dislike: str | None = None
    visual_elements_to_avoid: str | None = None
    words_to_avoid: str | None = None
    avoid_neon: bool | None = None
    avoid_clutter: bool | None = None
    creativity_level: int | None = Field(default=None, ge=1, le=3)
    brand_consistency_level: int | None = Field(default=None, ge=1, le=3)
    reference_priority_level: int | None = Field(default=None, ge=1, le=3)
    content_diversity_level: int | None = Field(default=None, ge=1, le=3)
    logo_storage_path: str | None = None


class ProductCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str | None = None
    price: str | None = None
    category: str | None = None
    is_active: bool = True


class ProductUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    price: str | None = None
    category: str | None = None
    is_active: bool | None = None


class ProductOut(ORMModel):
    id: uuid.UUID
    brand_id: uuid.UUID
    name: str
    description: str | None
    price: str | None
    category: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class ContentPillarCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    description: str | None = None
    sort_order: int = 0


class ContentPillarUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = None
    sort_order: int | None = None


class ContentPillarOut(ORMModel):
    id: uuid.UUID
    brand_id: uuid.UUID
    name: str
    description: str | None
    sort_order: int
    created_at: datetime


class ReferenceImageOut(ORMModel):
    id: uuid.UUID
    brand_id: uuid.UUID
    product_id: uuid.UUID | None
    category: str
    storage_path: str
    signed_url: str | None = None
    title: str | None
    is_priority: bool
    usage_count: int
    embedding_status: str
    uploaded_at: datetime


class ReferenceImagePriorityUpdate(BaseModel):
    is_priority: bool


class NotificationOut(ORMModel):
    id: uuid.UUID
    brand_id: uuid.UUID
    type: str
    title: str
    body: str | None
    link_path: str | None
    read_at: datetime | None
    created_at: datetime


class OnDemandGenerateRequest(BaseModel):
    promotion: str
    content_type: str | None = None
    platform: str | None = None


class BrandStatsOut(BaseModel):
    pending_review: int
    approved_this_week: int
    rejected_this_week: int
    total_reference_images: int


class GoogleCallbackResponse(BaseModel):
    user_id: str
    email: str
    name: str | None
    access_token: str
    message: str


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "brand"
