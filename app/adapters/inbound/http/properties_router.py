from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel

router = APIRouter(prefix="/properties", tags=["properties"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class PropertyCreate(BaseModel):
    node_id: UUID
    name: str
    type: str
    description: str | None = None
    required: bool = False
    default_value: Any | None = None
    json_schema: dict[str, Any] = {}
    metadata: dict[str, Any] = {}


class PropertyUpdate(BaseModel):
    name: str | None = None
    type: str | None = None
    description: str | None = None
    required: bool | None = None
    default_value: Any | None = None
    json_schema: dict[str, Any] | None = None
    metadata: dict[str, Any] | None = None


# ---------------------------------------------------------------------------
# Dependency helper
# ---------------------------------------------------------------------------


def _repo(request: Request):
    return request.app.state.container.property_repo


def _node_repo(request: Request):
    return request.app.state.container.node_repo


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_property(
    body: PropertyCreate,
    repo=Depends(_repo),
    node_repo=Depends(_node_repo),
):
    node = await node_repo.get(body.node_id)
    if node is None:
        raise HTTPException(status_code=404, detail="Node not found")
    prop_id = await repo.create(
        name=body.name,
        type=body.type,
        description=body.description,
        required=body.required,
        default_value=body.default_value,
        schema=body.json_schema,
        metadata=body.metadata,
    )
    await repo.link_to_node(UUID(str(prop_id)), body.node_id)
    return await repo.get(UUID(str(prop_id)))


@router.get("")
async def list_properties(workflow_id: UUID | None = None, repo=Depends(_repo)):
    if workflow_id is not None:
        return await repo.list_by_workflow(workflow_id)
    return await repo.list_all()


@router.get("/{property_id}")
async def get_property(property_id: UUID, repo=Depends(_repo)):
    prop = await repo.get(property_id)
    if prop is None:
        raise HTTPException(status_code=404, detail="Property not found")
    return prop


@router.patch("/{property_id}")
async def update_property(property_id: UUID, body: PropertyUpdate, repo=Depends(_repo)):
    fields = body.model_dump(exclude_none=True)
    if "json_schema" in fields:
        fields["schema"] = fields.pop("json_schema")
    prop = await repo.update(property_id, fields)
    if prop is None:
        raise HTTPException(status_code=404, detail="Property not found")
    return prop


@router.delete("/{property_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_property(property_id: UUID, repo=Depends(_repo)):
    deleted = await repo.delete(property_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Property not found")
