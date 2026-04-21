from abc import ABC, abstractmethod
from uuid import UUID


class ConditionRepository(ABC):
    @abstractmethod
    async def create(
        self,
        edge_id: UUID,
        operator: str,
        property_name: str | None,
        compare_value: object | None,
        prompt: str | None,
        logic_operator: str,
        metadata: dict,
    ) -> UUID:
        raise NotImplementedError

    @abstractmethod
    async def get(self, condition_id: UUID) -> dict | None:
        raise NotImplementedError

    @abstractmethod
    async def list_by_edge(self, edge_id: UUID) -> list[dict]:
        raise NotImplementedError

    @abstractmethod
    async def update(self, condition_id: UUID, fields: dict) -> dict | None:
        raise NotImplementedError

    @abstractmethod
    async def delete(self, condition_id: UUID) -> bool:
        raise NotImplementedError
