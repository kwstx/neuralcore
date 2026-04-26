import asyncio
import logging
from uuid import uuid4
from typing import Dict, Any, Optional
from .fabric.backbone import NeuroSemanticFabric

# Configure logging for the actor system
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("NeuralActor")

class NeuralActor:
    """
    The atomic unit of the NeuralCore actor-model system. 
    Each actor is an autonomous entity that reacts to neuro-semantic events
    and maintains its own internal state, isolated from other actors.
    """
    def __init__(self, actor_id: str = None, fabric: Optional[NeuroSemanticFabric] = None):
        self.actor_id = actor_id or f"nc-actor-{uuid4().hex[:12]}"
        self.fabric = fabric or NeuroSemanticFabric()
        self.is_active = False
        self._subs = []

    async def boot(self):
        """Initializes the actor and its fabric connection."""
        logger.info(f"Booting Actor: {self.actor_id}")
        await self.fabric.connect()
        self.is_active = True
        await self.on_start()

    async def on_start(self):
        """Lifecycle hook: Override to define startup behavior and subscriptions."""
        pass

    async def send(self, subject: str, data: Dict[str, Any], context: Optional[Dict] = None):
        """
        Emits an event into the global Neuro-Semantic Fabric.
        
        Args:
            subject (str): The logical channel for the event.
            data (dict): The message content.
            context (dict, optional): Knowledge graph context for semantic embedding.
        """
        message = {
            "header": {
                "sender": self.actor_id,
                "type": "event"
            },
            "body": data
        }
        await self.fabric.publish_event(subject, message, graph_context=context)

    async def listen(self, subject: str, handler):
        """
        Registers a callback for semantic events matching the subject.
        """
        sub = await self.fabric.subscribe(subject, handler, queue_group=self.actor_id)
        self._subs.append(sub)
        logger.info(f"Actor {self.actor_id} subscribed to {subject}")

    async def shutdown(self):
        """Gracefully terminates the actor's operations."""
        logger.info(f"Shutting down Actor: {self.actor_id}")
        self.is_active = False
        # Fabric cleanup
        self.fabric.shutdown()
