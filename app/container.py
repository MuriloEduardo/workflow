import structlog

from app.adapters.inbound.amqp.consumer import RabbitMQConsumer
from app.adapters.outbound.amqp.publisher import RabbitMQPublisher
from app.adapters.outbound.postgres.execution_repo import PostgresExecutionRepository
from app.adapters.outbound.postgres.pending_message_repo import (
    PostgresPendingMessageRepository,
)
from app.adapters.outbound.postgres.session_repo import PostgresSessionRepository
from app.domain.services.debounce import DebounceService
from app.domain.services.session import SessionService
from app.ports.outbound.execution_repository import ExecutionRepository
from app.infrastructure.config.settings import Settings
from app.infrastructure.database.postgres_connection import PostgresConnection
from app.infrastructure.messaging.rabbitmq_connection import RabbitMQConnection
from app.ports.inbound.message_handler import MessageHandler

logger = structlog.get_logger(__name__)


class Container:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or Settings()
        self._connection: RabbitMQConnection | None = None
        self._publisher: RabbitMQPublisher | None = None
        self._database: PostgresConnection | None = None
        self._debounce_service: DebounceService | None = None
        self._session_service: SessionService | None = None
        self._execution_repo: ExecutionRepository | None = None

    @property
    def connection(self) -> RabbitMQConnection:
        if self._connection is None:
            self._connection = RabbitMQConnection(self.settings)
        return self._connection

    @property
    def publisher(self) -> RabbitMQPublisher:
        if self._publisher is None:
            self._publisher = RabbitMQPublisher(self.connection)
        return self._publisher

    @property
    def database(self) -> PostgresConnection:
        if self._database is None:
            self._database = PostgresConnection(self.settings)
        return self._database

    @property
    def debounce_service(self) -> DebounceService:
        if self._debounce_service is None:
            repo = PostgresPendingMessageRepository(self.database)
            self._debounce_service = DebounceService(
                repository=repo,
                publisher=self.publisher,
                debounce_seconds=self.settings.debounce_seconds,
            )
        return self._debounce_service

    @property
    def execution_repo(self) -> ExecutionRepository:
        if self._execution_repo is None:
            self._execution_repo = PostgresExecutionRepository(self.database)
        return self._execution_repo

    @property
    def session_service(self) -> SessionService:
        if self._session_service is None:
            repo = PostgresSessionRepository(self.database)
            self._session_service = SessionService(
                repository=repo,
                default_timeout=self.settings.session_timeout_seconds,
            )
        return self._session_service

    def consumer(self, handler: MessageHandler) -> RabbitMQConsumer:
        return RabbitMQConsumer(self.connection, handler)

    async def shutdown(self) -> None:
        if self._database:
            await self._database.close()
        if self._connection:
            await self._connection.close()
        logger.info("container.shutdown")
