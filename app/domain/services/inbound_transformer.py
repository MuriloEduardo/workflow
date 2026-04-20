"""
Inbound message transformers.

The workflow is responsible for understanding raw payloads from each
integration and transforming them into its internal domain model.
Communication stays agnostic — it just forwards raw bytes.
"""

from __future__ import annotations

import json
import uuid
from typing import Any

import structlog

logger = structlog.get_logger(__name__)


class InboundPayload:
    """Normalised result after transforming a raw channel payload."""

    __slots__ = (
        "sender_id",
        "content",
        "channel_type",
        "message_id",
        "tenant_id",
        "raw",
    )

    def __init__(
        self,
        sender_id: str,
        content: str,
        channel_type: str,
        message_id: str | None = None,
        tenant_id: str | None = None,
        raw: dict[str, Any] | None = None,
    ) -> None:
        self.sender_id = sender_id
        self.content = content
        self.channel_type = channel_type
        self.message_id = message_id or uuid.uuid4().hex
        self.tenant_id = tenant_id
        self.raw = raw or {}


def _transform_meta(payload: dict[str, Any]) -> InboundPayload:
    """Extract content from a Meta / WhatsApp Cloud API webhook payload."""

    # Real Meta webhooks have nested entry → changes → value → messages
    for entry in payload.get("entry", []):
        for change in entry.get("changes", []):
            value = change.get("value", {})

            metadata = value.get("metadata", {})
            tenant_id = metadata.get("phone_number_id")

            contacts = value.get("contacts", [])
            wa_id = contacts[0].get("wa_id") if contacts else None

            for msg in value.get("messages", []):
                # Skip non-text messages (reactions, status, etc.)
                content = msg.get("text", {}).get("body", "")
                if not content:
                    continue

                return InboundPayload(
                    sender_id=wa_id or msg.get("from", "unknown"),
                    content=content,
                    channel_type="whatsapp",
                    message_id=msg.get("id"),
                    tenant_id=tenant_id,
                    raw=payload,
                )

    # Fallback: simplified/test payload with a direct "prompt" field
    return InboundPayload(
        sender_id=payload.get("request_id", "unknown"),
        content=payload.get("prompt", ""),
        channel_type="whatsapp",
        message_id=payload.get("request_id", uuid.uuid4().hex),
        raw=payload,
    )


# Map routing-key suffix → transformer function
_TRANSFORMERS: dict[str, Any] = {
    "meta": _transform_meta,
}


def transform_inbound(routing_key: str, raw_bytes: bytes) -> InboundPayload:
    """
    Given a routing key (e.g. ``channel.inbound.meta``) and the raw message
    bytes, return a normalised ``InboundPayload``.
    """
    payload: dict[str, Any] = json.loads(raw_bytes)

    # Last segment of the routing key identifies the integration
    integration = routing_key.rsplit(".", maxsplit=1)[-1]

    transformer = _TRANSFORMERS.get(integration)
    if transformer is None:
        logger.warning(
            "transform.unknown_integration",
            integration=integration,
            routing_key=routing_key,
        )
        # Best-effort: treat the whole payload as a generic message
        return InboundPayload(
            sender_id=payload.get("sender_id", "unknown"),
            content=payload.get("content", payload.get("prompt", json.dumps(payload))),
            channel_type=integration,
            raw=payload,
        )

    return transformer(payload)
