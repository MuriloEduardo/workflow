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


def _extract_meta_content(msg: dict[str, Any]) -> str:
    """Extract displayable content from any Meta message type."""
    msg_type = msg.get("type", "text")

    if msg_type == "text":
        return (msg.get("text") or {}).get("body", "")

    if msg_type == "location":
        loc = msg.get("location") or {}
        parts = [f"📍 {loc.get('latitude')},{loc.get('longitude')}"]
        if loc.get("name"):
            parts.append(loc["name"])
        if loc.get("address"):
            parts.append(loc["address"])
        return " — ".join(parts)

    # Media types: image, video, audio, document, sticker
    media = msg.get(msg_type) or {}
    if media.get("caption"):
        return media["caption"]

    return f"[{msg_type}]"


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
                msg_type = msg.get("type", "text")

                # Skip reactions and status updates
                if msg_type in ("reaction", "unsupported"):
                    continue

                content = _extract_meta_content(msg)
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
