import json
from uuid import UUID

from app.infrastructure.database.postgres_connection import PostgresConnection
from app.ports.outbound.edge_repository import EdgeRepository

_COLS = "id, source_node_id, target_node_id, label, condition, condition_prompt, priority, metadata, created_at, updated_at"


def _row_to_dict(row: object) -> dict:
    d = dict(row)
    d["id"] = str(d["id"])
    d["source_node_id"] = str(d["source_node_id"])
    d["target_node_id"] = str(d["target_node_id"])
    d["created_at"] = d["created_at"].isoformat()
    d["updated_at"] = d["updated_at"].isoformat()
    return d


class PostgresEdgeRepository(EdgeRepository):
    def __init__(self, database: PostgresConnection) -> None:
        self._database = database

    async def create(
        self,
        source_node_id: UUID,
        target_node_id: UUID,
        label: str | None,
        condition: dict | None,
        condition_prompt: str | None,
        priority: int,
        metadata: dict,
    ) -> UUID:
        pool = await self._database.get_pool()
        return await pool.fetchval(
            """
            INSERT INTO edges
                (source_node_id, target_node_id, label, condition, condition_prompt, priority, metadata)
            VALUES ($1,$2,$3,$4::jsonb,$5,$6,$7::jsonb)
            RETURNING id
            """,
            source_node_id,
            target_node_id,
            label,
            json.dumps(condition) if condition is not None else None,
            condition_prompt,
            priority,
            json.dumps(metadata),
        )

    async def get(self, edge_id: UUID) -> dict | None:
        pool = await self._database.get_pool()
        row = await pool.fetchrow(f"SELECT {_COLS} FROM edges WHERE id = $1", edge_id)
        return _row_to_dict(row) if row else None

    async def list_by_source(self, source_node_id: UUID) -> list[dict]:
        pool = await self._database.get_pool()
        rows = await pool.fetch(
            f"SELECT {_COLS} FROM edges WHERE source_node_id = $1 ORDER BY priority, created_at",
            source_node_id,
        )
        return [_row_to_dict(r) for r in rows]

    async def list_all(self) -> list[dict]:
        pool = await self._database.get_pool()
        rows = await pool.fetch(
            f"SELECT {_COLS} FROM edges ORDER BY priority, created_at"
        )
        return [_row_to_dict(r) for r in rows]

    async def update(self, edge_id: UUID, fields: dict) -> dict | None:
        if not fields:
            return await self.get(edge_id)
        allowed = {"label", "condition", "condition_prompt", "priority", "metadata"}
        json_cols = {"condition", "metadata"}
        sets, params = [], [edge_id]
        for key, val in fields.items():
            if key not in allowed:
                continue
            params.append(
                json.dumps(val) if key in json_cols and val is not None else val
            )
            cast = "::jsonb" if key in json_cols else ""
            sets.append(f"{key} = ${len(params)}{cast}")
        if not sets:
            return await self.get(edge_id)
        sets.append("updated_at = now()")
        pool = await self._database.get_pool()
        row = await pool.fetchrow(
            f"UPDATE edges SET {', '.join(sets)} WHERE id = $1 RETURNING {_COLS}",
            *params,
        )
        return _row_to_dict(row) if row else None

    async def delete(self, edge_id: UUID) -> bool:
        pool = await self._database.get_pool()
        result = await pool.execute("DELETE FROM edges WHERE id = $1", edge_id)
        return result.split()[-1] != "0"
