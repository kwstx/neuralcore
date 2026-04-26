import asyncio
import json
import logging
from typing import Dict, Any, Callable, List
from .embedding_engine import NeuroSemanticEncoder

logger = logging.getLogger("LocalFabric")

class LocalFabric:
    """
    In-memory implementation of the Neuro-Semantic Fabric for local testing.
    Uses asyncio Queues to simulate event propagation without NATS/Kafka.
    """
    def __init__(self):
        self.encoder = NeuroSemanticEncoder()
        self.subscriptions: Dict[str, List[Callable]] = {}
        self._running = False

    async def connect(self):
        logger.info("LocalFabric connected (in-memory mode).")
        self._running = True

    async def publish_event(self, subject: str, payload: dict, graph_context: dict = None):
        """
        Publishes an event locally.
        """
        # Compute embedding (simulated)
        semantic_data = payload.get('description', json.dumps(payload))
        embedding = self.encoder.encode(semantic_data, graph_context=graph_context)
        
        logger.info(f"LocalFabric: Publishing to {subject}")
        
        # Trigger matching subscriptions
        for sub_pattern, handlers in self.subscriptions.items():
            if self._matches(subject, sub_pattern):
                for handler in handlers:
                    # Create a task to run the handler
                    asyncio.create_task(handler(payload, embedding))

    async def subscribe(self, subject: str, callback: Callable, queue_group: str = None):
        """
        Subscribes to a subject.
        """
        if subject not in self.subscriptions:
            self.subscriptions[subject] = []
        self.subscriptions[subject].append(callback)
        logger.info(f"LocalFabric: Subscribed to {subject}")
        
        # Return a handle that can be used to unsubscribe (mocked)
        return {"subject": subject, "handler": callback}

    def _matches(self, subject: str, pattern: str) -> bool:
        # Simple wildcard support: 'agent.*' or 'agent.>'
        if pattern == "*" or pattern == ">":
            return True
        if "*" in pattern:
            prefix = pattern.split("*")[0]
            return subject.startswith(prefix)
        if pattern.endswith(".>"):
            prefix = pattern[:-2]
            return subject.startswith(prefix)
        return subject == pattern

    def shutdown(self):
        self._running = False
        self.subscriptions.clear()
        logger.info("LocalFabric shutdown.")
