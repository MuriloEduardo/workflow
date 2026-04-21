from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

import asyncpg

if TYPE_CHECKING:
    from app.infrastructure.config.settings import Settings

logger = logging.getLogger(__name__)

# Neon serverless closes idle connections after ~5 min.
# Keep pool connections alive for at most 3 minutes to avoid stale sockets.
_MAX_INACTIVE_LIFETIME = 180.0  # seconds


class PostgresConnection:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._pool: Any = None
        self._closed = True

    async def connect(self) -> Any:
        if self._pool and not self._closed:
            return self._pool

        self._pool = await asyncpg.create_pool(
            str(self._settings.database_url),
            min_size=2,
            max_size=10,
            max_inactive_connection_lifetime=_MAX_INACTIVE_LIFETIME,
        )
        self._closed = False
        logger.info("Connected to PostgreSQL")
        return self._pool

    async def get_pool(self) -> Any:
        if self._pool is None or self._closed:
            return await self.connect()
        return self._pool

    async def reconnect(self) -> Any:
        """Close existing pool (if any) and open a fresh one."""
        if self._pool and not self._closed:
            try:
                await self._pool.close()
            except Exception:  # noqa: BLE001
                pass
        self._pool = None
        self._closed = True
        return await self.connect()

    async def close(self) -> None:
        if self._pool and not self._closed:
            await self._pool.close()
            self._closed = True
            logger.info("PostgreSQL connection closed")
