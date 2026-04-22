import json
from uuid import UUID

from app.infrastructure.database.postgres_connection import PostgresConnection
from app.ports.outbound.node_repository import NodeRepository

_COLS = 'id, name, description, status, prompt, response_format, config, metadata, "order", priority, created_at, updated_at'


def _row_to_dict(row: object) -> dict:
    d = dict(row)
    d["id"] = str(d["id"])
    d["created_at"] = d["created_at"].isoformat()
    d["updated_at"] = d["updated_at"].isoformat()
    return d


class PostgresNodeRepository(NodeRepository):
    def __init__(self, database: PostgresConnection) -> None:
        self._database = database

    async def create(
        self,
        name: str,
        description: str | None,
        status: str,
        prompt: str | None,
        response_format: dict | None,
        config: dict,
        metadata: dict,
        order: int | None,
        priority: int,
    ) -> UUID:
        pool = await self._database.get_pool()
        return await pool.fetchval(
            """
            INSERT INTO nodes
                (name, description, status, prompt, response_format,
                 config, metadata, "order", priority)
            VALUES ($1,$2,$3,$4,$5::jsonb,$6::jsonb,$7::jsonb,$8,$9)
            RETURNING id
            """,
            name,
            description,
            status,
            prompt,
            json.dumps(response_format) if response_format is not None else None,
            json.dumps(config),
            json.dumps(metadata),
            order,
            priority,
        )

    async def get(self, node_id: UUID) -> dict | None:
        pool = await self._database.get_pool()
        row = await pool.fetchrow(f"SELECT {_COLS} FROM nodes WHERE id = $1", node_id)
        return _row_to_dict(row) if row else None

    async def list_all(self) -> list[dict]:
        pool = await self._database.get_pool()
        rows = await pool.fetch(
            f'SELECT {_COLS} FROM nodes ORDER BY "order" NULLS LAST, created_at'
        )
        return [_row_to_dict(r) for r in rows]

    async def update(self, node_id: UUID, fields: dict) -> dict | None:
        if not fields:
            return await self.get(node_id)
        allowed = {
            "name",
            "description",
            "status",
            "prompt",
            "response_format",
            "config",
            "metadata",
            "order",
            "priority",
        }
        json_cols = {"response_format", "config", "metadata"}
        sets, params = [], [node_id]
        for key, val in fields.items():
            if key not in allowed:
                continue
            params.append(
                json.dumps(val) if key in json_cols and val is not None else val
            )
            col = f'"{key}"' if key == "order" else key
            cast = "::jsonb" if key in json_cols else ""
            sets.append(f"{col} = ${len(params)}{cast}")
        if not sets:
            return await self.get(node_id)
        sets.append("updated_at = now()")
        pool = await self._database.get_pool()
        row = await pool.fetchrow(
            f"UPDATE nodes SET {', '.join(sets)} WHERE id = $1 RETURNING {_COLS}",
            *params,
        )
        return _row_to_dict(row) if row else None

    async def delete(self, node_id: UUID) -> bool:
        pool = await self._database.get_pool()
        result = await pool.execute("DELETE FROM nodes WHERE id = $1", node_id)
        return result.split()[-1] != "0"
