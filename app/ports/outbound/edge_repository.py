from abc import ABC, abstractmethod
from uuid import UUID


class EdgeRepository(ABC):
    @abstractmethod
    async def create(
        self,
        source_node_id: UUID,
        target_node_id: UUID,
        label: str | None,
        priority: int,
        metadata: dict,
    ) -> UUID:
        raise NotImplementedError

    @abstractmethod
    async def get(self, edge_id: UUID) -> dict | None:
        raise NotImplementedError

    @abstractmethod
    async def list_by_source(self, source_node_id: UUID) -> list[dict]:
        raise NotImplementedError

    @abstractmethod
    async def list_all(self) -> list[dict]:
        raise NotImplementedError

    @abstractmethod
    async def update(self, edge_id: UUID, fields: dict) -> dict | None:
        raise NotImplementedError

    @abstractmethod
    async def delete(self, edge_id: UUID) -> bool:
        raise NotImplementedError
