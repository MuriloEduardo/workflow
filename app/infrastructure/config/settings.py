from pydantic import AmqpDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    rabbitmq_url: AmqpDsn
    rabbitmq_prefetch_count: int = 10
    rabbitmq_reconnect_delay: float = 5.0
    rabbitmq_max_retries: int = 5

    database_url: str

    debounce_seconds: float = 5.0
    debounce_poll_interval: float = 2.0

    session_timeout_seconds: int = 1800

    http_host: str = "0.0.0.0"
    http_port: int = 80

    app_name: str = "workflow"
    log_level: str = "INFO"
