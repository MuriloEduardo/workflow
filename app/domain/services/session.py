from __future__ import annotations

import uuid

import structlog

from app.ports.outbound.session_repository import SessionRepository

logger = structlog.get_logger(__name__)


class SessionInfo:
    """Lightweight result from resolve_session."""

    __slots__ = ("session_id", "thread_id", "is_new")

    def __init__(self, session_id: str, thread_id: str, *, is_new: bool) -> None:
        self.session_id = session_id
        self.thread_id = thread_id
        self.is_new = is_new


class SessionService:
    def __init__(
        self,
        repository: SessionRepository,
        default_timeout: int = 1800,
    ) -> None:
        self._repo = repository
        self._default_timeout = default_timeout

    async def resolve(
        self,
        tenant_id: str,
        channel_type: str,
        sender_id: str,
    ) -> SessionInfo:
        """
        Return an active session for the given user, creating one if needed.
        Expired sessions are marked and a fresh one is created.
        """
        row = await self._repo.get_active(tenant_id, channel_type, sender_id)

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
                )

            # Expired — close and create new
            await self._repo.expire(row["id"])
            logger.info("session.expired", session_id=str(row["id"]))

        thread_id = uuid.uuid4().hex
        session_id = await self._repo.create(
            tenant_id=tenant_id,
            channel_type=channel_type,
            sender_id=sender_id,
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
        )
