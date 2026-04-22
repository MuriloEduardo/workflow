import structlog

from app.adapters.inbound.amqp.consumer import RabbitMQConsumer
from app.adapters.outbound.amqp.publisher import RabbitMQPublisher
from app.adapters.outbound.postgres.condition_repo import PostgresConditionRepository
from app.adapters.outbound.postgres.edge_repo import PostgresEdgeRepository
from app.adapters.outbound.postgres.execution_repo import PostgresExecutionRepository
from app.adapters.outbound.postgres.node_repo import PostgresNodeRepository
from app.adapters.outbound.postgres.pending_message_repo import (
    PostgresPendingMessageRepository,
)
from app.adapters.outbound.postgres.property_repo import PostgresPropertyRepository
from app.adapters.outbound.postgres.session_repo import PostgresSessionRepository
from app.adapters.outbound.postgres.tenant_repo import PostgresTenantRepository
from app.adapters.outbound.postgres.workflow_repo import PostgresWorkflowRepository
from app.domain.services.debounce import DebounceService
from app.domain.services.session import SessionService
from app.ports.outbound.condition_repository import ConditionRepository
from app.ports.outbound.edge_repository import EdgeRepository
from app.ports.outbound.execution_repository import ExecutionRepository
from app.ports.outbound.node_repository import NodeRepository
from app.ports.outbound.property_repository import PropertyRepository
from app.ports.outbound.tenant_repository import TenantRepository
from app.ports.outbound.workflow_repository import WorkflowRepository
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
        self._tenant_repo: TenantRepository | None = None
        self._node_repo: NodeRepository | None = None
        self._edge_repo: EdgeRepository | None = None
        self._property_repo: PropertyRepository | None = None
        self._condition_repo: ConditionRepository | None = None
        self._workflow_repo: WorkflowRepository | None = None

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
                execution_repo=self.execution_repo,
            )
        return self._debounce_service

    @property
    def execution_repo(self) -> ExecutionRepository:
        if self._execution_repo is None:
            self._execution_repo = PostgresExecutionRepository(self.database)
        return self._execution_repo

    @property
    def tenant_repo(self) -> TenantRepository:
        if self._tenant_repo is None:
            self._tenant_repo = PostgresTenantRepository(self.database)
        return self._tenant_repo

    @property
    def session_service(self) -> SessionService:
        if self._session_service is None:
            repo = PostgresSessionRepository(self.database)
            self._session_service = SessionService(
                repository=repo,
                tenant_repository=self.tenant_repo,
                default_timeout=self.settings.session_timeout_seconds,
            )
        return self._session_service

    @property
    def node_repo(self) -> NodeRepository:
        if self._node_repo is None:
            self._node_repo = PostgresNodeRepository(self.database)
        return self._node_repo

    @property
    def edge_repo(self) -> EdgeRepository:
        if self._edge_repo is None:
            self._edge_repo = PostgresEdgeRepository(self.database)
        return self._edge_repo

    @property
    def property_repo(self) -> PropertyRepository:
        if self._property_repo is None:
            self._property_repo = PostgresPropertyRepository(self.database)
        return self._property_repo

    @property
    def condition_repo(self) -> ConditionRepository:
        if self._condition_repo is None:
            self._condition_repo = PostgresConditionRepository(self.database)
        return self._condition_repo

    @property
    def workflow_repo(self) -> WorkflowRepository:
        if self._workflow_repo is None:
            self._workflow_repo = PostgresWorkflowRepository(self.database)
        return self._workflow_repo

    def consumer(self, handler: MessageHandler) -> RabbitMQConsumer:
        return RabbitMQConsumer(self.connection, handler)

    async def shutdown(self) -> None:
        if self._database:
            await self._database.close()
        if self._connection:
            await self._connection.close()
        logger.info("container.shutdown")
