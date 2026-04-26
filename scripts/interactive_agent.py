import asyncio
import logging
import sys
import os
import json

# Add the project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from libs.actor import NeuralActor
from libs.fabric.local import LocalFabric
from libs.substrate.persistence.sqlite import SQLiteTemporalGraph

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger("InteractiveAgent")

class SimpleActor(NeuralActor):
    """
    An actor that simply prints what it receives and writes to SQLite.
    """
    def __init__(self, actor_id, fabric, substrate):
        super().__init__(actor_id=actor_id, fabric=fabric)
        self.substrate = substrate

    async def on_start(self):
        logger.info(f"Actor {self.actor_id} is online.")
        await self.listen("user.input", self.handle_input)

    async def handle_input(self, payload, embedding):
        text = payload.get("text", "")
        logger.info(f"\n[ACTOR RECEIVED]: {text}")
        
        # Simulate an action
        node_id = f"input_{hash(text)}"
        self.substrate.create_unified_node(
            node_id=node_id,
            label="UserInput",
            properties={"content": text},
            embedding=[0.0]*768, # Dummy embedding for speed
            confidence=1.0,
            provenance="cli_interaction"
        )
        logger.info(f"[ACTOR ACTION]: Persisted to SQLite as {node_id}")

async def main():
    fabric = LocalFabric()
    substrate = SQLiteTemporalGraph("interactive_test.db")
    
    agent = SimpleActor("cli-agent", fabric, substrate)
    await agent.boot()
    
    print("\n--- NeuralCore Interactive CLI ---")
    print("Type message and press Enter to inject 'user.input' event.")
    print("Type 'exit' to quit.\n")
    
    loop = asyncio.get_event_loop()
    
    while True:
        # We use run_in_executor to avoid blocking the event loop with input()
        user_text = await loop.run_in_executor(None, input, "> ")
        
        if user_text.lower() in ['exit', 'quit']:
            break
            
        if not user_text.strip():
            continue
            
        # Inject the event
        await fabric.publish_event("user.input", {"text": user_text})
        
        # Give the actor a moment to process and print
        await asyncio.sleep(0.5)

    await agent.shutdown()
    print("Agent shut down. Goodbye!")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
