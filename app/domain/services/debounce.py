import uuid

import structlog

from app.domain.entities.orchestration import (
    CognitionRequest,
    WorkflowContext,
)
from app.ports.outbound.execution_repository import ExecutionRepository
from app.ports.outbound.message_publisher import MessagePublisher
from app.ports.outbound.pending_message_repository import PendingMessageRepository

logger = structlog.get_logger(__name__)

COGNITION_EXCHANGE = "cognition.exchange"
COGNITION_REQUEST_KEY = "cognition.request"


class DebounceService:
    def __init__(
        self,
        repository: PendingMessageRepository,
        publisher: MessagePublisher,
        debounce_seconds: float = 10.0,
        execution_repo: ExecutionRepository | None = None,
    ) -> None:
        self._repository = repository
        self._publisher = publisher
        self._debounce_seconds = debounce_seconds
        self._execution_repo = execution_repo

    async def enqueue(self, group_key: str, content: str, metadata: dict) -> None:
        msg_id = await self._repository.insert(group_key, content, metadata)
        logger.info("debounce.enqueued", group_key=group_key, message_id=str(msg_id))

    async def flush_mature_groups(self) -> int:
        groups = await self._repository.get_mature_groups(self._debounce_seconds)
        flushed = 0

        for group_key in groups:
            messages = await self._repository.flush_group(group_key)
            if not messages:
                continue
            request_id = await self._publish_to_cognition(group_key, messages)
            logger.info(
                "debounce.flushed",
                group_key=group_key,
                message_count=len(messages),
                request_id=request_id,
            )
            flushed += 1

        return flushed

    async def _publish_to_cognition(self, group_key: str, messages: list[dict]) -> str:
        combined_content = "\n".join(m["content"] for m in messages)
        first_meta = messages[0]["metadata"]
        session_id = first_meta.get("session_id", group_key)
        thread_id = first_meta.get("thread_id", session_id)

        flow_state = await self._build_flow_state(thread_id)

        request = CognitionRequest(
            request_id=str(uuid.uuid4()),
            prompt=combined_content,
            context=WorkflowContext(
                session_id=thread_id,
                state={"flow": flow_state} if flow_state else {},
                metadata={
                    "group_key": group_key,
                    "message_count": len(messages),
                    "original_metadata": first_meta,
                },
            ),
        )

        await self._publisher.publish(
            message=request.model_dump_json().encode(),
            routing_key=COGNITION_REQUEST_KEY,
            exchange_name=COGNITION_EXCHANGE,
        )

        return request.request_id

    async def _build_flow_state(self, session_id: str) -> dict:
        if not self._execution_repo:
            return {}
        flow = await self._execution_repo.get_session_flow(session_id)
        if not flow:
            return {}
        return {
            "current_node_id": flow["node_id"],
            "current_node_name": flow["node_name"],
            "current_node_prompt": flow["node_prompt"],
            "incoming_edge": (
                {
                    "id": flow["incoming_edge_id"],
                    "label": flow["incoming_edge_label"],
                    "condition_prompt": flow["incoming_edge_condition"],
                }
                if flow.get("incoming_edge_id")
                else None
            ),
            "next_edges": flow.get("next_edges") or [],
        }
