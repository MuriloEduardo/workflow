from abc import ABC, abstractmethod
from uuid import UUID


class PendingMessageRepository(ABC):
    @abstractmethod
    async def insert(self, group_key: str, content: str, metadata: dict) -> UUID:
        raise NotImplementedError

    @abstractmethod
    async def flush_group(self, group_key: str) -> list[dict]:
        """Atomically fetch and delete all messages for a group. Returns list of {content, metadata}."""
        raise NotImplementedError

    @abstractmethod
    async def get_mature_groups(self, debounce_seconds: float) -> list[str]:
        """Return group_keys where the newest message is older than debounce_seconds."""
        raise NotImplementedError
