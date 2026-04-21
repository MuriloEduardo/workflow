from uuid import UUID

from app.infrastructure.database.postgres_connection import PostgresConnection
from app.ports.outbound.tenant_repository import TenantRepository


class PostgresTenantRepository(TenantRepository):
    def __init__(self, database: PostgresConnection) -> None:
        self._database = database

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
