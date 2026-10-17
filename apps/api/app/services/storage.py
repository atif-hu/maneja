from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

import httpx
from supabase import Client, create_client

from app.core.config import get_settings

logger = logging.getLogger(__name__)


_client: httpx.AsyncClient | None = None
_url_cache: dict[tuple[str, str], tuple[float, str]] = {}
_URL_CACHE_MAX = 2000
_URL_REFRESH_MARGIN = 300


def _get_client() -> httpx.AsyncClient:
    global _client
    if _client is None or _client.is_closed:
        _client = httpx.AsyncClient(
            timeout=15.0,
            limits=httpx.Limits(max_connections=50, max_keepalive_connections=20),
        )
    return _client


async def close_client() -> None:
    global _client
    if _client is not None and not _client.is_closed:
        await _client.aclose()
    _client = None


async def create_signed_urls(
    items: list[tuple[str | None, bool]],
    *,
    bucket: str | None = None,
) -> list[str | None]:
    """Sign many paths concurrently. `items` is (storage_path, approved)."""
    sem = asyncio.Semaphore(16)

    async def one(path: str | None, approved: bool) -> str | None:
        async with sem:
            return await create_signed_url(path, approved=approved, bucket=bucket)

    return list(await asyncio.gather(*(one(p, a) for p, a in items)))


def get_supabase_admin() -> Client:
    settings = get_settings()
    return create_client(settings.supabase_url, settings.supabase_service_role_key)


async def create_signed_url(
    storage_path: str | None,
    *,
    approved: bool = False,
    bucket: str | None = None,
    expires_in: int = 3600,
) -> str | None:
    """
    Create a signed URL for a storage object.

    `bucket` selects the bucket directly (e.g. "brand-references"). When omitted,
    falls back to the original brand-drafts/brand-approved behavior selected by
    `approved`, including the draft-fallback retry for images not yet promoted.
    """
    if not storage_path:
        return None
    settings = get_settings()
    if not settings.supabase_service_role_key:
        return None

    explicit_bucket = bucket is not None
    bucket = bucket or ("brand-approved" if approved else "brand-drafts")
    cache_key = (bucket, storage_path)
    cached = _url_cache.get(cache_key)
    now = time.monotonic()
    if cached and cached[0] - now > _URL_REFRESH_MARGIN:
        return cached[1]
    url = f"{settings.supabase_url.rstrip('/')}/storage/v1/object/sign/{bucket}/{storage_path}"
    headers = {
        "Authorization": f"Bearer {settings.supabase_service_role_key}",
        "apikey": settings.supabase_service_role_key,
        "Content-Type": "application/json",
    }
    try:
        client = _get_client()
        resp = await client.post(url, headers=headers, json={"expiresIn": expires_in})
        if resp.status_code >= 400 and not explicit_bucket and approved:
            url = (
                f"{settings.supabase_url.rstrip('/')}/storage/v1/object/sign/"
                f"brand-drafts/{storage_path}"
            )
            resp = await client.post(url, headers=headers, json={"expiresIn": expires_in})
        resp.raise_for_status()
        data: dict[str, Any] = resp.json()
        signed = data.get("signedURL") or data.get("signedUrl")
        if not signed:
            return None
        if not signed.startswith("http"):
            signed = f"{settings.supabase_url.rstrip('/')}/storage/v1{signed}"
        if len(_url_cache) >= _URL_CACHE_MAX:
            _url_cache.clear()
        _url_cache[cache_key] = (now + expires_in, signed)
        return signed
    except Exception:
        logger.exception("Failed to create signed URL for %s", storage_path)
        return None


async def upload_reference_image(
    storage_path: str, content: bytes, content_type: str | None
) -> bool:
    """Upload reference image bytes to the brand-references bucket (service-role, upsert)."""
    settings = get_settings()
    if not settings.supabase_service_role_key:
        return False
    headers = {
        "Authorization": f"Bearer {settings.supabase_service_role_key}",
        "apikey": settings.supabase_service_role_key,
        "Content-Type": content_type or "application/octet-stream",
        "x-upsert": "true",
    }
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            url = (
                f"{settings.supabase_url.rstrip('/')}/storage/v1/object/"
                f"brand-references/{storage_path}"
            )
            resp = await client.post(url, headers=headers, content=content)
            if resp.status_code >= 400:
                logger.warning(
                    "Reference image upload failed for %s: %s", storage_path, resp.text
                )
                return False
            return True
    except Exception:
        logger.exception("upload_reference_image failed for %s", storage_path)
        return False


async def promote_to_approved(storage_path: str) -> None:
    """Copy a draft object into the approved bucket (best-effort)."""
    settings = get_settings()
    if not settings.supabase_service_role_key:
        return
    headers = {
        "Authorization": f"Bearer {settings.supabase_service_role_key}",
        "apikey": settings.supabase_service_role_key,
    }
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            get_url = (
                f"{settings.supabase_url.rstrip('/')}/storage/v1/object/brand-drafts/{storage_path}"
            )
            got = await client.get(get_url, headers=headers)
            if got.status_code >= 400:
                logger.warning("Could not download draft %s: %s", storage_path, got.status_code)
                return
            put_url = (
                f"{settings.supabase_url.rstrip('/')}/storage/v1/object/brand-approved/{storage_path}"
            )
            put_headers = {**headers, "Content-Type": "image/png", "x-upsert": "true"}
            put = await client.post(put_url, headers=put_headers, content=got.content)
            if put.status_code >= 400:
                logger.warning("Promote failed for %s: %s", storage_path, put.text)
    except Exception:
        logger.exception("promote_to_approved failed for %s", storage_path)
