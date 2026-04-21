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

    async def get_session_flow(self, session_id: str) -> list[dict]:
        pool = await self._database.get_pool()
        rows = await pool.fetch(
            """
            WITH ordered AS (
                SELECT
                    id, node_id, status, response, model,
                    total_tokens, latency_ms, error, created_at,
                    LAG(node_id) OVER (ORDER BY created_at) AS prev_node_id
                FROM executions
                WHERE session_id = $1 AND node_id IS NOT NULL
            )
            SELECT
                o.id,
                o.node_id,
                o.status,
                o.response,
                o.model,
                o.total_tokens,
                o.latency_ms,
                o.error,
                o.created_at,
                e_in.id               AS incoming_edge_id,
                e_in.label            AS incoming_edge_label,
                e_in.condition_prompt AS incoming_edge_condition,
                (
                    SELECT json_agg(
                        json_build_object(
                            'id',             e.id,
                            'target_node_id', e.target_node_id,
                            'label',          e.label,
                            'condition_prompt', e.condition_prompt,
                            'priority',       e.priority
                        ) ORDER BY e.priority, e.created_at
                    )
                    FROM edges e WHERE e.source_node_id = o.node_id
                ) AS next_edges
            FROM ordered o
            LEFT JOIN edges e_in
                ON e_in.source_node_id = o.prev_node_id
               AND e_in.target_node_id = o.node_id
            ORDER BY o.created_at
            """,
            session_id,
        )
        result = []
        for r in rows:
            d = dict(r)
            d["id"] = str(d["id"])
            d["node_id"] = str(d["node_id"])
            d["created_at"] = d["created_at"].isoformat()
            if d["incoming_edge_id"]:
                d["incoming_edge_id"] = str(d["incoming_edge_id"])
            result.append(d)
        return result
