"""
Workflow service orchestration entities.
The orchestrator knows all schemas to coordinate between services.
"""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ChannelType(str, Enum):
    WHATSAPP = "whatsapp"
    EMAIL = "email"
    SMS = "sms"
    TELEGRAM = "telegram"
    VOICE = "voice"


class ChannelMetadata(BaseModel):
    model_config = {"extra": "allow"}

    channel_type: ChannelType
    sender_id: str | None = None
    recipient_id: str | None = None
    thread_id: str | None = None
    platform_metadata: dict[str, Any] = Field(default_factory=dict)


class WorkflowContext(BaseModel):
    model_config = {"extra": "allow"}

    session_id: str
    conversation_id: str | None = None
    user_id: str | None = None
    state: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class CognitionRequest(BaseModel):
    request_id: str
    prompt: str
    model: str | None = None
    max_tokens: int = 1024
    temperature: float = 0.7
    context: WorkflowContext | None = None


class CognitionResponse(BaseModel):
    request_id: str
    content: str
    messages: list[str] = []
    model: str
    tokens_used: int | None = None
    error: str | None = None
    context: WorkflowContext | None = None


class InboundChannelMessage(BaseModel):
    model_config = {"extra": "allow"}

    message_id: str
    content: str
    channel: ChannelMetadata
    received_at: str
    raw_payload: dict[str, Any] = Field(default_factory=dict)


class OutboundChannelMessage(BaseModel):
    message_id: str
    content: str
    channel: ChannelMetadata
    priority: int = 0
    scheduled_at: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class WorkflowMessage(BaseModel):
    request_id: str
    inbound_message: InboundChannelMessage | None = None
    cognition_request: CognitionRequest | None = None
    cognition_response: CognitionResponse | None = None
    outbound_message: OutboundChannelMessage | None = None
    context: WorkflowContext


__all__ = [
    "ChannelType",
    "ChannelMetadata",
    "InboundChannelMessage",
    "OutboundChannelMessage",
    "CognitionRequest",
    "CognitionResponse",
    "WorkflowContext",
    "WorkflowMessage",
]
