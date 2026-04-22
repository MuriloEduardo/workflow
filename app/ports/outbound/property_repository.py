from abc import ABC, abstractmethod
from uuid import UUID


class PropertyRepository(ABC):
    @abstractmethod
    async def create(
        self,
        name: str,
        type: str,
        description: str | None,
        required: bool,
        default_value: object | None,
        schema: dict,
        metadata: dict,
    ) -> UUID:
        raise NotImplementedError

    @abstractmethod
    async def get(self, property_id: UUID) -> dict | None:
        raise NotImplementedError

    @abstractmethod
    async def list_all(self) -> list[dict]:
        raise NotImplementedError

    @abstractmethod
    async def update(self, property_id: UUID, fields: dict) -> dict | None:
        raise NotImplementedError

    @abstractmethod
    async def delete(self, property_id: UUID) -> bool:
        raise NotImplementedError

    # ------------------------------------------------------------------
    # Node ↔ Property junction
    # ------------------------------------------------------------------

    @abstractmethod
    async def link_to_node(self, property_id: UUID, node_id: UUID) -> None:
        raise NotImplementedError

    @abstractmethod
    async def unlink_from_node(self, property_id: UUID, node_id: UUID) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def list_by_node(self, node_id: UUID) -> list[dict]:
        raise NotImplementedError
