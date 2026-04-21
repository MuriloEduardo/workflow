from abc import ABC, abstractmethod
from uuid import UUID


class SessionRepository(ABC):
    @abstractmethod
    async def get_active(
        self, tenant_id: UUID, channel_type: str, contact_id: UUID
    ) -> dict | None:
        raise NotImplementedError

    @abstractmethod
    async def create(
        self,
        tenant_id: UUID,
        channel_type: str,
        contact_id: UUID,
        thread_id: str,
        timeout_seconds: int,
    ) -> UUID:
        raise NotImplementedError

    @abstractmethod
    async def touch(self, session_id: UUID) -> None:
        """Update last_activity to now()."""
        raise NotImplementedError

    @abstractmethod
    async def expire(self, session_id: UUID) -> None:
        raise NotImplementedError
