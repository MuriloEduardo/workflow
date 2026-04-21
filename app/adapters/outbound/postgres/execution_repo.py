import json
from uuid import UUID

from app.infrastructure.database.postgres_connection import PostgresConnection
from app.ports.outbound.execution_repository import ExecutionRepository


class PostgresExecutionRepository(ExecutionRepository):
    def __init__(self, database: PostgresConnection) -> None:
        self._database = database

    async def create(
        self,
        request_id: str,
        status: str,
        node_id: str | None = None,
        tenant_id: str | None = None,
        contact_id: str | None = None,
        session_id: str | None = None,
        prompt: str | None = None,
        response: str | None = None,
        model: str | None = None,
        input_tokens: int | None = None,
        output_tokens: int | None = None,
        total_tokens: int | None = None,
        latency_ms: int | None = None,
        error: str | None = None,
        metadata: dict | None = None,
    ) -> UUID:
        pool = await self._database.get_pool()
        return await pool.fetchval(
            """
            INSERT INTO executions (
                request_id, status,
                node_id, tenant_id, contact_id, session_id,
                prompt, response, model,
                input_tokens, output_tokens, total_tokens, latency_ms,
                error, metadata
            ) VALUES (
                $1,  $2,
                $3::uuid,  $4::uuid,  $5::uuid,  $6,
                $7,  $8,  $9,
                $10, $11, $12, $13,
                $14, $15::jsonb
            )
            RETURNING id
            """,
            request_id,
            status,
            node_id,
            tenant_id,
            contact_id,
            session_id,
            prompt,
            response,
            model,
            input_tokens,
            output_tokens,
            total_tokens,
            latency_ms,
            error,
            json.dumps(metadata or {}),
        )
