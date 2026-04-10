import logging

from faststream import FastStream

from app.broker import broker

logging.basicConfig(level=logging.INFO)

# Register subscribers by importing the consumer module
import app.worker.consumer  # noqa: F401

app = FastStream(broker)

if __name__ == "__main__":
    import asyncio
    asyncio.run(app.run())
