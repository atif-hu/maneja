from __future__ import annotations

import logging
from typing import Any

import httpx

from orchestrator.config import get_settings

logger = logging.getLogger(__name__)


async def upload_draft(path: str, content: bytes, content_type: str = "image/png") -> None:
    settings = get_settings()
    if not settings.supabase_service_role_key:
        logger.warning("No service role key; skipping upload for %s", path)
        return

    url = f"{settings.supabase_url.rstrip('/')}/storage/v1/object/brand-drafts/{path}"
    headers = {
        "Authorization": f"Bearer {settings.supabase_service_role_key}",
        "apikey": settings.supabase_service_role_key,
        "Content-Type": content_type,
        "x-upsert": "true",
    }
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(url, headers=headers, content=content)
        if resp.status_code >= 400:
            logger.error("Upload failed %s: %s", resp.status_code, resp.text)
            resp.raise_for_status()


async def download_object(bucket: str, path: str) -> bytes | None:
    settings = get_settings()
    if not settings.supabase_service_role_key:
        logger.warning("No service role key; skipping download for %s/%s", bucket, path)
        return None

    url = f"{settings.supabase_url.rstrip('/')}/storage/v1/object/{bucket}/{path}"
    headers = {
        "Authorization": f"Bearer {settings.supabase_service_role_key}",
        "apikey": settings.supabase_service_role_key,
    }
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.get(url, headers=headers)
        if resp.status_code >= 400:
            logger.error("Download failed %s/%s: %s %s", bucket, path, resp.status_code, resp.text)
            return None
        return resp.content


async def move_to_approved(path: str) -> None:
    """Optional: copy draft object into approved bucket (best-effort)."""
    settings = get_settings()
    if not settings.supabase_service_role_key:
        return
    # Download then upload — simple and reliable across Supabase versions
    headers = {
        "Authorization": f"Bearer {settings.supabase_service_role_key}",
        "apikey": settings.supabase_service_role_key,
    }
    async with httpx.AsyncClient(timeout=60.0) as client:
        get_url = f"{settings.supabase_url.rstrip('/')}/storage/v1/object/brand-drafts/{path}"
        got = await client.get(get_url, headers=headers)
        if got.status_code >= 400:
            return
        put_url = f"{settings.supabase_url.rstrip('/')}/storage/v1/object/brand-approved/{path}"
        put_headers = {**headers, "Content-Type": "image/png", "x-upsert": "true"}
        await client.post(put_url, headers=put_headers, content=got.content)
