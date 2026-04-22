from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel

router = APIRouter(prefix="/conditions", tags=["conditions"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class ConditionCreate(BaseModel):
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


# ---------------------------------------------------------------------------
# Dependency helper
# ---------------------------------------------------------------------------


def _repo(request: Request):
    return request.app.state.container.condition_repo


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_condition(body: ConditionCreate, repo=Depends(_repo)):
    condition_id = await repo.create(
        operator=body.operator,
        compare_value=body.compare_value,
        prompt=body.prompt,
        logic_operator=body.logic_operator,
        metadata=body.metadata,
    )
    return await repo.get(UUID(str(condition_id)))


@router.get("")
async def list_conditions(edge_id: UUID | None = None, repo=Depends(_repo)):
    if edge_id is not None:
        return await repo.list_by_edge(edge_id)
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
    condition = await repo.update(condition_id, fields)
    if condition is None:
        raise HTTPException(status_code=404, detail="Condition not found")
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
