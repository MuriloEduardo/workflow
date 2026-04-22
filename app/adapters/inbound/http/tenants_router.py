from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel

router = APIRouter(prefix="/tenants", tags=["tenants"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class TenantCreate(BaseModel):
    slug: str
    name: str
    status: str = "active"
    metadata: dict[str, Any] = {}


class TenantUpdate(BaseModel):
    slug: str | None = None
    name: str | None = None
    status: str | None = None
    metadata: dict[str, Any] | None = None


class ContactCreate(BaseModel):
    channel_type: str
    sender_id: str
    name: str | None = None
    metadata: dict[str, Any] = {}


class ContactUpdate(BaseModel):
    name: str | None = None
    metadata: dict[str, Any] | None = None


# ---------------------------------------------------------------------------
# Dependency helper
# ---------------------------------------------------------------------------


def _repo(request: Request):
    return request.app.state.container.tenant_repo


# ---------------------------------------------------------------------------
# Tenant endpoints
# ---------------------------------------------------------------------------


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_tenant(body: TenantCreate, repo=Depends(_repo)):
    tenant_id = await repo.create_tenant(
        slug=body.slug,
        name=body.name,
        status=body.status,
        metadata=body.metadata,
    )
    return await repo.get_tenant(UUID(str(tenant_id)))


@router.get("")
async def list_tenants(repo=Depends(_repo)):
    return await repo.list_tenants()


@router.get("/{tenant_id}")
async def get_tenant(tenant_id: UUID, repo=Depends(_repo)):
    tenant = await repo.get_tenant(tenant_id)
    if tenant is None:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return tenant


@router.patch("/{tenant_id}")
async def update_tenant(tenant_id: UUID, body: TenantUpdate, repo=Depends(_repo)):
    fields = body.model_dump(exclude_none=True)
    tenant = await repo.update_tenant(tenant_id, fields)
    if tenant is None:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return tenant


@router.delete("/{tenant_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tenant(tenant_id: UUID, repo=Depends(_repo)):
    deleted = await repo.delete_tenant(tenant_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Tenant not found")


# ---------------------------------------------------------------------------
# Tenant Contact sub-resource
# ---------------------------------------------------------------------------


@router.post("/{tenant_id}/contacts", status_code=status.HTTP_201_CREATED)
async def create_contact(tenant_id: UUID, body: ContactCreate, repo=Depends(_repo)):
    contact_id = await repo.create_contact(
        tenant_id=tenant_id,
        channel_type=body.channel_type,
        sender_id=body.sender_id,
        name=body.name,
        metadata=body.metadata,
    )
    return await repo.get_contact(UUID(str(contact_id)))


@router.get("/{tenant_id}/contacts")
async def list_contacts(tenant_id: UUID, repo=Depends(_repo)):
    return await repo.list_contacts(tenant_id)


@router.get("/{tenant_id}/contacts/{contact_id}")
async def get_contact(tenant_id: UUID, contact_id: UUID, repo=Depends(_repo)):
    contact = await repo.get_contact(contact_id)
    if contact is None or contact.get("tenant_id") != str(tenant_id):
        raise HTTPException(status_code=404, detail="Contact not found")
    return contact


@router.patch("/{tenant_id}/contacts/{contact_id}")
async def update_contact(
    tenant_id: UUID, contact_id: UUID, body: ContactUpdate, repo=Depends(_repo)
):
    contact = await repo.get_contact(contact_id)
    if contact is None or contact.get("tenant_id") != str(tenant_id):
        raise HTTPException(status_code=404, detail="Contact not found")
    fields = body.model_dump(exclude_none=True)
    updated = await repo.update_contact(contact_id, fields)
    if updated is None:
        raise HTTPException(status_code=404, detail="Contact not found")
    return updated


@router.delete(
    "/{tenant_id}/contacts/{contact_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def delete_contact(tenant_id: UUID, contact_id: UUID, repo=Depends(_repo)):
    contact = await repo.get_contact(contact_id)
    if contact is None or contact.get("tenant_id") != str(tenant_id):
        raise HTTPException(status_code=404, detail="Contact not found")
    await repo.delete_contact(contact_id)
