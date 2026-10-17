from __future__ import annotations

import json
import logging
import uuid

from redis import Redis

from app.core.config import get_settings

logger = logging.getLogger(__name__)

QUEUE_KEY = "brand-manager:jobs:daily_generate"
EMBED_QUEUE_KEY = "brand-manager:jobs:embed_reference_image"


def get_redis() -> Redis:
    return Redis.from_url(get_settings().redis_url, decode_responses=True)


def enqueue_daily_generate(brand_id: uuid.UUID, scheduled_for: str) -> None:
    """Push a generation job for the orchestrator worker."""
    payload = {
        "type": "daily_generate",
        "brand_id": str(brand_id),
        "scheduled_for": scheduled_for,
    }
    client = get_redis()
    client.rpush(QUEUE_KEY, json.dumps(payload))
    logger.info("Enqueued daily_generate for brand=%s date=%s", brand_id, scheduled_for)


def enqueue_embed_reference_image(reference_image_id: uuid.UUID) -> None:
    """Push an embedding job for the orchestrator worker to process a reference image."""
    payload = {
        "type": "embed_reference_image",
        "reference_image_id": str(reference_image_id),
    }
    client = get_redis()
    client.rpush(EMBED_QUEUE_KEY, json.dumps(payload))
    logger.info("Enqueued embed_reference_image for reference_image=%s", reference_image_id)
