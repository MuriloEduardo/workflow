import json
from uuid import UUID

from app.infrastructure.database.postgres_connection import PostgresConnection
from app.ports.outbound.condition_repository import ConditionRepository

_COLS = "id, edge_id, operator, property_name, compare_value, prompt, logic_operator, metadata, created_at, updated_at"


def _row_to_dict(row: object) -> dict:
    d = dict(row)
    d["id"] = str(d["id"])
    d["edge_id"] = str(d["edge_id"])
    d["created_at"] = d["created_at"].isoformat()
    d["updated_at"] = d["updated_at"].isoformat()
    return d


class PostgresConditionRepository(ConditionRepository):
    def __init__(self, database: PostgresConnection) -> None:
        self._database = database

    async def create(
        self,
        edge_id: UUID,
        operator: str,
        property_name: str | None,
        compare_value: object | None,
        prompt: str | None,
        logic_operator: str,
        metadata: dict,
    ) -> UUID:
        pool = await self._database.get_pool()
        return await pool.fetchval(
            """
            INSERT INTO conditions
                (edge_id, operator, property_name, compare_value, prompt, logic_operator, metadata)
            VALUES ($1,$2,$3,$4::jsonb,$5,$6,$7::jsonb)
            RETURNING id
            """,
            edge_id,
            operator,
            property_name,
            json.dumps(compare_value) if compare_value is not None else None,
            prompt,
            logic_operator,
            json.dumps(metadata),
        )

    async def get(self, condition_id: UUID) -> dict | None:
        pool = await self._database.get_pool()
        row = await pool.fetchrow(
            f"SELECT {_COLS} FROM conditions WHERE id = $1", condition_id
        )
        return _row_to_dict(row) if row else None

    async def list_by_edge(self, edge_id: UUID) -> list[dict]:
        pool = await self._database.get_pool()
        rows = await pool.fetch(
            f"SELECT {_COLS} FROM conditions WHERE edge_id = $1 ORDER BY created_at",
            edge_id,
        )
        return [_row_to_dict(r) for r in rows]

    async def update(self, condition_id: UUID, fields: dict) -> dict | None:
        if not fields:
            return await self.get(condition_id)
        allowed = {
            "operator",
            "property_name",
            "compare_value",
            "prompt",
            "logic_operator",
            "metadata",
        }
        json_cols = {"compare_value", "metadata"}
        sets, params = [], [condition_id]
        for key, val in fields.items():
            if key not in allowed:
                continue
            params.append(
                json.dumps(val) if key in json_cols and val is not None else val
            )
            cast = "::jsonb" if key in json_cols else ""
            sets.append(f"{key} = ${len(params)}{cast}")
        if not sets:
            return await self.get(condition_id)
        sets.append("updated_at = now()")
        pool = await self._database.get_pool()
        row = await pool.fetchrow(
            f"UPDATE conditions SET {', '.join(sets)} WHERE id = $1 RETURNING {_COLS}",
            *params,
        )
        return _row_to_dict(row) if row else None

    async def delete(self, condition_id: UUID) -> bool:
        pool = await self._database.get_pool()
        result = await pool.execute(
            "DELETE FROM conditions WHERE id = $1", condition_id
        )
        return result.split()[-1] != "0"
