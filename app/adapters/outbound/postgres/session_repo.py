from uuid import UUID

from app.infrastructure.database.postgres_connection import PostgresConnection
from app.ports.outbound.session_repository import SessionRepository


class PostgresSessionRepository(SessionRepository):
    def __init__(self, database: PostgresConnection) -> None:
        self._database = database

    async def get_active(
        self, tenant_id: UUID, channel_type: str, contact_id: UUID
    ) -> dict | None:
        pool = await self._database.get_pool()
        row = await pool.fetchrow(
            """
            SELECT id, thread_id, timeout_seconds, last_activity,
                   EXTRACT(EPOCH FROM (now() - last_activity)) AS idle_seconds
            FROM sessions
            WHERE tenant_id = $1
              AND channel_type = $2
              AND contact_id = $3
              AND status = 'active'
            """,
            tenant_id,
            channel_type,
            contact_id,
        )
        if row is None:
            return None
        return dict(row)

    async def create(
        self,
        tenant_id: UUID,
        channel_type: str,
        contact_id: UUID,
        thread_id: str,
        timeout_seconds: int,
    ) -> UUID:
        pool = await self._database.get_pool()
        return await pool.fetchval(
            """
            INSERT INTO sessions (tenant_id, channel_type, contact_id, thread_id, timeout_seconds)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING id
            """,
            tenant_id,
            channel_type,
            contact_id,
            thread_id,
            timeout_seconds,
        )

    async def touch(self, session_id: UUID) -> None:
        pool = await self._database.get_pool()
        await pool.execute(
            "UPDATE sessions SET last_activity = now() WHERE id = $1",
            session_id,
        )

    async def expire(self, session_id: UUID) -> None:
        pool = await self._database.get_pool()
        await pool.execute(
            "UPDATE sessions SET status = 'expired' WHERE id = $1",
            session_id,
        )
