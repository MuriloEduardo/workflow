import json
from uuid import UUID

from app.infrastructure.database.postgres_connection import PostgresConnection
from app.ports.outbound.condition_repository import ConditionRepository

_COLS = "id, operator, compare_value, prompt, logic_operator, metadata, created_at, updated_at"

_EDGE_IDS = (
    "ARRAY("
    "SELECT ec.edge_id::text FROM edge_conditions ec "
    "WHERE ec.condition_id = c.id ORDER BY ec.edge_id"
    ") AS edge_ids"
)


def _row_to_dict(row: object) -> dict:
    d = dict(row)
    d["id"] = str(d["id"])
    d["created_at"] = d["created_at"].isoformat()
    d["updated_at"] = d["updated_at"].isoformat()
    for field in ("compare_value", "metadata"):
        if isinstance(d.get(field), str):
            d[field] = json.loads(d[field])
    d["edge_ids"] = list(d.get("edge_ids") or [])
    return d


class PostgresConditionRepository(ConditionRepository):
    def __init__(self, database: PostgresConnection) -> None:
        self._database = database

    async def create(
        self,
        operator: str,
        compare_value: object | None,
        prompt: str | None,
        logic_operator: str,
        metadata: dict,
    ) -> UUID:
        pool = await self._database.get_pool()
        return await pool.fetchval(
            """
            INSERT INTO conditions
                (operator, compare_value, prompt, logic_operator, metadata)
            VALUES ($1,$2::jsonb,$3,$4,$5::jsonb)
            RETURNING id
            """,
            operator,
            json.dumps(compare_value) if compare_value is not None else None,
            prompt,
            logic_operator,
            json.dumps(metadata),
        )

    async def get(self, condition_id: UUID) -> dict | None:
        pool = await self._database.get_pool()
        row = await pool.fetchrow(
            f"""
            SELECT c.{_COLS.replace(", ", ", c.")}, {_EDGE_IDS}
            FROM conditions c
            WHERE c.id = $1
            """,
            condition_id,
        )
        return _row_to_dict(row) if row else None

    async def list_all(self) -> list[dict]:
        pool = await self._database.get_pool()
        rows = await pool.fetch(
            f"""
            SELECT c.{_COLS.replace(", ", ", c.")}, {_EDGE_IDS}
            FROM conditions c
            ORDER BY c.created_at
            """
        )
        return [_row_to_dict(r) for r in rows]

    async def list_by_edge(self, edge_id: UUID) -> list[dict]:
        pool = await self._database.get_pool()
        rows = await pool.fetch(
            f"""
            SELECT c.{_COLS.replace(", ", ", c.")}, {_EDGE_IDS}
            FROM conditions c
            JOIN edge_conditions ec ON ec.condition_id = c.id
            WHERE ec.edge_id = $1
            ORDER BY c.created_at
            """,
            edge_id,
        )
        return [_row_to_dict(r) for r in rows]

    async def list_by_workflow(self, workflow_id: UUID) -> list[dict]:
        pool = await self._database.get_pool()
        rows = await pool.fetch(
            f"""
            SELECT c.{_COLS.replace(", ", ", c.")}, {_EDGE_IDS}
            FROM conditions c
            WHERE EXISTS (
                SELECT 1 FROM edge_conditions ec
                JOIN edges e ON e.id = ec.edge_id
                JOIN nodes n ON n.id = e.source_node_id
                WHERE ec.condition_id = c.id AND n.workflow_id = $1
            )
            ORDER BY c.created_at
            """,
            workflow_id,
        )
        return [_row_to_dict(r) for r in rows]

    async def update(self, condition_id: UUID, fields: dict) -> dict | None:
        if not fields:
            return await self.get(condition_id)
        allowed = {
            "operator",
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
        result = await pool.execute(
            f"UPDATE conditions SET {', '.join(sets)} WHERE id = $1",
            *params,
        )
        if result.split()[-1] == "0":
            return None
        return await self.get(condition_id)

    async def delete(self, condition_id: UUID) -> bool:
        pool = await self._database.get_pool()
        result = await pool.execute(
            "DELETE FROM conditions WHERE id = $1", condition_id
        )
        return result.split()[-1] != "0"

    # ------------------------------------------------------------------
    # Edge ↔ Condition junction
    # ------------------------------------------------------------------

    async def link_edge(self, condition_id: UUID, edge_id: UUID) -> None:
        pool = await self._database.get_pool()
        await pool.execute(
            """
            INSERT INTO edge_conditions (edge_id, condition_id)
            VALUES ($1, $2)
            ON CONFLICT DO NOTHING
            """,
            edge_id,
            condition_id,
        )

    async def unlink_edge(self, condition_id: UUID, edge_id: UUID) -> bool:
        pool = await self._database.get_pool()
        result = await pool.execute(
            "DELETE FROM edge_conditions WHERE edge_id = $1 AND condition_id = $2",
            edge_id,
            condition_id,
        )
        return result.split()[-1] != "0"

    # ------------------------------------------------------------------
    # Condition ↔ Property junction
    # ------------------------------------------------------------------

    async def link_property(self, condition_id: UUID, property_id: UUID) -> None:
        pool = await self._database.get_pool()
        await pool.execute(
            """
            INSERT INTO condition_properties (condition_id, property_id)
            VALUES ($1, $2)
            ON CONFLICT DO NOTHING
            """,
            condition_id,
            property_id,
        )

    async def unlink_property(self, condition_id: UUID, property_id: UUID) -> bool:
        pool = await self._database.get_pool()
        result = await pool.execute(
            "DELETE FROM condition_properties WHERE condition_id = $1 AND property_id = $2",
            condition_id,
            property_id,
        )
        return result.split()[-1] != "0"

    async def list_properties(self, condition_id: UUID) -> list[dict]:
        pool = await self._database.get_pool()
        rows = await pool.fetch(
            """
            SELECT p.id, p.name, p.type, p.description, p.required,
                   p.default_value, p.schema, p.metadata, p.created_at, p.updated_at
            FROM properties p
            JOIN condition_properties cp ON cp.property_id = p.id
            WHERE cp.condition_id = $1
            ORDER BY p.name
            """,
            condition_id,
        )
        result = []
        for r in rows:
            d = dict(r)
            d["id"] = str(d["id"])
            d["created_at"] = d["created_at"].isoformat()
            d["updated_at"] = d["updated_at"].isoformat()
            for field in ("default_value", "schema", "metadata"):
                if isinstance(d.get(field), str):
                    d[field] = json.loads(d[field])
            result.append(d)
        return result
