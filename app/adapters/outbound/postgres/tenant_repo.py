import json
from uuid import UUID

from app.infrastructure.database.postgres_connection import PostgresConnection
from app.ports.outbound.tenant_repository import TenantRepository

_TENANT_COLS = "id, slug, name, status, metadata, created_at, updated_at"
_CONTACT_COLS = (
    "id, tenant_id, channel_type, sender_id, name, metadata, created_at, updated_at"
)


def _tenant_row(row) -> dict:
    d = dict(row)
    d["id"] = str(d["id"])
    d["created_at"] = d["created_at"].isoformat()
    d["updated_at"] = d["updated_at"].isoformat()
    if isinstance(d.get("metadata"), str):
        d["metadata"] = json.loads(d["metadata"])
    return d


def _contact_row(row) -> dict:
    d = dict(row)
    d["id"] = str(d["id"])
    d["tenant_id"] = str(d["tenant_id"])
    d["created_at"] = d["created_at"].isoformat()
    d["updated_at"] = d["updated_at"].isoformat()
    if isinstance(d.get("metadata"), str):
        d["metadata"] = json.loads(d["metadata"])
    return d


class PostgresTenantRepository(TenantRepository):
    def __init__(self, database: PostgresConnection) -> None:
        self._database = database

    # ------------------------------------------------------------------
    # Tenants
    # ------------------------------------------------------------------

    async def create_tenant(
        self, slug: str, name: str, status: str, metadata: dict
    ) -> UUID:
        pool = await self._database.get_pool()
        return await pool.fetchval(
            """
            INSERT INTO tenants (slug, name, status, metadata)
            VALUES ($1, $2, $3, $4::jsonb)
            RETURNING id
            """,
            slug,
            name,
            status,
            json.dumps(metadata),
        )

    async def upsert_tenant(self, slug: str, name: str) -> UUID:
        pool = await self._database.get_pool()
        return await pool.fetchval(
            """
            INSERT INTO tenants (slug, name)
            VALUES ($1, $2)
            ON CONFLICT (slug) DO UPDATE
                SET updated_at = now()
            RETURNING id
            """,
            slug,
            name,
        )

    async def get_tenant(self, tenant_id: UUID) -> dict | None:
        pool = await self._database.get_pool()
        row = await pool.fetchrow(
            f"SELECT {_TENANT_COLS} FROM tenants WHERE id = $1", tenant_id
        )
        return _tenant_row(row) if row else None

    async def list_tenants(self) -> list[dict]:
        pool = await self._database.get_pool()
        rows = await pool.fetch(
            f"SELECT {_TENANT_COLS} FROM tenants ORDER BY created_at"
        )
        return [_tenant_row(r) for r in rows]

    async def update_tenant(self, tenant_id: UUID, fields: dict) -> dict | None:
        if not fields:
            return await self.get_tenant(tenant_id)
        allowed = {"slug", "name", "status", "metadata"}
        json_cols = {"metadata"}
        sets, params = [], [tenant_id]
        for key, val in fields.items():
            if key not in allowed:
                continue
            params.append(
                json.dumps(val) if key in json_cols and val is not None else val
            )
            cast = "::jsonb" if key in json_cols else ""
            sets.append(f"{key} = ${len(params)}{cast}")
        if not sets:
            return await self.get_tenant(tenant_id)
        sets.append("updated_at = now()")
        pool = await self._database.get_pool()
        row = await pool.fetchrow(
            f"UPDATE tenants SET {', '.join(sets)} WHERE id = $1 RETURNING {_TENANT_COLS}",
            *params,
        )
        return _tenant_row(row) if row else None

    async def delete_tenant(self, tenant_id: UUID) -> bool:
        pool = await self._database.get_pool()
        result = await pool.execute("DELETE FROM tenants WHERE id = $1", tenant_id)
        return result.split()[-1] != "0"

    # ------------------------------------------------------------------
    # Tenant Contacts
    # ------------------------------------------------------------------

    async def upsert_contact(
        self,
        tenant_id: UUID,
        channel_type: str,
        sender_id: str,
    ) -> UUID:
        pool = await self._database.get_pool()
        return await pool.fetchval(
            """
            INSERT INTO tenant_contacts (tenant_id, channel_type, sender_id)
            VALUES ($1, $2, $3)
            ON CONFLICT (tenant_id, channel_type, sender_id) DO UPDATE
                SET updated_at = now()
            RETURNING id
            """,
            tenant_id,
            channel_type,
            sender_id,
        )

    async def create_contact(
        self,
        tenant_id: UUID,
        channel_type: str,
        sender_id: str,
        name: str | None,
        metadata: dict,
    ) -> UUID:
        pool = await self._database.get_pool()
        return await pool.fetchval(
            """
            INSERT INTO tenant_contacts (tenant_id, channel_type, sender_id, name, metadata)
            VALUES ($1, $2, $3, $4, $5::jsonb)
            ON CONFLICT (tenant_id, channel_type, sender_id) DO UPDATE
                SET name = EXCLUDED.name,
                    metadata = EXCLUDED.metadata,
                    updated_at = now()
            RETURNING id
            """,
            tenant_id,
            channel_type,
            sender_id,
            name,
            json.dumps(metadata),
        )

    async def get_contact(self, contact_id: UUID) -> dict | None:
        pool = await self._database.get_pool()
        row = await pool.fetchrow(
            f"SELECT {_CONTACT_COLS} FROM tenant_contacts WHERE id = $1", contact_id
        )
        return _contact_row(row) if row else None

    async def list_contacts(self, tenant_id: UUID) -> list[dict]:
        pool = await self._database.get_pool()
        rows = await pool.fetch(
            f"SELECT {_CONTACT_COLS} FROM tenant_contacts WHERE tenant_id = $1 ORDER BY created_at",
            tenant_id,
        )
        return [_contact_row(r) for r in rows]

    async def update_contact(self, contact_id: UUID, fields: dict) -> dict | None:
        if not fields:
            return await self.get_contact(contact_id)
        allowed = {"name", "metadata"}
        json_cols = {"metadata"}
        sets, params = [], [contact_id]
        for key, val in fields.items():
            if key not in allowed:
                continue
            params.append(
                json.dumps(val) if key in json_cols and val is not None else val
            )
            cast = "::jsonb" if key in json_cols else ""
            sets.append(f"{key} = ${len(params)}{cast}")
        if not sets:
            return await self.get_contact(contact_id)
        sets.append("updated_at = now()")
        pool = await self._database.get_pool()
        row = await pool.fetchrow(
            f"UPDATE tenant_contacts SET {', '.join(sets)} WHERE id = $1 RETURNING {_CONTACT_COLS}",
            *params,
        )
        return _contact_row(row) if row else None

    async def delete_contact(self, contact_id: UUID) -> bool:
        pool = await self._database.get_pool()
        result = await pool.execute(
            "DELETE FROM tenant_contacts WHERE id = $1", contact_id
        )
        return result.split()[-1] != "0"
