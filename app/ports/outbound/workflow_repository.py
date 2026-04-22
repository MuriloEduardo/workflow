from abc import ABC, abstractmethod
from uuid import UUID


class WorkflowRepository(ABC):
    @abstractmethod
    async def create(
        self,
        tenant_id: UUID,
        name: str,
        description: str | None,
        status: str,
        metadata: dict,
    ) -> UUID:
        raise NotImplementedError

    @abstractmethod
    async def get(self, workflow_id: UUID) -> dict | None:
        raise NotImplementedError

    @abstractmethod
    async def list_all(self) -> list[dict]:
        raise NotImplementedError

    @abstractmethod
    async def list_by_tenant(self, tenant_id: UUID) -> list[dict]:
        raise NotImplementedError

    @abstractmethod
    async def update(self, workflow_id: UUID, fields: dict) -> dict | None:
        raise NotImplementedError

    @abstractmethod
    async def delete(self, workflow_id: UUID) -> bool:
        raise NotImplementedError
