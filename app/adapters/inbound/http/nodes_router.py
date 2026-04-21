from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel

router = APIRouter(prefix="/nodes", tags=["nodes"])


# ---------------------------------------------------------------------------
# Request / Response schemas
# ---------------------------------------------------------------------------


class NodeCreate(BaseModel):
    name: str
    description: str | None = None
    status: str = "active"
    prompt: str | None = None
    response_format: dict[str, Any] | None = None
    properties: dict[str, Any] = {}
    config: dict[str, Any] = {}
    metadata: dict[str, Any] = {}
    order: int | None = None
    priority: int = 0


class NodeUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    status: str | None = None
    prompt: str | None = None
    response_format: dict[str, Any] | None = None
    properties: dict[str, Any] | None = None
    config: dict[str, Any] | None = None
    metadata: dict[str, Any] | None = None
    order: int | None = None
    priority: int | None = None


# ---------------------------------------------------------------------------
# Dependency helper
# ---------------------------------------------------------------------------


def _repo(request: Request):
    return request.app.state.container.node_repo


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_node(body: NodeCreate, repo=Depends(_repo)):
    node_id = await repo.create(
        name=body.name,
        description=body.description,
        status=body.status,
        prompt=body.prompt,
        response_format=body.response_format,
        properties=body.properties,
        config=body.config,
        metadata=body.metadata,
        order=body.order,
        priority=body.priority,
    )
    node = await repo.get(UUID(str(node_id)))
    return node


@router.get("")
async def list_nodes(repo=Depends(_repo)):
    return await repo.list_all()


@router.get("/{node_id}")
async def get_node(node_id: UUID, repo=Depends(_repo)):
    node = await repo.get(node_id)
    if node is None:
        raise HTTPException(status_code=404, detail="Node not found")
    return node


@router.patch("/{node_id}")
async def update_node(node_id: UUID, body: NodeUpdate, repo=Depends(_repo)):
    fields = body.model_dump(exclude_none=True)
    node = await repo.update(node_id, fields)
    if node is None:
        raise HTTPException(status_code=404, detail="Node not found")
    return node


@router.delete("/{node_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_node(node_id: UUID, repo=Depends(_repo)):
    deleted = await repo.delete(node_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Node not found")
