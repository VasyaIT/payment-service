import asyncio
import logging
import uuid
from datetime import datetime, timezone

from faststream.rabbit import RabbitMessage
from sqlalchemy import select

from app.broker import broker, payments_queue, payments_exchange, dlq_queue, dlx_exchange
from app.database import async_session
from app.models.payment import Payment, PaymentStatus
from app.worker import gateway, webhook

logger = logging.getLogger(__name__)

MAX_RETRIES = 3


@broker.subscriber(payments_queue, payments_exchange)
async def handle_payment(data: dict, msg: RabbitMessage) -> None:
    headers = msg.headers or {}
    retry_count = int(headers.get("x-retry-count", 0))
    payment_id = data.get("payment_id")

    logger.info("Processing payment %s (attempt %d/%d)", payment_id, retry_count + 1, MAX_RETRIES)

    try:
        async with async_session() as session:
            result = await session.execute(
                select(Payment)
                .where(Payment.id == uuid.UUID(payment_id))
                .with_for_update()
            )
            payment = result.scalar_one_or_none()

            if not payment:
                logger.error("Payment %s not found, skipping", payment_id)
                await msg.ack()
                return

            if payment.status != PaymentStatus.PENDING:
                logger.info("Payment %s already processed (%s), skipping", payment_id, payment.status.value)
                await msg.ack()
                return

            success = await gateway.process_payment()

            payment.status = PaymentStatus.SUCCEEDED if success else PaymentStatus.FAILED
            payment.processed_at = datetime.now(timezone.utc)
            await session.commit()
            final_status = payment.status.value
            processed_at = payment.processed_at.isoformat()

        await webhook.send_with_retry(
            url=data["webhook_url"],
            payload={
                "payment_id": payment_id,
                "status": final_status,
                "processed_at": processed_at,
            },
        )

        await msg.ack()
        logger.info("Payment %s completed: %s", payment_id, final_status)

    except Exception as e:
        logger.error("Error processing payment %s: %s", payment_id, e)
        if retry_count < MAX_RETRIES - 1:
            delay = 2 ** (retry_count + 1)
            logger.info("Retrying payment %s in %ds", payment_id, delay)
            await asyncio.sleep(delay)
            await broker.publish(
                data,
                exchange=payments_exchange,
                routing_key="payments.new",
                headers={"x-retry-count": str(retry_count + 1)},
            )
            await msg.ack()
        else:
            logger.error("Payment %s moved to DLQ after %d attempts", payment_id, MAX_RETRIES)
            await msg.nack(requeue=False)


@broker.subscriber(dlq_queue, dlx_exchange)
async def handle_dlq(data: dict, msg: RabbitMessage) -> None:
    logger.error("DLQ message received: payment_id=%s", data.get("payment_id"))
    await msg.ack()
