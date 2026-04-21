"""
Funnel entities: Tenants, TenantContacts, Nodes, Edges and Executions.

Nodes represent steps of a funnel/workflow definition.
Edges are directed transitions between nodes (source → target).
Executions record cognition call results produced during a node activation.

Cardinality:
  - Tenant  1 ── N  TenantContact
  - Node    1 ── N  Edge  (as source)
  - Node    1 ── N  Edge  (as target)
  - Edge    N ── 1  Node  (source_node_id)
  - Edge    N ── 1  Node  (target_node_id)
  - Node    1 ── N  Execution
  - Tenant  1 ── N  Execution
  - TenantContact 1 ── N  Execution
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
    """A single step inside a funnel definition."""

    id: str
    name: str
    description: str | None = None
    node_type: str = "step"
    status: str = "active"
    config: dict[str, Any] = Field(default_factory=dict)
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
    """

    id: str
    source_node_id: str
    target_node_id: str
    label: str | None = None
    condition: dict[str, Any] | None = None  # optional routing condition
    priority: int = 0
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: str
    updated_at: str


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
