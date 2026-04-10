from faststream.rabbit import RabbitBroker, RabbitExchange, RabbitQueue, ExchangeType

from app.config import settings

broker = RabbitBroker(settings.rabbitmq_url)

payments_exchange = RabbitExchange("payments", type=ExchangeType.DIRECT, durable=True)
dlx_exchange = RabbitExchange("payments.dlx", type=ExchangeType.DIRECT, durable=True)

payments_queue = RabbitQueue(
    "payments.new",
    routing_key="payments.new",
    durable=True,
    arguments={
        "x-dead-letter-exchange": "payments.dlx",
        "x-dead-letter-routing-key": "payments.dlq",
    },
)

dlq_queue = RabbitQueue(
    "payments.dlq",
    routing_key="payments.dlq",
    durable=True,
)
