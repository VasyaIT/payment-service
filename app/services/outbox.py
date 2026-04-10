import asyncio
import logging
from datetime import datetime, timezone

from sqlalchemy import select

from app.broker import broker, payments_exchange
from app.database import async_session
from app.models.outbox import OutboxEvent

logger = logging.getLogger(__name__)


class OutboxPublisher:
    def __init__(self, poll_interval: int = 2):
        self.poll_interval = poll_interval
        self._task: asyncio.Task | None = None

    async def start(self) -> None:
        self._task = asyncio.create_task(self._run())

    async def stop(self) -> None:
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

    async def _run(self) -> None:
        while True:
            try:
                await self._publish_pending()
            except Exception as e:
                logger.error("Outbox publisher error: %s", e)
            await asyncio.sleep(self.poll_interval)

    async def _publish_pending(self) -> None:
        async with async_session() as session:
            result = await session.execute(
                select(OutboxEvent)
                .where(OutboxEvent.published.is_(False))
                .limit(100)
                .with_for_update(skip_locked=True)
            )
            events = result.scalars().all()

            for event in events:
                try:
                    await broker.publish(
                        event.payload,
                        exchange=payments_exchange,
                        routing_key="payments.new",
                    )
                    event.published = True
                    event.published_at = datetime.now(timezone.utc)
                except Exception as e:
                    logger.error("Failed to publish event %s: %s", event.id, e)

            await session.commit()
