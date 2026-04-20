import structlog

from app.domain.entities.orchestration import CognitionResponse
from app.domain.services.outbound_transformer import build_outbound_messages
from app.ports.inbound.message_handler import MessageHandler
from app.ports.outbound.message_publisher import MessagePublisher

logger = structlog.get_logger(__name__)

COMMUNICATION_EXCHANGE = "communication.exchange"
COMMUNICATION_SEND_KEY = "send.message"


class CognitionResponseHandler(MessageHandler):
    """
    Handles responses from cognition service.
    Workflow orchestrates: receives from cognition → transforms → sends to communication.
    """

    def __init__(self, publisher: MessagePublisher) -> None:
        self._publisher = publisher

    async def handle(
        self, message: bytes, routing_key: str, headers: dict | None = None
    ) -> None:
        if not message:
            logger.warning("cognition_response.empty_message", routing_key=routing_key)
            return

        logger.info("cognition_response.received", routing_key=routing_key)

        cognition_resp = CognitionResponse.model_validate_json(message)

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
