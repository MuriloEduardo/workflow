from app.adapters.inbound.amqp.handlers.cognition_response_handler import (
    CognitionResponseHandler,
)
from app.container import Container
from app.workers import worker


@worker(
    name="cognition_response",
    queue="workflow.cognition.response",
    exchange="cognition.exchange",
    routing_key="cognition.response",
)
def create_cognition_response_handler(
    container: Container,
) -> CognitionResponseHandler:
    return CognitionResponseHandler(publisher=container.publisher)
