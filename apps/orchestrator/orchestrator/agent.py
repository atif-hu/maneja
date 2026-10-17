from __future__ import annotations

import asyncio
import json
import logging
import uuid
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from orchestrator.config import get_settings
from orchestrator.providers import get_provider
from orchestrator.embeddings import get_embedding_provider, to_vector_literal
from orchestrator.storage import upload_draft, download_object
from orchestrator.providers import ReferenceImage
from orchestrator.claude_orchestrator import ClaudePromptOrchestrator

logger = logging.getLogger(__name__)



class AgentOrchestrator:
    def __init__(self) -> None:
        settings = get_settings()
        self.engine = create_async_engine(settings.database_url, pool_pre_ping=True)
        self.Session = async_sessionmaker(self.engine, class_=AsyncSession, expire_on_commit=False)
        self.provider = get_provider()
        self.embedding_provider = get_embedding_provider()
        self.claude_orchestrator = ClaudePromptOrchestrator() if settings.claude_api_key else None
        self.max_retries = settings.max_provider_retries

    async def close(self) -> None:
        await self.engine.dispose()

    # ------------------------------------------------------------------
    # Daily / on-demand generation
    # ------------------------------------------------------------------

    async def run_daily_generate(self, brand_id: str, scheduled_for: str) -> None:
        """Entry point for the `daily_generate` job.

        The redis payload is identical for the cron-scheduled path and the
        API's "generate now" on-demand path — {"type": "daily_generate",
        "brand_id", "scheduled_for"} — and carries no run_id. `_claim_or_create_run`
        is therefore the single place that decides which `generation_runs`
        row this job acts on (see its docstring for the exact strategy),
        rather than this method branching on a run_id that the payload
        doesn't have.
        """
        brand_uuid = uuid.UUID(brand_id)
        day = date.fromisoformat(scheduled_for)
        async with self.Session() as db:
            run_id, on_demand_brief = await self._claim_or_create_run(db, brand_uuid, day)
            if run_id is None:
                logger.info("Skipping brand=%s date=%s (already completed)", brand_id, day)
                return

            brand_memory = await self._load_brand_memory(db, brand_uuid)
            concepts = await self._decide_daily_concepts(brand_memory, on_demand_brief)

            try:
                for slot, concept in enumerate(concepts, start=1):
                    existing = await db.execute(
                        text(
                            """
                            select id, status, storage_path
                            from generated_images
                            where run_id = :run_id and slot = :slot
                            """
                        ),
                        {"run_id": run_id, "slot": slot},
                    )
                    row = existing.first()
                    if row and row[1] == "pending_review" and row[2]:
                        logger.info("Slot %s already done for run %s", slot, run_id)
                        continue

                    reference_ids = await self._rank_reference_images(db, brand_uuid, concept)
                    idea_id = await self._upsert_content_idea(
                        db, run_id, brand_uuid, slot, concept, reference_ids
                    )
                    await self._generate_slot(
                        db, brand_uuid, run_id, slot, concept, idea_id, reference_ids
                    )

                await db.execute(
                    text(
                        """
                        update generation_runs
                        set status = 'completed',
                            completed_at = :now,
                            agent_meta = agent_meta || CAST(:meta AS jsonb)
                        where id = :id
                        """
                    ),
                    {
                        "id": run_id,
                        "now": datetime.now(timezone.utc),
                        "meta": json.dumps({"slots": 3}),
                    },
                )
                await db.commit()
                await self._notify_brand_members(db, brand_uuid)
                logger.info("Completed run %s for brand %s", run_id, brand_id)
            except Exception as exc:
                logger.exception("Run failed for brand=%s", brand_id)
                await db.execute(
                    text(
                        """
                        update generation_runs
                        set status = 'failed',
                            error_message = :err,
                            completed_at = :now
                        where id = :id
                        """
                    ),
                    {
                        "id": run_id,
                        "err": str(exc)[:2000],
                        "now": datetime.now(timezone.utc),
                    },
                )
                await db.commit()
                raise

    async def _claim_or_create_run(
        self, db: AsyncSession, brand_id: uuid.UUID, day: date
    ) -> tuple[uuid.UUID | None, dict]:
        """
        Decide which `generation_runs` row a `daily_generate` job for
        (brand_id, day) should act on, and return (run_id, on_demand_brief).

        Both the cron-scheduled path and the API's on-demand "generate now"
        path enqueue the exact same payload shape and carry no run_id, so
        this is the single source of truth for run selection. Scheduled
        runs are still deduplicated per-day via the partial unique index
        `generation_runs_scheduled_unique (brand_id, scheduled_for) where
        run_type = 'scheduled'`; on-demand runs are pre-created by the API
        route before the job is enqueued and can coexist with a scheduled
        run for the same day, so we can no longer assume (brand_id, day)
        maps to a single row.

        Strategy: lock every row for (brand_id, day) and process the most
        recently created one that is not yet 'completed'. This naturally
        resolves to a just-created on-demand row when a scheduled run for
        today already finished, and to an older still-pending on-demand run
        once a newer one has been processed. Only when NO row exists at all
        do we create a fresh row here, and it is always 'scheduled' —
        on-demand rows are only ever created by the API route.

        Known limitation: if two on-demand runs for the same brand/day are
        queued back-to-back before either starts, both jobs could resolve
        to the same newest pending row in a rare race; this is safe (not
        corrupting) because slot generation is idempotent per (run_id,
        slot), it just means the older on-demand row would only get picked
        up once the newer one completes. Passing run_id through the queue
        payload would remove this ambiguity entirely and is a reasonable
        follow-up if on-demand volume ever makes this matter.
        """
        result = await db.execute(
            text(
                """
                select id, status, run_type, agent_meta
                from generation_runs
                where brand_id = :brand_id and scheduled_for = :day
                order by created_at desc
                for update
                """
            ),
            {"brand_id": brand_id, "day": day},
        )
        rows = result.mappings().all()

        candidate = next((r for r in rows if r["status"] != "completed"), None)

        if candidate is None:
            if rows:
                # Every run for today (scheduled and/or on-demand) is done.
                return None, {}
            run_id = uuid.uuid4()
            await db.execute(
                text(
                    """
                    insert into generation_runs (id, brand_id, scheduled_for, status, run_type, started_at)
                    values (:id, :brand_id, :day, 'running', 'scheduled', :now)
                    """
                ),
                {
                    "id": run_id,
                    "brand_id": brand_id,
                    "day": day,
                    "now": datetime.now(timezone.utc),
                },
            )
            await db.commit()
            return run_id, {}

        run_id = candidate["id"]
        on_demand_brief: dict = {}
        if candidate["run_type"] == "on_demand":
            meta = candidate["agent_meta"] or {}
            if isinstance(meta, str):
                try:
                    meta = json.loads(meta)
                except json.JSONDecodeError:
                    meta = {}
            on_demand_brief = meta.get("on_demand_brief") or {}

        if candidate["status"] != "running":
            await db.execute(
                text(
                    """
                    update generation_runs
                    set status = 'running', started_at = :now, error_message = null
                    where id = :id
                    """
                ),
                {"id": run_id, "now": datetime.now(timezone.utc)},
            )
            await db.commit()

        return run_id, on_demand_brief

    # ------------------------------------------------------------------
    # Brand memory
    # ------------------------------------------------------------------

    async def _load_brand_memory(self, db: AsyncSession, brand_id: uuid.UUID) -> dict:
        """Load everything generation decisions are grounded in: brand +
        brand_profile (may not exist yet if the owner hasn't filled it in —
        defaults to empty, never crashes), active products, reference images
        for visual style guidance, and the last 14 days of approved/rejected
        images with reviewer notes."""
        brand_row = await db.execute(
            text("select id, name, slug, timezone, style_guide from brands where id = :id"),
            {"id": brand_id},
        )
        brand = brand_row.mappings().first()
        if not brand:
            raise RuntimeError(f"Brand {brand_id} not found")

        profile_row = await db.execute(
            text("select * from brand_profiles where brand_id = :id"),
            {"id": brand_id},
        )
        profile = profile_row.mappings().first()

        product_rows = await db.execute(
            text(
                """
                select id, name, description, price, category
                from products
                where brand_id = :id and is_active = true
                order by name
                """
            ),
            {"id": brand_id},
        )
        products = [dict(r) for r in product_rows.mappings()]

        reference_rows = await db.execute(
            text(
                """
                select id, storage_path, is_priority
                from reference_images
                where brand_id = :id
                order by is_priority desc, uploaded_at desc
                limit 10
                """
            ),
            {"id": brand_id},
        )
        reference_images = [dict(r) for r in reference_rows.mappings()]

        since = datetime.now(timezone.utc) - timedelta(days=14)
        history_rows = await db.execute(
            text(
                """
                select
                  gi.id as image_id,
                  ci.headline as headline,
                  a.decision as decision,
                  a.note as note,
                  a.decided_at as decided_at
                from generated_images gi
                join approvals a on a.image_id = gi.id
                left join content_ideas ci on ci.id = gi.content_idea_id
                where gi.brand_id = :brand_id and a.decided_at >= :since
                order by a.decided_at desc
                limit 30
                """
            ),
            {"brand_id": brand_id, "since": since},
        )
        history = [dict(r) for r in history_rows.mappings()]

        return {
            "brand": dict(brand),
            "profile": dict(profile) if profile else {},
            "products": products,
            "reference_images": reference_images,
            "approval_history": history,
        }

    # ------------------------------------------------------------------
    # Concept planning
    # ------------------------------------------------------------------

    async def _decide_daily_concepts(
        self, brand_memory: dict, on_demand_brief: dict | None = None
    ) -> list[dict]:
        """Return exactly 3 dicts, each shaped:
        {headline, rationale, prompt, content_pillar_id, product_id}
        """
        if self.claude_orchestrator:
            try:
                ref_images_data = None
                if brand_memory.get("reference_images"):
                    ref_images_data = await self._get_reference_image_bytes(
                        brand_memory["reference_images"]
                    )

                raw_concepts = await self.claude_orchestrator.generate_daily_concepts(
                    brand_memory, on_demand_brief, reference_images=ref_images_data
                )
                concepts = self._resolve_concepts(raw_concepts, brand_memory)
                logger.info(
                    "Generated %d concepts via Claude orchestrator",
                    len(concepts),
                )
                if logger.isEnabledFor(logging.DEBUG):
                    try:
                        logger.debug("Concepts: %s", json.dumps(concepts, indent=2, default=str))
                    except Exception:
                        logger.debug("Concepts: %s", concepts)
                return concepts
            except Exception:
                logger.exception(
                    "Claude concept generation failed; falling back to templated concepts"
                )
        else:
            logger.warning("Claude API key not configured; using fallback templated concepts")
        return self._plan_concepts_fallback(brand_memory, on_demand_brief)

    def _resolve_concepts(self, raw_concepts: list[dict], brand_memory: dict) -> list[dict]:
        """Map Claude's product NAME strings back to actual ids from
        brand_memory (case-insensitive exact match; None if no match/not provided)."""
        product_by_name = {p["name"].strip().lower(): p["id"] for p in brand_memory.get("products", [])}

        resolved = []
        for c in raw_concepts:
            product_name = (c.get("product") or "").strip().lower()
            resolved.append(
                {
                    "headline": c["headline"],
                    "rationale": c.get("rationale", ""),
                    "prompt": c["prompt"],
                    "content_pillar_id": None,
                    "product_id": product_by_name.get(product_name),
                }
            )
        return resolved

    def _plan_concepts_fallback(
        self, brand_memory: dict, on_demand_brief: dict | None = None
    ) -> list[dict]:
        """No-API-key / Claude-failure safety net. Generates 3 varied concepts."""
        brand = brand_memory["brand"]
        profile = brand_memory.get("profile") or {}
        products = brand_memory.get("products", [])
        on_demand_brief = on_demand_brief or {}

        product = products[0] if products else None
        style = profile.get("photography_style") or brand.get("style_guide") or "clean, modern, high-contrast"
        brand_name = brand["name"]

        concepts = [
            {
                "headline": (
                    f"{product['name']} takes centre stage" if product else f"{brand_name} hero product moment"
                ),
                "rationale": "Showcases the product/offering directly with a strong, on-brand visual style.",
                "prompt": (
                    f"Create a brand-aligned hero product image for {brand_name}. Style: {style}. "
                    + (
                        f"Feature the product '{product['name']}': {product.get('description') or ''}. "
                        if product
                        else ""
                    )
                    + "Natural light, clean composition, no text overlay."
                ),
                "content_pillar_id": None,
                "product_id": product["id"] if product else None,
            },
            {
                "headline": f"{brand_name} in everyday life",
                "rationale": "Places the brand in an authentic, relatable lifestyle context.",
                "prompt": (
                    f"Create a lifestyle marketing image for {brand_name} that feels authentic and "
                    f"relatable. Style: {style}. Human presence implied, warm natural setting, no text overlay."
                ),
                "content_pillar_id": None,
                "product_id": None,
            },
            {
                "headline": f"Ask your audience: {brand_name} edition",
                "rationale": "A bold, scroll-stopping composition designed to prompt comments/shares.",
                "prompt": (
                    f"Create a bold, graphic, scroll-stopping social image for {brand_name} designed to "
                    f"spark engagement (question, poll-style, or reaction-bait framing). Style: {style}. "
                    "Strong brand palette, high contrast, no text overlay."
                ),
                "content_pillar_id": None,
                "product_id": None,
            },
        ]

        if on_demand_brief:
            promotion = on_demand_brief.get("promotion")
            platform = on_demand_brief.get("platform")
            for c in concepts:
                extra = []
                if platform:
                    extra.append(f"Optimised for {platform}.")
                if promotion:
                    extra.append(f"Highlight this promotion: {promotion}.")
                if extra:
                    c["prompt"] = c["prompt"] + " " + " ".join(extra)

        return concepts

    # ------------------------------------------------------------------
    # Reference image loading
    # ------------------------------------------------------------------

    async def _get_reference_image_bytes(
        self, reference_images: list[dict]
    ) -> list[bytes] | None:
        """Download reference images from storage paths and return as bytes list."""
        if not reference_images:
            return None

        images_bytes = []
        for ref in reference_images[:5]:
            try:
                image_bytes = await download_object("brand-references", ref["storage_path"])
                if image_bytes:
                    images_bytes.append(image_bytes)
            except Exception as e:
                logger.warning("Failed to download reference image %s: %s", ref["storage_path"], e)

        return images_bytes if images_bytes else None

    async def _load_reference_images(
        self, db: AsyncSession, reference_image_ids: list[uuid.UUID]
    ) -> list[ReferenceImage] | None:
        """Download reference images from storage and return as ReferenceImage objects."""
        if not reference_image_ids:
            return None

        ref_result = await db.execute(
            text(
                """
                select id, storage_path
                from reference_images
                where id = any(CAST(:ids AS uuid[]))
                order by uploaded_at desc
                """
            ),
            {"ids": reference_image_ids},
        )
        ref_rows = [dict(r) for r in ref_result.mappings()]

        ref_images = []
        for ref in ref_rows:
            try:
                image_bytes = await download_object("brand-references", ref["storage_path"])
                if image_bytes:
                    ref_images.append(ReferenceImage(image_bytes=image_bytes, mime_type="image/png"))
            except Exception as e:
                logger.warning("Failed to download reference image %s: %s", ref["storage_path"], e)

        return ref_images if ref_images else None

    # ------------------------------------------------------------------
    # Prompt enhancement with reference images
    # ------------------------------------------------------------------

    async def _enhance_prompt_with_reference_images(
        self, db: AsyncSession, prompt: str, reference_image_ids: list[uuid.UUID]
    ) -> str:
        """Enhance the generation prompt with reference image instructions.
        If reference images exist, include strict instructions to match their
        style. If insufficient, instruct to fetch from Google and use as guide."""
        if not reference_image_ids:
            reference_instructions = (
                "\n\nREFERENCE STRATEGY: No brand reference images available. "
                "Search Google Images for similar professional brand photography to use as style reference. "
                "Maintain visual consistency as if this image belongs to the same brand collection."
            )
            return prompt + reference_instructions

        ref_result = await db.execute(
            text(
                """
                select id, storage_path, is_priority
                from reference_images
                where id = any(CAST(:ids AS uuid[]))
                order by is_priority desc, uploaded_at desc
                """
            ),
            {"ids": reference_image_ids},
        )
        ref_rows = [dict(r) for r in ref_result.mappings()]

        if len(ref_rows) < 3:
            reference_instructions = (
                f"\n\nREFERENCE STRATEGY: Use these {len(ref_rows)} brand reference image(s) as PRIMARY style guide: "
                f"{', '.join(r['storage_path'] for r in ref_rows)}. "
                "Additionally, search Google Images for similar professional brand photography to supplement the reference set. "
                "Generated image MUST match the exact visual style, design aesthetic, color palette, lighting, and composition "
                "of the reference images provided. The image should look like it was taken/created for the same brand/business."
            )
        else:
            reference_instructions = (
                f"\n\nREFERENCE STRATEGY: STRICTLY match these {len(ref_rows)} brand reference image(s): "
                f"{', '.join(r['storage_path'] for r in ref_rows)}. "
                "Use them as the definitive visual guide. Generate the image as if it belongs directly alongside these references. "
                "Match the exact style, design, aesthetic, color palette, lighting, composition, and quality. "
                "The image should appear to have been clicked/created for the same brand."
            )

        return prompt + reference_instructions

    # ------------------------------------------------------------------
    # Reference image ranking
    # ------------------------------------------------------------------

    async def _rank_reference_images(
        self, db: AsyncSession, brand_id: uuid.UUID, concept: dict
    ) -> list[uuid.UUID]:
        """Embed the concept brief and rank this brand's reference images
        by is_priority desc, then cosine distance asc, taking the top 3.
        If no reference images for this brand have embeddings yet (e.g.
        embed jobs haven't run), fall back to is_priority desc, uploaded_at
        desc so priority-only ranking still works before embeddings exist —
        simpler than mixing partial vector data with sentinel distances for
        every image, and correct either way since `image_embeddings` rows
        are populated asynchronously by the embed-job worker path."""
        embedded_count = await db.execute(
            text(
                """
                select count(*)
                from image_embeddings ie
                join reference_images ri on ri.id = ie.source_id
                where ie.source_type = 'reference_image' and ri.brand_id = :brand_id
                """
            ),
            {"brand_id": brand_id},
        )
        has_embeddings = (embedded_count.scalar() or 0) > 0

        params: dict = {"brand_id": brand_id, "limit": 3}

        if has_embeddings:
            query_text = f"{concept.get('headline', '')} {concept.get('rationale', '')}".strip()
            if not query_text:
                query_text = "brand content image"
            query_vector = await self.embedding_provider.embed_text(query_text)
            params["query_vector"] = to_vector_literal(query_vector)
            sql = """
                select ri.id
                from reference_images ri
                left join image_embeddings ie
                  on ie.source_type = 'reference_image' and ie.source_id = ri.id
                where ri.brand_id = :brand_id
                order by ri.is_priority desc,
                         coalesce(ie.embedding <=> CAST(:query_vector AS vector), 2.0) asc,
                         ri.uploaded_at desc
                limit :limit
            """
        else:
            sql = """
                select ri.id
                from reference_images ri
                where ri.brand_id = :brand_id
                order by ri.is_priority desc, ri.uploaded_at desc
                limit :limit
            """

        result = await db.execute(text(sql), params)
        ids = [row[0] for row in result.fetchall()]
        if ids:
            await db.execute(
                text(
                    "update reference_images set usage_count = usage_count + 1 "
                    "where id = any(CAST(:ids AS uuid[]))"
                ),
                {"ids": ids},
            )
        return ids

    # ------------------------------------------------------------------
    # Content idea + slot generation
    # ------------------------------------------------------------------

    async def _upsert_content_idea(
        self,
        db: AsyncSession,
        run_id: uuid.UUID,
        brand_id: uuid.UUID,
        slot: int,
        concept: dict,
        reference_image_ids: list[uuid.UUID],
    ) -> uuid.UUID:
        idea_id = uuid.uuid4()
        prompt_brief = {"prompt": concept["prompt"], "rationale": concept.get("rationale")}
        result = await db.execute(
            text(
                """
                insert into content_ideas
                  (id, run_id, brand_id, slot, headline, rationale,
                   content_pillar_id, product_id, reference_image_ids, prompt_brief)
                values
                  (:id, :run_id, :brand_id, :slot, :headline,
                   :rationale, :content_pillar_id, :product_id, CAST(:reference_image_ids AS uuid[]),
                   CAST(:prompt_brief AS jsonb))
                on conflict (run_id, slot) do update set
                  headline = excluded.headline,
                  rationale = excluded.rationale,
                  content_pillar_id = excluded.content_pillar_id,
                  product_id = excluded.product_id,
                  reference_image_ids = excluded.reference_image_ids,
                  prompt_brief = excluded.prompt_brief
                returning id
                """
            ),
            {
                "id": idea_id,
                "run_id": run_id,
                "brand_id": brand_id,
                "slot": slot,
                "headline": concept["headline"],
                "rationale": concept.get("rationale"),
                "content_pillar_id": concept.get("content_pillar_id"),
                "product_id": concept.get("product_id"),
                "reference_image_ids": reference_image_ids,
                "prompt_brief": json.dumps(prompt_brief),
            },
        )
        await db.commit()
        return result.scalar_one()

    async def _generate_slot(
        self,
        db: AsyncSession,
        brand_id: uuid.UUID,
        run_id: uuid.UUID,
        slot: int,
        concept: dict,
        content_idea_id: uuid.UUID,
        reference_image_ids: list[uuid.UUID],
    ) -> None:
        prompt = concept["prompt"]

        existing = await db.execute(
            text(
                """
                select id, status, storage_path from generated_images
                where run_id = :run_id and slot = :slot
                """
            ),
            {"run_id": run_id, "slot": slot},
        )
        row = existing.first()
        if row and row[1] == "pending_review" and row[2]:
            logger.info("Slot %s already done for run %s", slot, run_id)
            return

        image_id = row[0] if row else uuid.uuid4()
        if row is None:
            await db.execute(
                text(
                    """
                    insert into generated_images
                      (id, run_id, brand_id, slot, prompt, status, content_idea_id)
                    values
                      (:id, :run_id, :brand_id, :slot, :prompt, 'generating', :content_idea_id)
                    """
                ),
                {
                    "id": image_id,
                    "run_id": run_id,
                    "brand_id": brand_id,
                    "slot": slot,
                    "prompt": prompt,
                    "content_idea_id": content_idea_id,
                },
            )
            await db.commit()

        enhanced_prompt = await self._enhance_prompt_with_reference_images(
            db, prompt, reference_image_ids
        )

        ref_images = await self._load_reference_images(db, reference_image_ids)

        asset = None
        last_err: Exception | None = None
        for attempt in range(1, self.max_retries + 1):
            try:
                asset = await self.provider.generate(
                    enhanced_prompt, slot=slot, reference_images=ref_images
                )
                break
            except Exception as exc:
                last_err = exc
                logger.warning("Provider attempt %s failed: %s", attempt, exc)
                await asyncio.sleep(2**attempt)
        if asset is None:
            raise RuntimeError(f"Image generation failed after retries: {last_err}")

        path = f"{brand_id}/{run_id}/{slot}.png"
        await upload_draft(path, asset.image_bytes, asset.mime_type)

        meta = dict(asset.meta)
        meta["reference_image_ids"] = [str(i) for i in reference_image_ids]

        await db.execute(
            text(
                """
                update generated_images
                set storage_path = :path,
                    status = 'pending_review',
                    provider = :provider,
                    provider_meta = CAST(:meta AS jsonb),
                    prompt = :prompt,
                    updated_at = :now
                where id = :id
                """
            ),
            {
                "id": image_id,
                "path": path,
                "provider": asset.provider,
                "meta": json.dumps(meta),
                "prompt": enhanced_prompt,
                "now": datetime.now(timezone.utc),
            },
        )
        await db.commit()
        logger.info("Slot %s ready for review (run=%s)", slot, run_id)

    # ------------------------------------------------------------------
    # Notifications
    # ------------------------------------------------------------------

    async def _notify_brand_members(self, db: AsyncSession, brand_id: uuid.UUID) -> None:
        brand_row = await db.execute(text("select name from brands where id = :id"), {"id": brand_id})
        brand_row_result = brand_row.first()
        brand_name = brand_row_result[0] if brand_row_result else "your brand"

        members = await db.execute(
            text("select user_id from brand_members where brand_id = :id"),
            {"id": brand_id},
        )
        user_ids = [r[0] for r in members.fetchall()]
        for user_id in user_ids:
            await db.execute(
                text(
                    """
                    insert into notifications (id, brand_id, user_id, type, title, body, link_path)
                    values (:id, :brand_id, :user_id, 'generation_ready', :title, :body, :link_path)
                    """
                ),
                {
                    "id": uuid.uuid4(),
                    "brand_id": brand_id,
                    "user_id": user_id,
                    "title": f"New concepts ready for {brand_name}",
                    "body": "3 new content concepts are ready for your review.",
                    "link_path": "/dashboard",
                },
            )
        if user_ids:
            await db.commit()

    # ------------------------------------------------------------------
    # Reference image embedding (embed_reference_image job)
    # ------------------------------------------------------------------

    async def embed_reference_image(self, reference_image_id: str) -> None:
        ref_uuid = uuid.UUID(reference_image_id)
        async with self.Session() as db:
            row = await db.execute(
                text("select id, brand_id, storage_path from reference_images where id = :id"),
                {"id": ref_uuid},
            )
            ref = row.mappings().first()
            if not ref:
                logger.warning("reference_image %s not found; skipping embed job", reference_image_id)
                return

            try:
                image_bytes = await download_object("brand-references", ref["storage_path"])
                if image_bytes is None:
                    raise RuntimeError(f"Could not download {ref['storage_path']}")

                vector = await self.embedding_provider.embed_image(image_bytes)

                await db.execute(
                    text(
                        """
                        insert into image_embeddings (id, brand_id, source_type, source_id, model, embedding)
                        values (:id, :brand_id, 'reference_image', :source_id, :model,
                                CAST(:embedding AS vector))
                        on conflict (source_type, source_id) do update
                          set embedding = excluded.embedding,
                              model = excluded.model,
                              brand_id = excluded.brand_id
                        """
                    ),
                    {
                        "id": uuid.uuid4(),
                        "brand_id": ref["brand_id"],
                        "source_id": ref["id"],
                        "model": self.embedding_provider.name,
                        "embedding": to_vector_literal(vector),
                    },
                )
                await db.execute(
                    text("update reference_images set embedding_status = 'ready' where id = :id"),
                    {"id": ref["id"]},
                )
                await db.commit()
                logger.info("Embedded reference image %s", reference_image_id)
            except Exception:
                logger.exception("Failed to embed reference image %s", reference_image_id)
                await db.rollback()
                await db.execute(
                    text("update reference_images set embedding_status = 'failed' where id = :id"),
                    {"id": ref["id"]},
                )
                await db.commit()
