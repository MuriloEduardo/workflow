from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel

router = APIRouter(prefix="/nodes", tags=["nodes"])


# ---------------------------------------------------------------------------
# Request / Response schemas
# ---------------------------------------------------------------------------


class NodeCreate(BaseModel):
    workflow_id: UUID | None = None
    name: str
    description: str | None = None
    status: str = "active"
    prompt: str | None = None
    response_format: dict[str, Any] | None = None
    config: dict[str, Any] = {}
    metadata: dict[str, Any] = {}
    order: int | None = None
    priority: int = 0


class NodeUpdate(BaseModel):
    workflow_id: UUID | None = None
    name: str | None = None
    description: str | None = None
    status: str | None = None
    prompt: str | None = None
    response_format: dict[str, Any] | None = None
    config: dict[str, Any] | None = None
    metadata: dict[str, Any] | None = None
    order: int | None = None
    priority: int | None = None


# ---------------------------------------------------------------------------
# Dependency helpers
# ---------------------------------------------------------------------------


def _repo(request: Request):
    return request.app.state.container.node_repo


def _property_repo(request: Request):
    return request.app.state.container.property_repo


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_node(body: NodeCreate, repo=Depends(_repo)):
    node_id = await repo.create(
        workflow_id=body.workflow_id,
        name=body.name,
        description=body.description,
        status=body.status,
        prompt=body.prompt,
        response_format=body.response_format,
        config=body.config,
        metadata=body.metadata,
        order=body.order,
        priority=body.priority,
    )
    node = await repo.get(UUID(str(node_id)))
    return node


@router.get("")
async def list_nodes(workflow_id: UUID | None = None, repo=Depends(_repo)):
    if workflow_id is not None:
        return await repo.list_by_workflow(workflow_id)
    return await repo.list_all_full()


@router.get("/{node_id}")
async def get_node(node_id: UUID, repo=Depends(_repo)):
    node = await repo.get_full(node_id)
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


# ---------------------------------------------------------------------------
# Node ↔ Property sub-resource
# ---------------------------------------------------------------------------


@router.get("/{node_id}/properties")
async def list_node_properties(
    node_id: UUID, prop_repo=Depends(_property_repo), repo=Depends(_repo)
):
    node = await repo.get(node_id)
    if node is None:
        raise HTTPException(status_code=404, detail="Node not found")
    return await prop_repo.list_by_node(node_id)


@router.post(
    "/{node_id}/properties/{property_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def link_node_property(
    node_id: UUID,
    property_id: UUID,
    prop_repo=Depends(_property_repo),
    repo=Depends(_repo),
):
    node = await repo.get(node_id)
    if node is None:
        raise HTTPException(status_code=404, detail="Node not found")
    await prop_repo.link_to_node(property_id, node_id)


@router.delete(
    "/{node_id}/properties/{property_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def unlink_node_property(
    node_id: UUID,
    property_id: UUID,
    prop_repo=Depends(_property_repo),
):
    removed = await prop_repo.unlink_from_node(property_id, node_id)
    if not removed:
        raise HTTPException(status_code=404, detail="Association not found")
