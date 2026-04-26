import os
from typing import List, Optional, Dict, Any
from sqlalchemy import create_engine, Column, Integer, String, JSON, DateTime, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from pgvector.sqlalchemy import Vector
from datetime import datetime

Base = declarative_base()

class DenseKnowledgeNode(Base):
    """
    PostgreSQL representation for dense vector storage.
    Optimized for similarity search using pgvector.
    """
    __tablename__ = 'dense_knowledge'

    id = Column(String, primary_key=True)
    embedding = Column(Vector(768))  # 768-dimensional embeddings
    content_raw = Column(JSON)       # Original payload
    metadata_props = Column(JSON)    # Typed properties
    created_at = Column(DateTime, default=datetime.utcnow)

class PostgresKnowledgeStore:
    def __init__(self, connection_string: str = None):
        self.connection_string = connection_string or os.getenv(
            "POSTGRES_DSN", "postgresql://neuro:core@localhost:5432/neuralcore"
        )
        self.engine = create_engine(self.connection_string)
        self.Session = sessionmaker(bind=self.engine)

    def initialize(self):
        """Provision the database and enable pgvector."""
        with self.engine.connect() as conn:
            conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
        Base.metadata.create_all(self.engine)

    def upsert_node(self, node_id: str, vector: List[float], metadata: Dict[str, Any]):
        session = self.Session()
        try:
            node = DenseKnowledgeNode(
                id=node_id,
                embedding=vector,
                metadata_props=metadata
            )
            session.merge(node)
            session.commit()
        finally:
            session.close()

    def semantic_search(self, query_vector: List[float], limit: int = 10):
        session = self.Session()
        try:
            results = session.query(DenseKnowledgeNode).order_by(
                DenseKnowledgeNode.embedding.cosine_distance(query_vector)
            ).limit(limit).all()
            return results
        finally:
            session.close()
