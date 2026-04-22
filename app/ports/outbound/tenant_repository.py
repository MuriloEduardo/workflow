from abc import ABC, abstractmethod
from uuid import UUID


class TenantRepository(ABC):
    # ------------------------------------------------------------------
    # Tenants
    # ------------------------------------------------------------------

    @abstractmethod
    async def create_tenant(
        self, slug: str, name: str, status: str, metadata: dict
    ) -> UUID:
        raise NotImplementedError

    @abstractmethod
    async def upsert_tenant(self, slug: str, name: str) -> UUID:
        """Return the id of the tenant identified by slug. Creates if absent."""
        raise NotImplementedError

    @abstractmethod
    async def get_tenant(self, tenant_id: UUID) -> dict | None:
        raise NotImplementedError

    @abstractmethod
    async def list_tenants(self) -> list[dict]:
        raise NotImplementedError

    @abstractmethod
    async def update_tenant(self, tenant_id: UUID, fields: dict) -> dict | None:
        raise NotImplementedError

    @abstractmethod
    async def delete_tenant(self, tenant_id: UUID) -> bool:
        raise NotImplementedError

    # ------------------------------------------------------------------
    # Tenant Contacts
    # ------------------------------------------------------------------

    @abstractmethod
    async def upsert_contact(
        self,
        tenant_id: UUID,
        channel_type: str,
        sender_id: str,
    ) -> UUID:
        """Return the id of the contact. Creates if absent."""
        raise NotImplementedError

    @abstractmethod
    async def create_contact(
        self,
        tenant_id: UUID,
        channel_type: str,
        sender_id: str,
        name: str | None,
        metadata: dict,
    ) -> UUID:
        raise NotImplementedError

    @abstractmethod
    async def get_contact(self, contact_id: UUID) -> dict | None:
        raise NotImplementedError

    @abstractmethod
    async def list_contacts(self, tenant_id: UUID) -> list[dict]:
        raise NotImplementedError

    @abstractmethod
    async def update_contact(self, contact_id: UUID, fields: dict) -> dict | None:
        raise NotImplementedError

    @abstractmethod
    async def delete_contact(self, contact_id: UUID) -> bool:
        raise NotImplementedError
