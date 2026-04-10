import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.outbox import OutboxEvent
from app.models.payment import Payment
from app.schemas.payment import PaymentCreate


class PaymentService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_payment(
        self, data: PaymentCreate, idempotency_key: str
    ) -> Payment:
        result = await self.db.execute(
            select(Payment).where(Payment.idempotency_key == idempotency_key)
        )
        existing = result.scalar_one_or_none()
        if existing:
            return existing

        payment = Payment(
            id=uuid.uuid4(),
            amount=data.amount,
            currency=data.currency,
            description=data.description,
            metadata_=data.metadata,
            idempotency_key=idempotency_key,
            webhook_url=str(data.webhook_url),
        )
        self.db.add(payment)
        await self.db.flush()

        # Outbox event in the same transaction
        outbox_event = OutboxEvent(
            aggregate_id=payment.id,
            event_type="payment.new",
            payload={
                "payment_id": str(payment.id),
                "amount": str(payment.amount),
                "currency": payment.currency.value,
                "description": payment.description,
                "metadata": data.metadata,
                "webhook_url": str(data.webhook_url),
            },
        )
        self.db.add(outbox_event)

        await self.db.commit()
        await self.db.refresh(payment)
        return payment

    async def get_payment(self, payment_id: uuid.UUID) -> Payment | None:
        result = await self.db.execute(
            select(Payment).where(Payment.id == payment_id)
        )
        return result.scalar_one_or_none()
