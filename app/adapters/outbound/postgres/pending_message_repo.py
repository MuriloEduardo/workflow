import json
from uuid import UUID

from app.infrastructure.database.postgres_connection import PostgresConnection
from app.ports.outbound.pending_message_repository import PendingMessageRepository


class PostgresPendingMessageRepository(PendingMessageRepository):
    def __init__(self, database: PostgresConnection) -> None:
        self._database = database

    async def insert(self, group_key: str, content: str, metadata: dict) -> UUID:
        pool = await self._database.get_pool()
        row = await pool.fetchval(
            """
            INSERT INTO pending_messages (group_key, content, metadata)
            VALUES ($1, $2, $3::jsonb)
            RETURNING id
            """,
            group_key,
            content,
            json.dumps(metadata),
        )
        return row

    async def flush_group(self, group_key: str) -> list[dict]:
        pool = await self._database.get_pool()
        rows = await pool.fetch(
            """
            DELETE FROM pending_messages
            WHERE id IN (
                SELECT id FROM pending_messages
                WHERE group_key = $1
                ORDER BY created_at
                FOR UPDATE SKIP LOCKED
            )
            RETURNING content, metadata, created_at
            """,
            group_key,
        )
        return [
            {
                "content": r["content"],
                "metadata": (
                    json.loads(r["metadata"])
                    if isinstance(r["metadata"], str)
                    else r["metadata"]
                ),
                "created_at": r["created_at"].isoformat(),
            }
            for r in rows
        ]

    async def get_mature_groups(self, debounce_seconds: float) -> list[str]:
        pool = await self._database.get_pool()
        rows = await pool.fetch(
            """
            SELECT group_key
            FROM pending_messages
            GROUP BY group_key
            HAVING MAX(created_at) < NOW() - INTERVAL '1 second' * $1
            """,
            debounce_seconds,
        )
        return [r["group_key"] for r in rows]
