from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field

router = APIRouter(prefix="/conditions", tags=["conditions"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class ConditionCreate(BaseModel):
    edge_id: UUID
    operator: str
    compare_value: Any | None = None
    prompt: str | None = None
    logic_operator: str = "AND"
    metadata: dict[str, Any] = {}


class ConditionUpdate(BaseModel):
    operator: str | None = None
    compare_value: Any | None = None
    prompt: str | None = None
    logic_operator: str | None = None
    metadata: dict[str, Any] | None = None
    edge_ids: list[UUID] | None = Field(
        default=None, description="Substitui completamente as edges vinculadas"
    )
    property_ids: list[UUID] | None = Field(
        default=None, description="Substitui completamente as properties vinculadas"
    )


# ---------------------------------------------------------------------------
# Dependency helper
# ---------------------------------------------------------------------------


def _repo(request: Request):
    return request.app.state.container.condition_repo


def _edge_repo(request: Request):
    return request.app.state.container.edge_repo


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_condition(
    body: ConditionCreate,
    repo=Depends(_repo),
    edge_repo=Depends(_edge_repo),
):
    edge = await edge_repo.get(body.edge_id)
    if edge is None:
        raise HTTPException(status_code=404, detail="Edge not found")
    condition_id = await repo.create(
        operator=body.operator,
        compare_value=body.compare_value,
        prompt=body.prompt,
        logic_operator=body.logic_operator,
        metadata=body.metadata,
    )
    await repo.link_edge(UUID(str(condition_id)), body.edge_id)
    return await repo.get(UUID(str(condition_id)))


@router.get("")
async def list_conditions(
    edge_id: UUID | None = None,
    workflow_id: UUID | None = None,
    repo=Depends(_repo),
):
    if edge_id is not None:
        return await repo.list_by_edge(edge_id)
    if workflow_id is not None:
        return await repo.list_by_workflow(workflow_id)
    return await repo.list_all()


@router.get("/{condition_id}")
async def get_condition(condition_id: UUID, repo=Depends(_repo)):
    condition = await repo.get(condition_id)
    if condition is None:
        raise HTTPException(status_code=404, detail="Condition not found")
    return condition


@router.patch("/{condition_id}")
async def update_condition(
    condition_id: UUID, body: ConditionUpdate, repo=Depends(_repo)
):
    fields = body.model_dump(exclude_none=True)
    edge_ids = fields.pop("edge_ids", None)
    property_ids = fields.pop("property_ids", None)

    if fields:
        condition = await repo.update(condition_id, fields)
    else:
        condition = await repo.get(condition_id)

    if condition is None:
        raise HTTPException(status_code=404, detail="Condition not found")

    if edge_ids is not None:
        await repo.sync_edges(condition_id, edge_ids)
    if property_ids is not None:
        await repo.sync_properties(condition_id, property_ids)

    if edge_ids is not None or property_ids is not None:
        condition = await repo.get(condition_id)

    return condition


@router.delete("/{condition_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_condition(condition_id: UUID, repo=Depends(_repo)):
    deleted = await repo.delete(condition_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Condition not found")


# ---------------------------------------------------------------------------
# Condition ↔ Property sub-resource
# ---------------------------------------------------------------------------


@router.get("/{condition_id}/properties")
async def list_condition_properties(condition_id: UUID, repo=Depends(_repo)):
    condition = await repo.get(condition_id)
    if condition is None:
        raise HTTPException(status_code=404, detail="Condition not found")
    return await repo.list_properties(condition_id)


@router.post(
    "/{condition_id}/properties/{property_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def link_condition_property(
    condition_id: UUID, property_id: UUID, repo=Depends(_repo)
):
    condition = await repo.get(condition_id)
    if condition is None:
        raise HTTPException(status_code=404, detail="Condition not found")
    await repo.link_property(condition_id, property_id)


@router.delete(
    "/{condition_id}/properties/{property_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def unlink_condition_property(
    condition_id: UUID, property_id: UUID, repo=Depends(_repo)
):
    removed = await repo.unlink_property(condition_id, property_id)
    if not removed:
        raise HTTPException(status_code=404, detail="Association not found")
