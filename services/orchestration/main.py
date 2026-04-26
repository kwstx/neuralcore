import asyncio
import logging
import sys
import os

# Ensure the library path is accessible
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from libs.actor import NeuralActor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("OrchestrationContext")

class OrchestrationService(NeuralActor):
    """
    DDD Bounded Context: Agent Orchestration.
    Declaratively manages the swarm lifecycle, coordinating between 
    different agents and responding to deployment requests from the K8s Operator.
    """
    def __init__(self, actor_id: str = "nc-orchestrator-01"):
        super().__init__(actor_id=actor_id)
        self.active_swarm = {}

    async def on_start(self):
        logger.info("Initializing Orchestration Context...")
        # Listen for spawn and lifecycle events
        await self.listen("swarm.lifecycle.spawn", self.handle_agent_spawn)
        await self.listen("swarm.lifecycle.terminate", self.handle_agent_terminate)

    async def handle_agent_spawn(self, payload, embedding):
        """
        Coordinates the entry of a new agent into the swarm.
        """
        body = payload.get('body', {})
        agent_id = body.get('agent_id')
        agent_type = body.get('type')
        
        logger.info(f"Orchestrating lifecycle for {agent_type} agent: {agent_id}")
        
        # Register in internal registry
        self.active_swarm[agent_id] = {
            "type": agent_type,
            "status": "initializing",
            "semantic_signature": embedding.tolist()[:5] # Log prefix of signature
        }
        
        # Broadcast readiness across the fabric
        await self.send("swarm.status.active", {
            "agent_id": agent_id,
            "status": "ready"
        })

    async def handle_agent_terminate(self, payload, embedding):
        """Cleanly removes an agent from the swarm registry."""
        agent_id = payload.get('body', {}).get('agent_id')
        if agent_id in self.active_swarm:
            del self.active_swarm[agent_id]
            logger.info(f"Agent {agent_id} removed from active swarm.")

async def main():
    service = OrchestrationService()
    try:
        await service.boot()
        while service.is_active:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        await service.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
