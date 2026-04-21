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

            combined_content = "\n".join(m["content"] for m in messages)
            first_meta = messages[0]["metadata"]
            session_id = first_meta.get("session_id", group_key)
            thread_id = first_meta.get("thread_id", session_id)

            flow_state: dict = {}
            if self._execution_repo:
                flow = await self._execution_repo.get_session_flow(thread_id)
                if flow:
                    last = flow[-1]
                    flow_state = {
                        "current_node_id": last["node_id"],
                        "incoming_edge": (
                            {
                                "id": last["incoming_edge_id"],
                                "label": last["incoming_edge_label"],
                                "condition_prompt": last["incoming_edge_condition"],
                            }
                            if last.get("incoming_edge_id")
                            else None
                        ),
                        "next_edges": last.get("next_edges") or [],
                    }

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

            logger.info(
                "debounce.flushed",
                group_key=group_key,
                message_count=len(messages),
                request_id=request.request_id,
            )
            flushed += 1

        return flushed
