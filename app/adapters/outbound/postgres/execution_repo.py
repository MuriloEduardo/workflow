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
        selected_edge_id: str | None = None,
        justification: str | None = None,
        confidence: float | None = None,
    ) -> UUID:
        pool = await self._database.get_pool()
        return await pool.fetchval(
            """
            INSERT INTO executions (
                request_id, status,
                node_id, tenant_id, contact_id, session_id,
                prompt, response, model,
                input_tokens, output_tokens, total_tokens, latency_ms,
                error, metadata, selected_edge_id,
                justification, confidence
            ) VALUES (
                $1,  $2,
                $3::uuid,  $4::uuid,  $5::uuid,  $6,
                $7,  $8,  $9,
                $10, $11, $12, $13,
                $14, $15::jsonb, $16::uuid,
                $17, $18
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
            selected_edge_id,
            justification,
            confidence,
        )

    async def get_session_flow(self, session_id: str) -> dict | None:
        pool = await self._database.get_pool()
        row = await pool.fetchrow(
            """
            WITH last_edge AS (
                SELECT selected_edge_id
                FROM executions
                WHERE session_id = $1 AND selected_edge_id IS NOT NULL
                ORDER BY created_at DESC
                LIMIT 1
            ),
            current_node_id AS (
                SELECT COALESCE(
                    (SELECT e.target_node_id FROM edges e WHERE e.id = (SELECT selected_edge_id FROM last_edge)),
                    (SELECT id FROM nodes ORDER BY "order" NULLS LAST, created_at LIMIT 1)
                ) AS id
            )
            SELECT
                n.id           AS node_id,
                n.name         AS node_name,
                n.prompt       AS node_prompt,
                e_in.id        AS incoming_edge_id,
                e_in.label     AS incoming_edge_label,
                (
                    SELECT string_agg(c.prompt, E'\n' ORDER BY c.created_at)
                    FROM conditions c
                    JOIN edge_conditions ec ON ec.condition_id = c.id
                    WHERE ec.edge_id = e_in.id AND c.prompt IS NOT NULL
                ) AS incoming_edge_condition,
                (
                    SELECT json_agg(
                        json_build_object(
                            'id',               e.id,
                            'target_node_id',   e.target_node_id,
                            'label',            e.label,
                            'condition_prompt', (
                                SELECT string_agg(c.prompt, E'\n' ORDER BY c.created_at)
                                FROM conditions c
                                JOIN edge_conditions ec ON ec.condition_id = c.id
                                WHERE ec.edge_id = e.id AND c.prompt IS NOT NULL
                            ),
                            'priority',         e.priority
                        ) ORDER BY e.priority, e.created_at
                    )
                    FROM edges e WHERE e.source_node_id = n.id
                ) AS next_edges
            FROM current_node_id cni
            JOIN nodes n ON n.id = cni.id
            LEFT JOIN last_edge le ON true
            LEFT JOIN edges e_in ON e_in.id = le.selected_edge_id
            """,
            session_id,
        )
        if row is None:
            return None
        d = dict(row)
        d["node_id"] = str(d["node_id"])
        if d["incoming_edge_id"]:
            d["incoming_edge_id"] = str(d["incoming_edge_id"])
        if isinstance(d.get("next_edges"), str):
            import json as _json

            try:
                d["next_edges"] = _json.loads(d["next_edges"])
            except (_json.JSONDecodeError, TypeError):
                d["next_edges"] = []
        if not d.get("next_edges"):
            d["next_edges"] = []
        # Stringify UUID fields inside next_edges
        for edge in d["next_edges"]:
            if isinstance(edge, dict):
                for key in ("id", "target_node_id"):
                    if edge.get(key) is not None:
                        edge[key] = str(edge[key])
        return d
