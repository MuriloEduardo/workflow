from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel

router = APIRouter(prefix="/workflows", tags=["workflows"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class WorkflowCreate(BaseModel):
    tenant_id: UUID
    name: str
    description: str | None = None
    status: str = "active"
    metadata: dict[str, Any] = {}


class WorkflowUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    status: str | None = None
    metadata: dict[str, Any] | None = None


# ---------------------------------------------------------------------------
# Dependency helper
# ---------------------------------------------------------------------------


def _repo(request: Request):
    return request.app.state.container.workflow_repo


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_workflow(body: WorkflowCreate, repo=Depends(_repo)):
    workflow_id = await repo.create(
        tenant_id=body.tenant_id,
        name=body.name,
        description=body.description,
        status=body.status,
        metadata=body.metadata,
    )
    return await repo.get(UUID(str(workflow_id)))


@router.get("")
async def list_workflows(tenant_id: UUID | None = None, repo=Depends(_repo)):
    if tenant_id is not None:
        return await repo.list_by_tenant(tenant_id)
    return await repo.list_all()


@router.get("/{workflow_id}")
async def get_workflow(workflow_id: UUID, repo=Depends(_repo)):
    workflow = await repo.get(workflow_id)
    if workflow is None:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return workflow


@router.patch("/{workflow_id}")
async def update_workflow(workflow_id: UUID, body: WorkflowUpdate, repo=Depends(_repo)):
    fields = body.model_dump(exclude_none=True)
    workflow = await repo.update(workflow_id, fields)
    if workflow is None:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return workflow


@router.delete("/{workflow_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_workflow(workflow_id: UUID, repo=Depends(_repo)):
    deleted = await repo.delete(workflow_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Workflow not found")
