from neo4j import GraphDatabase
from datetime import datetime
from typing import List, Dict, Any, Optional

class Neo4jTemporalGraph:
    """
    Neo4j cluster client for temporal graph persistence where nodes carry
    vector embeddings, confidence scores, and provenance metadata.
    """
    def __init__(self, uri: Optional[str] = None, user: Optional[str] = None, password: Optional[str] = None) -> None:
        self.uri = uri or "bolt://localhost:7687"
        self.driver = GraphDatabase.driver(
            self.uri, auth=(user or "neo4j", password or "password")
        )

    def close(self) -> None:
        self.driver.close()

    def create_unified_node(
        self,
        node_id: str,
        label: str,
        properties: Dict[str, Any],
        embedding: List[float],
        confidence: float,
        provenance: str
    ) -> None:
        """
        Create a node with temporal stamps, embeddings, and epistemic metadata.
        """
        with self.driver.session() as session:
            session.execute_write(
                self._upsert_node_tx,
                node_id, label, properties, embedding, confidence, provenance
            )

    @staticmethod
    def _upsert_node_tx(
        tx: Any, node_id: str, label: str, props: Dict[str, Any], embedding: List[float], confidence: float, provenance: str
    ) -> None:
        query = (
            f"MERGE (n:{label} {{id: $node_id}}) "
            "SET n += $props, "
            "    n.embedding = $embedding, "
            "    n.confidence_score = $confidence, "
            "    n.provenance = $provenance, "
            "    n.last_updated = $timestamp "
            "RETURN n"
        )
        tx.run(
            query,
            node_id=node_id,
            props=props,
            embedding=embedding,
            confidence=confidence,
            provenance=provenance,
            timestamp=datetime.utcnow().isoformat()
        )

    def create_temporal_edge(
        self,
        source_id: str,
        target_id: str,
        rel_type: str,
        temporal_props: Dict[str, Any]
    ) -> None:
        """
        Establish a relationship with explicit temporal stamps.
        """
        with self.driver.session() as session:
            session.execute_write(
                self._create_rel_tx,
                source_id, target_id, rel_type, temporal_props
            )

    @staticmethod
    def _create_rel_tx(tx: Any, source_id: str, target_id: str, rel_type: str, props: Dict[str, Any]) -> None:
        query = (
            "MATCH (a {id: $source_id}), (b {id: $target_id}) "
            f"MERGE (a)-[r:{rel_type}]->(b) "
            "SET r += $props, "
            "    r.created_at = $timestamp "
            "RETURN r"
        )
        tx.run(
            query,
            source_id=source_id,
            target_id=target_id,
            props=props,
            timestamp=datetime.utcnow().isoformat()
        )
