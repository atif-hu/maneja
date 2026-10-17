from __future__ import annotations

import enum
import uuid
from datetime import date, datetime, time
from typing import Any

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    SmallInteger,
    Text,
    Time,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class MemberRole(str, enum.Enum):
    owner = "owner"
    admin = "admin"
    viewer = "viewer"


class BrandStatus(str, enum.Enum):
    active = "active"
    paused = "paused"
    archived = "archived"


class RunStatus(str, enum.Enum):
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"


class ImageStatus(str, enum.Enum):
    generating = "generating"
    pending_review = "pending_review"
    approved = "approved"
    rejected = "rejected"
    archived = "archived"


class ApprovalDecision(str, enum.Enum):
    approved = "approved"
    rejected = "rejected"


class ConceptType(str, enum.Enum):
    product = "product"
    lifestyle = "lifestyle"
    engagement = "engagement"


class ReferenceCategory(str, enum.Enum):
    products = "products"
    brand = "brand"
    lifestyle = "lifestyle"
    people = "people"
    locations = "locations"
    inspiration = "inspiration"


class NotificationType(str, enum.Enum):
    generation_ready = "generation_ready"
    system = "system"


class EmbeddingSource(str, enum.Enum):
    reference_image = "reference_image"
    generated_image = "generated_image"


class SocialPlatform(str, enum.Enum):
    instagram = "instagram"
    facebook = "facebook"


class PostStatus(str, enum.Enum):
    draft = "draft"
    scheduled = "scheduled"
    published = "published"
    failed = "failed"


class RunKind(str, enum.Enum):
    scheduled = "scheduled"
    on_demand = "on_demand"


class Brand(Base):
    __tablename__ = "brands"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    slug: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    timezone: Mapped[str] = mapped_column(Text, nullable=False, default="UTC")
    daily_run_at: Mapped[time] = mapped_column(Time, nullable=False)
    status: Mapped[BrandStatus] = mapped_column(
        Enum(BrandStatus, name="brand_status", create_type=False),
        nullable=False,
        default=BrandStatus.active,
    )
    style_guide: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    members: Mapped[list[BrandMember]] = relationship(back_populates="brand")
    prompts: Mapped[list[BrandPrompt]] = relationship(back_populates="brand")
    runs: Mapped[list[GenerationRun]] = relationship(back_populates="brand")


class BrandMember(Base):
    __tablename__ = "brand_members"
    __table_args__ = (UniqueConstraint("brand_id", "user_id"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    brand_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("brands.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    role: Mapped[MemberRole] = mapped_column(
        Enum(MemberRole, name="member_role", create_type=False),
        nullable=False,
        default=MemberRole.viewer,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    brand: Mapped[Brand] = relationship(back_populates="members")


class BrandPrompt(Base):
    __tablename__ = "brand_prompts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    brand_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("brands.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(Text, nullable=False)
    template: Mapped[str] = mapped_column(Text, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    brand: Mapped[Brand] = relationship(back_populates="prompts")


class GenerationRun(Base):
    __tablename__ = "generation_runs"
    __table_args__ = (
        # Partial unique index: only the cron-scheduled path is once-per-day;
        # on-demand ("generate now") runs may coexist with the day's scheduled run.
        Index(
            "generation_runs_scheduled_unique",
            "brand_id",
            "scheduled_for",
            unique=True,
            postgresql_where=text("run_type = 'scheduled'"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    brand_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("brands.id", ondelete="CASCADE"), nullable=False
    )
    scheduled_for: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[RunStatus] = mapped_column(
        Enum(RunStatus, name="run_status", create_type=False),
        nullable=False,
        default=RunStatus.pending,
    )
    run_type: Mapped[RunKind] = mapped_column(
        Enum(RunKind, name="run_kind", create_type=False),
        nullable=False,
        default=RunKind.scheduled,
    )
    agent_meta: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    error_message: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    brand: Mapped[Brand] = relationship(back_populates="runs")
    images: Mapped[list[GeneratedImage]] = relationship(back_populates="run")


class GeneratedImage(Base):
    __tablename__ = "generated_images"
    __table_args__ = (UniqueConstraint("run_id", "slot"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("generation_runs.id", ondelete="CASCADE"), nullable=False
    )
    brand_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("brands.id", ondelete="CASCADE"), nullable=False
    )
    slot: Mapped[int] = mapped_column(Integer, nullable=False)
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    storage_path: Mapped[str | None] = mapped_column(Text)
    status: Mapped[ImageStatus] = mapped_column(
        Enum(ImageStatus, name="image_status", create_type=False),
        nullable=False,
        default=ImageStatus.generating,
    )
    provider: Mapped[str | None] = mapped_column(Text)
    provider_meta: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    content_idea_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("content_ideas.id", ondelete="SET NULL")
    )
    concept_type: Mapped[ConceptType | None] = mapped_column(
        Enum(ConceptType, name="concept_type", create_type=False)
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    run: Mapped[GenerationRun] = relationship(back_populates="images")
    approvals: Mapped[list[Approval]] = relationship(back_populates="image")


class Approval(Base):
    __tablename__ = "approvals"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    image_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("generated_images.id", ondelete="CASCADE"), nullable=False
    )
    reviewer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    decision: Mapped[ApprovalDecision] = mapped_column(
        Enum(ApprovalDecision, name="approval_decision", create_type=False),
        nullable=False,
    )
    note: Mapped[str | None] = mapped_column(Text)
    decided_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    image: Mapped[GeneratedImage] = relationship(back_populates="approvals")


class BrandProfile(Base):
    __tablename__ = "brand_profiles"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    brand_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("brands.id", ondelete="CASCADE"), nullable=False, unique=True
    )

    # Business
    industry: Mapped[str | None] = mapped_column(Text)
    description: Mapped[str | None] = mapped_column(Text)
    website: Mapped[str | None] = mapped_column(Text)
    location: Mapped[str | None] = mapped_column(Text)

    # Audience
    target_customer: Mapped[str | None] = mapped_column(Text)
    audience_age_range: Mapped[str | None] = mapped_column(Text)
    audience_interests: Mapped[str | None] = mapped_column(Text)

    # Visual identity
    brand_colors: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    typography: Mapped[str | None] = mapped_column(Text)
    photography_style: Mapped[str | None] = mapped_column(Text)

    # Content personality
    tone: Mapped[str | None] = mapped_column(Text)
    voice: Mapped[str | None] = mapped_column(Text)
    brand_dna: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)

    # Preferences / avoid-list
    things_i_like: Mapped[str | None] = mapped_column(Text)
    things_i_dislike: Mapped[str | None] = mapped_column(Text)
    visual_elements_to_avoid: Mapped[str | None] = mapped_column(Text)
    words_to_avoid: Mapped[str | None] = mapped_column(Text)
    avoid_neon: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    avoid_clutter: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # AI behaviour sliders (1-3)
    creativity_level: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=2)
    brand_consistency_level: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=3)
    reference_priority_level: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=3)
    content_diversity_level: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=2)

    logo_storage_path: Mapped[str | None] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Product(Base):
    __tablename__ = "products"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    brand_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("brands.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    price: Mapped[str | None] = mapped_column(Text)
    category: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ContentPillar(Base):
    __tablename__ = "content_pillars"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    brand_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("brands.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ReferenceImage(Base):
    __tablename__ = "reference_images"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    brand_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("brands.id", ondelete="CASCADE"), nullable=False
    )
    product_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("products.id", ondelete="SET NULL")
    )
    category: Mapped[ReferenceCategory] = mapped_column(
        Enum(ReferenceCategory, name="reference_category", create_type=False),
        nullable=False,
        default=ReferenceCategory.inspiration,
    )
    storage_path: Mapped[str] = mapped_column(Text, nullable=False)
    title: Mapped[str | None] = mapped_column(Text)
    is_priority: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    usage_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    ai_caption: Mapped[str | None] = mapped_column(Text)
    ai_tags: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    embedding_status: Mapped[str] = mapped_column(Text, nullable=False, default="pending")
    uploaded_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ImageEmbedding(Base):
    __tablename__ = "image_embeddings"
    __table_args__ = (UniqueConstraint("source_type", "source_id"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    brand_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("brands.id", ondelete="CASCADE"), nullable=False
    )
    source_type: Mapped[EmbeddingSource] = mapped_column(
        Enum(EmbeddingSource, name="embedding_source", create_type=False), nullable=False
    )
    source_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    model: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[Any] = mapped_column(Vector(512), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ContentIdea(Base):
    __tablename__ = "content_ideas"
    __table_args__ = (UniqueConstraint("run_id", "slot"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("generation_runs.id", ondelete="CASCADE"), nullable=False
    )
    brand_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("brands.id", ondelete="CASCADE"), nullable=False
    )
    slot: Mapped[int] = mapped_column(Integer, nullable=False)
    concept_type: Mapped[ConceptType | None] = mapped_column(
        Enum(ConceptType, name="concept_type", create_type=False)
    )
    headline: Mapped[str] = mapped_column(Text, nullable=False)
    rationale: Mapped[str | None] = mapped_column(Text)
    content_pillar_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("content_pillars.id", ondelete="SET NULL")
    )
    product_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("products.id", ondelete="SET NULL")
    )
    reference_image_ids: Mapped[list[uuid.UUID]] = mapped_column(
        ARRAY(UUID(as_uuid=True)), nullable=False, default=list
    )
    prompt_brief: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    brand_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("brands.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    type: Mapped[NotificationType] = mapped_column(
        Enum(NotificationType, name="notification_type", create_type=False),
        nullable=False,
        default=NotificationType.generation_ready,
    )
    title: Mapped[str] = mapped_column(Text, nullable=False)
    body: Mapped[str | None] = mapped_column(Text)
    link_path: Mapped[str | None] = mapped_column(Text)
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class SocialAccount(Base):
    __tablename__ = "social_accounts"
    __table_args__ = (UniqueConstraint("brand_id", "platform"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    brand_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("brands.id", ondelete="CASCADE"), nullable=False
    )
    platform: Mapped[SocialPlatform] = mapped_column(
        Enum(SocialPlatform, name="social_platform", create_type=False), nullable=False
    )
    external_account_id: Mapped[str | None] = mapped_column(Text)
    display_name: Mapped[str | None] = mapped_column(Text)
    access_token_encrypted: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(Text, nullable=False, default="disconnected")
    connected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ScheduledPost(Base):
    __tablename__ = "scheduled_posts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    brand_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("brands.id", ondelete="CASCADE"), nullable=False
    )
    image_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("generated_images.id", ondelete="CASCADE"), nullable=False
    )
    social_account_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("social_accounts.id", ondelete="SET NULL")
    )
    platform: Mapped[SocialPlatform] = mapped_column(
        Enum(SocialPlatform, name="social_platform", create_type=False), nullable=False
    )
    caption: Mapped[str | None] = mapped_column(Text)
    scheduled_for: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[PostStatus] = mapped_column(
        Enum(PostStatus, name="post_status", create_type=False),
        nullable=False,
        default=PostStatus.draft,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class PublishingEvent(Base):
    __tablename__ = "publishing_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scheduled_post_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("scheduled_posts.id", ondelete="CASCADE"), nullable=False
    )
    event_type: Mapped[str] = mapped_column(Text, nullable=False)
    detail: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
