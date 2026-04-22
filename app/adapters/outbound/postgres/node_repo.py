import json
from uuid import UUID

from app.infrastructure.database.postgres_connection import PostgresConnection
from app.ports.outbound.node_repository import NodeRepository

_COLS = 'id, workflow_id, name, description, status, prompt, response_format, config, metadata, "order", priority, created_at, updated_at'


def _row_to_dict(row: object) -> dict:
    d = dict(row)
    d["id"] = str(d["id"])
    d["workflow_id"] = str(d["workflow_id"]) if d.get("workflow_id") else None
    d["created_at"] = d["created_at"].isoformat()
    d["updated_at"] = d["updated_at"].isoformat()
    for field in ("response_format", "config", "metadata"):
        if isinstance(d.get(field), str):
            d[field] = json.loads(d[field])
    return d


class PostgresNodeRepository(NodeRepository):
    def __init__(self, database: PostgresConnection) -> None:
        self._database = database

    async def create(
        self,
        workflow_id: UUID | None,
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
                (workflow_id, name, description, status, prompt, response_format,
                 config, metadata, "order", priority)
            VALUES ($1,$2,$3,$4,$5,$6::jsonb,$7::jsonb,$8::jsonb,$9,$10)
            RETURNING id
            """,
            workflow_id,
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

    # ------------------------------------------------------------------
    # Full read (with embedded relations)
    # ------------------------------------------------------------------

    _FULL_PROPS = """
        COALESCE(
            jsonb_agg(
                jsonb_build_object(
                    'id',            p.id::text,
                    'name',          p.name,
                    'type',          p.type,
                    'description',   p.description,
                    'required',      p.required,
                    'default_value', p.default_value,
                    'schema',        p.schema,
                    'metadata',      p.metadata
                ) ORDER BY p.name
            ) FILTER (WHERE p.id IS NOT NULL),
            '[]'::jsonb
        ) AS properties
    """

    _FULL_JOINS = """
        LEFT JOIN node_properties np ON np.node_id = n.id
        LEFT JOIN properties p       ON p.id = np.property_id
    """

    _FULL_GROUP = (
        "n.id, n.workflow_id, n.name, n.description, n.status, n.prompt, "
        'n.response_format, n.config, n.metadata, n."order", n.priority, '
        "n.created_at, n.updated_at"
    )

    def _full_row_to_dict(self, row) -> dict:
        d = dict(row)
        d["id"] = str(d["id"])
        d["workflow_id"] = str(d["workflow_id"]) if d.get("workflow_id") else None
        d["created_at"] = d["created_at"].isoformat()
        d["updated_at"] = d["updated_at"].isoformat()
        for field in ("response_format", "config", "metadata"):
            if isinstance(d.get(field), str):
                d[field] = json.loads(d[field])
        if isinstance(d.get("properties"), str):
            d["properties"] = json.loads(d["properties"])
        return d

    async def get_full(self, node_id: UUID) -> dict | None:
        pool = await self._database.get_pool()
        row = await pool.fetchrow(
            f"""
            SELECT {self._FULL_GROUP.replace('n.', 'n.')}, {self._FULL_PROPS}
            FROM nodes n
            {self._FULL_JOINS}
            WHERE n.id = $1
            GROUP BY {self._FULL_GROUP}
            """,
            node_id,
        )
        return self._full_row_to_dict(row) if row else None

    async def list_all_full(self) -> list[dict]:
        pool = await self._database.get_pool()
        rows = await pool.fetch(
            f"""
            SELECT {self._FULL_GROUP.replace('n.', 'n.')}, {self._FULL_PROPS}
            FROM nodes n
            {self._FULL_JOINS}
            GROUP BY {self._FULL_GROUP}
            ORDER BY n."order" NULLS LAST, n.created_at
            """
        )
        return [self._full_row_to_dict(r) for r in rows]

    async def list_by_workflow(self, workflow_id: UUID) -> list[dict]:
        pool = await self._database.get_pool()
        rows = await pool.fetch(
            f"""
            SELECT {self._FULL_GROUP}, {self._FULL_PROPS}
            FROM nodes n
            {self._FULL_JOINS}
            WHERE n.workflow_id = $1
            GROUP BY {self._FULL_GROUP}
            ORDER BY n."order" NULLS LAST, n.created_at
            """,
            workflow_id,
        )
        return [self._full_row_to_dict(r) for r in rows]
