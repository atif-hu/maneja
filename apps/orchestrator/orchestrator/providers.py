from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from io import BytesIO

from PIL import Image, ImageDraw

from orchestrator.config import get_settings


@dataclass
class GeneratedAsset:
    image_bytes: bytes
    mime_type: str
    provider: str
    meta: dict


@dataclass
class ReferenceImage:
    """Reference image for style guidance."""
    image_bytes: bytes
    mime_type: str = "image/png"


class ImageProvider(ABC):
    @abstractmethod
    async def generate(
        self, prompt: str, *, slot: int, reference_images: list[ReferenceImage] | None = None
    ) -> GeneratedAsset:
        raise NotImplementedError


class StubImageProvider(ImageProvider):
    """Deterministic placeholder PNG for local/dev without API keys."""

    async def generate(
        self, prompt: str, *, slot: int, reference_images: list[ReferenceImage] | None = None
    ) -> GeneratedAsset:
        img = Image.new("RGB", (1024, 1024), color=(28, 42, 32))
        draw = ImageDraw.Draw(img)
        # Accent band
        draw.rectangle([0, 0, 1024, 120], fill=(196, 240, 130))
        draw.text((40, 40), f"Brand Manager · slot {slot}", fill=(19, 32, 20))
        # Prompt preview
        wrapped = prompt[:220] + ("…" if len(prompt) > 220 else "")
        y = 180
        for i in range(0, len(wrapped), 48):
            draw.text((40, y), wrapped[i : i + 48], fill=(242, 239, 230))
            y += 36
        buf = BytesIO()
        img.save(buf, format="PNG")
        return GeneratedAsset(
            image_bytes=buf.getvalue(),
            mime_type="image/png",
            provider="stub",
            meta={"slot": slot},
        )


class OpenAIImageProvider(ImageProvider):
    async def generate(
        self, prompt: str, *, slot: int, reference_images: list[ReferenceImage] | None = None
    ) -> GeneratedAsset:
        from openai import AsyncOpenAI

        settings = get_settings()
        if not settings.openai_api_key:
            raise RuntimeError("OPENAI_API_KEY is required for openai provider")

        client = AsyncOpenAI(api_key=settings.openai_api_key)
        result = await client.images.generate(
            model=settings.image_model,
            prompt=prompt,
            size="1024x1024",
            n=1,
        )
        item = result.data[0]
        # Prefer b64 if present; otherwise fetch URL
        if getattr(item, "b64_json", None):
            import base64

            raw = base64.b64decode(item.b64_json)
        elif getattr(item, "url", None):
            import httpx

            async with httpx.AsyncClient(timeout=60.0) as http:
                resp = await http.get(item.url)
                resp.raise_for_status()
                raw = resp.content
        else:
            raise RuntimeError("OpenAI image response missing b64_json and url")

        return GeneratedAsset(
            image_bytes=raw,
            mime_type="image/png",
            provider="openai",
            meta={"slot": slot, "model": settings.image_model},
        )


class ReplicateImageProvider(ImageProvider):
    async def generate(
        self, prompt: str, *, slot: int, reference_images: list[ReferenceImage] | None = None
    ) -> GeneratedAsset:
        import asyncio
        import os
        import httpx
        import replicate

        settings = get_settings()
        if not settings.replicate_api_key:
            raise RuntimeError("REPLICATE_API_KEY is required for replicate provider")

        os.environ["REPLICATE_API_TOKEN"] = settings.replicate_api_key

        def _run_replicate():
            return replicate.run(
                settings.image_model,
                input={
                    "prompt": prompt,
                    "aspect_ratio": "1:1",
                    "output_format": "png",
                    "resolution": "1K",
                },
            )

        output = await asyncio.to_thread(_run_replicate)

        if not output:
            raise RuntimeError("Replicate returned empty output")

        item = output[0] if isinstance(output, list) else output

        if isinstance(item, str):
            image_url = item
        elif hasattr(item, 'url'):
            image_url = item.url
        else:
            image_url = str(item)

        async with httpx.AsyncClient(timeout=60.0) as http:
            resp = await http.get(image_url)
            resp.raise_for_status()
            raw = resp.content

        return GeneratedAsset(
            image_bytes=raw,
            mime_type="image/png",
            provider="replicate",
            meta={"slot": slot, "model": settings.image_model, "url": image_url},
        )


class PollinationsImageProvider(ImageProvider):
    async def generate(
        self, prompt: str, *, slot: int, reference_images: list[ReferenceImage] | None = None
    ) -> GeneratedAsset:
        import httpx
        from urllib.parse import quote

        url = f"https://image.pollinations.ai/prompt/{quote(prompt)}"
        async with httpx.AsyncClient(timeout=120.0) as http:
            resp = await http.get(url)
            resp.raise_for_status()
            raw = resp.content

        return GeneratedAsset(
            image_bytes=raw,
            mime_type="image/png",
            provider="pollinations",
            meta={"slot": slot},
        )


def get_provider() -> ImageProvider:
    settings = get_settings()
    if settings.image_provider == "openai":
        return OpenAIImageProvider()
    if settings.image_provider == "replicate":
        return ReplicateImageProvider()
    if settings.image_provider == "pollinations":
        return PollinationsImageProvider()
    return StubImageProvider()
