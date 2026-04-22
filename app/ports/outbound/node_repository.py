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

    @abstractmethod
    async def get_full(self, node_id: UUID) -> dict | None:
        """Returns node with embedded properties list."""
        raise NotImplementedError

    @abstractmethod
    async def list_all_full(self) -> list[dict]:
        """Returns all nodes with embedded properties list."""
        raise NotImplementedError
