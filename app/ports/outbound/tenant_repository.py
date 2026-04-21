from abc import ABC, abstractmethod
from uuid import UUID


class TenantRepository(ABC):
    @abstractmethod
    async def upsert_tenant(self, slug: str, name: str) -> UUID:
        """
        Return the id of the tenant identified by slug.
        Creates a new active tenant if one does not exist yet.
        """
        raise NotImplementedError

    @abstractmethod
    async def upsert_contact(
        self,
        tenant_id: UUID,
        channel_type: str,
        sender_id: str,
    ) -> UUID:
        """
        Return the id of the tenant_contact for (tenant_id, channel_type, sender_id).
        Creates a new contact if one does not exist yet.
        """
        raise NotImplementedError
