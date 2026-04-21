from abc import ABC, abstractmethod
from uuid import UUID


class ExecutionRepository(ABC):
    @abstractmethod
    async def create(
        self,
        request_id: str,
        status: str,
        node_id: str | None = None,
        tenant_id: str | None = None,
        contact_id: str | None = None,
        session_id: str | None = None,
        prompt: str | None = None,
        response: str | None = None,
        model: str | None = None,
        input_tokens: int | None = None,
        output_tokens: int | None = None,
        total_tokens: int | None = None,
        latency_ms: int | None = None,
        error: str | None = None,
        metadata: dict | None = None,
    ) -> UUID:
        raise NotImplementedError

    @abstractmethod
    async def get_session_flow(self, session_id: str) -> list[dict]:
        """
        Returns executions for a session ordered by time, each annotated with
        incoming_edge (edge that came from the previous node) and
        outgoing_edge (edge that leads to the next node).
        """
        raise NotImplementedError
