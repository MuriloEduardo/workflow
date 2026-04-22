import json
from uuid import UUID

from app.infrastructure.database.postgres_connection import PostgresConnection
from app.ports.outbound.edge_repository import EdgeRepository

_COLS = "id, source_node_id, target_node_id, label, priority, metadata, created_at, updated_at"


def _row_to_dict(row: object) -> dict:
    d = dict(row)
    d["id"] = str(d["id"])
    d["source_node_id"] = str(d["source_node_id"])
    d["target_node_id"] = str(d["target_node_id"])
    d["created_at"] = d["created_at"].isoformat()
    d["updated_at"] = d["updated_at"].isoformat()
    if isinstance(d.get("metadata"), str):
        d["metadata"] = json.loads(d["metadata"])
    return d


class PostgresEdgeRepository(EdgeRepository):
    def __init__(self, database: PostgresConnection) -> None:
        self._database = database

    async def create(
        self,
        source_node_id: UUID,
        target_node_id: UUID,
        label: str | None,
        priority: int,
        metadata: dict,
    ) -> UUID:
        pool = await self._database.get_pool()
        return await pool.fetchval(
            """
            INSERT INTO edges
                (source_node_id, target_node_id, label, priority, metadata)
            VALUES ($1,$2,$3,$4,$5::jsonb)
            RETURNING id
            """,
            source_node_id,
            target_node_id,
            label,
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
        allowed = {"label", "priority", "metadata"}
        json_cols = {"metadata"}
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

    # ------------------------------------------------------------------
    # Full read (with embedded relations)
    # ------------------------------------------------------------------

    _FULL_CONDITIONS = """
        COALESCE(
            jsonb_agg(
                jsonb_build_object(
                    'id',             c.id::text,
                    'operator',       c.operator,
                    'compare_value',  c.compare_value,
                    'prompt',         c.prompt,
                    'logic_operator', c.logic_operator,
                    'metadata',       c.metadata,
                    'properties', (
                        SELECT COALESCE(
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
                            ),
                            '[]'::jsonb
                        )
                        FROM condition_properties cp
                        JOIN properties p ON p.id = cp.property_id
                        WHERE cp.condition_id = c.id
                    )
                ) ORDER BY c.created_at
            ) FILTER (WHERE c.id IS NOT NULL),
            '[]'::jsonb
        ) AS conditions
    """

    _FULL_JOINS = """
        LEFT JOIN edge_conditions ec ON ec.edge_id = e.id
        LEFT JOIN conditions c       ON c.id = ec.condition_id
    """

    _FULL_GROUP = (
        "e.id, e.source_node_id, e.target_node_id, e.label, "
        "e.priority, e.metadata, e.created_at, e.updated_at"
    )

    def _full_row_to_dict(self, row) -> dict:
        d = dict(row)
        d["id"] = str(d["id"])
        d["source_node_id"] = str(d["source_node_id"])
        d["target_node_id"] = str(d["target_node_id"])
        d["created_at"] = d["created_at"].isoformat()
        d["updated_at"] = d["updated_at"].isoformat()
        if isinstance(d.get("metadata"), str):
            d["metadata"] = json.loads(d["metadata"])
        if isinstance(d.get("conditions"), str):
            d["conditions"] = json.loads(d["conditions"])
        return d

    async def get_full(self, edge_id: UUID) -> dict | None:
        pool = await self._database.get_pool()
        row = await pool.fetchrow(
            f"""
            SELECT {self._FULL_GROUP}, {self._FULL_CONDITIONS}
            FROM edges e
            {self._FULL_JOINS}
            WHERE e.id = $1
            GROUP BY {self._FULL_GROUP}
            """,
            edge_id,
        )
        return self._full_row_to_dict(row) if row else None

    async def list_all_full(self) -> list[dict]:
        pool = await self._database.get_pool()
        rows = await pool.fetch(
            f"""
            SELECT {self._FULL_GROUP}, {self._FULL_CONDITIONS}
            FROM edges e
            {self._FULL_JOINS}
            GROUP BY {self._FULL_GROUP}
            ORDER BY e.priority, e.created_at
            """
        )
        return [self._full_row_to_dict(r) for r in rows]

    async def list_by_source_full(self, source_node_id: UUID) -> list[dict]:
        pool = await self._database.get_pool()
        rows = await pool.fetch(
            f"""
            SELECT {self._FULL_GROUP}, {self._FULL_CONDITIONS}
            FROM edges e
            {self._FULL_JOINS}
            WHERE e.source_node_id = $1
            GROUP BY {self._FULL_GROUP}
            ORDER BY e.priority, e.created_at
            """,
            source_node_id,
        )
        return [self._full_row_to_dict(r) for r in rows]
