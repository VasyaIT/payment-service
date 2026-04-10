import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.broker import broker, payments_exchange, payments_queue, dlx_exchange, dlq_queue
from app.config import settings
from app.services.outbox import OutboxPublisher
from app.api.v1.router import v1_router

logging.basicConfig(level=logging.INFO)

outbox_publisher = OutboxPublisher(poll_interval=settings.outbox_poll_interval)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await broker.start()
    # Ensure exchanges and queues exist (idempotent declarations)
    await broker.declare_exchange(payments_exchange)
    await broker.declare_exchange(dlx_exchange)
    await broker.declare_queue(payments_queue)
    await broker.declare_queue(dlq_queue)

    await outbox_publisher.start()
    yield
    await outbox_publisher.stop()
    await broker.close()


app = FastAPI(title="Payment Processing Service", lifespan=lifespan)
app.include_router(v1_router)
