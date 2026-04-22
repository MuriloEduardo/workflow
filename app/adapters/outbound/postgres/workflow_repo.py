import json
from uuid import UUID

from app.infrastructure.database.postgres_connection import PostgresConnection
from app.ports.outbound.workflow_repository import WorkflowRepository

_COLS = "id, tenant_id, name, description, status, metadata, created_at, updated_at"


def _row_to_dict(row: object) -> dict:
    d = dict(row)
    d["id"] = str(d["id"])
    d["tenant_id"] = str(d["tenant_id"])
    d["created_at"] = d["created_at"].isoformat()
    d["updated_at"] = d["updated_at"].isoformat()
    if isinstance(d.get("metadata"), str):
        d["metadata"] = json.loads(d["metadata"])
    return d


class PostgresWorkflowRepository(WorkflowRepository):
    def __init__(self, database: PostgresConnection) -> None:
        self._database = database

    async def create(
        self,
        tenant_id: UUID,
        name: str,
        description: str | None,
        status: str,
        metadata: dict,
    ) -> UUID:
        pool = await self._database.get_pool()
        return await pool.fetchval(
            """
            INSERT INTO workflows (tenant_id, name, description, status, metadata)
            VALUES ($1, $2, $3, $4, $5::jsonb)
            RETURNING id
            """,
            tenant_id,
            name,
            description,
            status,
            json.dumps(metadata),
        )

    async def get(self, workflow_id: UUID) -> dict | None:
        pool = await self._database.get_pool()
        row = await pool.fetchrow(
            f"SELECT {_COLS} FROM workflows WHERE id = $1", workflow_id
        )
        return _row_to_dict(row) if row else None

    async def list_all(self) -> list[dict]:
        pool = await self._database.get_pool()
        rows = await pool.fetch(f"SELECT {_COLS} FROM workflows ORDER BY created_at")
        return [_row_to_dict(r) for r in rows]

    async def list_by_tenant(self, tenant_id: UUID) -> list[dict]:
        pool = await self._database.get_pool()
        rows = await pool.fetch(
            f"SELECT {_COLS} FROM workflows WHERE tenant_id = $1 ORDER BY created_at",
            tenant_id,
        )
        return [_row_to_dict(r) for r in rows]

    async def update(self, workflow_id: UUID, fields: dict) -> dict | None:
        if not fields:
            return await self.get(workflow_id)
        allowed = {"name", "description", "status", "metadata"}
        json_cols = {"metadata"}
        sets, params = [], [workflow_id]
        for key, val in fields.items():
            if key not in allowed:
                continue
            params.append(
                json.dumps(val) if key in json_cols and val is not None else val
            )
            cast = "::jsonb" if key in json_cols else ""
            sets.append(f"{key} = ${len(params)}{cast}")
        if not sets:
            return await self.get(workflow_id)
        sets.append("updated_at = now()")
        pool = await self._database.get_pool()
        row = await pool.fetchrow(
            f"UPDATE workflows SET {', '.join(sets)} WHERE id = $1 RETURNING {_COLS}",
            *params,
        )
        return _row_to_dict(row) if row else None

    async def delete(self, workflow_id: UUID) -> bool:
        pool = await self._database.get_pool()
        result = await pool.execute("DELETE FROM workflows WHERE id = $1", workflow_id)
        return result.split()[-1] != "0"
