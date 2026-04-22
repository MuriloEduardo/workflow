from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel

router = APIRouter(prefix="/edges", tags=["edges"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class EdgeCreate(BaseModel):
    workflow_id: UUID | None = None
    source_node_id: UUID
    target_node_id: UUID
    label: str | None = None
    priority: int = 0
    metadata: dict[str, Any] = {}


class EdgeUpdate(BaseModel):
    workflow_id: UUID | None = None
    source_node_id: UUID | None = None
    target_node_id: UUID | None = None
    label: str | None = None
    priority: int | None = None
    metadata: dict[str, Any] | None = None


# ---------------------------------------------------------------------------
# Dependency helper
# ---------------------------------------------------------------------------


def _repo(request: Request):
    return request.app.state.container.edge_repo


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_edge(body: EdgeCreate, repo=Depends(_repo)):
    edge_id = await repo.create(
        workflow_id=body.workflow_id,
        source_node_id=body.source_node_id,
        target_node_id=body.target_node_id,
        label=body.label,
        priority=body.priority,
        metadata=body.metadata,
    )
    return await repo.get(UUID(str(edge_id)))


@router.get("")
async def list_edges(
    source_node_id: UUID | None = None,
    workflow_id: UUID | None = None,
    repo=Depends(_repo),
):
    if source_node_id is not None:
        return await repo.list_by_source_full(source_node_id)
    if workflow_id is not None:
        return await repo.list_by_workflow(workflow_id)
    return await repo.list_all_full()


@router.get("/{edge_id}")
async def get_edge(edge_id: UUID, repo=Depends(_repo)):
    edge = await repo.get_full(edge_id)
    if edge is None:
        raise HTTPException(status_code=404, detail="Edge not found")
    return edge


@router.patch("/{edge_id}")
async def update_edge(edge_id: UUID, body: EdgeUpdate, repo=Depends(_repo)):
    fields = body.model_dump(exclude_none=True)
    edge = await repo.update(edge_id, fields)
    if edge is None:
        raise HTTPException(status_code=404, detail="Edge not found")
    return edge


@router.delete("/{edge_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_edge(edge_id: UUID, repo=Depends(_repo)):
    deleted = await repo.delete(edge_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Edge not found")


# ---------------------------------------------------------------------------
# Edge ↔ Condition sub-resource
# ---------------------------------------------------------------------------


def _condition_repo(request: Request):
    return request.app.state.container.condition_repo


@router.get("/{edge_id}/conditions")
async def list_edge_conditions(
    edge_id: UUID, repo=Depends(_repo), condition_repo=Depends(_condition_repo)
):
    edge = await repo.get(edge_id)
    if edge is None:
        raise HTTPException(status_code=404, detail="Edge not found")
    return await condition_repo.list_by_edge(edge_id)


@router.post(
    "/{edge_id}/conditions/{condition_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def link_edge_condition(
    edge_id: UUID,
    condition_id: UUID,
    repo=Depends(_repo),
    condition_repo=Depends(_condition_repo),
):
    edge = await repo.get(edge_id)
    if edge is None:
        raise HTTPException(status_code=404, detail="Edge not found")
    await condition_repo.link_edge(condition_id, edge_id)


@router.delete(
    "/{edge_id}/conditions/{condition_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def unlink_edge_condition(
    edge_id: UUID,
    condition_id: UUID,
    condition_repo=Depends(_condition_repo),
):
    removed = await condition_repo.unlink_edge(condition_id, edge_id)
    if not removed:
        raise HTTPException(status_code=404, detail="Association not found")
