import asyncio
import random


async def process_payment() -> bool:
    """Emulates external payment gateway: 2-5s delay, 90% success rate."""
    delay = random.uniform(2, 5)
    await asyncio.sleep(delay)
    return random.random() < 0.9
