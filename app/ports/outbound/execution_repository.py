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
        selected_edge_id: str | None = None,
        justification: str | None = None,
        confidence: float | None = None,
    ) -> UUID:
        raise NotImplementedError

    @abstractmethod
    async def get_session_flow(self, session_id: str) -> dict | None:
        """
        Returns the current flow state for a session:
        - current_node: node where the session currently is
        - incoming_edge: the edge that concluded and led to current_node (None if first node)
        - next_edges: all outgoing edges from current_node
        """
        raise NotImplementedError
