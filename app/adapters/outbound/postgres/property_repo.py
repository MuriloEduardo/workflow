import json
from uuid import UUID

from app.infrastructure.database.postgres_connection import PostgresConnection
from app.ports.outbound.property_repository import PropertyRepository

_COLS = "id, name, type, description, required, default_value, schema, metadata, created_at, updated_at"


def _row_to_dict(row: object) -> dict:
    d = dict(row)
    d["id"] = str(d["id"])
    d["created_at"] = d["created_at"].isoformat()
    d["updated_at"] = d["updated_at"].isoformat()
    return d


class PostgresPropertyRepository(PropertyRepository):
    def __init__(self, database: PostgresConnection) -> None:
        self._database = database

    async def create(
        self,
        name: str,
        type: str,
        description: str | None,
        required: bool,
        default_value: object | None,
        schema: dict,
        metadata: dict,
    ) -> UUID:
        pool = await self._database.get_pool()
        return await pool.fetchval(
            """
            INSERT INTO properties (name, type, description, required, default_value, schema, metadata)
            VALUES ($1,$2,$3,$4,$5::jsonb,$6::jsonb,$7::jsonb)
            RETURNING id
            """,
            name,
            type,
            description,
            required,
            json.dumps(default_value) if default_value is not None else None,
            json.dumps(schema),
            json.dumps(metadata),
        )

    async def get(self, property_id: UUID) -> dict | None:
        pool = await self._database.get_pool()
        row = await pool.fetchrow(
            f"SELECT {_COLS} FROM properties WHERE id = $1", property_id
        )
        return _row_to_dict(row) if row else None

    async def list_all(self) -> list[dict]:
        pool = await self._database.get_pool()
        rows = await pool.fetch(f"SELECT {_COLS} FROM properties ORDER BY name")
        return [_row_to_dict(r) for r in rows]

    async def update(self, property_id: UUID, fields: dict) -> dict | None:
        if not fields:
            return await self.get(property_id)
        allowed = {
            "name",
            "type",
            "description",
            "required",
            "default_value",
            "schema",
            "metadata",
        }
        json_cols = {"default_value", "schema", "metadata"}
        sets, params = [], [property_id]
        for key, val in fields.items():
            if key not in allowed:
                continue
            params.append(
                json.dumps(val) if key in json_cols and val is not None else val
            )
            cast = "::jsonb" if key in json_cols else ""
            sets.append(f"{key} = ${len(params)}{cast}")
        if not sets:
            return await self.get(property_id)
        sets.append("updated_at = now()")
        pool = await self._database.get_pool()
        row = await pool.fetchrow(
            f"UPDATE properties SET {', '.join(sets)} WHERE id = $1 RETURNING {_COLS}",
            *params,
        )
        return _row_to_dict(row) if row else None

    async def delete(self, property_id: UUID) -> bool:
        pool = await self._database.get_pool()
        result = await pool.execute("DELETE FROM properties WHERE id = $1", property_id)
        return result.split()[-1] != "0"

    # ------------------------------------------------------------------
    # Node ↔ Property junction
    # ------------------------------------------------------------------

    async def link_to_node(self, property_id: UUID, node_id: UUID) -> None:
        pool = await self._database.get_pool()
        await pool.execute(
            """
            INSERT INTO node_properties (node_id, property_id)
            VALUES ($1, $2)
            ON CONFLICT DO NOTHING
            """,
            node_id,
            property_id,
        )

    async def unlink_from_node(self, property_id: UUID, node_id: UUID) -> bool:
        pool = await self._database.get_pool()
        result = await pool.execute(
            "DELETE FROM node_properties WHERE node_id = $1 AND property_id = $2",
            node_id,
            property_id,
        )
        return result.split()[-1] != "0"

    async def list_by_node(self, node_id: UUID) -> list[dict]:
        pool = await self._database.get_pool()
        rows = await pool.fetch(
            f"""
            SELECT p.{_COLS.replace(", ", ", p.")}
            FROM properties p
            JOIN node_properties np ON np.property_id = p.id
            WHERE np.node_id = $1
            ORDER BY p.name
            """,
            node_id,
        )
        return [_row_to_dict(r) for r in rows]
