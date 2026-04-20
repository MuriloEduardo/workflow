import structlog

from app.domain.services.debounce import DebounceService
from app.domain.services.inbound_transformer import transform_inbound
from app.domain.services.session import SessionService
from app.ports.inbound.message_handler import MessageHandler

logger = structlog.get_logger(__name__)

DEFAULT_TENANT = "default"


class ChannelInboundHandler(MessageHandler):
    """
    Handles raw inbound payloads from communication channels.
    Resolves (or creates) a session, then enqueues into the debounce buffer.
    """

    def __init__(self, debounce: DebounceService, session: SessionService) -> None:
        self._debounce = debounce
        self._session = session

    async def handle(
        self, message: bytes, routing_key: str, headers: dict | None = None
    ) -> None:
        if not message:
            logger.warning("channel_inbound.empty_message", routing_key=routing_key)
            return

        logger.info("channel_inbound.received", routing_key=routing_key)

        inbound = transform_inbound(routing_key, message)

        tenant_id = inbound.tenant_id or DEFAULT_TENANT

        session = await self._session.resolve(
            tenant_id=tenant_id,
            channel_type=inbound.channel_type,
            sender_id=inbound.sender_id,
        )

        group_key = session.session_id

        await self._debounce.enqueue(
            group_key=group_key,
            content=inbound.content,
            metadata={
                "message_id": inbound.message_id,
                "channel_type": inbound.channel_type,
                "sender_id": inbound.sender_id,
                "session_id": session.session_id,
                "thread_id": session.thread_id,
                "tenant_id": tenant_id,
            },
        )
        logger.info(
            "channel_inbound.enqueued",
            group_key=group_key,
            thread_id=session.thread_id,
            is_new_session=session.is_new,
        )
