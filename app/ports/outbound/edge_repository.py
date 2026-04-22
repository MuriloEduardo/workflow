from abc import ABC, abstractmethod
from uuid import UUID


class EdgeRepository(ABC):
    @abstractmethod
    async def create(
        self,
        workflow_id: UUID | None,
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

    @abstractmethod
    async def get_full(self, edge_id: UUID) -> dict | None:
        """Returns edge with embedded conditions (each with embedded properties)."""
        raise NotImplementedError

    @abstractmethod
    async def list_all_full(self) -> list[dict]:
        """Returns all edges with embedded conditions and their properties."""
        raise NotImplementedError

    @abstractmethod
    async def list_by_source_full(self, source_node_id: UUID) -> list[dict]:
        """Returns edges by source node with embedded conditions and their properties."""
        raise NotImplementedError

    @abstractmethod
    async def list_by_workflow(self, workflow_id: UUID) -> list[dict]:
        """Returns all edges (full) belonging to a workflow."""
        raise NotImplementedError
