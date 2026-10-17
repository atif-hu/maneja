from __future__ import annotations

import json
import logging
import re

from anthropic import AsyncAnthropic

from orchestrator.config import get_settings

logger = logging.getLogger(__name__)



def _strip_code_fences(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z]*\n?", "", text)
        text = re.sub(r"\n?```$", "", text)
    return text.strip()


def _slider(name: str, level: int | None, low: str, mid: str, high: str) -> str:
    level = level or 2
    text = {1: low, 2: mid, 3: high}.get(level, mid)
    return f"- {name} ({level}/3): {text}"


def _format_brand_memory(brand_memory: dict, on_demand_brief: dict | None) -> str:
    brand = brand_memory.get("brand") or {}
    profile = brand_memory.get("profile") or {}
    products = brand_memory.get("products") or []
    reference_images = brand_memory.get("reference_images") or []
    history = brand_memory.get("approval_history") or []

    products_text = "\n".join(
        f"  - {p['name']} ({p.get('category') or 'uncategorised'}): {p.get('description') or ''}"
        for p in products
    ) or "  (none configured yet)"

    reference_text = "\n".join(
        f"  - {img.get('storage_path', 'unknown')} {'(priority)' if img.get('is_priority') else ''}"
        for img in reference_images
    ) or "  (none uploaded yet — will fall back to Google image search)"

    if history:
        lines = []
        for h in history[:15]:
            note = f' — reviewer note: "{h["note"]}"' if h.get("note") else ""
            when = h["decided_at"].date().isoformat() if h.get("decided_at") else "unknown date"
            lines.append(
                f'  - [{when}] {h.get("decision")}: "{h.get("headline") or ""}{note}'
            )
        history_text = "\n".join(lines)
    else:
        history_text = "  (no approval history yet — this may be an early run for this brand)"

    on_demand_text = ""
    if on_demand_brief:
        on_demand_text = f"""

THIS IS AN ON-DEMAND REQUEST
The brand owner triggered this generation right now (not the routine daily run) with this brief:
- Requested content type: {on_demand_brief.get('content_type', 'n/a')}
- Promotion / focus: {on_demand_brief.get('promotion', 'n/a')}
- Target platform: {on_demand_brief.get('platform', 'n/a')}
Bias the concept whose subject/angle matches the requested content type most strongly toward this brief.
The other two concepts should still be generated normally, but may also nod to the target platform."""

    return f"""BRAND IDENTITY
- Name: {brand.get('name', 'Unknown')}
- Industry: {profile.get('industry') or 'n/a'}
- Description: {profile.get('description') or 'n/a'}
- Location: {profile.get('location') or 'n/a'}
- Legacy style guide notes: {brand.get('style_guide') or 'n/a'}

AUDIENCE
- Target customer: {profile.get('target_customer') or 'n/a'}
- Age range: {profile.get('audience_age_range') or 'n/a'}
- Interests: {profile.get('audience_interests') or 'n/a'}

VISUAL IDENTITY
- Brand colors: {json.dumps(profile.get('brand_colors') or [])}
- Typography: {profile.get('typography') or 'n/a'}
- Photography style: {profile.get('photography_style') or 'n/a'}

CONTENT PERSONALITY
- Tone: {profile.get('tone') or 'n/a'}
- Voice: {profile.get('voice') or 'n/a'}
- Brand DNA adjectives: {json.dumps(profile.get('brand_dna') or [])}

PREFERENCES / AVOID-LIST
- Things they like: {profile.get('things_i_like') or 'n/a'}
- Things they dislike: {profile.get('things_i_dislike') or 'n/a'}
- Visual elements to avoid: {profile.get('visual_elements_to_avoid') or 'n/a'}
- Words to avoid: {profile.get('words_to_avoid') or 'n/a'}
- Avoid neon: {profile.get('avoid_neon', False)}
- Avoid clutter: {profile.get('avoid_clutter', False)}

AI BEHAVIOUR SETTINGS (owner-configured, 1-3 scale)
{_slider("Creativity", profile.get('creativity_level'), "stay very safe and predictably on-brand", "balance safe execution with fresh ideas", "be highly experimental and surprising")}
{_slider("Brand consistency", profile.get('brand_consistency_level'), "a loose interpretation of the visual identity is fine", "follow the visual identity reasonably closely", "strictly and literally follow the visual identity")}
{_slider("Reference image priority", profile.get('reference_priority_level'), "treat reference images as loose inspiration only", "let reference images meaningfully inform the concept", "concepts must closely match the style/design of reference images")}
{_slider("Content diversity", profile.get('content_diversity_level'), "stay close to what has worked before", "mix familiar ideas with new ones", "actively explore new territory versus past content")}

REFERENCE IMAGES (Visual Style Guide)
{reference_text}
These images represent the exact visual style, design, aesthetic, and quality the brand owner wants.
Every concept MUST align with the style and design of these reference images. They are the source of truth for visual direction.

PRODUCTS / SERVICES
{products_text}

APPROVAL HISTORY (last 14 days, most recent first — real reviewer decisions and notes)
{history_text}{on_demand_text}"""


class ClaudePromptOrchestrator:
    def __init__(self) -> None:
        settings = get_settings()
        if not settings.claude_api_key:
            raise RuntimeError("CLAUDE_API_KEY is required for Claude orchestration")
        self.client = AsyncAnthropic(api_key=settings.claude_api_key)

    async def generate_daily_concepts(
        self,
        brand_memory: dict,
        on_demand_brief: dict | None = None,
        reference_images: list[bytes] | None = None,
    ) -> list[dict]:
        """Generate exactly 3 distinct content concepts grounded in the brand's full
        memory (identity, audience, visual identity, tone, avoid-lists, AI-behaviour
        sliders, reference images for style guide, products, and real approval
        history with reviewer notes). Reference images are passed as actual image bytes
        for visual context."""
        context = _format_brand_memory(brand_memory, on_demand_brief)

        instruction = f"""You are the concept-planning step for an automated brand content generator.

{context}

TASK
Generate exactly THREE distinct content concepts for today. These must NOT be 3 stylistic variations of
one idea — each concept should be genuinely different in subject, mood, or angle while remaining
authentic to the brand.

CRITICAL: Every concept MUST align with the style, design, aesthetic, and quality shown in the reference
images attached below. These images are the definitive visual guide — use them as the primary inspiration
and source of truth. All concepts must feel like they belong with those reference images.

Ground the headline, rationale, and prompt for each concept in the brand identity, audience, visual
identity, tone, avoid-lists, AI-behaviour settings, and ESPECIALLY the visual style of the reference images.
Critically, use the approval history: lean into what reviewers have approved before, and steer away
from anything a rejection note called out.

Where a product genuinely fits a concept, reference it by its exact name from PRODUCTS / SERVICES above;
otherwise use an empty string.

Return ONLY valid JSON — no markdown code fences, no commentary before or after — matching exactly this
schema:
{{
  "concepts": [
    {{"headline": "...", "rationale": "...", "prompt": "...", "content_pillar": "", "product": "..."}},
    {{"headline": "...", "rationale": "...", "prompt": "...", "content_pillar": "", "product": "..."}},
    {{"headline": "...", "rationale": "...", "prompt": "...", "content_pillar": "", "product": "..."}}
  ]
}}

The "prompt" field must be a detailed, standalone image-generation prompt (100-150 words) describing the
actual scene. ALWAYS emphasize matching the style and visual language of the reference images in the prompt."""

        messages: list[dict] = [{"role": "user", "content": self._build_message_content(instruction, reference_images)}]
        response_text = await self._call(messages)
        concepts = self._parse(response_text)

        if concepts is None:
            logger.warning("Concept response failed validation; retrying once with a re-ask")
            messages.append({"role": "assistant", "content": response_text})
            messages.append(
                {
                    "role": "user",
                    "content": (
                        "That reply was not valid JSON matching the required schema (exactly 3 "
                        "objects, each with a non-empty headline and prompt). Reply again with ONLY the "
                        "corrected JSON object — no markdown fences, no commentary."
                    ),
                }
            )
            response_text = await self._call(messages)
            concepts = self._parse(response_text)
            if concepts is None:
                logger.error("Failed to parse concept response after retry: %s", response_text)
                raise RuntimeError("Failed to parse concept orchestration response after retry")

        return concepts

    def _build_message_content(self, instruction: str, reference_images: list[bytes] | None) -> list[dict] | str:
        """Build message content with text and optional vision attachments."""
        if not reference_images:
            return instruction

        import base64

        content = [{"type": "text", "text": instruction}]
        for i, image_bytes in enumerate(reference_images):
            b64 = base64.standard_b64encode(image_bytes).decode("utf-8")
            content.append(
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/png",
                        "data": b64,
                    },
                }
            )
        return content

    async def _call(self, messages: list[dict]) -> str:
        settings = get_settings()
        message = await self.client.messages.create(
            model=settings.claude_model,
            max_tokens=3000,
            messages=messages,
        )
        # Some models return non-text blocks first (e.g. extended-thinking
        # ThinkingBlock) — find the first actual text block rather than
        # assuming content[0] is text.
        for block in message.content:
            if getattr(block, "type", None) == "text":
                return block.text
        raise RuntimeError("Claude response contained no text block")

    def _parse(self, response_text: str) -> list[dict] | None:
        cleaned = _strip_code_fences(response_text)
        try:
            data = json.loads(cleaned)
            concepts = data["concepts"]
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            logger.warning("Concept response parse error: %s", e)
            return None

        if not isinstance(concepts, list) or len(concepts) != 3:
            logger.warning("Expected exactly 3 concepts, got %s", len(concepts) if isinstance(concepts, list) else concepts)
            return None

        for c in concepts:
            if not c.get("headline") or not c.get("prompt"):
                logger.warning("Concept missing headline/prompt: %s", c)
                return None

        return concepts
