import asyncio
import logging
import sys
import os

# Ensure the library path is accessible
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from libs.actor import NeuralActor
from libs.ontology_service import EpistemicEngine
from libs.utils.types import EmbeddingVector
from typing import Dict, Any, List, Tuple

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("PersistenceContext")

from libs.substrate.manager import HybridSubstrateManager

class PersistenceService(NeuralActor):
    """
    DDD Bounded Context: Knowledge Persistence.
    Isolates the storage and validation of the system's epistemic state.
    Utilizes a Hybrid Knowledge Substrate (Postgres + Neo4j) for scaling.
    """
    def __init__(self, actor_id: str = "nc-persistence-01") -> None:
        super().__init__(actor_id=actor_id)
        # Initialize the OWL 2 DL ontology engine
        self.epistemic_state: EpistemicEngine = EpistemicEngine()
        # Initialize the next-gen hybrid substrate
        self.substrate: HybridSubstrateManager = HybridSubstrateManager()

    async def on_start(self) -> None:
        logger.info("Initializing Persistence Context with Hybrid Substrate...")
        # Provision databases
        self.substrate.postgres.initialize()
        # Subscribe to knowledge ingestion events
        await self.listen("knowledge.ingest", self.handle_knowledge_ingest)
        
    async def handle_knowledge_ingest(self, payload: Dict[str, Any], embedding: EmbeddingVector) -> None:
        """
        Handles incoming triples, ensures epistemic consistency, 
        and updates the substrate (Postgres/pgvector + Neo4j).
        """
        body: Dict[str, Any] = payload.get('body', {})
        triples: List[Tuple[str, str, str]] = body.get('triples', [])
        metadata: Dict[str, Any] = payload.get('header', {})
        
        logger.info(f"Received {len(triples)} triples for substrate ingestion.")
        
        # 1. Update the Epistemic State
        self.epistemic_state.ingest_triples(triples)
        
        # 2. Epistemic Consistency Check
        if self.epistemic_state.check_logical_consistency():
            # 3. Commit to Hybrid Substrate
            # We treat the entire batch as a unified artifact for this demo
            self.substrate.ingest_artifact(
                artifact_type="knowledge_graph",
                source_path=metadata.get("sender", "unknown"),
                metadata={"triples_count": len(triples), **metadata}
            )
            
            logger.info("Epistemic state and substrate storage updated.")
            await self.send("persistence.committed", {
                "result": "success",
                "triples_anchored": len(triples),
                "substrate_status": "synced"
            })
        else:
            logger.warning("Ontological conflict. Rejecting update.")
            await self.send("persistence.conflict", {"error": "logical_inconsistency"})

async def main() -> None:
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
