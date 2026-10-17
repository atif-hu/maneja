"""Cron-like loop that asks the API to enqueue due daily jobs."""

from __future__ import annotations

import asyncio
import logging
import signal

import httpx

from orchestrator.config import get_settings

logger = logging.getLogger(__name__)


async def tick_once() -> None:
    settings = get_settings()
    url = f"{settings.api_base_url.rstrip('/')}/internal/jobs/enqueue-daily"
    headers = {"Authorization": f"Bearer {settings.internal_job_secret}"}
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(url, headers=headers)
        if resp.status_code >= 400:
            logger.error("Enqueue failed %s: %s", resp.status_code, resp.text)
            return
        data = resp.json()
        logger.info("Enqueue tick: %s", data)


async def run_scheduler() -> None:
    settings = get_settings()
    stop = asyncio.Event()

    def _stop(*_: object) -> None:
        stop.set()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, _stop)
        except NotImplementedError:
            signal.signal(sig, lambda *_: stop.set())

    logger.info(
        "Scheduler started; interval=%ss api=%s",
        settings.scheduler_interval_seconds,
        settings.api_base_url,
    )
    while not stop.is_set():
        try:
            await tick_once()
        except Exception:
            logger.exception("Scheduler tick failed")
        try:
            await asyncio.wait_for(stop.wait(), timeout=settings.scheduler_interval_seconds)
        except asyncio.TimeoutError:
            pass


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )
    asyncio.run(run_scheduler())


if __name__ == "__main__":
    main()
