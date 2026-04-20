"""
Workflow-specific entities.
Focuses on orchestration and state management.
"""

from pydantic import BaseModel, Field
from typing import Any, Literal


class ConversationState(BaseModel):
    """Current state of a conversation."""

    session_id: str
    conversation_id: str
    user_id: str | None = None
    current_step: str = "initial"
    variables: dict[str, Any] = Field(default_factory=dict)
    history: list[dict[str, Any]] = Field(default_factory=list)
    created_at: str
    updated_at: str


class WorkflowAction(BaseModel):
    """Action to be executed in workflow."""

    action_type: Literal[
        "send_message", "call_cognition", "update_state", "end_conversation"
    ]
    parameters: dict[str, Any] = Field(default_factory=dict)
    priority: int = 0
