import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Any, Optional

class SQLiteTemporalGraph:
    """
    Local SQLite implementation of temporal graph persistence for smoke tests.
    Stores nodes and edges in a local .db file.
    """
    def __init__(self, db_path: str = "neuralcore_local.db") -> None:
        self.db_path = db_path
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _init_db(self) -> None:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # Table for nodes
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS nodes (
                    id TEXT PRIMARY KEY,
                    label TEXT,
                    properties TEXT,
                    embedding BLOB,
                    confidence_score REAL,
                    provenance TEXT,
                    last_updated TEXT
                )
            ''')
            # Table for edges
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS edges (
                    source_id TEXT,
                    target_id TEXT,
                    rel_type TEXT,
                    properties TEXT,
                    created_at TEXT,
                    FOREIGN KEY(source_id) REFERENCES nodes(id),
                    FOREIGN KEY(target_id) REFERENCES nodes(id)
                )
            ''')
            conn.commit()

    def create_unified_node(
        self,
        node_id: str,
        label: str,
        properties: Dict[str, Any],
        embedding: List[float],
        confidence: float,
        provenance: str
    ) -> None:
        timestamp = datetime.utcnow().isoformat()
        props_json = json.dumps(properties)
        embedding_blob = json.dumps(embedding).encode('utf-8')
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO nodes 
                (id, label, properties, embedding, confidence_score, provenance, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (node_id, label, props_json, embedding_blob, confidence, provenance, timestamp))
            conn.commit()

    def create_temporal_edge(
        self,
        source_id: str,
        target_id: str,
        rel_type: str,
        temporal_props: Dict[str, Any]
    ) -> None:
        timestamp = datetime.utcnow().isoformat()
        props_json = json.dumps(temporal_props)
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO edges (source_id, target_id, rel_type, properties, created_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (source_id, target_id, rel_type, props_json, timestamp))
            conn.commit()

    def get_node(self, node_id: str) -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM nodes WHERE id = ?', (node_id,))
            row = cursor.fetchone()
            if row:
                return {
                    "id": row[0],
                    "label": row[1],
                    "properties": json.loads(row[2]),
                    "embedding": json.loads(row[3].decode('utf-8')),
                    "confidence": row[4],
                    "provenance": row[5],
                    "last_updated": row[6]
                }
        return None

    def close(self) -> None:
        pass
