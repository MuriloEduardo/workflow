"""
Outbound message transformers.

The workflow builds outbound payloads that the communication service
understands.  Communication's ``OutboundChannelMessage`` schema is the
contract — the workflow is responsible for constructing it correctly
from the cognition response and the original session context.
"""

from __future__ import annotations

from typing import Any

import structlog

from app.domain.entities.orchestration import (
    ChannelMetadata,
    ChannelType,
    CognitionResponse,
    OutboundChannelMessage,
)

logger = structlog.get_logger(__name__)


def build_outbound_messages(
    cognition_response: CognitionResponse,
) -> list[OutboundChannelMessage]:
    """
    Transform a CognitionResponse into one or more OutboundChannelMessages.
    If ``messages`` is populated each entry becomes a separate message;
    otherwise falls back to the single ``content`` field.
    """
    ctx_meta: dict[str, Any] = {}
    if cognition_response.context:
        ctx_meta = cognition_response.context.metadata

    original = ctx_meta.get("original_metadata", {})

    channel_type_str = original.get("channel_type", "whatsapp")
    try:
        channel_type = ChannelType(channel_type_str)
    except ValueError:
        channel_type = ChannelType.WHATSAPP

    _sender_id = original.get("sender_id")
    if not _sender_id or _sender_id == "unknown":
        _sender_id = None

    recipient_id = _sender_id or (
        cognition_response.context.session_id if cognition_response.context else None
    )

    if not recipient_id:
        logger.error(
            "outbound_transformer.missing_recipient",
            request_id=cognition_response.request_id,
            original_metadata=original,
        )

    channel = ChannelMetadata(
        channel_type=channel_type,
        recipient_id=recipient_id,
    )

    texts = cognition_response.messages or [cognition_response.content]
    base_id = cognition_response.request_id

    inbound_msg_id = original.get("message_id")
    base_meta = {"inbound_message_id": inbound_msg_id} if inbound_msg_id else {}

    return [
        OutboundChannelMessage(
            message_id=f"{base_id}-{i}" if len(texts) > 1 else base_id,
            content=text,
            channel=channel,
            metadata=base_meta,
        )
        for i, text in enumerate(texts)
    ]
