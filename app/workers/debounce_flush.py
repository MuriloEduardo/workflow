import asyncio

import structlog

from app.domain.services.debounce import DebounceService
from app.infrastructure.database.postgres_connection import PostgresConnection

logger = structlog.get_logger(__name__)

_CONNECTION_ERRORS = (
    "ConnectionDoesNotExistError",
    "ConnectionResetError",
    "InterfaceError",
)


def _is_connection_error(exc: BaseException) -> bool:
    return type(exc).__name__ in _CONNECTION_ERRORS or isinstance(
        exc, (ConnectionResetError, OSError)
    )


class DebounceFlushWorker:
    """Polls PostgreSQL for mature debounce groups and flushes them to cognition."""

    def __init__(
        self,
        debounce: DebounceService,
        database: PostgresConnection,
        poll_interval: float = 2.0,
    ) -> None:
        self._debounce = debounce
        self._database = database
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
            except (
                Exception
            ) as exc:  # pylint: disable=broad-exception-caught  # noqa: BLE001
                if _is_connection_error(exc):
                    logger.warning("debounce_flush.db_reconnect", reason=str(exc))
                    try:
                        await self._database.reconnect()
                    except Exception:  # noqa: BLE001
                        logger.exception("debounce_flush.reconnect_failed")
                else:
                    logger.exception("debounce_flush.error")

            await asyncio.sleep(self._poll_interval)

    def stop(self) -> None:
        self._running = False
