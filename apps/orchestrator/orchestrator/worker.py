from __future__ import annotations

import asyncio
import json
import logging
import signal

from redis import Redis
from redis.exceptions import ConnectionError as RedisConnectionError
from redis.exceptions import TimeoutError as RedisTimeoutError

from orchestrator.agent import AgentOrchestrator
from orchestrator.config import get_settings

logger = logging.getLogger(__name__)
DAILY_QUEUE_KEY = "brand-manager:jobs:daily_generate"
EMBED_QUEUE_KEY = "brand-manager:jobs:embed_reference_image"


async def process_loop() -> None:
    settings = get_settings()
    redis = Redis.from_url(settings.redis_url, decode_responses=True)
    agent = AgentOrchestrator()
    stop = asyncio.Event()

    def _stop(*_: object) -> None:
        stop.set()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, _stop)
        except NotImplementedError:
            # Windows
            signal.signal(sig, lambda *_: stop.set())

    logger.info("Orchestrator worker listening on %s, %s", DAILY_QUEUE_KEY, EMBED_QUEUE_KEY)
    try:
        while not stop.is_set():
            try:
                item = await asyncio.to_thread(redis.blpop, [DAILY_QUEUE_KEY, EMBED_QUEUE_KEY], 5)
            except (RedisTimeoutError, RedisConnectionError):
                # A blocking read can legitimately hit a socket-level hiccup
                # (idle connection reset by NAT/proxy, etc.) with nothing to
                # dequeue — treat exactly like a normal BLPOP timeout instead
                # of crashing the whole worker process.
                logger.debug("Redis blpop socket hiccup; retrying")
                continue
            if item is None:
                continue
            queue_key, raw = item
            try:
                payload = json.loads(raw)
            except json.JSONDecodeError:
                logger.error("Invalid job payload on %s: %s", queue_key, raw)
                continue

            job_type = payload.get("type")
            try:
                if queue_key == DAILY_QUEUE_KEY and job_type == "daily_generate":
                    brand_id = payload["brand_id"]
                    scheduled_for = payload["scheduled_for"]
                    logger.info(
                        "Processing daily_generate brand=%s date=%s", brand_id, scheduled_for
                    )
                    await agent.run_daily_generate(brand_id, scheduled_for)
                elif queue_key == EMBED_QUEUE_KEY and job_type == "embed_reference_image":
                    reference_image_id = payload["reference_image_id"]
                    logger.info(
                        "Processing embed_reference_image id=%s", reference_image_id
                    )
                    # Failures here are caught and recorded on the reference_images
                    # row itself (embedding_status='failed'); nothing to requeue.
                    await agent.embed_reference_image(reference_image_id)
                else:
                    logger.warning("Unknown job on %s: %s", queue_key, payload)
            except Exception:
                logger.exception("Job failed; requeue with delay")
                await asyncio.sleep(5)
                # Dead-letter simplistic: push once more with attempt count
                attempts = int(payload.get("attempts", 0)) + 1
                if attempts <= 3:
                    payload["attempts"] = attempts
                    redis.rpush(queue_key, json.dumps(payload))
                else:
                    logger.error("Giving up on job after %s attempts: %s", attempts, payload)
    finally:
        await agent.close()


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )
    asyncio.run(process_loop())


if __name__ == "__main__":
    main()
