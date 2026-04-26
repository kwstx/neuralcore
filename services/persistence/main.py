import os
import asyncio
from nats.aio.client import Client as NATS
from nats.aio.errors import ErrTimeout, ErrNoServers
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("PersistenceService")

class PersistenceService:
    def __init__(self):
        self.nc = NATS()
        self.nats_url = os.getenv("NATS_URL", "nats://localhost:4222")

    async def connect(self):
        try:
            await self.nc.connect(self.nats_url)
            logger.info(f"Connected to NATS at {self.nats_url}")
            self.js = self.nc.jetstream()
            
            # Ensure the stream exists for persistence
            await self.js.add_stream(name="NEURALCORE_EVENTS", subjects=["nc.events.*"])
            logger.info("NeuralCore Event Stream initialized.")
        except Exception as e:
            logger.error(f"Failed to connect to NATS: {e}")

    async def process_event(self, msg):
        subject = msg.subject
        data = msg.data
        logger.info(f"Received event on {subject}: {len(data)} bytes")
        # TODO: Implement event sourcing logic and Knowledge Graph projection
        await msg.ack()

    async def run(self):
        await self.connect()
        # Create a pull subscription for at-least-once delivery guarantees
        self.sub = await self.js.pull_subscribe("nc.events.>", "persistence-worker")
        
        while True:
            try:
                msgs = await self.sub.fetch(10, timeout=1)
                for msg in msgs:
                    await self.process_event(msg)
            except ErrTimeout:
                continue
            except Exception as e:
                logger.error(f"Error in event loop: {e}")
                await asyncio.sleep(1)

if __name__ == "__main__":
    service = PersistenceService()
    asyncio.run(service.run())
