import asyncio

import structlog

from app.domain.services.debounce import DebounceService

logger = structlog.get_logger(__name__)


class DebounceFlushWorker:
    """Polls PostgreSQL for mature debounce groups and flushes them to cognition."""

    def __init__(self, debounce: DebounceService, poll_interval: float = 2.0) -> None:
        self._debounce = debounce
        self._poll_interval = poll_interval
        self._running = False

    async def start(self) -> None:
        self._running = True
        logger.info("debounce_flush.started", poll_interval=self._poll_interval)

        while self._running:
            try:
                flushed = await self._debounce.flush_mature_groups()
                if flushed:
                    logger.info("debounce_flush.cycle", groups_flushed=flushed)
            except Exception:  # pylint: disable=broad-exception-caught  # noqa: BLE001
                logger.exception("debounce_flush.error")

            await asyncio.sleep(self._poll_interval)

    def stop(self) -> None:
        self._running = False
