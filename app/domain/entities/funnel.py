"""
Funnel entities: Tenants, TenantContacts, Nodes, Edges and Executions.

Nodes represent steps of a funnel/workflow definition.
Edges are directed transitions between nodes (source → target).
Executions record cognition call results produced during a node activation.

Cardinality:
  - Tenant        1 ── N  TenantContact
  - Node          1 ── N  Edge  (as source)
  - Node          1 ── N  Edge  (as target)
  - Edge          N ── 1  Node  (source_node_id)
  - Edge          N ── 1  Node  (target_node_id)
  - Node          1 ── N  Execution
  - Tenant        1 ── N  Execution
  - TenantContact 1 ── N  Execution
  - Edge          N ── N  Condition  (via EdgeCondition)
  - Node          N ── N  Property   (via NodeProperty)
  - Condition     N ── N  Property   (via ConditionProperty)
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Tenant
# ---------------------------------------------------------------------------


class Tenant(BaseModel):
    id: str
    name: str
    slug: str
    status: str = "active"
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: str
    updated_at: str


# ---------------------------------------------------------------------------
# TenantContact
# ---------------------------------------------------------------------------


class TenantContact(BaseModel):
    """One contact per channel identity (sender_id + channel_type) per tenant."""

    id: str
    tenant_id: str
    channel_type: str
    sender_id: str
    name: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: str
    updated_at: str


# ---------------------------------------------------------------------------
# Node
# ---------------------------------------------------------------------------


class Node(BaseModel):
    """
    A single step inside a funnel definition.

    Represents a state/action in the workflow where cognition is called or decisions are made.
    Each node can have properties (schema fields) that define what data to extract.
    Supports different node types (extraction, evaluation, writing, etc.).
    """

    id: str
    name: str
    description: str | None = None
    status: str = "active"

    # Core prompt/instruction for this node
    prompt: str | None = None

    # Configuration for LLM response format
    response_format: dict[str, Any] | None = None  # tool calling schema

    # Additional node configuration
    config: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)

    # Order/priority for execution
    order: int | None = None
    priority: int = 0

    created_at: str
    updated_at: str


# ---------------------------------------------------------------------------
# Edge
# ---------------------------------------------------------------------------


class Edge(BaseModel):
    """
    A directed transition between two nodes.

    One source node may have many outgoing edges.
    Each edge has exactly one source and one target node.

    Edges can have conditions that determine whether the transition should be taken.
    Multiple edges from the same source are evaluated by priority (lower = higher priority).
    """

    id: str
    source_node_id: str
    target_node_id: str

    # Human-readable label/description
    label: str | None = None

    # Routing logic
    condition: dict[str, Any] | None = None  # optional routing condition/rules
    condition_prompt: str | None = None  # natural language condition for LLM evaluation

    # Priority for edge evaluation (lower number = higher priority)
    priority: int = 0

    # Additional edge configuration
    metadata: dict[str, Any] = Field(default_factory=dict)

    created_at: str
    updated_at: str


# ---------------------------------------------------------------------------
# Property (Schema field for extraction nodes)
# ---------------------------------------------------------------------------


class Property(BaseModel):
    """
    Represents a property/field that can be extracted at a node.

    Used in extraction nodes to define the schema of data to collect.
    Properties can be referenced in conditions for edge evaluation.
    """

    id: str
    name: str
    type: str  # string, integer, boolean, array, object, etc.
    description: str | None = None

    # Validation rules
    required: bool = False
    default_value: Any | None = None

    # JSON schema properties
    schema: dict[str, Any] = Field(default_factory=dict)

    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: str
    updated_at: str


# ---------------------------------------------------------------------------
# Condition (Detailed condition logic for edges)
# ---------------------------------------------------------------------------


class Condition(BaseModel):
    """
    Represents a condition that must be satisfied for an edge to be taken.

    Conditions can reference properties and use operators to evaluate values.
    Multiple conditions on an edge can be combined with AND/OR logic.
    """

    id: str

    # Condition logic
    operator: str  # eq, neq, contains, gt, lt, exists, is_null, etc.
    compare_value: Any | None = None  # value to compare against

    # Natural language condition (for LLM evaluation)
    prompt: str | None = None

    # Combining multiple conditions
    logic_operator: str = "AND"  # AND, OR

    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: str
    updated_at: str


# ---------------------------------------------------------------------------
# Junction: Edge ↔ Condition
# ---------------------------------------------------------------------------


class EdgeCondition(BaseModel):
    """Association between an edge and a condition (N:N)."""

    edge_id: str
    condition_id: str


# ---------------------------------------------------------------------------
# Junction: Node ↔ Property
# ---------------------------------------------------------------------------


class NodeProperty(BaseModel):
    """Association between a node and a property (N:N)."""

    node_id: str
    property_id: str


# ---------------------------------------------------------------------------
# Junction: Condition ↔ Property
# ---------------------------------------------------------------------------


class ConditionProperty(BaseModel):
    """Association between a condition and a property (N:N)."""

    condition_id: str
    property_id: str


# ---------------------------------------------------------------------------
# Execution
# ---------------------------------------------------------------------------


class Execution(BaseModel):
    """
    Records a cognition call result triggered during a node activation.

    Stores inputs sent to cognition and the response obtained,
    together with observability data (model, tokens, latency).
    """

    id: str
    request_id: str
    node_id: str | None = None
    tenant_id: str | None = None
    contact_id: str | None = None
    session_id: str | None = None
    status: str = "pending"

    # Cognition input / output
    prompt: str | None = None
    response: str | None = None
    model: str | None = None

    # Observability
    input_tokens: int | None = None
    output_tokens: int | None = None
    total_tokens: int | None = None
    latency_ms: int | None = None

    error: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: str
    updated_at: str
