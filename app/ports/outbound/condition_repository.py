from abc import ABC, abstractmethod
from uuid import UUID


class ConditionRepository(ABC):
    @abstractmethod
    async def create(
        self,
        workflow_id: UUID | None,
        operator: str,
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
    async def list_all(self) -> list[dict]:
        raise NotImplementedError

    @abstractmethod
    async def list_by_edge(self, edge_id: UUID) -> list[dict]:
        raise NotImplementedError

    @abstractmethod
    async def list_by_workflow(self, workflow_id: UUID) -> list[dict]:
        """Returns all conditions belonging to a workflow."""
        raise NotImplementedError

    @abstractmethod
    async def update(self, condition_id: UUID, fields: dict) -> dict | None:
        raise NotImplementedError

    @abstractmethod
    async def delete(self, condition_id: UUID) -> bool:
        raise NotImplementedError

    # ------------------------------------------------------------------
    # Edge ↔ Condition junction
    # ------------------------------------------------------------------

    @abstractmethod
    async def link_edge(self, condition_id: UUID, edge_id: UUID) -> None:
        raise NotImplementedError

    @abstractmethod
    async def unlink_edge(self, condition_id: UUID, edge_id: UUID) -> bool:
        raise NotImplementedError

    # ------------------------------------------------------------------
    # Condition ↔ Property junction
    # ------------------------------------------------------------------

    @abstractmethod
    async def link_property(self, condition_id: UUID, property_id: UUID) -> None:
        raise NotImplementedError

    @abstractmethod
    async def unlink_property(self, condition_id: UUID, property_id: UUID) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def list_properties(self, condition_id: UUID) -> list[dict]:
        raise NotImplementedError
