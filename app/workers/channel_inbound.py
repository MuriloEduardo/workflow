from app.adapters.inbound.amqp.handlers.channel_inbound_handler import (
    ChannelInboundHandler,
)
from app.container import Container
from app.workers import worker


@worker(
    name="channel_inbound",
    queue="workflow.channel.inbound",
    exchange="communication.channel.inbound",
    routing_key="channel.inbound.meta",
)
def create_channel_inbound_handler(container: Container) -> ChannelInboundHandler:
    return ChannelInboundHandler(
        debounce=container.debounce_service,
        session=container.session_service,
    )
