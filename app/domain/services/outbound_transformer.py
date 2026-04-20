"""
Outbound message transformers.

The workflow builds outbound payloads that the communication service
understands.  Communication's ``OutboundChannelMessage`` schema is the
contract — the workflow is responsible for constructing it correctly
from the cognition response and the original session context.
"""

from __future__ import annotations

from typing import Any

from app.domain.entities.orchestration import (
    ChannelMetadata,
    ChannelType,
    CognitionResponse,
    OutboundChannelMessage,
)


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

    channel = ChannelMetadata(
        channel_type=channel_type,
        recipient_id=(
            (s := original.get("sender_id")) if s and s != "unknown" else None
        )
        or (
            cognition_response.context.session_id
            if cognition_response.context
            else None
        )
        or None,
    )

    texts = cognition_response.messages or [cognition_response.content]
    base_id = cognition_response.request_id

    return [
        OutboundChannelMessage(
            message_id=f"{base_id}-{i}" if len(texts) > 1 else base_id,
            content=text,
            channel=channel,
        )
        for i, text in enumerate(texts)
    ]
