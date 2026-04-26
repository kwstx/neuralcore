import os
from typing import List, Optional, Dict, Any, cast
from sqlalchemy import create_engine, Column, Integer, String, JSON, DateTime, Float, text
from sqlalchemy.orm import sessionmaker, Mapped, mapped_column, DeclarativeBase
from pgvector.sqlalchemy import Vector
from datetime import datetime

class Base(DeclarativeBase):
    pass

class DenseKnowledgeNode(Base):
    """
    PostgreSQL representation for dense vector storage.
    Optimized for similarity search using pgvector.
    """
    __tablename__ = 'dense_knowledge'

    id: Mapped[str] = mapped_column(String, primary_key=True)
    embedding: Mapped[Any] = mapped_column(Vector(768))  # 768-dimensional embeddings
    content_raw: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)       # Original payload
    metadata_props: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)    # Typed properties
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class PostgresKnowledgeStore:
    def __init__(self, connection_string: Optional[str] = None) -> None:
        self.connection_string: str = connection_string or os.getenv(
            "POSTGRES_DSN", "postgresql://neuro:core@localhost:5432/neuralcore"
        ) or "postgresql://neuro:core@localhost:5432/neuralcore"
        self.engine = create_engine(self.connection_string)
        self.Session = sessionmaker(bind=self.engine)

    def initialize(self) -> None:
        """Provision the database and enable pgvector."""
        with self.engine.connect() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            conn.commit()
        Base.metadata.create_all(self.engine)

    def upsert_node(self, node_id: str, vector: List[float], metadata: Dict[str, Any]) -> None:
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

    def semantic_search(self, query_vector: List[float], limit: int = 10) -> List[Any]:
        session = self.Session()
        try:
            results = session.query(DenseKnowledgeNode).order_by(
                DenseKnowledgeNode.embedding.cosine_distance(query_vector)
            ).limit(limit).all()
            return results
        finally:
            session.close()
