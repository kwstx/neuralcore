import asyncio
import logging
import sys
import os

# Add the project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from libs.actor import NeuralActor
from libs.fabric.local import LocalFabric
from libs.substrate.persistence.sqlite import SQLiteTemporalGraph

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SmokeTest")

class ReasoningActor(NeuralActor):
    """
    A simple actor for smoke testing that reacts to 'task.assigned' events.
    It simulates 'Reasoning' and then performs an 'Action' by recording 
    a result in the SQLite substrate.
    """
    def __init__(self, actor_id, fabric, substrate):
        super().__init__(actor_id=actor_id, fabric=fabric)
        self.substrate = substrate

    async def on_start(self):
        logger.info(f"ReasoningActor {self.actor_id} started. Waiting for tasks...")
        await self.listen("task.assigned", self.handle_task)

    async def handle_task(self, payload, embedding):
        task_id = payload.get("task_id")
        description = payload.get("description")
        logger.info(f"Actor {self.actor_id} received task {task_id}: {description}")
        
        # 1. Simulate Reasoning
        logger.info(f"Actor {self.actor_id} is reasoning about the task...")
        await asyncio.sleep(0.5) 
        
        # 2. Perform Action (Store result in SQLite)
        logger.info(f"Actor {self.actor_id} performing action: persisting result.")
        self.substrate.create_unified_node(
            node_id=f"result_{task_id}",
            label="ActionResult",
            properties={
                "status": "completed",
                "task_ref": task_id,
                "actor_ref": self.actor_id
            },
            embedding=embedding.tolist() if hasattr(embedding, 'tolist') else [0]*768,
            confidence=0.95,
            provenance="smoke_test"
        )
        
        # 3. Notify completion
        await self.send("task.completed", {"task_id": task_id, "status": "success"})
        logger.info(f"Actor {self.actor_id} completed task {task_id}")

async def run_smoke_test():
    # Initialize Local Components
    fabric = LocalFabric()
    await fabric.connect()
    
    substrate = SQLiteTemporalGraph("smoke_test.db")
    
    # Spawn Agent
    agent = ReasoningActor("smoke-agent-001", fabric, substrate)
    await agent.boot()
    
    # Simulate a task being injected (CLI verification simulation)
    logger.info("Injecting mock context event: task.assigned")
    await fabric.publish_event("task.assigned", {
        "task_id": "T-1000",
        "description": "Verify the local SQLite persistence and reasoning loop."
    })
    
    # Wait for processing
    await asyncio.sleep(2)
    
    # Verify result in SQLite
    result = substrate.get_node("result_T-1000")
    if result:
        logger.info("Verification SUCCESS: Action result found in SQLite!")
        logger.info(f"Result details: {result['properties']}")
    else:
        logger.error("Verification FAILED: Action result NOT found in SQLite.")
    
    # Cleanup
    await agent.shutdown()
    fabric.shutdown()

if __name__ == "__main__":
    asyncio.run(run_smoke_test())
