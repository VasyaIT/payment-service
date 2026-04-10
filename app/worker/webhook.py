import asyncio
import logging

import httpx

logger = logging.getLogger(__name__)

MAX_RETRIES = 3


async def send_with_retry(url: str, payload: dict) -> None:
    for attempt in range(MAX_RETRIES):
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(url, json=payload)
                resp.raise_for_status()
                logger.info("Webhook delivered to %s", url)
                return
        except Exception as e:
            logger.warning(
                "Webhook attempt %d/%d to %s failed: %s",
                attempt + 1,
                MAX_RETRIES,
                url,
                e,
            )
            if attempt < MAX_RETRIES - 1:
                await asyncio.sleep(2**attempt)
    logger.error("Webhook delivery failed after %d attempts: %s", MAX_RETRIES, url)
