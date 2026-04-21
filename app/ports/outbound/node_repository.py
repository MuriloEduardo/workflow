from abc import ABC, abstractmethod
from uuid import UUID


class NodeRepository(ABC):
    @abstractmethod
    async def create(
        self,
        name: str,
        description: str | None,
        status: str,
        prompt: str | None,
        response_format: dict | None,
        properties: dict,
        config: dict,
        metadata: dict,
        order: int | None,
        priority: int,
    ) -> UUID:
        raise NotImplementedError

    @abstractmethod
    async def get(self, node_id: UUID) -> dict | None:
        raise NotImplementedError

    @abstractmethod
    async def list_all(self) -> list[dict]:
        raise NotImplementedError

    @abstractmethod
    async def update(self, node_id: UUID, fields: dict) -> dict | None:
        raise NotImplementedError

    @abstractmethod
    async def delete(self, node_id: UUID) -> bool:
        raise NotImplementedError
