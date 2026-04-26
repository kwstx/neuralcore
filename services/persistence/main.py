import asyncio
import logging
import sys
import os

# Ensure the library path is accessible
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from libs.actor import NeuralActor
from libs.ontology_service import EpistemicEngine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("PersistenceContext")

class PersistenceService(NeuralActor):
    """
    DDD Bounded Context: Knowledge Persistence.
    Isolates the storage and validation of the system's epistemic state.
    Prevents crosstalk by confining knowledge updates to this context.
    """
    def __init__(self, actor_id: str = "nc-persistence-01"):
        super().__init__(actor_id=actor_id)
        # Initialize the OWL 2 DL ontology engine
        self.epistemic_state = EpistemicEngine()

    async def on_start(self):
        logger.info("Initializing Persistence Context...")
        # Subscribe to knowledge ingestion events with wildcard support
        await self.listen("knowledge.ingest", self.handle_knowledge_ingest)
        
    async def handle_knowledge_ingest(self, payload, embedding):
        """
        Handles incoming triples, ensures epistemic consistency, 
        and updates the long-term knowledge graph.
        """
        # Actor data structure: { "header": {...}, "body": { "triples": [...] } }
        body = payload.get('body', {})
        triples = body.get('triples', [])
        
        logger.info(f"Received {len(triples)} triples for ingestion.")
        
        # 1. Update the Epistemic State (Centralized yet decentralized pub-sub backbone)
        self.epistemic_state.ingest_triples(triples)
        
        # 2. Epistemic Consistency Check (Safety Invariant)
        # Ensures the entire system behaves as a single coherent epistemic entity
        if self.epistemic_state.check_logical_consistency():
            logger.info("Epistemic state verified as consistent.")
            # Acknowledge successful anchoring
            await self.send("persistence.committed", {
                "result": "success",
                "triples_anchored": len(triples),
                "causal_link": payload.get('header', {}).get('sender')
            })
        else:
            logger.warning("Ontological conflict detected. Rejecting update.")
            await self.send("persistence.conflict", {
                "result": "rejected",
                "error": "logical_inconsistency"
            })

async def main():
    service = PersistenceService()
    try:
        await service.boot()
        # Keep the service alive
        while service.is_active:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        await service.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
