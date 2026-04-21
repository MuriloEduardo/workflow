import time

import structlog

from app.domain.entities.orchestration import CognitionResponse
from app.domain.services.outbound_transformer import build_outbound_messages
from app.ports.inbound.message_handler import MessageHandler
from app.ports.outbound.execution_repository import ExecutionRepository
from app.ports.outbound.message_publisher import MessagePublisher

logger = structlog.get_logger(__name__)

COMMUNICATION_EXCHANGE = "communication.exchange"
COMMUNICATION_SEND_KEY = "send.message"


class CognitionResponseHandler(MessageHandler):
    """
    Handles responses from cognition service.
    Workflow orchestrates: receives from cognition → registers execution → sends to communication.
    """

    def __init__(
        self,
        publisher: MessagePublisher,
        execution_repo: ExecutionRepository,
    ) -> None:
        self._publisher = publisher
        self._execution_repo = execution_repo

    async def handle(
        self, message: bytes, routing_key: str, headers: dict | None = None
    ) -> None:
        if not message:
            logger.warning("cognition_response.empty_message", routing_key=routing_key)
            return

        received_at = time.monotonic()
        logger.info("cognition_response.received", routing_key=routing_key)

        cognition_resp = CognitionResponse.model_validate_json(message)

        latency_ms = int((time.monotonic() - received_at) * 1000)

        session_id = (
            cognition_resp.context.session_id if cognition_resp.context else None
        )

        status = "failed" if cognition_resp.error else "completed"

        execution_id = await self._execution_repo.create(
            request_id=cognition_resp.request_id,
            status=status,
            session_id=session_id,
            response=cognition_resp.content,
            model=cognition_resp.model,
            total_tokens=cognition_resp.tokens_used,
            latency_ms=latency_ms,
            error=cognition_resp.error,
        )

        logger.info(
            "cognition_response.execution_saved",
            execution_id=str(execution_id),
            request_id=cognition_resp.request_id,
            status=status,
        )

        if cognition_resp.error:
            logger.warning(
                "cognition_response.error",
                request_id=cognition_resp.request_id,
                error=cognition_resp.error,
            )
            return

        outbound_list = build_outbound_messages(cognition_resp)

        for outbound in outbound_list:
            await self._publisher.publish(
                message=outbound.model_dump_json().encode(),
                routing_key=COMMUNICATION_SEND_KEY,
                exchange_name=COMMUNICATION_EXCHANGE,
                headers=headers,
            )
            logger.info(
                "cognition_response.forwarded_to_communication",
                message_id=outbound.message_id,
            )

        logger.info(
            "cognition_response.done",
            request_id=cognition_resp.request_id,
            messages_sent=len(outbound_list),
        )
