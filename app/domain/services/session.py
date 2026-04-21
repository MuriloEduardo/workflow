from __future__ import annotations

import uuid
from uuid import UUID

import structlog

from app.ports.outbound.session_repository import SessionRepository
from app.ports.outbound.tenant_repository import TenantRepository

logger = structlog.get_logger(__name__)


class SessionInfo:
    """Lightweight result from resolve_session."""

    __slots__ = ("session_id", "thread_id", "is_new", "tenant_id", "contact_id")

    def __init__(
        self,
        session_id: str,
        thread_id: str,
        *,
        is_new: bool,
        tenant_id: str,
        contact_id: str,
    ) -> None:
        self.session_id = session_id
        self.thread_id = thread_id
        self.is_new = is_new
        self.tenant_id = tenant_id
        self.contact_id = contact_id


class SessionService:
    def __init__(
        self,
        repository: SessionRepository,
        tenant_repository: TenantRepository,
        default_timeout: int = 1800,
    ) -> None:
        self._repo = repository
        self._tenant_repo = tenant_repository
        self._default_timeout = default_timeout

    async def resolve(
        self,
        tenant_slug: str,
        channel_type: str,
        sender_id: str,
        tenant_name: str | None = None,
    ) -> SessionInfo:
        """
        Resolve (or create) a session for the given sender.

        Upserts the tenant (by slug) and the tenant_contact (by sender_id),
        then looks up the active session keyed on their UUIDs.
        """
        tenant_id: UUID = await self._tenant_repo.upsert_tenant(
            slug=tenant_slug,
            name=tenant_name or tenant_slug,
        )
        contact_id: UUID = await self._tenant_repo.upsert_contact(
            tenant_id=tenant_id,
            channel_type=channel_type,
            sender_id=sender_id,
        )

        row = await self._repo.get_active(tenant_id, channel_type, contact_id)

        if row is not None:
            idle = row["idle_seconds"]
            timeout = row["timeout_seconds"]

            if idle < timeout:
                await self._repo.touch(row["id"])
                logger.debug(
                    "session.reused",
                    session_id=str(row["id"]),
                    idle_seconds=round(idle),
                )
                return SessionInfo(
                    session_id=str(row["id"]),
                    thread_id=row["thread_id"],
                    is_new=False,
                    tenant_id=str(tenant_id),
                    contact_id=str(contact_id),
                )

            await self._repo.expire(row["id"])
            logger.info("session.expired", session_id=str(row["id"]))

        thread_id = uuid.uuid4().hex
        session_id = await self._repo.create(
            tenant_id=tenant_id,
            channel_type=channel_type,
            contact_id=contact_id,
            thread_id=thread_id,
            timeout_seconds=self._default_timeout,
        )
        logger.info(
            "session.created",
            session_id=str(session_id),
            thread_id=thread_id,
        )
        return SessionInfo(
            session_id=str(session_id),
            thread_id=thread_id,
            is_new=True,
            tenant_id=str(tenant_id),
            contact_id=str(contact_id),
        )
